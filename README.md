# JD-CV Matcher

A web application that tailors your CV to specific job descriptions using AI (Groq API). Built with **FastAPI** (backend) and **Vanilla JS** (frontend), it analyzes job postings, generates personalized cover letters, validates honesty, and produces ATS-friendly PDFs.

---

## Features

- **AI-Powered CV Tailoring**: Automatically rewrite your CV to match job descriptions using Groq LLM
- **Intelligent Skill Matching**: Highlights matched and missing keywords from the job posting
- **Cover Letter Generation**: Creates tailored, professional cover letters
- **Honesty Validation**: AI validates that tailored content is honest and doesn't misrepresent your experience
- **ATS-Friendly PDF Export**: Generates German-format CVs optimized for applicant tracking systems
- **Match Score**: Real-time matching score (0-100) between your CV and job description
- **Learning Roadmap**: Suggests concrete projects to build missing skills
- **Web Interface**: Responsive UI for easy interaction

---

## App Flow

```
User Input (Job Description + Company Name)
        ↓
    [Step 1] Analyze & Tailor CV via Groq
        ├─ Load your CV (my_cv.txt)
        ├─ Create system prompt (German market, C#→Python/AI/DevOps transition)
        ├─ Call Groq LLM to rewrite CV & generate cover letter
        └─ Return: tailored_cv, cover_letter, match_score, learning roadmap
        ↓
    [Step 2] Validate Tailored Content (Honesty Check)
        ├─ Compare original CV with tailored version
        ├─ Detect overstatements or fabrications
        └─ Return: verdict (pass/review/flag), warnings
        ↓
    [Step 3] Save & Generate PDF
        ├─ Write .txt file with cover letter + tailored CV + validation flags
        ├─ Generate ATS-friendly PDF using ReportLab
        └─ Save both files to output/ folder
        ↓
    [Step 4] Return Results to Frontend
        └─ JSON with analysis, validation, file paths, download URL
        ↓
    User Downloads PDF & Reviews Results
```

---

## Technology Stack

### Backend
- **FastAPI**: Lightweight Python web framework
- **Groq API**: LLM for CV analysis and tailoring
- **ReportLab**: PDF generation with German ATS formatting
- **Pydantic**: Data validation

### Frontend
- **HTML5 + Vanilla JavaScript**: No build tools required
- **Responsive CSS**: Dark theme UI
- **Fetch API**: Communicate with backend

### Project Structure
```
jd-cv-matcher/
├── main.py                    # FastAPI app, endpoints, orchestration
├── tailor.py                  # CV tailoring logic, Groq prompts
├── pdf_generator.py           # ATS-friendly PDF generation
├── my_cv.txt                  # Your CV (plain text)
├── requirements.txt           # Python dependencies
├── .env                       # Environment variables (GROQ_API_KEY)
├── static/
│   └── index.html            # Frontend UI
└── output/                    # Generated .txt and .pdf files
```

---

## Setup Instructions

