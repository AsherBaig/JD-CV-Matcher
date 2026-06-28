# JD-CV Matcher

A web application that tailors your CV to specific job descriptions using AI (Groq API). Built with **FastAPI** (backend) and **Vanilla JS** (frontend), it analyzes job postings, generates personalized cover letters, validates honesty, produces ATS-friendly PDFs, and provides a learning roadmap to close skill gaps.

---

## Features

- **AI-Powered CV Tailoring** — Rewrites your CV to match the JD using Groq LLM (llama-3.3-70b-versatile)
- **Bilingual Support** — Detects JD language (German/English) and generates CV + cover letter in the same language
- **Match Score** — Realistic 0-100 score showing how well your CV matches the JD
- **Keyword Analysis** — Matched keywords (green) and missing keywords (red)
- **Full Cover Letter** — 4-paragraph professional cover letter written as a senior recruiter, ready to send
- **Honesty Validator** — Second AI call checks the tailored CV for fabricated or overstated skills
- **Learning Roadmap** — Per missing skill: what it is, what you already know, timeline, and a concrete project to build
- **CV Edits Suggestions** — Specific edits to make to your base CV for this role type
- **How to Position Yourself** — Advice on framing your transition story for interviews
- **ATS-Friendly PDF** — German-format PDF (single column, Helvetica, ALL CAPS headers, MM/YYYY dates, 2.5cm margins)
- **German Language Warning** — Yellow banner when JD is German reminding you to review LLM-generated German text
- **Auto-save** — Saves `.txt` and `.pdf` to `output/` folder named after the company

---

## App Flow

```
User Input (Job Description + Company Name)
        ↓
    [Step 1] Analyze & Tailor CV via Groq
        ├─ Detect JD language (German or English)
        ├─ Load your CV (my_cv.txt)
        ├─ Call Groq LLM — returns tailored CV, cover letter, score, roadmap, cv edits
        └─ CV and cover letter generated in same language as JD
        ↓
    [Step 2] Validate Tailored Content (Honesty Check)
        ├─ Second Groq call compares original vs tailored CV
        ├─ Flags fabricated skills, overstated experience, changed dates
        └─ Returns verdict: "safe" or "review" with specific flags
        ↓
    [Step 3] Save & Generate PDF
        ├─ Write .txt file (validation flags + cover letter + tailored CV)
        ├─ Generate ATS-friendly PDF using ReportLab
        └─ Save both to output/ folder
        ↓
    [Step 4] Return Results to Frontend
        └─ JSON with all analysis, validation, language flag, download URL
        ↓
    User Reviews Results → Downloads PDF → Applies
```

---

## Results Tabs

| Tab | What it shows |
|---|---|
| **Tailored CV** | Full rewritten CV + Download PDF button |
| **Cover Letter** | 4-paragraph cover letter ready to send |
| **How to Position Yourself** | Transition framing advice for this specific role |
| **Learning Roadmap** | Per missing skill: explanation, connection to existing skills, timeline, project idea |
| **CV Edits to Make** | Specific edits for your base `my_cv.txt` — current text (red) vs suggested (green) |

---

## Technology Stack

### Backend
- **FastAPI** — Python web framework
- **Groq API** — LLM inference (llama-3.3-70b-versatile)
- **ReportLab** — ATS-friendly PDF generation
- **python-dotenv** — Environment variable management

### Frontend
- **HTML5 + Vanilla JavaScript** — No framework, no build tools
- **CSS** — Dark theme, tab switching, verdict banners
- **Fetch API** — REST calls to FastAPI backend

### Project Structure
```
jd-cv-matcher/
├── main.py              # FastAPI app, endpoints, orchestration
├── tailor.py            # Groq prompts, CV tailoring, validation logic
├── pdf_generator.py     # ATS-friendly PDF generation with ReportLab
├── my_cv.txt            # Your CV in plain text — edit this
├── requirements.txt     # Python dependencies
├── .env                 # GROQ_API_KEY (not committed)
├── .env.example         # Template for .env
├── static/
│   └── index.html       # Single-page frontend
└── output/              # Generated .txt and .pdf files (not committed)
```

---

## Setup

