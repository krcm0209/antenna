/** Thin fetch wrappers for the Antenna API. */

const BASE = "";

async function fetchJSON(url) {
  const resp = await fetch(url);
  if (!resp.ok) throw new Error(`API error: ${resp.status}`);
  return resp.json();
}

export async function lookupAtLocation(lat, lon, { service, sortBy } = {}) {
  const params = new URLSearchParams({ lat, lon });
  if (service) params.set("service", service);
  if (sortBy) params.set("sort_by", sortBy);
  return fetchJSON(`${BASE}/lookup/at-location?${params}`);
}

export async function getContour(facilityId) {
  return fetchJSON(`${BASE}/contours/${facilityId}`);
}

export async function searchStations(term) {
  return fetchJSON(`${BASE}/stations/search/${encodeURIComponent(term)}`);
}
