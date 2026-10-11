import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import client, { errMsg } from "../api/client";
import { UrgencyBadge } from "../components/Badges";
import { fmtDateTime } from "../utils";

export default function AvailableDonations() {
  const [rows, setRows] = useState(null);
  const [matches, setMatches] = useState({});
  const [q, setQ] = useState("");
  const [urg, setUrg] = useState("all");
  const [maxKm, setMaxKm] = useState("");
  const [sort, setSort] = useState("match");
  const [error, setError] = useState("");

  useEffect(() => {
    Promise.all([client.get("/donations?status_filter=posted"), client.get("/recommendations/for-ngo")])
      .then(([d, r]) => {
        setRows(d.data);
        setMatches(Object.fromEntries(r.data.map((x) => [x.id, x.match_score])));
      })
      .catch((e) => setError(errMsg(e)));
  }, []);

  const list = useMemo(() => {
    let l = (rows || []).filter((d) =>
      (!q || d.food_type.toLowerCase().includes(q.toLowerCase())) &&
      (urg === "all" || d.urgency === urg) &&
      (!maxKm || (d.distance_km ?? 0) <= Number(maxKm)));
    const key = { match: (d) => -(matches[d.id] ?? -1), distance: (d) => d.distance_km ?? 1e9, urgency: (d) => d.hours_left };
    return [...l].sort((a, b) => key[sort](a) - key[sort](b));
  }, [rows, q, urg, maxKm, sort, matches]);

  return (
    <>
      <h2>Available surplus food</h2>
      {error && <div className="alert error">{error}</div>}
      <div className="card row gap wrap filters">
        <input placeholder="Search food type" value={q} onChange={(e) => setQ(e.target.value)} />
        <select value={urg} onChange={(e) => setUrg(e.target.value)}>
          <option value="all">Any urgency</option><option value="high">High</option><option value="medium">Medium</option><option value="low">Low</option>
        </select>
        <input type="number" min="0" placeholder="Max km" value={maxKm} onChange={(e) => setMaxKm(e.target.value)} style={{ width: 110 }} />
        <select value={sort} onChange={(e) => setSort(e.target.value)}>
          <option value="match">Sort: best match</option><option value="distance">Sort: nearest</option><option value="urgency">Sort: most urgent</option>
        </select>
      </div>
      {!rows ? <p>Loading...</p> : list.length === 0 ? <p className="muted">No donations match your filters.</p> : (
        <div className="grid cards">
          {list.map((d) => (
            <div className="card" key={d.id}>
              <div className="row between"><h3>{d.food_type}</h3>{matches[d.id] != null && <span className="score">{matches[d.id]}%</span>}</div>
              <p className="muted small-text">{d.donor_name} · {d.address}</p>
              <p><strong>{d.quantity_kg} kg</strong> · {d.servings} servings · {d.distance_km ?? "?"} km away</p>
              <p className="small-text">Expires {fmtDateTime(d.expiry_time)}</p>
              <UrgencyBadge level={d.urgency} hours={d.hours_left} />
              <div style={{ marginTop: 10 }}><Link className="btn primary small" to={`/donations/${d.id}`}>View &amp; accept</Link></div>
            </div>
          ))}
        </div>
      )}
    </>
  );
}
