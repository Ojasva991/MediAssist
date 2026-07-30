import { useEffect, useState, useCallback } from "react";
import { Link } from "react-router-dom";
import { QRCodeSVG } from "qrcode.react";
import { Phone, ShieldAlert, Droplet, Pill, HeartPulse, ArrowLeft, RefreshCcw, QrCode, MapPin, Navigation, LocateFixed, ExternalLink, WifiOff } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import { SosInfoSkeleton } from "@/components/sos/SosInfoSkeleton";
import { useAuth } from "@/context/AuthContext";
import { getPassport } from "@/api/passport";
import { getNearbyHospitals } from "@/api/emergency";
import { HospitalsMap } from "@/components/sos/HospitalsMap";
import { useOnlineStatus } from "@/hooks/useOnlineStatus";
import { ROUTES } from "@/constants/routes";

const EMERGENCY_NUMBER = "112"; // India's unified emergency number

/**
 * Plain-text emergency card, encoded directly into the QR code itself -
 * deliberately NOT a link to a backend page. Encoding the data directly
 * means anyone's phone camera can read it immediately with no app, no
 * login, and no new public/unauthenticated endpoint exposing private
 * medical data on the backend. Same idea as a MedicAlert bracelet.
 */
function buildEmergencyCardText(passport) {
  const lines = [
    "EMERGENCY MEDICAL INFO",
    `Name: ${passport.name}`,
    `Age: ${passport.age}  Gender: ${passport.gender}  Blood Group: ${passport.blood_group}`,
    `Allergies: ${passport.allergies?.trim() || "None recorded"}`,
    `Chronic Conditions: ${passport.chronic_diseases?.trim() || "None recorded"}`,
    `Medications: ${passport.medications?.trim() || "None recorded"}`,
    `Emergency Contact: ${passport.emergency_contact_name} - ${passport.emergency_contact_phone}`,
  ];
  return lines.join("\n");
}

