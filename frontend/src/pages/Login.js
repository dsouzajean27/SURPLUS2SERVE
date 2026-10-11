import { useState } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";
import client, { errMsg } from "../api/client";
import { useAuth } from "../context/AuthContext";
import LocationInput from "../components/LocationInput";
import { homePathFor } from "../utils";

export default function Login({ mode = "login" }) {
  const { user, login } = useAuth();
  const nav = useNavigate();
  const [f, setF] = useState({ name: "", email: "", password: "", role: "donor", phone: "", admin_code: "" });
  const [loc, setLoc] = useState({ address: "", lat: null, lng: null });
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const reg = mode === "register";
  const set = (k) => (e) => setF({ ...f, [k]: e.target.value });

  if (user) return <Navigate to={homePathFor(user.role)} replace />;

  async function submit(e) {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      if (reg) {
        const body = {
          name: f.name, email: f.email, password: f.password, role: f.role,
          phone: f.phone || null,
          location: { address: loc.address, lat: loc.lat, lng: loc.lng },
        };
        if (f.role === "admin") body.admin_code = f.admin_code;
        await client.post("/auth/register", body);
      }
      const u = await login(f.email, f.password);
      nav(homePathFor(u.role), { replace: true });
    } catch (err) {
      setError(errMsg(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="auth-wrap">
      <div className="auth-hero">
        <h1>🌱 Surplus<span>2</span>Serve</h1>
        <p>AI-based surplus food redistribution. Donors post surplus food, the system finds the best-suited NGO, and every meal is tracked from pickup to delivery.</p>
        <Link to="/impact" className="btn ghost light">See our impact</Link>
      </div>
      <form className="card auth-card" onSubmit={submit}>
        <h2>{reg ? "Create your account" : "Welcome back"}</h2>
        {error && <div className="alert error">{error}</div>}
        {reg && (
          <>
            <div className="field">
              <label>I am a</label>
              <select value={f.role} onChange={set("role")}>
                <option value="donor">Food donor (restaurant, hotel, store, event)</option>
                <option value="ngo">Recipient organisation (NGO, food bank, shelter)</option>
                <option value="admin">Administrator</option>
              </select>
            </div>
            <div className="field"><label>Organisation / name</label><input value={f.name} onChange={set("name")} required /></div>
            <div className="field"><label>Phone</label><input value={f.phone} onChange={set("phone")} /></div>
            <LocationInput label="Address" value={loc} onChange={setLoc} />
            {f.role === "admin" && (
              <div className="field"><label>Admin sign-up code</label><input value={f.admin_code} onChange={set("admin_code")} required /></div>
            )}
          </>
        )}
        <div className="field"><label>Email</label><input type="email" value={f.email} onChange={set("email")} required /></div>
        <div className="field"><label>Password</label><input type="password" minLength={6} value={f.password} onChange={set("password")} required /></div>
        <button className="btn primary block" disabled={busy}>{busy ? "Please wait..." : reg ? "Register" : "Login"}</button>
        <p className="muted center">
          {reg ? <>Already have an account? <Link to="/login">Login</Link></> : <>New here? <Link to="/register">Register</Link></>}
        </p>
      </form>
    </div>
  );
}
