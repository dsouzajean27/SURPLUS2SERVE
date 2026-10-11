import { STATUS_LABEL, fmtDateTime } from "../utils";

export default function Timeline({ history }) {
  if (!history?.length) return <p className="muted">No history yet.</p>;
  return (
    <ol className="timeline">
      {history.map((h) => (
        <li key={h.id}>
          <span className={`dot st-${h.status}`} />
          <div>
            <strong>{STATUS_LABEL[h.status] || h.status}</strong>
            <span className="muted"> · {fmtDateTime(h.changed_at)}</span>
            {h.note && <div className="muted small-text">{h.note}</div>}
          </div>
        </li>
      ))}
    </ol>
  );
}
