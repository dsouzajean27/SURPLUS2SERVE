import { STATUS_LABEL, hoursText } from "../utils";

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
