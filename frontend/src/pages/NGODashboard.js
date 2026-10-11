import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import client from "../api/client";
import StatCard from "../components/StatCard";
import { UrgencyBadge } from "../components/Badges";

export default function NGODashboard() {
  const [stats, setStats] = useState({});
  const [recs, setRecs] = useState(null);

  useEffect(() => {
    client.get("/dashboard/ngo").then((r) => setStats(r.data)).catch(() => {});
    client.get("/recommendations/for-ngo").then((r) => setRecs(r.data)).catch(() => setRecs([]));
  }, []);

  return (
    <>
      <h2>Recipient dashboard</h2>
      <div className="grid stats">
        <StatCard label="Requirements posted" value={stats.requirements_posted} />
        <StatCard tone="green" label="Donations received" value={stats.donations_received} />
        <StatCard tone="green" label="Food received (kg)" value={stats.food_rescued_kg} />
        <StatCard tone="green" label="Servings" value={stats.servings_redistributed} />
        <StatCard label="In progress" value={stats.active_donations} />
      </div>
      <div className="card">
        <div className="row between wrap">
          <h3>🤖 Best matches for your requirements</h3>
          <Link to="/ngo/donations" className="btn small">All available food</Link>
        </div>
        {recs === null ? <p>Loading...</p> : recs.length === 0 ? (
          <p className="muted">No matching food right now. <Link to="/ngo/requirements">Add a requirement</Link> so we can match donations to you.</p>
        ) : recs.slice(0, 4).map((d) => (
          <div key={d.id} className="rec">
            <div className="row between wrap">
              <strong>{d.food_type} · {d.quantity_kg} kg</strong>
              <span className="score">{d.match_score}%</span>
            </div>
            <div className="muted small-text">{d.donor_name} · {d.distance_km} km · {d.match_explanation}</div>
            <div className="row between wrap" style={{ marginTop: 6 }}>
              <UrgencyBadge level={d.urgency} hours={d.hours_left} />
              <Link className="btn small primary" to={`/donations/${d.id}`}>View &amp; accept</Link>
            </div>
          </div>
        ))}
      </div>
    </>
  );
}