### Prerequisites
- Python 3.9+
- Free Groq API key from [console.groq.com](https://console.groq.com)

### Installation

```bash
# 1. Clone the repo
git clone https://github.com/AsherBaig/JD-CV-Matcher.git
cd JD-CV-Matcher

# 2. Create virtual environment
python3 -m venv .venv
source .venv/bin/activate      # macOS/Linux
# .venv\Scripts\activate       # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up API key
cp .env.example .env
# Edit .env and add your Groq API key:
# GROQ_API_KEY=gsk_your_key_here

# 5. Add your CV
# Edit my_cv.txt with your real CV content

# 6. Start the server
uvicorn main:app --reload
```

Open **http://localhost:8000** in your browser.

---

## API Endpoints

### `POST /analyze`
Analyze a job description and tailor your CV.

**Request:**
```json
{
  "job_description": "Full job posting text...",
  "company_name": "Company Name"
}
```

**Response:**
```json
{
  "jd_language": "de",
  "match_score": 78,
  "matched_keywords": ["Python", "Docker", "REST APIs"],
  "missing_keywords": ["n8n", "Prometheus"],
  "tailored_cv": "Full rewritten CV in JD language...",
  "cover_letter": "4-paragraph cover letter in JD language...",
  "positioning_tip": "How to frame your transition for this role...",
  "learning_roadmap": [
    {
      "skill": "n8n",
      "what_it_is": "Visual workflow automation like Azure Logic Apps but open source",
      "connects_to": "Your REST API and webhook experience from ASP.NET Core",
      "timeline": "1 weekend",
      "project_idea": "Build a job alert pipeline — scrape listings, filter by keyword, send Telegram notification"
    }
  ],
  "cv_edits": [
    {
      "section": "Professional Summary",
      "current": "looking to support development...",
      "suggested": "seeking to apply Python and AI/LLM skills...",
      "reason": "Better targets AI/automation roles"
    }
  ],
  "validation": {
    "verdict": "safe",
    "flags": [],
    "summary": "All claims consistent with original CV."
  },
  "saved_as": "CompanyName_20260628_120000.txt",
  "pdf_filename": "CompanyName_20260628_120000.pdf"
}
```

### `GET /download-pdf/{filename}`
Download a generated ATS PDF.

### `GET /`
Serves the frontend.

---

## German ATS PDF Format

The generated PDF follows German CV standards:
- Single column layout — no tables, no text boxes
- Helvetica font — ATS-safe, no custom fonts
- Section headers in ALL CAPS with horizontal rule
- Dates in MM/YYYY format
- Bullet points with • character
- Language levels as words: "Intermediate (B1)" not "B1"
- Maximum 2 pages
- 2.5cm margins — standard German business document

---

## Honesty Validation

A second independent Groq call checks the tailored CV against the original for:

| Flag | What it catches |
|---|---|
| Skill fabricated | Skill appears in tailored CV but not in original |
| Skill overstated | "Learning" skill presented as mastered |
| Language overstated | German B1 changed to B2 or higher |
| Date changed | Employment dates modified |
| Experience inflated | Years of experience increased |

Result shown as **✅ Safe to Send** (green) or **⚠️ Review Before Sending** (orange) with specific flags listed.

---

## Bilingual Support

- JD in **English** → CV and cover letter in English, no warning
- JD in **German** → CV and cover letter in German (formal Hochdeutsch, Sie form), yellow warning banner shown reminding you to review before sending

---

## Troubleshooting

| Issue | Solution |
|---|---|
| `GROQ_API_KEY is not set` | Add key to `.env` file |
| `my_cv.txt not found` | Save your CV as `my_cv.txt` in project root |
| PDF generation fails | Restart server: `uvicorn main:app --reload` |
| JSON parse error | Run analysis again — LLM occasionally returns malformed JSON |
| Server not reachable | Check uvicorn is running at port 8000 |

---

## Changelog

| Version | What changed |
|---|---|
| v1.0 | Initial release — CV tailoring, match score, keywords, cover letter, PDF |
| v1.1 | Added honesty validator (Safe to Send verdict) |
| v1.2 | Added Learning Roadmap, CV Edits, How to Position Yourself tabs |
| v1.3 | Missing skills from 4 expansion areas added to CV skills + projects |
| v1.4 | Cover letter formatted as 4 paragraphs instead of single block |
| v1.5 | Bilingual support — detects German JDs, generates output in German, shows review warning |

---

## License

Personal use project. Fork and adapt as needed.
