import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import client, { errMsg } from "../api/client";
import { StatusBadge, UrgencyBadge } from "../components/Badges";
import MapView from "../components/MapView";
import { fmtDateTime } from "../utils";

export default function Pickups() {
  const [rows, setRows] = useState(null);
  const [col, setCol] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    client.get("/donations?mine=true").then((r) => setRows(r.data)).catch((e) => setError(errMsg(e)));
    client.get("/routes/collection").then((r) => setCol(r.data)).catch(() => {});
  }, []);

  const markers = col?.stops?.length
    ? [{ lat: col.start.lat, lng: col.start.lng, kind: "ngo", label: "Your organisation" },
       ...col.stops.map((s) => ({ lat: s.lat, lng: s.lng, kind: "donor", label: `${s.order}. ${s.donor_name} - ${s.food_type}` }))]
    : [];
  const line = col?.stops?.length ? [[col.start.lat, col.start.lng], ...col.stops.map((s) => [s.lat, s.lng])] : null;

  return (
    <>
      <h2>My pickups &amp; deliveries</h2>
      {error && <div className="alert error">{error}</div>}
      {col?.stops?.length > 0 && (
        <div className="card">
          <h3>🚚 Suggested collection trip ({col.total_km} km)</h3>
          <p className="muted small-text">Nearest-neighbour order for collecting from several donors in one trip.</p>
          <MapView markers={markers} line={line} height={260} />
          <ol>{col.stops.map((s) => <li key={s.donation_id}>{s.donor_name} – {s.food_type} <span className="muted">({s.leg_km} km leg)</span></li>)}</ol>
        </div>
      )}
      <div className="card">
        {!rows ? <p>Loading...</p> : rows.length === 0 ? <p className="muted">You haven't accepted any donations yet. <Link to="/ngo/donations">Browse available food</Link>.</p> : (
          <div className="table-wrap"><table>
            <thead><tr><th>Food</th><th>From</th><th>Qty</th><th>Expires</th><th>Status</th><th /></tr></thead>
            <tbody>{rows.map((d) => (
              <tr key={d.id}>
                <td><strong>{d.food_type}</strong></td>
                <td>{d.donor_name}<div className="muted small-text">{d.address}</div></td>
                <td>{d.quantity_kg} kg</td>
                <td>{fmtDateTime(d.expiry_time)} {["accepted", "pickup_pending"].includes(d.status) && <div><UrgencyBadge level={d.urgency} /></div>}</td>
                <td><StatusBadge status={d.status} /></td>
                <td><Link className="btn small" to={`/donations/${d.id}`}>Open</Link></td>
              </tr>))}
            </tbody></table></div>
        )}
      </div>
    </>
  );
}
