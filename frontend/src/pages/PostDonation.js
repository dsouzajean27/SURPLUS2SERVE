import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import client, { errMsg } from "../api/client";
import { useAuth } from "../context/AuthContext";
import LocationInput from "../components/LocationInput";
import { QualityBadge } from "../components/Badges";
import { CHECKLIST, localInputToIso, toLocalInput } from "../utils";

export default function PostDonation() {
  const { user } = useAuth();
  const nav = useNavigate();
  const now = new Date();
  const [f, setF] = useState({
    food_type: "", quantity_kg: "", servings: "", storage_condition: "refrigerated",
    prep_time: toLocalInput(new Date(now.getTime() - 30 * 60000)),
    expiry_time: toLocalInput(new Date(now.getTime() + 6 * 3600000)),
  });
  const [loc, setLoc] = useState({
    address: user.address || "", lat: user.latitude ?? null, lng: user.longitude ?? null,
  });
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [photo, setPhoto] = useState(null);
  const [preview, setPreview] = useState(null);
  const set = (k) => (e) => setF({ ...f, [k]: e.target.value });
  const [allergens, setAllergens] = useState("");
  const [packaging, setPackaging] = useState("sealed");
  const [checks, setChecks] = useState(Object.fromEntries(CHECKLIST.map(([k]) => [k, false])));
  const [quality, setQuality] = useState(null);

  // Live food-safety score (same rules the server enforces when you post)
  useEffect(() => {
    if (!f.expiry_time) return;
    const t = setTimeout(() => {
      client.post("/donations/quality-preview", {
        food_type: f.food_type, storage_condition: f.storage_condition,
        prep_time: f.prep_time ? localInputToIso(f.prep_time) : null,
        expiry_time: localInputToIso(f.expiry_time),
        packaging, hygiene_checklist: checks, has_photo: !!photo,
      }).then((r) => setQuality(r.data)).catch(() => setQuality(null));
    }, 400);
    return () => clearTimeout(t);
  }, [f.food_type, f.storage_condition, f.prep_time, f.expiry_time, packaging, checks, photo]);

  function pickPhoto(e) {
    const file = e.target.files[0];
    if (!file) return;
    if (file.size > 5 * 1024 * 1024) { setError("Photo is too large (max 5 MB)"); return; }
    setError("");
    setPhoto(file);
    setPreview(URL.createObjectURL(file));
  }

  async function submit(e) {
    e.preventDefault();
    setError("");
    if (new Date(f.expiry_time) <= new Date()) return setError("Expiry time must be in the future");
    if (f.prep_time && new Date(f.prep_time) >= new Date(f.expiry_time)) return setError("Expiry must be after preparation time");
    if (quality?.status === "rejected") return setError("This food fails the safety check: " + (quality.blockers.join(" ") || "score too low") + " It cannot be donated.");
    setBusy(true);
    try {
      let image_url = null;
      if (photo) {
        const fd = new FormData();
        fd.append("file", photo);
        const up = await client.post("/uploads/food-image", fd);
        image_url = up.data.image_url;
      }
      const res = await client.post("/donations", {
        image_url,
        allergens: allergens.trim() || null,
        packaging,
        hygiene_checklist: checks,
        food_type: f.food_type,
        quantity_kg: Number(f.quantity_kg),
        servings: Number(f.servings),
        storage_condition: f.storage_condition,
        prep_time: localInputToIso(f.prep_time),
        expiry_time: localInputToIso(f.expiry_time),
        location: { address: loc.address, lat: loc.lat, lng: loc.lng },
      });
      nav(`/donations/${res.data.id}`);
    } catch (err) {
      setError(errMsg(err));
      setBusy(false);
    }
  }

  return (
    <form className="card narrow" onSubmit={submit}>
      <h2>Post surplus food</h2>
      <p className="muted">The system will rank the best-suited recipient organisations as soon as you post.</p>
      {error && <div className="alert error">{error}</div>}
      <div className="field"><label>Food type / description</label>
        <input value={f.food_type} onChange={set("food_type")} placeholder="e.g. cooked rice, bread, mixed vegetables" required /></div>
      <div className="row gap">
        <div className="field grow"><label>Quantity (kg)</label>
          <input type="number" min="0.1" step="0.1" value={f.quantity_kg} onChange={set("quantity_kg")} required /></div>
        <div className="field grow"><label>Servings</label>
          <input type="number" min="1" step="1" value={f.servings} onChange={set("servings")} required /></div>
      </div>
      <div className="field"><label>Storage condition</label>
        <select value={f.storage_condition} onChange={set("storage_condition")}>
          <option value="room_temp">Room temperature</option>
          <option value="refrigerated">Refrigerated</option>
          <option value="frozen">Frozen</option>
        </select></div>
      <div className="row gap">
        <div className="field grow"><label>Prepared at</label>
          <input type="datetime-local" value={f.prep_time} onChange={set("prep_time")} /></div>
        <div className="field grow"><label>Expiry / best before</label>
          <input type="datetime-local" value={f.expiry_time} onChange={set("expiry_time")} required /></div>
      </div>
      <div className="field"><label>Food photo (optional, JPG/PNG/WEBP, max 5 MB)</label>
        <input type="file" accept="image/jpeg,image/png,image/webp" onChange={pickPhoto} />
        {preview && <img className="img-preview" src={preview} alt="Preview" />}</div>
      <div className="field"><label>Allergens (optional)</label>
        <input value={allergens} onChange={(e) => setAllergens(e.target.value)} placeholder="e.g. nuts, dairy, gluten - leave empty if none known" maxLength={255} /></div>
      <div className="field"><label>Packaging</label>
        <select value={packaging} onChange={(e) => setPackaging(e.target.value)}>
          <option value="sealed">Sealed container / wrapped</option>
          <option value="covered">Covered (lid / foil)</option>
          <option value="open">Open</option>
        </select></div>
      <fieldset className="safety-box">
        <legend>🧪 Food-safety declaration</legend>
        <p className="muted small-text">Tick only what is true. Recipients see your answers, and food that fails the safety rules cannot be posted.</p>
        {CHECKLIST.map(([k, label]) => (
          <label className="check" key={k}>
            <input type="checkbox" checked={checks[k]} onChange={(e) => setChecks({ ...checks, [k]: e.target.checked })} /> {label}
          </label>
        ))}
        {quality && (
          <div className={`quality-preview q-${quality.status}`}>
            <QualityBadge quality={quality} />
            {[...quality.blockers, ...quality.notes].map((n, i) => <div className="small-text" key={i}>• {n}</div>)}
          </div>
        )}
      </fieldset>
      <LocationInput label="Pickup location" value={loc} onChange={setLoc} />
      <button className="btn primary block" disabled={busy}>{busy ? "Posting..." : "Post donation"}</button>
    </form>
  );
}
