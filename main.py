import io
import os
import re
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import pdfplumber

from tailor import analyze_and_tailor, validate_tailored_cv, load_cv
from pdf_generator import generate_pdf
import db

# Load environment variables from .env into os.environ so the Groq client
# can find GROQ_API_KEY automatically.
load_dotenv()

app = FastAPI(title="JD-CV Matcher")

# The Next.js frontend runs on its own dev server (port 3000), so the browser
# treats it as a different origin and blocks its calls to this API by default.
# Allow that one origin explicitly — never "*", which would let any site call this.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_methods=["*"],
    allow_headers=["*"],
)

OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)

db.init_db()


# Request body shape for POST /analyze.
class AnalyzeRequest(BaseModel):
    job_description: str
    company_name: str
    cv_text: str | None = None


# Request body shape for PATCH /applications/{id}.
class StatusUpdate(BaseModel):
    status: str


# Strips characters illegal in filenames on Windows and macOS.
def sanitize_filename(name: str) -> str:
    return re.sub(r'[^a-zA-Z0-9_\- ]', '', name).strip().replace(" ", "_")


# Parses CV text from an uploaded file (PDF, TXT, etc.)
async def extract_text_from_file(file: UploadFile) -> str | None:
    if not file:
        return None

    try:
        content = await file.read()
        filename = file.filename.lower()

        if filename.endswith(".pdf"):
            with pdfplumber.open(io.BytesIO(content)) as pdf:
                text = "\n".join(page.extract_text() or "" for page in pdf.pages)
                return text.strip() if text.strip() else None
        else:
            return content.decode("utf-8").strip()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not parse file: {str(e)}")


# POST /analyze — main endpoint.
# Step 1: tailor the CV via Groq.
# Step 2: validate the tailored CV for honesty via a second Groq call.
# Step 3: generate an ATS-friendly PDF.
# Step 4: save both .txt and .pdf to the output folder, and record the run in the database.
# Step 5: return full analysis + pdf download URL to the frontend.
@app.post("/analyze")
async def analyze(
    job_description: str = Form(...),
    company_name: str = Form(...),
    file: UploadFile = File(None),
):
    if not job_description.strip():
        raise HTTPException(status_code=400, detail="Job description cannot be empty.")
    if not company_name.strip():
        raise HTTPException(status_code=400, detail="Company name cannot be empty.")

    # Use uploaded file if provided, otherwise fall back to my_cv.txt
    cv_to_use = None

    if file: # Get CV text (either from uploaded file)
        cv_to_use = await extract_text_from_file(file)
    elif Path("my_cv.txt").exists(): # Get CV text (else from file on disk)
        cv_to_use = load_cv()
    else:
        raise HTTPException(status_code=400, detail="No CV provided and my_cv.txt not found.")

    api_key = os.getenv("GROQ_API_KEY", "")
    if not api_key or api_key == "your_groq_api_key_here":
        raise HTTPException(status_code=500, detail="GROQ_API_KEY is not set in your .env file.")

    # Step 1 — tailor
    result = analyze_and_tailor(job_description, cv_text=cv_to_use)

    # Step 2 — validate
    original_cv = cv_to_use
    tailored_cv = result.get("tailored_cv", "")
    try:
        validation = validate_tailored_cv(original_cv, tailored_cv)
    except Exception:
        validation = {
            "verdict": "review",
            "flags": [],
            "summary": "Automated validation could not complete — please review manually."
        }
    result["validation"] = validation

    # Step 3 & 4 — save .txt and generate .pdf
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = sanitize_filename(company_name)
    base_name = f"{safe_name}_{timestamp}"

    txt_path = OUTPUT_DIR / f"{base_name}.txt"
    pdf_path = OUTPUT_DIR / f"{base_name}.pdf"

    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(f"SAFETY CHECK: {validation.get('verdict', '?').upper()}\n")
        if validation.get("flags"):
            for flag in validation["flags"]:
                f.write(f"  ⚠ {flag.get('type')}: {flag.get('detail')}\n")
        f.write("\n")
        f.write(f"COVER LETTER\n{'=' * 60}\n")
        f.write(result.get("cover_letter", "") + "\n\n")
        f.write(f"TAILORED CV\n{'=' * 60}\n")
        f.write(tailored_cv)

    # Generate the ATS-friendly PDF
    try:
        generate_pdf(tailored_cv, str(pdf_path))
        result["pdf_filename"] = f"{base_name}.pdf"
    except Exception as e:
        import traceback
        traceback.print_exc()   # prints full error to terminal so we can see it
        result["pdf_filename"] = None
        result["pdf_error"] = str(e)

    result["saved_as"] = f"{base_name}.txt"
    result["application_id"] = db.save_application(
        company_name.strip(), job_description, result
    )
    return result


# GET /applications — dashboard data: summary rows (newest first) plus stats.
@app.get("/applications")
def list_applications():
    return {"stats": db.get_stats(), "applications": db.list_applications()}


# GET /applications/{id} — one stored application including its full analysis result.
@app.get("/applications/{app_id}")
def get_application(app_id: int):
    application = db.get_application(app_id)
    if application is None:
        raise HTTPException(status_code=404, detail="Application not found.")
    return application


# PATCH /applications/{id} — move an application through the pipeline (applied, interview, ...).
@app.patch("/applications/{app_id}")
def update_application_status(app_id: int, body: StatusUpdate):
    if body.status not in db.STATUSES:
        raise HTTPException(status_code=400, detail=f"Status must be one of: {', '.join(db.STATUSES)}")
    if not db.update_status(app_id, body.status):
        raise HTTPException(status_code=404, detail="Application not found.")
    return {"id": app_id, "status": body.status}


# DELETE /applications/{id} — removes the record (generated files in output/ are kept).
@app.delete("/applications/{app_id}")
def delete_application(app_id: int):
    if not db.delete_application(app_id):
        raise HTTPException(status_code=404, detail="Application not found.")
    return {"deleted": app_id}


# GET /download-pdf/{filename} — streams the generated PDF back to the browser
# as a file download. Equivalent to returning a FileStreamResult in ASP.NET Core.
@app.get("/download-pdf/{filename}")
async def download_pdf(filename: str):
    # Security: strip any path traversal characters so nobody can escape the output folder
    safe = Path(filename).name
    file_path = OUTPUT_DIR / safe

    if not file_path.exists() or file_path.suffix != ".pdf":
        raise HTTPException(status_code=404, detail="PDF not found.")

    return FileResponse(
        path=str(file_path),
        media_type="application/pdf",
        filename=safe,
        headers={"Content-Disposition": f'attachment; filename="{safe}"'}
    )


# GET / — serves the single-page frontend.
@app.get("/")
async def root():
    return FileResponse("static/index.html")


app.mount("/static", StaticFiles(directory="static"), name="static")
