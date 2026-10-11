import { useState } from "react";
import client, { errMsg } from "../api/client";
import { useAuth } from "../context/AuthContext";
import LocationInput from "../components/LocationInput";

export default function Profile() {
  const { user, updateUser } = useAuth();
  const [name, setName] = useState(user.name);
  const [phone, setPhone] = useState(user.phone || "");
  const [loc, setLoc] = useState({ address: user.address || "", lat: user.latitude ?? null, lng: user.longitude ?? null });
  const [msg, setMsg] = useState("");
  const [error, setError] = useState("");

  async function save(e) {
    e.preventDefault();
    setMsg(""); setError("");
    try {
      const r = await client.patch("/auth/me", { name, phone, location: { address: loc.address, lat: loc.lat, lng: loc.lng } });
      updateUser(r.data);
      setMsg("Profile saved");
    } catch (err) { setError(errMsg(err)); }
  }

  return (
    <form className="card narrow" onSubmit={save}>
      <h2>My profile</h2>
      <p className="muted">{user.email} · {user.role} · {user.verified ? "✅ verified" : "⏳ awaiting admin verification"}</p>
      {msg && <div className="alert ok">{msg}</div>}
      {error && <div className="alert error">{error}</div>}
      <div className="field"><label>Name</label><input value={name} onChange={(e) => setName(e.target.value)} required /></div>
      <div className="field"><label>Phone</label><input value={phone} onChange={(e) => setPhone(e.target.value)} /></div>
      <LocationInput value={loc} onChange={setLoc} />
      <button className="btn primary">Save changes</button>
    </form>
  );
}
