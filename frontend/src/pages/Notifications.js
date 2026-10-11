import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import client from "../api/client";
import { fmtDateTime } from "../utils";

const ICON = { new_match: "🍽️", accepted: "✅", status_change: "🔄", expiry_warning: "⏰", info: "ℹ️" };

export default function Notifications() {
  const [rows, setRows] = useState(null);
  const load = useCallback(() => client.get("/notifications").then((r) => setRows(r.data)).catch(() => setRows([])), []);
  useEffect(() => { load(); }, [load]);

  async function readAll() { await client.patch("/notifications/read-all"); load(); }
  async function read(n) { if (!n.read) { await client.patch(`/notifications/${n.id}/read`); load(); } }

  return (
    <>
      <div className="row between wrap"><h2>Notifications</h2>
        <button className="btn small" onClick={readAll}>Mark all as read</button></div>
      <div className="card">
        {!rows ? <p>Loading...</p> : rows.length === 0 ? <p className="muted">You're all caught up.</p> : rows.map((n) => (
          <div key={n.id} className={`note ${n.read ? "" : "unread"}`} onClick={() => read(n)}>
            <span className="ico">{ICON[n.type] || "ℹ️"}</span>
            <div className="grow">
              <div>{n.message}</div>
              <div className="muted small-text">{fmtDateTime(n.created_at)}{n.related_donation_id && <> · <Link to={`/donations/${n.related_donation_id}`}>View donation</Link></>}</div>
            </div>
          </div>
        ))}
      </div>
    </>
  );
}
