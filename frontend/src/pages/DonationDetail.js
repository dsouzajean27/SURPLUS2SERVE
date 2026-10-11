import { useCallback, useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import client, { errMsg } from "../api/client";
import { useAuth } from "../context/AuthContext";
import { StatusBadge, UrgencyBadge } from "../components/Badges";
import Timeline from "../components/Timeline";
import MapView from "../components/MapView";
import { FALLBACK_LABEL, fmtDateTime } from "../utils";

const FACTORS = [
  ["food", "Food match"], ["quantity", "Quantity"], ["distance", "Distance"],
  ["urgency_pickup", "Urgency / pickup"], ["demand", "Demand"],
];

function Recommendations({ rec }) {
  if (!rec) return null;
  if (rec.fallback) {
    return (
      <div className="card fallback">
        <h3>♻️ Circular-economy option</h3>
        <p>{rec.fallback.message}</p>
        <span className="badge st-posted">Suggested: {FALLBACK_LABEL[rec.fallback.type]}</span>
      </div>
    );
  }
  return (
    <div className="card">
      <h3>🤖 AI-recommended recipients</h3>
      <p className="muted small-text">Ranked by food match, quantity fit, distance, urgency/pickup availability and demand. The AI ranks recipients - it does not judge food safety.</p>
      {rec.recipients.map((r) => (
        <div key={r.requirement_id} className={`rec ${r.rank === 1 ? "best" : ""}`}>
          <div className="row between">
            <strong>#{r.rank} {r.ngo_name}{r.rank === 1 && " ⭐ recommended"}</strong>
            <span className="score">{r.score}%</span>
          </div>
          <div className="muted small-text">
            Needs {r.requirement.required_quantity_kg} kg {r.requirement.food_type} · {r.distance_km} km away · pickup: {r.requirement.pickup_availability.replace("_", " ")} · {r.explanation}
          </div>
          <div className="factors">
            {FACTORS.map(([k, label]) => (
              <div key={k} title={`${label}: ${r.breakdown[k]}%`}>
                <span className="small-text">{label}</span>
                <div className="bar"><i style={{ width: `${r.breakdown[k]}%` }} /></div>
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}

export default function DonationDetail() {
  const { id } = useParams();
  const { user } = useAuth();
  const nav = useNavigate();
  const [d, setD] = useState(null);
  const [history, setHistory] = useState([]);
  const [rec, setRec] = useState(null);
  const [route, setRoute] = useState(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    try {
      const [dr, hr] = await Promise.all([client.get(`/donations/${id}`), client.get(`/donations/${id}/history`)]);
      setD(dr.data);
      setHistory(hr.data);
      setError("");
      const x = dr.data;
      if (["donor", "admin"].includes(user.role) && ["posted", "expired"].includes(x.status)) {
        client.get(`/recommendations/donation/${id}`).then((r) => setRec(r.data)).catch(() => {});
      } else setRec(null);
      if (x.accepted_ngo_id && ["accepted", "pickup_pending", "delivered", "completed"].includes(x.status)) {
        client.get(`/routes/donation/${id}`).then((r) => setRoute(r.data)).catch(() => setRoute(null));
      } else setRoute(null);
    } catch (e) {
      setError(errMsg(e));
    }
  }, [id, user.role]);
  useEffect(() => { load(); }, [load]);

  async function act(fn) {
    setBusy(true);
    setError("");
    try { await fn(); await load(); } catch (e) { setError(errMsg(e)); } finally { setBusy(false); }
  }
  const setStatus = (status) => act(() => client.patch(`/donations/${id}/status`, { status }));

  if (error && !d) return <div className="alert error">{error}</div>;
  if (!d) return <p>Loading...</p>;

  const isOwner = user.role === "donor" && d.donor_id === user.id;
  const isRecipient = user.role === "ngo" && d.accepted_ngo_id === user.id;
  const isAdmin = user.role === "admin";
  const active = ["posted", "accepted", "pickup_pending"].includes(d.status);
  const actions = [];
  if (user.role === "ngo" && d.status === "posted")
    actions.push(<button key="a" className="btn primary" disabled={busy} onClick={() => act(() => client.post(`/donations/${id}/accept`))}>✅ Accept this donation</button>);
  if (d.status === "accepted" && (isOwner || isRecipient || isAdmin))
    actions.push(<button key="p" className="btn primary" disabled={busy} onClick={() => setStatus("pickup_pending")}>🚚 Mark pickup pending</button>);
  if (d.status === "pickup_pending" && (isOwner || isRecipient || isAdmin))
    actions.push(<button key="d" className="btn primary" disabled={busy} onClick={() => setStatus("delivered")}>📦 Mark delivered</button>);
  if (d.status === "delivered" && (isRecipient || isAdmin))
    actions.push(<button key="c" className="btn primary" disabled={busy} onClick={() => setStatus("completed")}>🎉 Confirm received &amp; complete</button>);
  if (active && (isOwner || isAdmin))
    actions.push(<button key="e" className="btn danger" disabled={busy} onClick={() => window.confirm("Mark this donation as expired?") && setStatus("expired")}>Mark expired</button>);
  if ((isOwner && d.status === "posted") || isAdmin)
    actions.push(<button key="x" className="btn danger ghost" disabled={busy} onClick={() => window.confirm("Delete this donation?") && act(async () => { await client.delete(`/donations/${id}`); nav(-1); })}>Delete</button>);

  const markers = [{ lat: d.latitude, lng: d.longitude, kind: "donor", label: `Pickup: ${d.donor_name || "Donor"}` }];
  if (route) markers.push({ lat: route.to.lat, lng: route.to.lng, kind: "ngo", label: `Recipient: ${route.to.name}` });

  return (
    <>
      <p><button className="link" onClick={() => nav(-1)}>← Back</button></p>
      {error && <div className="alert error">{error}</div>}
      <div className="grid two">
        <div>
          <div className="card">
            <div className="row between wrap">
              <h2>{d.food_type}</h2>
              <StatusBadge status={d.status} />
            </div>
            <table className="kv"><tbody>
              <tr><td>Quantity</td><td>{d.quantity_kg} kg · {d.servings} servings</td></tr>
              <tr><td>Donor</td><td>{d.donor_name}</td></tr>
              <tr><td>Pickup address</td><td>{d.address}</td></tr>
              <tr><td>Storage</td><td>{d.storage_condition.replace("_", " ")}</td></tr>
              <tr><td>Prepared</td><td>{fmtDateTime(d.prep_time)}</td></tr>
              <tr><td>Expires</td><td>{fmtDateTime(d.expiry_time)}</td></tr>
              {active && <tr><td>Urgency</td><td><UrgencyBadge level={d.urgency} /> <span className="muted small-text">{d.urgency_reason}</span></td></tr>}
              {d.distance_km != null && <tr><td>Distance from you</td><td>{d.distance_km} km</td></tr>}
              <tr><td>Recipient</td><td>{d.accepted_ngo_name || "Not accepted yet"}</td></tr>
              {d.fallback_recommendation !== "none" && <tr><td>Recovery option</td><td>{FALLBACK_LABEL[d.fallback_recommendation]}</td></tr>}
            </tbody></table>
            {actions.length > 0 && <div className="row gap wrap actions">{actions}</div>}
          </div>
          <Recommendations rec={rec} />
          <div className="card"><h3>Tracking</h3><Timeline history={history} /></div>
        </div>
        <div>
          <div className="card">
            <h3>📍 {route ? "Pickup route" : "Location"}</h3>
            <MapView markers={markers} line={route?.geometry} height={320} />
            {route && (
              <p>
                <strong>{route.distance_km} km</strong> · ~{Math.round(route.duration_min)} min
                <span className="muted small-text"> ({route.source === "osrm" ? "road route via OSRM" : "estimated - routing service unreachable"})</span>
                <br />
                <a href={route.directions_url} target="_blank" rel="noreferrer">Open turn-by-turn directions ↗</a>
              </p>
            )}
            {user.role === "ngo" && !isRecipient && <p className="muted small-text">Accept the donation to get a pickup route.</p>}
          </div>
        </div>
      </div>
    </>
  );
}
