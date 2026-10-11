import { useEffect, useState } from "react";
import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import client from "../api/client";

const LINKS = {
  donor: [["/donor", "Dashboard"], ["/donor/new", "Post food"]],
  ngo: [["/ngo", "Dashboard"], ["/ngo/donations", "Available food"], ["/ngo/pickups", "My pickups"], ["/ngo/requirements", "Requirements"], ["/demand", "Demand"]],
  admin: [["/admin", "Admin"], ["/demand", "Demand"]],
};

export default function Layout({ children }) {
  const { user, logout } = useAuth();
  const nav = useNavigate();
  const [unread, setUnread] = useState(0);
  const [open, setOpen] = useState(false);

  useEffect(() => {
    let alive = true;
    const load = () =>
      client.get("/notifications/unread-count").then((r) => alive && setUnread(r.data.unread)).catch(() => {});
    load();
    const t = setInterval(load, 20000);
    return () => {
      alive = false;
      clearInterval(t);
    };
  }, []);

  return (
    <>
      <header className="topbar">
        <div className="brand" onClick={() => nav("/")}>🌱 Surplus<span>2</span>Serve</div>
        <button className="burger" onClick={() => setOpen(!open)} aria-label="Menu">☰</button>
        <nav className={open ? "open" : ""} onClick={() => setOpen(false)}>
          {(LINKS[user.role] || []).map(([to, label]) => (
            <NavLink key={to} to={to} end>{label}</NavLink>
          ))}
          <NavLink to="/impact">Impact</NavLink>
          <NavLink to="/notifications">
            🔔{unread > 0 && <span className="bubble">{unread}</span>}
          </NavLink>
          <NavLink to="/profile">{user.name}</NavLink>
          <button className="btn small ghost" onClick={() => { logout(); nav("/login"); }}>Logout</button>
        </nav>
      </header>
      <main className="container">{children || <Outlet />}</main>
      <footer className="footer">Surplus2Serve · AI-based surplus food redistribution · DBIT Computer Engineering</footer>
    </>
  );
}
