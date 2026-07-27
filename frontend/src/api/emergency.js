import { apiClient } from "./client";

/**
 * GET /emergency/nearby-hospitals - confirmed against
 * app/models/emergency.py / app/routes/emergency.py. No auth required.
 *
 * Returns: [{ name, latitude, longitude, distance_km, address, phone }]
 */
export async function getNearbyHospitals(latitude, longitude, { radiusKm = 5 } = {}) {
  const { data } = await apiClient.get("/emergency/nearby-hospitals", {
    params: { lat: latitude, lon: longitude, radius_km: radiusKm },
  });
  return data;
}
