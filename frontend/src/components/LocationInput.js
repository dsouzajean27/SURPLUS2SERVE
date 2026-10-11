import { useState } from "react";
import client, { errMsg } from "../api/client";
import MapView from "./MapView";

/** value = {address, lat, lng}. Users type an address (coordinates are looked up in the
 *  background), or press "Use my location", or click the map. */
export default function LocationInput({ value, onChange, label = "Address" }) {
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState("");

  async function findOnMap() {
    if (!value.address || value.address.trim().length < 3) return setMsg("Type an address first");
    setBusy(true);
    setMsg("");
    try {
      const res = await client.get("/location/geocode", { params: { q: value.address } });
      onChange({ ...value, lat: res.data.lat, lng: res.data.lng });
      setMsg("Location found - click the map to fine-tune");
    } catch (e) {
      setMsg(errMsg(e, "Address not found"));
    } finally {
      setBusy(false);
    }
  }

  function useMine() {
    if (!navigator.geolocation) return setMsg("Geolocation not supported in this browser");
    setMsg("Getting your location...");
    navigator.geolocation.getCurrentPosition(
      (pos) =>
        {
          onChange({
            address: value.address || `Current location (${pos.coords.latitude.toFixed(4)}, ${pos.coords.longitude.toFixed(4)})`,
            lat: pos.coords.latitude,
            lng: pos.coords.longitude,
          });
          setMsg("Using your current location");
        },
      () => setMsg("Could not get your location - type the address instead")
    );
  }

  const has = value.lat != null && value.lng != null;
  return (
    <div className="field">
      <label>{label}</label>
      <input
        value={value.address}
        onChange={(e) => onChange({ address: e.target.value, lat: null, lng: null })}
        placeholder="e.g. Colaba Causeway, Mumbai"
        required
      />
      <div className="row gap">
        <button type="button" className="btn small" onClick={findOnMap} disabled={busy}>
          {busy ? "Searching..." : "Find on map"}
        </button>
        <button type="button" className="btn small" onClick={useMine}>Use my location</button>
        <span className="muted small-text">{msg || (has ? `${value.lat.toFixed(4)}, ${value.lng.toFixed(4)}` : "Coordinates are looked up automatically if you skip this")}</span>
      </div>
      {has && (
        <MapView
          height={200}
          markers={[{ lat: value.lat, lng: value.lng, kind: "pick", label: "Selected location" }]}
          onPick={(lat, lng) => onChange({ ...value, lat, lng })}
        />
      )}
    </div>
  );
}
