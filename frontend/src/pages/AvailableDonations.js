import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import client, { errMsg } from "../api/client";
import { QualityBadge, UrgencyBadge } from "../components/Badges";
import { useAuth } from "../context/AuthContext";
import { fmtDateTime, imgUrl } from "../utils";

export default function AvailableDonations() {
  const { user } = useAuth();
  const [rows, setRows] = useState(null);
  const [matches, setMatches] = useState({});
  const [q, setQ] = useState("");
  const [urg, setUrg] = useState("all");
  const [radius, setRadius] = useState("25");  // km, or "any"
  const [sort, setSort] = useState("match");
  const [error, setError] = useState("");

  useEffect(() => {
    const dq = radius === "any" ? "" : `&max_distance_km=${radius}`;
    const rq = radius === "any" ? "" : `?radius_km=${radius}`;
    setRows(null);
    Promise.all([client.get(`/donations?status_filter=posted${dq}`), client.get(`/recommendations/for-ngo${rq}`)])
      .then(([d, r]) => {
        setRows(d.data);
        setMatches(Object.fromEntries(r.data.map((x) => [x.id, x.match_score])));
        setError("");
      })
      .catch((e) => setError(errMsg(e)));
  }, [radius]);

  const list = useMemo(() => {
    let l = (rows || []).filter((d) =>
      (!q || d.food_type.toLowerCase().includes(q.toLowerCase())) &&
      (urg === "all" || d.urgency === urg));
    const key = { match: (d) => -(matches[d.id] ?? -1), distance: (d) => d.distance_km ?? 1e9, urgency: (d) => d.hours_left };
    return [...l].sort((a, b) => key[sort](a) - key[sort](b));
  }, [rows, q, urg, sort, matches]);

  return (
    <>
      <h2>Available surplus food</h2>
      {error && <div className="alert error">{error}</div>}
      {user.latitude == null && <div className="alert error">Your organisation has no location set, so distance filtering is off. Add your address in <Link to="/profile">Profile</Link>.</div>}
      <div className="card row gap wrap filters">
        <input placeholder="Search food type" value={q} onChange={(e) => setQ(e.target.value)} />
        <select value={urg} onChange={(e) => setUrg(e.target.value)}>
          <option value="all">Any urgency</option><option value="high">High</option><option value="medium">Medium</option><option value="low">Low</option>
        </select>
        <select value={radius} onChange={(e) => setRadius(e.target.value)} title="Only show food within this distance of your location">
          <option value="5">Within 5 km</option><option value="10">Within 10 km</option>
          <option value="25">Within 25 km</option><option value="50">Within 50 km</option>
          <option value="any">Any distance</option>
        </select>
        <select value={sort} onChange={(e) => setSort(e.target.value)}>
          <option value="match">Sort: best match</option><option value="distance">Sort: nearest</option><option value="urgency">Sort: most urgent</option>
        </select>
      </div>
      {!rows ? <p>Loading...</p> : list.length === 0 ? <p className="muted">No donations match your filters{radius !== "any" ? ` within ${radius} km` : ""}. Try a wider radius.</p> : (
        <div className="grid cards">
          {list.map((d) => (
            <div className="card" key={d.id}>
              {d.image_url && <img className="food-img" src={imgUrl(d.image_url)} alt={d.food_type} />}
              <div className="row between"><h3>{d.food_type}</h3>{matches[d.id] != null && <span className="score">{matches[d.id]}%</span>}</div>
              <p className="muted small-text">{d.donor_name} · {d.address}</p>
              <p><strong>{d.quantity_kg} kg</strong> · {d.servings} servings · {d.distance_km ?? "?"} km away</p>
              <p className="small-text">Expires {fmtDateTime(d.expiry_time)}</p>
              <UrgencyBadge level={d.urgency} hours={d.hours_left} /> <QualityBadge quality={d.quality} />
              <div style={{ marginTop: 10 }}><Link className="btn primary small" to={`/donations/${d.id}`}>View &amp; accept</Link></div>
            </div>
          ))}
        </div>
      )}
    </>
  );
}
