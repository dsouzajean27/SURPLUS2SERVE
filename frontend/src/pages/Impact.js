import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import client from "../api/client";
import StatCard from "../components/StatCard";
import { useAuth } from "../context/AuthContext";

export default function Impact() {
  const [d, setD] = useState(null);
  const { user } = useAuth();
  useEffect(() => {
    client.get("/dashboard/impact").then((r) => setD(r.data)).catch(() => setD({}));
  }, []);

  const body = (
    <>
      <h2>Platform impact</h2>
      <p className="muted">Live numbers from completed donations across all donors and recipient organisations.</p>
      {!d ? <p>Loading...</p> : (
        <>
          <div className="grid stats">
            <StatCard tone="green" label="Food rescued (kg)" value={d.food_rescued_kg} />
            <StatCard tone="green" label="Servings redistributed" value={d.servings_redistributed} />
            <StatCard label="Donations completed" value={d.completed_donations} hint={`${d.completion_rate ?? 0}% completion rate`} />
            <StatCard label="Recipient organisations served" value={d.recipient_orgs_served} />
            <StatCard label="Donors participating" value={d.donors_participating} />
            <StatCard tone="amber" label="Food waste avoided (kg)" value={d.waste_avoided_kg} />
            <StatCard tone="amber" label="CO₂e avoided (kg, estimate)" value={d.co2e_avoided_kg_estimate} hint="≈2.5 kg CO₂e per kg of food" />
            <StatCard tone="red" label="Donations expired" value={d.expired_donations} />
          </div>
        </>
      )}
    </>
  );
  if (user) return body;
  return (
    <div className="container">
      <p><Link to="/login">← Login / Register</Link></p>
      {body}
    </div>
  );
}
