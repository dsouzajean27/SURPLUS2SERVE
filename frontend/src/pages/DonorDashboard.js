import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import client, { errMsg } from "../api/client";
import StatCard from "../components/StatCard";
import { StatusBadge, UrgencyBadge } from "../components/Badges";
import { fmtDateTime, imgUrl } from "../utils";

export default function DonorDashboard() {
  const [donations, setDonations] = useState(null);
  const [stats, setStats] = useState({});
  const [error, setError] = useState("");
  const [filter, setFilter] = useState("all");

  const load = useCallback(async () => {
    try {
      const [d, s] = await Promise.all([client.get("/donations"), client.get("/dashboard/donor")]);
      setDonations(d.data);
      setStats(s.data);
    } catch (e) {
      setError(errMsg(e));
    }
  }, []);
  useEffect(() => { load(); }, [load]);

  const rows = (donations || []).filter((d) => filter === "all" || d.status === filter);
  return (
    <>
      <div className="row between wrap">
        <h2>Donor dashboard</h2>
        <Link to="/donor/new" className="btn primary">+ Post surplus food</Link>
      </div>
      {error && <div className="alert error">{error}</div>}
      <div className="grid stats">
        <StatCard label="Total donations" value={stats.total_donations} />
        <StatCard label="Active" value={stats.active_donations} />
        <StatCard tone="green" label="Completed" value={stats.completed_donations} />
        <StatCard tone="green" label="Food rescued (kg)" value={stats.food_rescued_kg} />
        <StatCard tone="green" label="Servings" value={stats.servings_redistributed} />
        <StatCard tone="red" label="Expired" value={stats.expired_donations} />
      </div>

      <div className="card">
        <div className="row between wrap">
          <h3>My donations</h3>
          <select value={filter} onChange={(e) => setFilter(e.target.value)} style={{ width: "auto" }}>
            <option value="all">All statuses</option>
            {["posted", "accepted", "pickup_pending", "delivered", "completed", "expired"].map((s) => (
              <option key={s} value={s}>{s.replace("_", " ")}</option>
            ))}
          </select>
        </div>
        {!donations ? <p>Loading...</p> : rows.length === 0 ? (
          <p className="muted">Nothing here yet. <Link to="/donor/new">Post your first surplus food</Link>.</p>
        ) : (
          <div className="table-wrap">
            <table>
              <thead><tr><th>Food</th><th>Qty</th><th>Expires</th><th>Urgency</th><th>Status</th><th>Recipient</th><th /></tr></thead>
              <tbody>
                {rows.map((d) => (
                  <tr key={d.id}>
                    <td>{d.image_url && <img className="food-thumb" src={imgUrl(d.image_url)} alt="" />}<strong>{d.food_type}</strong><div className="muted small-text">{d.address}</div></td>
                    <td>{d.quantity_kg} kg<div className="muted small-text">{d.servings} servings</div></td>
                    <td>{fmtDateTime(d.expiry_time)}</td>
                    <td>{["posted", "accepted", "pickup_pending"].includes(d.status) ? <UrgencyBadge level={d.urgency} hours={d.hours_left} /> : "-"}</td>
                    <td><StatusBadge status={d.status} /></td>
                    <td>{d.accepted_ngo_name || "-"}</td>
                    <td><Link className="btn small" to={`/donations/${d.id}`}>Open</Link></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </>
  );
}