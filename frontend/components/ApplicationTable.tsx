import Link from "next/link";
import {
  API,
  STATUSES,
  deleteApplication,
  formatDate,
  updateStatus,
  type ApplicationSummary,
  type Status,
} from "../lib/api";

// Colour band for the score pill — same thresholds as the vanilla frontend.
function scoreClass(score: number | null): string {
  if (score === null) return "score-low";
  if (score >= 75) return "score-high";
  if (score >= 50) return "score-mid";
  return "score-low";
}

// `onChanged` is a callback prop: the child does not own the data, so after a
// change it tells the parent to reload. Data flows down, events flow up.
export default function ApplicationTable({
  applications,
  onChanged,
}: {
  applications: ApplicationSummary[];
  onChanged: () => void;
}) {
  async function handleStatusChange(id: number, status: Status) {
    await updateStatus(id, status);
    onChanged();
  }

  async function handleDelete(id: number) {
    if (!confirm("Delete this application from the history?")) return;
    await deleteApplication(id);
    onChanged();
  }

  if (applications.length === 0) {
    return (
      <p className="empty-state">
        No applications yet — run an analysis in the main app to see it here.
      </p>
    );
  }

  return (
    <div className="table-wrap">
      <table className="app-table">
        <thead>
          <tr>
            <th>Company</th>
            <th>Date</th>
            <th>Score</th>
            <th>Lang</th>
            <th>Check</th>
            <th>Status</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {applications.map((app) => (
            <tr key={app.id}>
              <td className="company-cell">{app.company_name}</td>
              <td>{formatDate(app.created_at)}</td>
              <td>
                <span className={`score-pill ${scoreClass(app.match_score)}`}>
                  {app.match_score ?? "—"}%
                </span>
              </td>
              <td>
                <span className="lang-badge">
                  {(app.jd_language ?? "?").toUpperCase()}
                </span>
              </td>
              <td>
                {app.verdict === "safe"
                  ? "✅ Safe"
                  : app.verdict === "review"
                    ? "⚠️ Review"
                    : "—"}
              </td>
              <td>
                <select
                  className="status-select"
                  value={app.status}
                  onChange={(e) =>
                    handleStatusChange(app.id, e.target.value as Status)
                  }
                >
                  {STATUSES.map((status) => (
                    <option key={status} value={status}>
                      {status[0].toUpperCase() + status.slice(1)}
                    </option>
                  ))}
                </select>
              </td>
              <td className="row-actions">
                <Link className="btn" href={`/applications/${app.id}`}>
                  Open
                </Link>
                {app.pdf_filename && (
                  <a
                    className="btn"
                    href={`${API}/download-pdf/${encodeURIComponent(app.pdf_filename)}`}
                  >
                    PDF
                  </a>
                )}
                <button
                  className="btn btn-danger"
                  onClick={() => handleDelete(app.id)}
                >
                  Delete
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
