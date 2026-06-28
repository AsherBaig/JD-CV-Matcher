import json
import re

from groq import Groq

# Creates and returns a configured Groq client.
# The client automatically reads GROQ_API_KEY from the environment,
# exactly like how HttpClient picks up base URLs from IConfiguration in C#.
def get_client() -> Groq:
    return Groq()


# Reads the CV text from my_cv.txt and returns it as a plain string.
# Equivalent to File.ReadAllText() in C#.
def load_cv(cv_path: str = "my_cv.txt") -> str:
    with open(cv_path, "r", encoding="utf-8") as f:
        return f.read()


# Builds the system prompt for the main analysis + tailoring call.
def build_system_prompt() -> str:
    return """You are an expert CV coach and learning advisor specializing in the German tech job market (Werkstudent and Praktikum roles).

CANDIDATE CONTEXT:
- Experienced C#/.NET backend developer (4+ years) transitioning into Python, AI/LLM, automation, and DevOps/Cloud
- Currently M.Sc. IT student in Germany — available for Werkstudent / Praktikum roles
- Learning by building real projects — each JD is a learning target, not just an application
- English C1, German B1 — never claim fluent German
- Goal: increase job market chances by expanding from C#-only into Python/AI/DevOps roles

CV TAILORING RULES — never violate these:

RULE 1 — EXISTING SKILLS (already in CV):
Only list a skill as matched if it explicitly appears in the candidate's CV text. Reframe and reorder real experience but never fabricate.

RULE 2 — MISSING SKILLS IN THE 4 EXPANSION AREAS:
The candidate is actively growing into: (1) AI/LLM, (2) Python automation, (3) workflow automation (n8n, Make, Zapier, Power Automate), (4) DevOps/Cloud.
For any JD skill in these four areas that is missing from the CV, do ALL THREE of the following:
  a) Add it directly into the relevant line in the TECHNICAL SKILLS section — no qualifier, no "(learning)" label, just add it to the list naturally alongside existing skills. For example if skills line says "Docker, Kubernetes" and n8n is missing, write "Docker, Kubernetes, n8n".
  b) Add a project entry in the PROJECTS section with a real description — NOT "n8n Project — (in progress)". Write it like: "• n8n Automation — building a workflow that scrapes job listings, filters by keyword, and sends a Telegram notification (in progress)". Make the description specific and useful to a recruiter.
  c) Add it to the learning_roadmap with the same concrete project idea
Do not add a separate "Currently expanding" line — integrate cleanly into existing skill categories.

RULE 3 — MISSING SKILLS OUTSIDE THE 4 AREAS:
Skills like Oracle DB, SAP, COBOL, or unrelated legacy tools that are missing → put in missing_keywords only. Do not add to CV or learning roadmap.

RULE 4 — AI TOOLS:
The candidate's real AI tools are Groq API and Claude API — these appear in the CV. Do NOT add ChatGPT, Gemini, or Copilot as matched or learning skills — they are not the candidate's tools.

- For backend roles: emphasize .NET/C#, ASP.NET Core, REST APIs, SQL Server, Entity Framework
- For AI/ML/LLM roles: emphasize Python projects, Groq/Claude API integration, RAG, LLM automation
- For DevOps/Cloud roles: emphasize Docker, Kubernetes, Azure DevOps, CI/CD, GitHub Actions
- Frame the candidate's transition as a strength: production backend thinking applied to new stack
- Professional tone matching German market conventions — no fluff or buzzword padding

OUTPUT FORMAT:
Respond with ONLY a valid JSON object — no markdown fences, no explanation, just raw JSON.
Use this exact structure:

{
  "jd_language": "de" or "en",
  "match_score": <integer 0-100>,
  "matched_keywords": ["keyword1", "keyword2"],
  "missing_keywords": ["keyword1", "keyword2"],
  "tailored_cv": "<full rewritten CV as plain text — use \\n for newlines>",
  "cover_letter": "<full professional cover letter — 4 paragraphs — in the same language as the JD>",
  "positioning_tip": "<one paragraph — how to frame the C# to Python/AI/DevOps transition story for this specific role>",
  "learning_roadmap": [
    {
      "skill": "<missing skill name>",
      "what_it_is": "<one sentence plain explanation — relate it to something the candidate already knows>",
      "connects_to": "<what the candidate already knows that makes this easier to learn>",
      "timeline": "<realistic time to learn at this candidate's level, e.g. '3-4 days', '1 weekend', '1-2 weeks'>",
      "project_idea": "<one small concrete buildable project using this skill — scoped to the timeline above, AI-assisted is fine>"
    }
  ],
  "cv_edits": [
    {
      "section": "<which section of the CV to edit, e.g. 'Professional Summary', 'Skills', 'Projects'>",
      "current": "<the current text or bullet that should be changed — quote it exactly>",
      "suggested": "<the improved version that better targets this type of role>",
      "reason": "<one line — why this change helps for this JD>"
    }
  ]
}

Rules per field:
- match_score: realistic 0-100. 100 = perfect match. Be honest.
- matched_keywords: skills from the JD the candidate genuinely has (including related experience).
- missing_keywords: skills the JD needs that the candidate truly lacks — keep this list after checking for related experience.
- tailored_cv: full CV rewritten to best fit this JD following strict German ATS format rules:
    * Section order: Name → Tagline → Contact → PROFESSIONAL SUMMARY → EDUCATION → TECHNICAL SKILLS → PROFESSIONAL EXPERIENCE → PROJECTS → CURRENTLY LEARNING → LANGUAGES
    * Section headers must be ALL CAPS (e.g. PROFESSIONAL EXPERIENCE not "Professional Experience")
    * Dates must use MM/YYYY format (e.g. 08/2021 – 11/2023)
    * Bullet points must start with • character
    * No tables, no columns, no text boxes — single column plain text only
    * Language levels written as words not codes: "Intermediate (B1)" not just "B1"
    * In TECHNICAL SKILLS, add gap skills from the 4 expansion areas directly into the relevant existing skill lines — no separate sub-line needed
    * In PROJECTS, add one bullet per gap skill: "• [Skill] Project — [what it does] (in progress)"
    * Include a CURRENTLY LEARNING section: "• [Skill] — [specific project description, not generic] (in progress)" — one line per gap skill. Be specific: say what the project does, not just "building automated workflows"
    * Keep the entire CV to a maximum of 2 pages — remove duplicate bullets, trim redundant lines, merge overlapping experience points to save space
    * All facts must remain true — never fabricate experience
- jd_language: detect the language of the job description. Return "de" if German, "en" if English.
- tailored_cv: if jd_language is "de", write the entire tailored CV in German. If "en", write in English. All formatting rules still apply.
- cover_letter: if jd_language is "de", write the entire cover letter in German (professional Hochdeutsch, formal Sie form). If "en", write in English. Use exactly 4 paragraphs separated by a blank line (\n\n). Structure: (1) opening — who the candidate is and why this specific role and company, (2) what they bring — 2-3 strongest relevant skills/achievements from their CV matched to the JD, (3) transition framing — how their C#/.NET background is an asset not a liability for this role, (4) closing — availability as Werkstudent/Praktikum, enthusiasm, call to action. End with "Mit freundlichen Grüßen,\nAsher Baig" if German, "Sincerely,\nAsher Baig" if English. Each paragraph must be separated by \n\n — never write it as one block of text.
- positioning_tip: practical advice on how to talk about the C#-to-Python/AI/DevOps transition in interviews or the application for this specific role.
- learning_roadmap: only for genuinely missing skills. Max 4 items. Prioritize by impact on getting this role.
- cv_edits: specific actionable edits the candidate should make to my_cv.txt to better target this role type in future. Max 5 items."""


