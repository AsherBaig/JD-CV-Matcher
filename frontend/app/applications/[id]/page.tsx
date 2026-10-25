import Link from "next/link";
import { notFound } from "next/navigation";
import { API, fetchApplication, formatDate } from "../../../lib/api";

// No "use client" here — this is a server component. It is read-only, so it
// needs no state and no event handlers, and it can await its data directly.
// None of this component's JavaScript is sent to the browser.
//
// In Next 15 `params` is a Promise, so it has to be awaited.
export default async function ApplicationPage({
  params,
}: {
  params: Promise<{ id: string }>; // promise ek waada hai jo future me resolve hoga,, for eg: mere pas data nahe hai, lekin bad mein aega .. baad mein: ye lo data
 // is eg me promise ka mtlab hai jaldi tjhe id mlegi. tu await kro..
}) {
  const { id } = await params; // jabtk id nahe ata tb tk rukjaa mljae to
  const app = await fetchApplication(id);

  // Renders Next's 404 page instead of crashing.
  if (!app) notFound();

  const result = app.result ?? {};
  const roadmap = result.learning_roadmap ?? [];

  return (
    <>
      <Link className="back-link" href="/">
        ← Back to dashboard
      </Link>

      <h1>{app.company_name}</h1>
      <p className="subtitle">
        {formatDate(app.created_at)} · {app.match_score ?? "—"}% match ·{" "}
        {(app.jd_language ?? "?").toUpperCase()} · {app.status}
      </p>

      {result.validation && (
        <div
          className={`verdict ${result.validation.verdict === "safe" ? "verdict-safe" : "verdict-review"}`}
        >
          <strong>
            {result.validation.verdict === "safe"
              ? "✅ Safe to send"
              : "⚠️ Review before sending"}
          </strong>
          <p>{result.validation.summary}</p>
        </div>
      )}

      {app.pdf_filename && (
        <a
          className="btn btn-primary"
          href={`${API}/download-pdf/${encodeURIComponent(app.pdf_filename)}`}
        >
          ⬇ Download PDF
        </a>
      )}

      {result.matched_keywords && result.matched_keywords.length > 0 && (
        <section className="card">
          <h2 className="section-title">✅ Matched Keywords</h2>
          <div style={{ display: "flex", flexWrap: "wrap", gap: "0.5rem" }}>
            {result.matched_keywords.map((kw: string, i: number) => (
              <span key={i} style={{ background: "#14532d", color: "#86efac", padding: "0.4rem 0.8rem", borderRadius: "4px", fontSize: "0.85rem" }}>
                {kw}
              </span>
            ))}
          </div>
        </section>
      )}

      {result.missing_keywords && result.missing_keywords.length > 0 && (
        <section className="card">
          <h2 className="section-title">❌ Missing Keywords</h2>
          <div style={{ display: "flex", flexWrap: "wrap", gap: "0.5rem" }}>
            {result.missing_keywords.map((kw: string, i: number) => (
              <span key={i} style={{ background: "#450a0a", color: "#fca5a5", padding: "0.4rem 0.8rem", borderRadius: "4px", fontSize: "0.85rem" }}>
                {kw}
              </span>
            ))}
          </div>
        </section>
      )}

      {result.cover_letter && (
        <section className="card">
          <h2 className="section-title">Cover Letter</h2>
          {/* Split on blank lines so the stored \n\n become real paragraphs. */}
          {result.cover_letter.split(/\n\n+/).map((para, i) => (
            <p className="para" key={i}>
              {para}
            </p>
          ))}
        </section>
      )}

      {result.tailored_cv && (
        <section className="card">
          <h2 className="section-title">Tailored CV</h2>
          <pre className="cv-box">{result.tailored_cv}</pre>
        </section>
      )}

      {result.positioning_tip && (
        <section className="card">
          <h2 className="section-title">How to Position Yourself</h2>
          <p className="para">{result.positioning_tip}</p>
        </section>
      )}

      {roadmap.length > 0 && (
        <section className="card">
          <h2 className="section-title">Learning Roadmap</h2>
          {roadmap.map((item) => (
            <div className="roadmap-item" key={item.skill}>
              <div className="roadmap-skill">
                {item.skill}
                <span className="timeline-badge">⏱ {item.timeline}</span>
              </div>
              <p>{item.what_it_is}</p>
              <p className="project-box">🛠 {item.project_idea}</p>
            </div>
          ))}
        </section>
      )}

      {result.cv_edits && result.cv_edits.length > 0 && (
        <section className="card">
          <h2 className="section-title">✏️ CV Edits to Make</h2>
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
        </section>
      )}

      <section className="card">
        <h2 className="section-title">Job Description</h2>
        <pre className="cv-box">{app.job_description}</pre>
      </section>
    </>
  );
}
