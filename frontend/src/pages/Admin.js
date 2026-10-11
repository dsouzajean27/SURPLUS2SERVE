import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import client, { errMsg } from "../api/client";
import StatCard from "../components/StatCard";
import { StatusBadge } from "../components/Badges";
import { fmtDateTime } from "../utils";

export default function AdminDashboard() {
  const [ov, setOv] = useState(null);
  const [users, setUsers] = useState([]);
  const [donations, setDonations] = useState([]);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    try {
      const [o, u, d] = await Promise.all([client.get("/admin/overview"), client.get("/admin/users"), client.get("/donations")]);
      setOv(o.data); setUsers(u.data); setDonations(d.data);
    } catch (e) { setError(errMsg(e)); }
  }, []);
  useEffect(() => { load(); }, [load]);

  async function verify(u) {
    await client.patch(`/admin/users/${u.id}/verify`, null, { params: { verified: !u.verified } });
    load();
  }
  async function del(id) {
    if (!window.confirm("Delete this donation record?")) return;
    try { await client.delete(`/donations/${id}`); load(); } catch (e) { setError(errMsg(e)); }
  }

  if (!ov) return error ? <div className="alert error">{error}</div> : <p>Loading...</p>;
  const i = ov.impact;
  return (
    <>
      <h2>Admin dashboard</h2>
      {error && <div className="alert error">{error}</div>}
      <div className="grid stats">
        <StatCard label="Donors" value={ov.users_by_role.donor || 0} />
        <StatCard label="Recipient orgs" value={ov.users_by_role.ngo || 0} />
        <StatCard tone="amber" label="Awaiting verification" value={ov.unverified_users} />
        <StatCard label="Total donations" value={i.total_donations} />
        <StatCard label="Requirements" value={ov.total_requirements} />
        <StatCard tone="green" label="Completed" value={i.completed_donations} hint={`${i.completion_rate}% rate`} />
        <StatCard tone="green" label="Food rescued (kg)" value={i.food_rescued_kg} />
        <StatCard tone="red" label="Expired" value={i.expired_donations} />
      </div>

      <div className="card">
        <h3>Donations by status</h3>
        <div className="row gap wrap">
          {Object.entries(ov.donations_by_status).map(([s, n]) => <span key={s} className="row gap"><StatusBadge status={s} /> <strong>{n}</strong></span>)}
          {Object.keys(ov.donations_by_status).length === 0 && <span className="muted">No donations yet</span>}
        </div>
      </div>

      <div className="grid two">
        <div className="card">
          <h3>Users</h3>
          <div className="table-wrap"><table>
            <thead><tr><th>Name</th><th>Role</th><th>Verified</th></tr></thead>
            <tbody>{users.map((u) => (
              <tr key={u.id}>
                <td><strong>{u.name}</strong><div className="muted small-text">{u.email}</div></td>
                <td>{u.role}</td>
                <td>{u.role === "admin" ? "✅" : <button className={`btn small ${u.verified ? "" : "primary"}`} onClick={() => verify(u)}>{u.verified ? "Revoke" : "Verify"}</button>}</td>
              </tr>))}</tbody></table></div>
        </div>
        <div className="card">
          <h3>Recent activity</h3>
          {ov.recent_activity.length === 0 ? <p className="muted">No activity yet.</p> : ov.recent_activity.map((a, k) => (
            <div key={k} className="note"><div className="grow">
              <Link to={`/donations/${a.donation_id}`}>{a.food_type}</Link> → <StatusBadge status={a.status} />
              <div className="muted small-text">{fmtDateTime(a.at)}{a.note ? ` · ${a.note}` : ""}</div></div></div>
          ))}
        </div>
      </div>

      <div className="card">
        <h3>All donations</h3>
        <div className="table-wrap"><table>
          <thead><tr><th>Food</th><th>Donor</th><th>Recipient</th><th>Status</th><th /></tr></thead>
          <tbody>{donations.map((d) => (
            <tr key={d.id}>
              <td><strong>{d.food_type}</strong> <span className="muted small-text">{d.quantity_kg} kg</span></td>
              <td>{d.donor_name}</td><td>{d.accepted_ngo_name || "-"}</td>
              <td><StatusBadge status={d.status} /></td>
              <td className="row gap"><Link className="btn small" to={`/donations/${d.id}`}>Open</Link>
                <button className="btn small danger ghost" onClick={() => del(d.id)}>Delete</button></td>
            </tr>))}</tbody></table></div>
      </div>
    </>
  );
}
