// API datetimes are UTC. Treat strings without a timezone as UTC, show in local time.
export function parseDate(s) {
  if (!s) return null;
  if (s instanceof Date) return s;
  return new Date(/[zZ]|[+-]\d\d:?\d\d$/.test(s) ? s : s + "Z");
}

export function fmtDateTime(s) {
  const d = parseDate(s);
  return d ? d.toLocaleString([], { day: "2-digit", month: "short", hour: "2-digit", minute: "2-digit" }) : "-";
}

// <input type="datetime-local"> value for a Date (local time)
export function toLocalInput(d) {
  const p = (n) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}T${p(d.getHours())}:${p(d.getMinutes())}`;
}

// datetime-local value -> ISO string in UTC for the API
export function localInputToIso(v) {
  return v ? new Date(v).toISOString() : null;
}

export function hoursText(h) {
  if (h <= 0) return "expired window";
  if (h < 1) return `${Math.round(h * 60)} min left`;
  if (h < 48) return `${h.toFixed(1)} h left`;
  return `${Math.round(h / 24)} days left`;
}

export const STATUS_LABEL = {
  posted: "Posted",
  accepted: "Accepted",
  pickup_pending: "Pickup pending",
  delivered: "Delivered",
  completed: "Completed",
  expired: "Expired",
};

export const FALLBACK_LABEL = { compost: "Composting", animal_feed: "Animal feed", none: "-" };

export const homePathFor = (role) =>
  role === "donor" ? "/donor" : role === "ngo" ? "/ngo" : role === "admin" ? "/admin" : "/login";

// Uploaded images come back as "/uploads/x.jpg" - prefix with the backend origin.
export function imgUrl(path) {
  if (!path) return null;
  if (/^https?:\/\//.test(path)) return path;
  const api = process.env.REACT_APP_API_URL || "http://localhost:8000/api";
  return api.replace(/\/api\/?$/, "") + path;
}

// Phase 5 - food quality verification (keys match backend services/quality.py)
export const CHECKLIST = [
  ["hygienic_prep", "Prepared in a clean kitchen by people with clean hands"],
  ["not_plate_leftovers", "NOT leftovers from anyone's plate / a buffet that was already served"],
  ["stored_properly", "Kept at the storage condition chosen above the whole time"],
  ["clean_container", "Packed in a clean, food-grade container"],
  ["no_spoilage_signs", "No bad smell, mould, slime or discolouration"],
];
export const QUALITY_LABEL = { good: "Good quality", caution: "Check carefully", rejected: "Unsafe" };
