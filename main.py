import os
import re
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

from tailor import analyze_and_tailor, validate_tailored_cv, load_cv
from pdf_generator import generate_pdf

# Load environment variables from .env into os.environ so the Groq client
# can find GROQ_API_KEY automatically.
load_dotenv()

app = FastAPI(title="JD-CV Matcher")

OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)


# Request body shape for POST /analyze.
class AnalyzeRequest(BaseModel):
    job_description: str
    company_name: str


# Strips characters illegal in filenames on Windows and macOS.
def sanitize_filename(name: str) -> str:
    return re.sub(r'[^a-zA-Z0-9_\- ]', '', name).strip().replace(" ", "_")


# POST /analyze — main endpoint.
# Step 1: tailor the CV via Groq.
# Step 2: validate the tailored CV for honesty via a second Groq call.
# Step 3: generate an ATS-friendly PDF.
# Step 4: save both .txt and .pdf to the output folder.
# Step 5: return full analysis + pdf download URL to the frontend.
@app.post("/analyze")
async def analyze(request: AnalyzeRequest):
    if not request.job_description.strip():
        raise HTTPException(status_code=400, detail="Job description cannot be empty.")
    if not request.company_name.strip():
        raise HTTPException(status_code=400, detail="Company name cannot be empty.")
    if not Path("my_cv.txt").exists():
        raise HTTPException(status_code=500, detail="my_cv.txt not found. Add your CV to the project folder.")

    api_key = os.getenv("GROQ_API_KEY", "")
    if not api_key or api_key == "your_groq_api_key_here":
        raise HTTPException(status_code=500, detail="GROQ_API_KEY is not set in your .env file.")

    # Step 1 — tailor
    result = analyze_and_tailor(request.job_description)

    # Step 2 — validate
    original_cv = load_cv()
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
    safe_name = sanitize_filename(request.company_name)
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
    return result


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
