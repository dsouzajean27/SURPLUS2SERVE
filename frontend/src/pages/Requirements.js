import { useCallback, useEffect, useState } from "react";
import client, { errMsg } from "../api/client";
import { useAuth } from "../context/AuthContext";
import LocationInput from "../components/LocationInput";
import { fmtDateTime, localInputToIso } from "../utils";

const EMPTY = { food_type: "", required_quantity_kg: "", urgency: "medium", pickup_availability: "flexible", deadline: "" };

export default function Requirements() {
  const { user } = useAuth();
  const [rows, setRows] = useState(null);
  const [f, setF] = useState(EMPTY);
  const [loc, setLoc] = useState({ address: user.address || "", lat: user.latitude ?? null, lng: user.longitude ?? null });
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const set = (k) => (e) => setF({ ...f, [k]: e.target.value });

  const load = useCallback(() =>
    client.get("/requirements?mine=true").then((r) => setRows(r.data)).catch((e) => setError(errMsg(e))), []);
  useEffect(() => { load(); }, [load]);

  async function submit(e) {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      await client.post("/requirements", {
        food_type: f.food_type,
        required_quantity_kg: Number(f.required_quantity_kg),
        urgency: f.urgency,
        pickup_availability: f.pickup_availability,
        deadline: localInputToIso(f.deadline),
        location: { address: loc.address, lat: loc.lat, lng: loc.lng },
      });
      setF(EMPTY);
      await load();
    } catch (err) {
      setError(errMsg(err));
    } finally {
      setBusy(false);
    }
  }

  async function remove(id) {
    if (!window.confirm("Delete this requirement?")) return;
    try { await client.delete(`/requirements/${id}`); load(); } catch (e) { setError(errMsg(e)); }
  }

  return (
    <div className="grid two">
      <form className="card" onSubmit={submit}>
        <h2>Add a food requirement</h2>
        <p className="muted small-text">Use <code>any</code> as food type if you can use every kind of food.</p>
        {error && <div className="alert error">{error}</div>}
        <div className="field"><label>Food type needed</label>
          <input value={f.food_type} onChange={set("food_type")} placeholder="e.g. rice, bread, cooked meals, any" required /></div>
        <div className="row gap">
          <div className="field grow"><label>Quantity needed (kg)</label>
            <input type="number" min="0.1" step="0.1" value={f.required_quantity_kg} onChange={set("required_quantity_kg")} required /></div>
          <div className="field grow"><label>Urgency</label>
            <select value={f.urgency} onChange={set("urgency")}><option value="low">Low</option><option value="medium">Medium</option><option value="high">High</option></select></div>
        </div>
        <div className="row gap">
          <div className="field grow"><label>Pickup availability</label>
            <select value={f.pickup_availability} onChange={set("pickup_availability")}>
              <option value="immediate">Immediate</option><option value="within_2h">Within 2 hours</option>
              <option value="later_today">Later today</option><option value="flexible">Flexible</option></select></div>
          <div className="field grow"><label>Needed by (optional)</label>
            <input type="datetime-local" value={f.deadline} onChange={set("deadline")} /></div>
        </div>
        <LocationInput label="Collection location" value={loc} onChange={setLoc} />
        <button className="btn primary block" disabled={busy}>{busy ? "Saving..." : "Add requirement"}</button>
      </form>

      <div className="card">
        <h2>My requirements</h2>
        {!rows ? <p>Loading...</p> : rows.length === 0 ? <p className="muted">None yet.</p> : rows.map((r) => (
          <div key={r.id} className="rec">
            <div className="row between"><strong>{r.food_type} · {r.required_quantity_kg} kg</strong>
              <button className="btn small danger ghost" onClick={() => remove(r.id)}>Delete</button></div>
            <div className="muted small-text">
              <span className={`badge urg-${r.urgency}`}>{r.urgency}</span> pickup: {r.pickup_availability.replace("_", " ")}
              {r.deadline && <> · needed by {fmtDateTime(r.deadline)}</>}
              <div>{r.address}</div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
