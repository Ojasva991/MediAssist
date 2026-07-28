import { MapContainer, TileLayer, Marker, Popup, useMap } from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";

// Leaflet's default marker icons reference image files by relative path,
// which breaks under Vite's bundling (the images never resolve). Rebuilding
// the icon with explicit CDN URLs is the standard workaround - no local
// asset pipeline needed, and jsDelivr is already a CDN this kind of app can
// rely on being reachable.
const userIcon = new L.DivIcon({
  className: "",
  html: `<div style="width:16px;height:16px;border-radius:50%;background:var(--color-primary);border:3px solid white;box-shadow:0 0 0 2px var(--color-primary)"></div>`,
  iconSize: [16, 16],
  iconAnchor: [8, 8],
});

const hospitalIcon = new L.DivIcon({
  className: "",
  html: `<div style="width:14px;height:14px;border-radius:50% 50% 50% 0;background:var(--color-danger);border:2px solid white;transform:rotate(-45deg);box-shadow:0 1px 3px rgba(0,0,0,0.3)"></div>`,
  iconSize: [14, 14],
  iconAnchor: [7, 14],
});

// Recenters the map when the user's coordinates change (e.g. after a
// "Refresh" click) - MapContainer only reads its `center` prop on first
// render, so without this the map would stay stuck on the first location.
function RecenterOnChange({ lat, lon }) {
  const map = useMap();
  map.setView([lat, lon], map.getZoom());
  return null;
}

/**
 * Renders nearby hospitals (from GET /emergency/nearby-hospitals) as pins
 * on an interactive OpenStreetMap tile map. Free, no API key - same
 * "no new paid infra" reasoning as the Overpass lookup itself. Tile usage
 * follows OpenStreetMap's standard tile-usage policy (attribution shown,
 * reasonable non-bulk load for a single map per page view).
 */
export function HospitalsMap({ userLat, userLon, hospitals }) {
  return (
    <div className="overflow-hidden rounded-[var(--radius-card)] border border-border">
      <MapContainer
        center={[userLat, userLon]}
        zoom={14}
        scrollWheelZoom={false}
        style={{ height: "280px", width: "100%" }}
      >
        <RecenterOnChange lat={userLat} lon={userLon} />
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        <Marker position={[userLat, userLon]} icon={userIcon}>
          <Popup>You are here</Popup>
        </Marker>
        {hospitals.map((h, i) => (
          <Marker key={`${h.name}-${i}`} position={[h.latitude, h.longitude]} icon={hospitalIcon}>
            <Popup>
              <div className="text-sm">
                <p className="font-semibold">{h.name}</p>
                <p className="mt-0.5 text-xs text-ink-faint">
                  {h.distance_km} km away{h.address ? ` · ${h.address}` : ""}
                </p>
                <a
                  href={`https://www.google.com/maps/dir/?api=1&destination=${h.latitude},${h.longitude}`}
                  target="_blank"
                  rel="noreferrer"
                  className="mt-1 inline-block text-xs font-medium text-primary hover:underline"
                >
                  Directions
                </a>
              </div>
            </Popup>
          </Marker>
        ))}
      </MapContainer>
    </div>
  );
}