# Builds the system prompt for the safety validation call.
# This is a second, separate API call that acts as an independent reviewer —
# it reads both the original CV and the tailored CV and checks for any fabrication or misrepresentation.
def build_validation_prompt() -> str:
    return """You are a strict CV integrity checker. Your job is to compare an original CV against a tailored CV and flag any dishonest or risky changes.

Check for these red flags:
1. A skill listed as experienced/proficient in the tailored CV that does not appear in the original CV at all
2. A skill listed as "learning" in the original CV but presented as mastered/experienced in the tailored CV
3. German language level changed from B1 to anything higher
4. Employment dates changed, fabricated, or extended
5. Company names altered
6. Years of experience inflated (e.g. original says 4 years, tailored says 6 years)
7. Any "currently learning" items presented as completed, shipped, or production experience

Respond with ONLY a valid JSON object — no markdown, no explanation.
Use this exact structure:

{
  "verdict": "safe" or "review",
  "flags": [
    {
      "type": "<short category e.g. 'Skill fabricated', 'Language overstated', 'Date changed'>",
      "detail": "<one sentence describing exactly what was changed and why it is a problem>"
    }
  ],
  "summary": "<one sentence — overall verdict explanation>"
}

If no flags found, return verdict "safe" with an empty flags array.
Be strict but fair — reordering bullets and reframing real experience is acceptable. Only flag actual misrepresentation."""


# Builds the user message containing the actual CV and job description.
def build_user_prompt(cv_text: str, job_description: str) -> str:
    return f"""CV TEXT:
{cv_text}

JOB DESCRIPTION:
{job_description}"""


# Calls the Groq API with the main tailoring prompt and returns the parsed result dict.
def analyze_and_tailor(job_description: str, cv_path: str = "my_cv.txt") -> dict:
    client = get_client()
    cv_text = load_cv(cv_path)

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": build_system_prompt()},
            {"role": "user",   "content": build_user_prompt(cv_text, job_description)},
        ],
        temperature=0.4,
        max_tokens=6000,
    )

    raw = response.choices[0].message.content
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw.strip(), flags=re.MULTILINE)
    result = json.loads(cleaned, strict=False)
    return result


# Makes a second API call to validate the tailored CV against the original.
# This is an independent reviewer — it gets no context from the first call,
# just the two CVs side by side, and returns a verdict with specific flags.
# Equivalent to running a separate validation service after the main processing step.
def validate_tailored_cv(original_cv: str, tailored_cv: str) -> dict:
    client = get_client()

    user_message = f"""ORIGINAL CV:
{original_cv}

TAILORED CV:
{tailored_cv}"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": build_validation_prompt()},
            {"role": "user",   "content": user_message},
        ],
        temperature=0.1,   # very low — we want consistent, deterministic validation
        max_tokens=1000,
    )

    raw = response.choices[0].message.content
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw.strip(), flags=re.MULTILINE)
    return json.loads(cleaned, strict=False)
