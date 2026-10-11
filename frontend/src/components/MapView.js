import { useEffect } from "react";
import { MapContainer, TileLayer, Marker, Popup, Polyline, useMap, useMapEvents } from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";

// CRA/webpack can't resolve Leaflet's default marker images - point to the CDN copies.
const icon = (color) =>
  L.divIcon({
    className: "pin-wrap",
    html: `<span class="pin" style="background:${color}"></span>`,
    iconSize: [22, 22],
    iconAnchor: [11, 22],
    popupAnchor: [0, -20],
  });
export const ICONS = { donor: icon("#ea580c"), ngo: icon("#15803d"), pick: icon("#2563eb") };

function Fit({ points }) {
  const map = useMap();
  useEffect(() => {
    if (points.length > 1) map.fitBounds(points, { padding: [30, 30], animate: false });
    else if (points.length === 1) map.setView(points[0], 14, { animate: false });
  }, [map, points]);
  return null;
}

function Clicker({ onPick }) {
  useMapEvents({ click: (e) => onPick && onPick(e.latlng.lat, e.latlng.lng) });
  return null;
}

/** markers: [{lat,lng,label,kind}], line: [[lat,lng],...], onPick(lat,lng) makes the map clickable */
export default function MapView({ markers = [], line = null, onPick, height = 260 }) {
  const pts = markers.map((m) => [m.lat, m.lng]);
  const fit = line && line.length > 1 ? line : pts;
  const key = JSON.stringify(fit);
  return (
    <MapContainer center={pts[0] || [19.076, 72.8777]} zoom={12} style={{ height, width: "100%" }} className="map">
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        url="https://tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      {markers.map((m, i) => (
        <Marker key={i} position={[m.lat, m.lng]} icon={ICONS[m.kind] || ICONS.pick}>
          {m.label && <Popup>{m.label}</Popup>}
        </Marker>
      ))}
      {line && <Polyline positions={line} pathOptions={{ color: "#2563eb", weight: 4 }} />}
      <Fit key={key} points={fit} />
      {onPick && <Clicker onPick={onPick} />}
    </MapContainer>
  );
}
