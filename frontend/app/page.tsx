// Runs in the browser, not on the server — needed because this component holds
// state and its children handle clicks. Server components can do neither.
"use client";

import { useCallback, useEffect, useState } from "react";
import ApplicationTable from "../components/ApplicationTable";
import StatsCards from "../components/StatsCards";
import { fetchDashboard, type DashboardData } from "../lib/api";

export default function Dashboard() {
  // One piece of state per thing that can change independently.
  const [data, setData] = useState<DashboardData | null>(null);
  const [error, setError] = useState<string | null>(null);

  // useCallback keeps the same function instance between renders, so the
  // useEffect below does not re-run on every render.
  const load = useCallback(() => {
    fetchDashboard()
      .then((result) => {
        setData(result);
        setError(null);
      })
      .catch(() => setError("Could not reach the API — is uvicorn running?"));
  }, []);

  // Runs once after the first render, because `load` never changes.
  useEffect(() => {
    load();
  }, [load]);

  if (error) return <p className="error-box">{error}</p>;
  if (!data) return <p className="empty-state">Loading…</p>;

  return (
    <>
      <h1>Application Dashboard</h1>
      <p className="subtitle">
        Every CV you have tailored, with its match score and where it stands.
      </p>

      <StatsCards stats={data.stats} />

      <div className="card">
        <h2 className="section-title">Application History</h2>
        {/* Data flows down as props; the table calls load() when it changes something. */}
        <ApplicationTable applications={data.applications} onChanged={load} />
      </div>
    </>
  );
}
