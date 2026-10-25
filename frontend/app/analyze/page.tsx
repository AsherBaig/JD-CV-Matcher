"use client";

import { useState } from "react";
import Link from "next/link";
import { API } from "../../lib/api";

export default function AnalyzePage() {
  const [companyName, setCompanyName] = useState("");
  const [jobDesc, setJobDesc] = useState("");
  const [cvFile, setCvFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState("");
  const [activeTab, setActiveTab] = useState("cv");

  const handleAnalyze = async () => {
    if (!companyName.trim()) {
      setError("Please enter company name");
      return;
    }
    if (!jobDesc.trim()) {
      setError("Please paste job description");
      return;
    }
    if (!cvFile) {
      setError("Please upload your CV (PDF or TXT)");
      return;
    }

    setLoading(true);
    setError("");

    try {
      const formData = new FormData();
      formData.append("company_name", companyName);
      formData.append("job_description", jobDesc);
      if (cvFile) {
        formData.append("file", cvFile);
      }

      const res = await fetch(`${API}/analyze`, {
        method: "POST",
        body: formData,
      });

      if (!res.ok) {
        throw new Error("Analysis failed");
      }

      const data = await res.json();
      setResult(data);
    } catch (err) {
      setError("Could not reach server. Is uvicorn running?");
    } finally {
      setLoading(false);
    }
  };
 
  // if results exists then SHOW RESULTS (CV, cover letter, tabs, etc.) -- (HIDE FORM)
  if (result) {
    return (
      <div>
        <div style={{ marginBottom: "1.5rem" }}>
          <button
            onClick={() => { setResult(null); setActiveTab("cv"); }}
            className="btn btn-primary"
          >
            ← New Analysis
          </button>
        </div>

        <div className="card">
          <h2 className="section-title">Match Score</h2>
          <div style={{ fontSize: "2rem", fontWeight: "bold", marginBottom: "0.5rem" }}>
            {result.match_score ?? "—"}%
          </div>
          {result.jd_language === "de" && (
            <div style={{
              background: "#422006",
              border: "1px solid #d97706",
              borderRadius: "8px",
              padding: "1rem",
              marginBottom: "1rem",
              color: "#fde68a",
              fontSize: "0.9rem",
            }}>
              ⚠️ JD is in German — cover letter generated in German
            </div>
          )}
          {result.validation && (
            <div style={{
              background: result.validation.verdict === "safe" ? "#14532d" : "#451a03",
              border: result.validation.verdict === "safe" ? "1px solid #16a34a" : "1px solid #ea580c",
              borderRadius: "8px",
              padding: "1rem",
              marginBottom: "1rem",
              color: result.validation.verdict === "safe" ? "#86efac" : "#fdba74",
            }}>
              <strong>{result.validation.verdict === "safe" ? "✅ Safe to Send" : "⚠️ Review Before Sending"}</strong>
              <p style={{ marginTop: "0.5rem", color: "#cbd5e1" }}>{result.validation.summary}</p>
            </div>
          )}
        </div>

        <div className="card">
          {result.match_keywords && result.match_keywords.length > 0 && (
            <div style={{ marginBottom: "1.5rem" }}>
              <h3 style={{ fontSize: "0.85rem", fontWeight: "700", textTransform: "uppercase", color: "#64748b", marginBottom: "0.75rem" }}>✅ Matched Keywords</h3>
              <div style={{ display: "flex", flexWrap: "wrap", gap: "0.5rem" }}>
                {result.match_keywords.map((kw: string, i: number) => (
                  <span key={i} style={{ background: "#14532d", color: "#86efac", padding: "0.4rem 0.8rem", borderRadius: "4px", fontSize: "0.85rem", fontWeight: "500" }}>
                    {kw}
                  </span>
                ))}
              </div>
            </div>
          )}

          {result.missing_keywords && result.missing_keywords.length > 0 && (
            <div style={{ marginBottom: "1.5rem" }}>
              <h3 style={{ fontSize: "0.85rem", fontWeight: "700", textTransform: "uppercase", color: "#64748b", marginBottom: "0.75rem" }}>❌ Missing Keywords</h3>
              <div style={{ display: "flex", flexWrap: "wrap", gap: "0.5rem" }}>
                {result.missing_keywords.map((kw: string, i: number) => (
                  <span key={i} style={{ background: "#450a0a", color: "#fca5a5", padding: "0.4rem 0.8rem", borderRadius: "4px", fontSize: "0.85rem", fontWeight: "500" }}>
                    {kw}
                  </span>
                ))}
              </div>
            </div>
          )}

          <div style={{ display: "flex", gap: "0.5rem", marginBottom: "1.5rem", borderBottom: "1px solid #2d3348", flexWrap: "wrap" }}>
            {[
              { id: "cv", label: "Tailored CV" },
              { id: "letter", label: "Cover Letter" },
              { id: "position", label: "How to Position Yourself" },
              { id: "roadmap", label: "📚 Learning Roadmap" },
              { id: "edits", label: "✏️ CV Edits to Make" },
            ].map(tab => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                style={{
                  padding: "0.75rem 1.25rem",
                  background: activeTab === tab.id ? "#6366f1" : "transparent",
                  border: "none",
                  borderBottom: activeTab === tab.id ? "2px solid #6366f1" : "2px solid transparent",
                  color: activeTab === tab.id ? "#fff" : "#94a3b8",
                  cursor: "pointer",
                  fontSize: "0.95rem",
                  fontWeight: activeTab === tab.id ? "600" : "500",
                  transition: "all 0.2s",
                }}
              >
                {tab.label}
              </button>
            ))}
          </div>

          {activeTab === "cv" && result.tailored_cv && (
            <div>
              <pre className="cv-box">{result.tailored_cv}</pre>
            </div>
          )}

          {activeTab === "letter" && result.cover_letter && (
            <div>
              {result.cover_letter.split(/\n\n+/).map((para: string, i: number) => (
                <p key={i} className="para">{para}</p>
              ))}
            </div>
          )}

          {activeTab === "position" && (
            <div>
              {result.positioning_tip ? (
                <p className="para">{result.positioning_tip}</p>
              ) : (
                <p style={{ color: "#94a3b8" }}>No positioning advice available</p>
              )}
            </div>
          )}

          {activeTab === "roadmap" && result.learning_roadmap && result.learning_roadmap.length > 0 && (
            <div>
              {result.learning_roadmap.map((item: any) => (
                <div key={item.skill} className="roadmap-item">
                  <div className="roadmap-skill">
                    {item.skill}
                    <span className="timeline-badge">⏱ {item.timeline}</span>
                  </div>
                  <p>{item.what_it_is}</p>
                  <div className="project-box">🛠 {item.project_idea}</div>
                </div>
              ))}
            </div>
          )}

          {activeTab === "edits" && (
            <div>
              {result.cv_edits && result.cv_edits.length > 0 ? (
                <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
                  {result.cv_edits.map((edit: any, i: number) => (
                    <div key={i} style={{ background: "#0f1117", borderRadius: "8px", padding: "1rem", border: "1px solid #2d3348" }}>
                      {typeof edit === "string" ? (
                        <p>{edit}</p>
                      ) : (
                        <>
                          <div style={{ background: "#b45309", color: "#fef3c7", padding: "0.5rem 0.75rem", borderRadius: "4px", fontSize: "0.75rem", fontWeight: "700", marginBottom: "1rem", textTransform: "uppercase" }}>
                            {edit.section}
                          </div>

                          <div style={{ marginBottom: "0.75rem" }}>
                            <div style={{ fontSize: "0.8rem", fontWeight: "700", textTransform: "uppercase", color: "#94a3b8", marginBottom: "0.5rem" }}>Current</div>
                            <div style={{ background: "#450a0a", color: "#fca5a5", padding: "0.75rem", borderRadius: "4px", fontSize: "0.9rem", border: "1px solid #7c2d12" }}>
                              {edit.current}
                            </div>
                          </div>

                          <div style={{ marginBottom: "0.75rem" }}>
                            <div style={{ fontSize: "0.8rem", fontWeight: "700", textTransform: "uppercase", color: "#94a3b8", marginBottom: "0.5rem" }}>Suggested</div>
                            <div style={{ background: "#14532d", color: "#86efac", padding: "0.75rem", borderRadius: "4px", fontSize: "0.9rem", border: "1px solid #16a34a" }}>
                              {edit.suggested}
                            </div>
                          </div>

                          <div>
                            <div style={{ fontSize: "0.8rem", fontWeight: "700", textTransform: "uppercase", color: "#94a3b8", marginBottom: "0.5rem" }}>Why</div>
                            <div style={{ color: "#cbd5e1", fontSize: "0.9rem", padding: "0.75rem", background: "#1e2130", borderRadius: "4px", borderLeft: "3px solid #6366f1" }}>
                              📌 {edit.reason}
                            </div>
                          </div>
                        </>
                      )}
                    </div>
                  ))}
                </div>
              ) : (
                <p style={{ color: "#94a3b8" }}>No edits suggested</p>
              )}
            </div>
          )}

          {result.pdf_filename && (
            <div style={{ marginTop: "1.5rem", paddingTop: "1.5rem", borderTop: "1px solid #2d3348" }}>
              <a
                href={`${API}/download-pdf/${result.pdf_filename}`}
                download
                style={{
                  display: "inline-block",
                  background: "#16a34a",
                  color: "#fff",
                  padding: "0.75rem 1.5rem",
                  borderRadius: "8px",
                  textDecoration: "none",
                  fontWeight: "600",
                  fontSize: "0.95rem",
                  border: "none",
                  cursor: "pointer",
                }}
              >
                📥 Download PDF
              </a>
              <span style={{ marginLeft: "1rem", color: "#94a3b8", fontSize: "0.85rem" }}>
                ATS-formatted PDF ready
              </span>
            </div>
          )}
        </div>

        <Link href="/" className="btn btn-primary" style={{ marginTop: "1rem" }}>
          Go to Dashboard
        </Link>
      </div>
    );
  }
 

  // result exists nahe krega to ye SHOW FORM (inputs for company, CV, JD)--
  return (
    <div className="card">
      <h1>Analyze Your CV</h1>
      <p className="subtitle">Paste a job description → get tailored CV, match analysis, and learning roadmap</p>

      <div className="field" style={{ marginBottom: "1.2rem" }}>
        <label htmlFor="companyName" style={{ display: "block", marginBottom: "0.5rem", fontWeight: "600", fontSize: "0.85rem", color: "#94a3b8" }}>
          Company Name
        </label>
        <input
          type="text"
          id="companyName"
          placeholder="e.g. Siemens, SAP, schoolboost…"
          value={companyName}
          onChange={(e) => setCompanyName(e.target.value)}
          style={{
            width: "100%",
            padding: "0.75rem 1rem",
            background: "#0f1117",
            border: "1px solid #2d3348",
            borderRadius: "8px",
            color: "#e2e8f0",
            fontSize: "0.95rem",
          }}
        />
      </div>

      <div className="field" style={{ marginBottom: "1.2rem" }}>
        <label htmlFor="cvFile" style={{ display: "block", marginBottom: "0.5rem", fontWeight: "600", fontSize: "0.85rem", color: "#94a3b8" }}>
          Upload Your CV (PDF or Text)
        </label>
        <input
          type="file"
          id="cvFile"
          accept=".txt,.pdf"
          onChange={(e) => setCvFile(e.target.files?.[0] || null)}
          style={{
            width: "100%",
            padding: "0.75rem 1rem",
            background: "#0f1117",
            border: "1px solid #2d3348",
            borderRadius: "8px",
            color: "#e2e8f0",
            fontSize: "0.95rem",
          }}
        />
      </div>

      <div className="field" style={{ marginBottom: "1.2rem" }}>
        <label htmlFor="jobDesc" style={{ display: "block", marginBottom: "0.5rem", fontWeight: "600", fontSize: "0.85rem", color: "#94a3b8" }}>
          Job Description
        </label>
        <textarea
          id="jobDesc"
          placeholder="Paste the full job description here…"
          value={jobDesc}
          onChange={(e) => setJobDesc(e.target.value)}
          style={{
            width: "100%",
            minHeight: "220px",
            padding: "0.75rem 1rem",
            background: "#0f1117",
            border: "1px solid #2d3348",
            borderRadius: "8px",
            color: "#e2e8f0",
            fontSize: "0.95rem",
            fontFamily: "inherit",
            lineHeight: "1.6",
            resize: "vertical",
          }}
        />
      </div>

      {error && (
        <div className="error-box" style={{ marginBottom: "1rem" }}>
          {error}
        </div>
      )}

      <button
        onClick={handleAnalyze}
        disabled={loading}
        className="btn btn-primary"
        style={{
          width: "100%",
          padding: "0.9rem",
          background: loading ? "#4f46e5" : "#6366f1",
          opacity: loading ? 0.6 : 1,
          cursor: loading ? "not-allowed" : "pointer",
        }}
      >
        {loading ? "⏳ Analyzing... (~20 seconds)" : "Analyze & Tailor"}
      </button>

      <div style={{ marginTop: "1rem" }}>
        <Link href="/" className="btn" style={{ marginRight: "0.5rem" }}>
          Go to Dashboard
        </Link>
      </div>
    </div>
  );
}
