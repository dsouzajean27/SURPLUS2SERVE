export default function StatCard({ label, value, hint, tone }) {
  return (
    <div className={`stat ${tone || ""}`}>
      <div className="stat-value">{value ?? "-"}</div>
      <div className="stat-label">{label}</div>
      {hint && <div className="stat-hint">{hint}</div>}
    </div>
  );
}
