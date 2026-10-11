import { useEffect, useState } from "react";
import client, { errMsg } from "../api/client";

function Chart({ history, forecast }) {
  const all = [...history.map((h) => ({ ...h, f: false })), ...forecast.map((h) => ({ ...h, f: true }))];
  if (!all.length) return <p className="muted">No requirement history yet - NGOs need to post requirements first.</p>;
  const max = Math.max(...all.map((a) => a.quantity_kg), 1);
  const w = 100 / all.length;
  return (
    <svg viewBox="0 0 400 180" className="chart" role="img" aria-label="Demand history and forecast">
      {all.map((a, i) => {
        const h = (a.quantity_kg / max) * 130;
        return (
          <g key={i}>
            <rect x={(i * w * 4) + 4} y={150 - h} width={w * 4 - 8} height={h} rx="2" fill={a.f ? "#f59e0b" : "#16a34a"}>
              <title>{a.date}: {a.quantity_kg} kg{a.f ? " (forecast)" : ""}</title>
            </rect>
            <text x={(i * w * 4) + w * 2} y="166" fontSize="7" textAnchor="middle" fill="#6b7280">{(a.date || "").slice(5)}</text>
          </g>
        );
      })}
    </svg>
  );
}

export default function Demand() {
  const [data, setData] = useState(null);
  const [ft, setFt] = useState("all");
  const [error, setError] = useState("");

  useEffect(() => {
    setData(null);
    client.get("/demand/forecast", { params: ft === "all" ? {} : { food_type: ft } })
      .then((r) => setData(r.data)).catch((e) => setError(errMsg(e)));
  }, [ft]);

  return (
    <>
      <h2>Demand analysis &amp; forecast</h2>
      <p className="muted">Predicts how many kg of food recipient organisations will request per day over the next 7 days, using linear regression (scikit-learn) on historical requirements.</p>
      {error && <div className="alert error">{error}</div>}
      <div className="card">
        <div className="row between wrap">
          <select value={ft} onChange={(e) => setFt(e.target.value)} style={{ width: "auto" }}>
            <option value="all">All food types</option>
            {(data?.food_types || []).map((t) => <option key={t} value={t}>{t}</option>)}
          </select>
          {data && <span className="badge st-accepted">Expected next 7 days: {data.expected_total_kg_next_7_days} kg</span>}
        </div>
        {!data ? <p>Loading...</p> : (
          <>
            <Chart history={data.history} forecast={data.forecast} />
            <p className="small-text muted"><span className="swatch g" /> history &nbsp; <span className="swatch o" /> forecast · method: {data.method}</p>
          </>
        )}
      </div>
    </>
  );
}