### Prerequisites
- Python 3.9+
- Groq API key (get one free at [console.groq.com](https://console.groq.com))

### Installation

1. **Clone/navigate to project**
   ```bash
   cd jd-cv-matcher
   ```

2. **Create virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # macOS/Linux
   # OR
   venv\Scripts\activate  # Windows
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   Create a `.env` file in the project root:
   ```env
   GROQ_API_KEY=your_groq_api_key_here
   ```

5. **Add your CV**
   Save your CV as `my_cv.txt` in the project root (plain text format)

6. **Run the server**
   ```bash
   fastapi dev main.py
   ```
   Server starts at `http://localhost:8000`

---

## API Endpoints

### `POST /analyze`
Analyze a job description and tailor your CV.

**Request Body:**
```json
{
  "job_description": "Full job posting text here...",
  "company_name": "Company Name"
}
```

**Response:**
```json
{
  "match_score": 78,
  "matched_keywords": ["Python", "REST APIs", "Docker", ...],
  "missing_keywords": ["Kubernetes", "n8n", ...],
  "tailored_cv": "Full rewritten CV...",
  "cover_letter": "Professional cover letter...",
  "positioning_tip": "Frame your C# experience as...",
  "learning_roadmap": [
    {
      "skill": "n8n",
      "what_it_is": "Low-code workflow automation",
      "connects_to": "Your Zapier experience",
      "timeline": "3-4 days",
      "project_idea": "Build a job alert automation..."
    }
  ],
  "cv_edits": [...],
  "validation": {
    "verdict": "pass",
    "flags": [],
    "summary": "Content is honest and well-supported."
  },
  "saved_as": "Company_Name_20260628_120000.txt",
  "pdf_filename": "Company_Name_20260628_120000.pdf"
}
```

### `GET /download-pdf/{filename}`
Download a generated PDF file.

**Example:**
```
GET /download-pdf/Company_Name_20260628_120000.pdf
```

### `GET /`
Serves the frontend HTML interface.

---

## How It Works

### 1. CV Tailoring (tailor.py)
- Loads your original CV from `my_cv.txt`
- Uses Groq LLM with a detailed system prompt to:
  - Match skills from the job description to your CV
  - Identify missing skills in 4 expansion areas: AI/LLM, Python automation, workflow automation, DevOps/Cloud
  - Rewrite the CV to highlight relevant experience
  - Generate a professional cover letter
  - Create a learning roadmap for missing skills
  - Suggest specific edits

### 2. Honesty Validation (tailor.py)
- Compares original CV with tailored version
- Uses a second Groq call to detect:
  - Skills fabricated (not in original CV)
  - Experience overstated
  - Dates inconsistent
  - Returns flags and a verdict (pass/review/flag)

### 3. PDF Generation (pdf_generator.py)
- Converts tailored CV to ATS-friendly PDF
- Follows German CV standards:
  - Single column layout (no tables)
  - Section headers in ALL CAPS
  - Dates in MM/YYYY format
  - Standard fonts (Helvetica)
  - 2-page maximum
  - 2.5cm margins

### 4. File Storage (main.py)
- Saves both `.txt` and `.pdf` to `output/` folder
- Sanitizes filenames (removes special characters)
- Uses timestamps to prevent overwrites

---

## Frontend UI

The single-page frontend (static/index.html) provides:

1. **Input Section**
   - Text area for job description
   - Company name input field
   - Analyze button

2. **Results Section** (appears after analysis)
   - Match score with visual progress bar
   - Matched keywords (green tags)
   - Missing keywords (red tags)
   - Tabs: Tailored CV, Cover Letter, Learning Roadmap, CV Edits, Validation
   - Download PDF button

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GROQ_API_KEY` | ✓ Yes | Your Groq API key (get at console.groq.com) |

---

## Output Files

Generated files are saved in the `output/` folder:

- `{Company}_{Timestamp}.txt` — Text file containing validation flags, cover letter, and tailored CV
- `{Company}_{Timestamp}.pdf` — ATS-friendly PDF version of the tailored CV

**Example filename:**
```
Google_20260628_154442.txt
Google_20260628_154442.pdf
```

---

## Example Workflow

1. User visits `http://localhost:8000`
2. Pastes job description for "Python Developer @ Startup XYZ"
3. Enters company name "Startup XYZ"
4. Clicks "Analyze"
5. Backend:
   - Loads `my_cv.txt`
   - Calls Groq to tailor CV and generate cover letter
   - Validates honesty of tailored content
   - Generates PDF
   - Saves files to `output/`
6. Frontend displays results with match score, keywords, learning roadmap
7. User reviews cover letter and tailored CV in tabs
8. User clicks "Download PDF" to save the ATS-friendly CV

---

## Error Handling

The app validates:
- Job description is not empty
- Company name is not empty
- `my_cv.txt` exists
- `GROQ_API_KEY` is set in `.env`
- PDF generation completes successfully (with fallback error message if it fails)

All errors return HTTP status codes and descriptive messages.

---

## Customization

### Change System Prompt (tailor.py)
Edit `build_system_prompt()` to:
- Modify CV tailoring rules
- Change market focus (currently optimized for German tech market)
- Update the 4 expansion skill areas
- Adjust tone or professional standards

### Adjust PDF Styling (pdf_generator.py)
- Colors: `BLACK`, `DARK_GREY`, `MID_GREY`, `RULE_COLOR`, `ACCENT`
- Margins and spacing in section builders
- Font sizes and styles

### Frontend Theme (static/index.html)
- Modify CSS color variables
- Adjust layout and spacing
- Add form validation

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "GROQ_API_KEY is not set" | Create `.env` file with your API key |
| "my_cv.txt not found" | Save your CV as `my_cv.txt` in project root |
| PDF generation fails | Check ReportLab installation: `pip install reportlab` |
| API returns 500 error | Check server logs for Groq API errors or file path issues |
| Frontend won't load | Ensure FastAPI server is running at port 8000 |

---

## License

This project is for personal use. Modify as needed!

---

## Next Steps / Ideas

- [ ] Support multiple CV formats (upload .docx or .pdf)
- [ ] Add user accounts to save previous analyses
- [ ] Multi-language support (expand beyond German market)
- [ ] Batch job posting analysis
- [ ] Email integration to send tailored CVs directly
- [ ] Dark/light theme toggle
