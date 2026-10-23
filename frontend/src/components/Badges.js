import { STATUS_LABEL, QUALITY_LABEL, hoursText } from "../utils";

export function StatusBadge({ status }) {
  return <span className={`badge st-${status}`}>{STATUS_LABEL[status] || status}</span>;
}

export function UrgencyBadge({ level, hours }) {
  return (
    <span className={`badge urg-${level}`} title="Urgency from expiry, prep time and storage">
      {level.charAt(0).toUpperCase() + level.slice(1)} urgency{hours !== undefined ? ` · ${hoursText(hours)}` : ""}
    </span>
  );
}

export function QualityBadge({ quality }) {
  if (!quality) return null;
  return (
    <span className={`badge q-${quality.status}`} title="Food-safety score from storage, prep time, packaging and the donor's checklist">
      {QUALITY_LABEL[quality.status] || quality.status} · {quality.score}/100
    </span>
  );
}
