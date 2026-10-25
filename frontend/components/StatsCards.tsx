import type { Stats } from "../lib/api";

// Presentational component — it holds no state, it only renders what it is
// given. The `props` object is the React equivalent of Angular's @Input().
export default function StatsCards({ stats }: { stats: Stats }) {
  const cards = [
    { label: "Applications", value: stats.total },
    { label: "Avg match score", value: stats.total ? `${stats.avg_score}%` : "—" },
    { label: "Applied", value: stats.applied },
    { label: "Interviews", value: stats.interviews },
  ];

  return (
    <div className="stats-grid">
      {cards.map((card) => (
        <div className="stat-card" key={card.label}>
          <div className="stat-value">{card.value}</div>
          <div className="stat-label">{card.label}</div>
        </div>
      ))}
    </div>
  );
}
