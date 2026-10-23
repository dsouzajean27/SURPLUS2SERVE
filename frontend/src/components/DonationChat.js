import { useCallback, useEffect, useRef, useState } from "react";
import client, { errMsg } from "../api/client";
import { fmtDateTime } from "../utils";

function ContactCard({ label, c }) {
  const digits = c.phone ? c.phone.replace(/\D/g, "") : "";
  return (
    <div>
      <strong>{label}: {c.name}</strong>
      <p className="small-text">
        {c.phone
          ? <>📱 <a href={`tel:${c.phone}`}>{c.phone}</a> · <a href={`https://wa.me/${digits}`} target="_blank" rel="noreferrer">WhatsApp</a><br /></>
          : <>📱 No phone added<br /></>}
        ✉️ <a href={`mailto:${c.email}`}>{c.email}</a>
        {c.address && <><br />📍 {c.address}</>}
      </p>
    </div>
  );
}

// Contact details + in-app chat. Only rendered once an NGO has accepted the donation.
export default function DonationChat({ donationId, canSend }) {
  const [contact, setContact] = useState(null);
  const [msgs, setMsgs] = useState([]);
  const [text, setText] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const endRef = useRef(null);

  const load = useCallback(async () => {
    try {
      const [c, m] = await Promise.all([
        client.get(`/donations/${donationId}/contact`),
        client.get(`/donations/${donationId}/messages`),
      ]);
      setContact(c.data);
      setMsgs(m.data);
    } catch (e) { setError(errMsg(e)); }
  }, [donationId]);

  useEffect(() => {
    load();
    const t = setInterval(load, 8000);  // simple polling keeps the chat fresh
    return () => clearInterval(t);
  }, [load]);

  useEffect(() => { endRef.current?.scrollIntoView({ behavior: "smooth" }); }, [msgs.length]);

  async function send(e) {
    e.preventDefault();
    if (!text.trim()) return;
    setBusy(true);
    try {
      await client.post(`/donations/${donationId}/messages`, { text });
      setText("");
      setError("");
      await load();
    } catch (err) { setError(errMsg(err)); } finally { setBusy(false); }
  }

  return (
    <div className="card">
      <h3>📞 Contact &amp; chat</h3>
      {contact && (
        <div className="grid two">
          <ContactCard label="Donor" c={contact.donor} />
          <ContactCard label="Recipient NGO" c={contact.ngo} />
        </div>
      )}
      <div className="chat-box">
        {msgs.length === 0 && <p className="muted small-text">No messages yet. Say hello and agree on a pickup time.</p>}
        {msgs.map((m) => (
          <div key={m.id} className={`chat-msg ${m.mine ? "mine" : ""}`}>
            <div className="chat-meta">{m.mine ? "You" : m.sender_name} · {fmtDateTime(m.created_at)}</div>
            <div>{m.text}</div>
          </div>
        ))}
        <div ref={endRef} />
      </div>
      {error && <div className="alert error">{error}</div>}
      {canSend && (
        <form className="row gap" onSubmit={send}>
          <input className="grow" value={text} maxLength={1000} onChange={(e) => setText(e.target.value)} placeholder="Type a message..." />
          <button className="btn primary" disabled={busy || !text.trim()}>Send</button>
        </form>
      )}
    </div>
  );
}