export default function SOS() {
  const { user } = useAuth();
  const isOnline = useOnlineStatus();
  const [passport, setPassport] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [qrOpen, setQrOpen] = useState(false);

  // idle | locating | loading | error | done
  const [hospitalState, setHospitalState] = useState("idle");
  const [hospitals, setHospitals] = useState([]);
  const [hospitalError, setHospitalError] = useState(null);
  const [lastCoords, setLastCoords] = useState(null); // { lat, lon } - set as soon as geolocation succeeds, independent of Overpass's outcome
  const [hospitalView, setHospitalView] = useState("list"); // "list" | "map"

  const findNearbyHospitals = useCallback(() => {
    if (!isOnline) {
      setHospitalState("error");
      setHospitalError(
        "You're offline - hospital search needs an internet connection. Your Google Maps link " +
          "below and emergency call buttons above still work without one."
      );
      return;
    }
    if (!("geolocation" in navigator)) {
      setHospitalState("error");
      setHospitalError("Location isn't available on this device or browser.");
      return;
    }
    setHospitalState("locating");
    setHospitalError(null);
    navigator.geolocation.getCurrentPosition(
      async (position) => {
        const { latitude, longitude } = position.coords;
        setLastCoords({ lat: latitude, lon: longitude });
        setHospitalState("loading");
        try {
          const results = await getNearbyHospitals(latitude, longitude);
          setHospitals(results);
          setHospitalState("done");
        } catch (err) {
          setHospitalError(err.message);
          setHospitalState("error");
        }
      },
      (geoError) => {
        setHospitalState("error");
        setHospitalError(
          geoError.code === geoError.PERMISSION_DENIED
            ? "Location permission was denied. Enable it in your browser settings to find nearby hospitals."
            : "Couldn't get your location. Please try again."
        );
      },
      { enableHighAccuracy: true, timeout: 10000 }
    );
  }, [isOnline]);

  // Zero-backend, zero-API-key fallback: a plain Google Maps search URL.
  // Works even if every Overpass mirror is down, since it's just a link -
  // no server round-trip on our side at all. Uses precise coordinates once
  // we have them (from a successful geolocation call above), otherwise
  // falls back to Maps' own "near me" search, which asks for location
  // itself and doesn't need ours.
  const googleMapsHospitalsUrl = lastCoords
    ? `https://www.google.com/maps/search/hospitals/@${lastCoords.lat},${lastCoords.lon},14z`
    : "https://www.google.com/maps/search/hospitals+near+me";

  const load = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await getPassport(user.userId);
      setPassport(data);
    } catch (err) {
      if (err.status === 404) setPassport(null);
      else setError(err);
    } finally {
      setIsLoading(false);
    }
  }, [user.userId]);

  useEffect(() => {
    load();
  }, [load]);

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <Link
        to={ROUTES.DASHBOARD}
        className="flex items-center gap-1.5 text-sm font-medium text-ink-soft transition-colors hover:text-ink"
      >
        <ArrowLeft className="size-4" /> Back to dashboard
      </Link>

      {/* Emergency call block */}
      <div className="rounded-[var(--radius-card)] bg-danger p-6 text-white sm:p-8">
        <div className="flex items-center gap-3">
          <span className="flex size-11 shrink-0 items-center justify-center rounded-xl bg-white/15">
            <ShieldAlert className="size-6" />
          </span>
          <div>
            <p className="font-display text-lg font-bold">Emergency SOS</p>
            <p className="text-sm text-red-100">If this is life-threatening, call now.</p>
          </div>
        </div>

        <div className="mt-6 grid gap-3 sm:grid-cols-2">
          <Button asChild size="lg" className="bg-white text-danger hover:bg-danger-light">
            <a href={`tel:${EMERGENCY_NUMBER}`}>
              <Phone className="size-4" /> Call {EMERGENCY_NUMBER}
            </a>
          </Button>
          {passport?.emergency_contact_phone && (
            <Button
              asChild
              size="lg"
              variant="outline"
              className="border-white/40 bg-transparent text-white hover:bg-white/10"
            >
              <a href={`tel:${passport.emergency_contact_phone}`}>
                <Phone className="size-4" />
                Call {passport.emergency_contact_name || "emergency contact"}
              </a>
            </Button>
          )}
        </div>
      </div>

      {/* Nearby hospitals - best-effort, works even if not logged in */}
      <div className="rounded-[var(--radius-card)] border border-border bg-surface p-6">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <MapPin className="size-4 text-primary" />
            <p className="font-display text-sm font-semibold text-ink">Nearby hospitals</p>
          </div>
          {hospitalState !== "done" && (
            <Button
              size="sm"
              variant="outline"
              onClick={findNearbyHospitals}
              disabled={hospitalState === "locating" || hospitalState === "loading"}
            >
              <LocateFixed className="size-3.5" />
              {hospitalState === "locating"
                ? "Getting your location…"
                : hospitalState === "loading"
                ? "Searching…"
                : "Find nearby hospitals"}
            </Button>
          )}
          {hospitalState === "done" && (
            <div className="flex items-center gap-2">
              {hospitals.length > 0 && (
                <div className="flex overflow-hidden rounded-md border border-border">
                  <button
                    type="button"
                    onClick={() => setHospitalView("list")}
                    className={`px-2.5 py-1 text-xs font-medium ${
                      hospitalView === "list" ? "bg-primary-light text-primary-dark" : "text-ink-soft"
                    }`}
                  >
                    List
                  </button>
                  <button
                    type="button"
                    onClick={() => setHospitalView("map")}
                    className={`px-2.5 py-1 text-xs font-medium ${
                      hospitalView === "map" ? "bg-primary-light text-primary-dark" : "text-ink-soft"
                    }`}
                  >
                    Map
                  </button>
                </div>
              )}
              <Button size="sm" variant="ghost" onClick={findNearbyHospitals}>
                <RefreshCcw className="size-3.5" /> Refresh
              </Button>
            </div>
          )}
        </div>

        {hospitalState === "error" && (
          <p className="mt-3 text-sm text-danger">{hospitalError}</p>
        )}

        {hospitalState === "done" && hospitals.length === 0 && (
          <p className="mt-3 text-sm text-ink-soft">
            No hospitals found in our map data right now.
          </p>
        )}

        {hospitalState === "done" && hospitals.length > 0 && hospitalView === "map" && lastCoords && (
          <div className="mt-4">
            <HospitalsMap userLat={lastCoords.lat} userLon={lastCoords.lon} hospitals={hospitals} />
          </div>
        )}

        {hospitalState === "done" && hospitals.length > 0 && hospitalView === "list" && (
          <ul className="mt-4 space-y-3">
            {hospitals.map((h, i) => (
              <li
                key={`${h.name}-${i}`}
                className="flex items-center justify-between gap-3 border-t border-border pt-3 first:border-t-0 first:pt-0"
              >
                <div className="min-w-0">
                  <p className="truncate text-sm font-medium text-ink">{h.name}</p>
                  <p className="mt-0.5 font-mono text-xs text-ink-faint">
                    {h.distance_km} km away{h.address ? ` · ${h.address}` : ""}
                  </p>
                </div>
                <div className="flex shrink-0 items-center gap-2">
                  {h.phone && (
                    <Button asChild size="sm" variant="outline">
                      <a href={`tel:${h.phone}`}>
                        <Phone className="size-3.5" />
                      </a>
                    </Button>
                  )}
                  <Button asChild size="sm" variant="outline">
                    <a
                      href={`https://www.google.com/maps/dir/?api=1&destination=${h.latitude},${h.longitude}`}
                      target="_blank"
                      rel="noreferrer"
                    >
                      <Navigation className="size-3.5" /> Directions
                    </a>
                  </Button>
                </div>
              </li>
            ))}
          </ul>
        )}

        {/* Always available regardless of the Overpass lookup's outcome -
            this is a plain link, no backend call, so it can't fail the
            way the lookup above can. Kept as a guaranteed fallback, not
            the primary path, since inline results (above) are more
            convenient when they work. */}
        <div className="mt-4 border-t border-border pt-3">
          <a
            href={googleMapsHospitalsUrl}
            target="_blank"
            rel="noreferrer"
            className="inline-flex items-center gap-1.5 text-sm font-medium text-primary hover:underline"
          >
            <ExternalLink className="size-3.5" />
            Search hospitals near you on Google Maps
          </a>
        </div>
      </div>

      {/* Critical info at a glance */}
      <div>
        {!isOnline && (
          <div className="mb-3 flex items-center gap-2 rounded-[var(--radius-control)] bg-warning-light px-3 py-2 text-xs text-warning">
            <WifiOff className="size-3.5 shrink-0" />
            You're offline. Emergency calls and your saved info below still work - hospital
            search needs a connection.
          </div>
        )}
        <h2 className="mb-3 font-display text-sm font-semibold uppercase tracking-wide text-ink-faint">
          Show this to first responders
        </h2>

        {isLoading && <SosInfoSkeleton />}

        {error && (
          <div className="rounded-[var(--radius-control)] bg-danger-light px-4 py-3 text-sm text-danger">
            {error.message}
            <Button variant="link" className="ml-1 h-auto p-0 text-danger" onClick={load}>
              Retry
            </Button>
          </div>
        )}

        {!isLoading && !error && !passport && (
          <div className="rounded-[var(--radius-card)] border border-dashed border-border bg-surface p-8 text-center">
            <p className="text-sm text-ink-soft">
              No health passport on file yet. Add one so responders have what they need.
            </p>
            <Button asChild className="mt-4" size="sm">
              <Link to={ROUTES.PASSPORT}>Create health passport</Link>
            </Button>
          </div>
        )}

        {!isLoading && passport && (
          <div className="rounded-[var(--radius-card)] border border-border bg-surface p-6">
            <div className="flex flex-wrap items-center justify-between gap-2 border-b border-border pb-4">
              <div>
                <p className="font-display text-lg font-bold text-ink">{passport.name}</p>
                <p className="font-mono text-sm text-ink-soft">
                  {passport.age ? `${passport.age} yrs` : ""}
                </p>
              </div>
              {passport.blood_group && passport.blood_group !== "UNKNOWN" && (
                <span className="flex items-center gap-1.5 rounded-full bg-danger-light px-3 py-1.5 font-mono text-sm font-bold text-danger">
                  <Droplet className="size-4" /> {passport.blood_group}
                </span>
              )}
            </div>

            <div className="flex justify-end border-b border-border py-3">
              <Button variant="outline" size="sm" onClick={() => setQrOpen(true)}>
                <QrCode className="size-3.5" /> Show QR code
              </Button>
            </div>

            <div className="divide-y divide-border">
              <div className="py-4">
                <InfoBlock icon={ShieldAlert} label="Allergies" value={passport.allergies} emptyText="No known allergies recorded" />
              </div>
              <div className="py-4">
                <InfoBlock icon={HeartPulse} label="Chronic conditions" value={passport.chronic_diseases} emptyText="None recorded" />
              </div>
              <div className="pt-4">
                <InfoBlock icon={Pill} label="Current medications" value={passport.medications} emptyText="None recorded" />
              </div>
            </div>
          </div>
        )}
      </div>

      {!isLoading && (
        <Button variant="ghost" size="sm" onClick={load} className="mx-auto flex">
          <RefreshCcw className="size-3.5" /> Refresh info
        </Button>
      )}

      {passport && (
        <Dialog open={qrOpen} onOpenChange={setQrOpen}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Scan for emergency info</DialogTitle>
              <DialogDescription>
                Any phone camera can scan this - no app or login needed. The info is
                encoded directly in the code itself, not a link, so it still works
                offline.
              </DialogDescription>
            </DialogHeader>
            <div className="flex flex-col items-center gap-4 py-2">
              <div className="rounded-[var(--radius-card)] border border-border bg-white p-4">
                <QRCodeSVG value={buildEmergencyCardText(passport)} size={220} level="M" />
              </div>
              <p className="text-center text-xs text-ink-faint">
                Contains: name, age, blood group, allergies, conditions, medications, and
                emergency contact.
              </p>
            </div>
          </DialogContent>
        </Dialog>
      )}
    </div>
  );
}

function InfoBlock({ icon: Icon, label, value, emptyText }) {
  return (
    <div>
      <p className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wide text-ink-faint">
        <Icon className="size-3.5" /> {label}
      </p>
      <p className="mt-1 text-sm text-ink">
        {value?.trim() ? value : <span className="text-ink-faint">{emptyText}</span>}
      </p>
    </div>
  );
}
