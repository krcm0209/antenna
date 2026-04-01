/** Main application — wires UI events to API calls and map rendering. */

import { lookupAtLocation, getContour, searchStations } from "./api.js";
import {
  initMap,
  setClickMarker,
  clearContours,
  addContour,
  resetColorIndex,
  fitToContours,
} from "./map.js";

const sidebar = document.getElementById("sidebar");
const stationList = document.getElementById("station-list");
const searchInput = document.getElementById("search-input");
const searchBtn = document.getElementById("search-btn");
const serviceFilter = document.getElementById("service-filter");
const sortBy = document.getElementById("sort-by");
const statusEl = document.getElementById("status");

function setStatus(text) {
  statusEl.textContent = text;
}

function renderStations(stations, lat, lon) {
  stationList.innerHTML = "";

  if (stations.length === 0) {
    stationList.innerHTML = '<div class="empty">No stations found</div>';
    return;
  }

  for (const s of stations) {
    const card = document.createElement("div");
    card.className = "station-card";
    card.innerHTML = `
      <div class="station-header">
        <strong>${s.callsign}</strong>
        <span class="freq">${s.frequency} MHz</span>
      </div>
      <div class="station-detail">
        ${s.city || ""}, ${s.state || ""} &middot; ${s.distance_km} km
        ${s.estimated_signal_dbm != null ? `&middot; ${s.estimated_signal_dbm} dBm` : ""}
      </div>
      <div class="station-meta">${s.service} &middot; Class ${s.station_class || "?"} &middot; ${s.erp_kw ?? "?"} kW</div>
    `;

    card.addEventListener("click", () => loadContour(s));
    stationList.appendChild(card);
  }
}

async function loadContour(station) {
  setStatus(`Loading contour for ${station.callsign}...`);
  try {
    const data = await getContour(station.facility_id);
    addContour(data.geometry, {
      label: `${station.callsign} (${station.frequency} MHz)`,
      facilityId: station.facility_id,
    });
    fitToContours();
    setStatus(`Showing contour for ${station.callsign}`);
  } catch {
    setStatus(`No contour available for ${station.callsign}`);
  }
}

async function handleMapClick(lat, lon) {
  setClickMarker(lat, lon);
  clearContours();
  resetColorIndex();

  const service = serviceFilter.value || undefined;
  const sort = sortBy.value || undefined;

  setStatus(`Looking up stations at ${lat.toFixed(4)}, ${lon.toFixed(4)}...`);

  try {
    const data = await lookupAtLocation(lat, lon, { service, sortBy: sort });
    renderStations(data.stations, lat, lon);
    setStatus(`${data.stations.length} station(s) found`);

    // Load contours for all returned stations
    for (const s of data.stations) {
      try {
        const contour = await getContour(s.facility_id);
        addContour(contour.geometry, {
          label: `${s.callsign} (${s.frequency} MHz)`,
        });
      } catch {
        // Some stations may not have contour data
      }
    }
    if (data.stations.length > 0) fitToContours();
  } catch (err) {
    setStatus(`Error: ${err.message}`);
  }
}

async function handleSearch() {
  const term = searchInput.value.trim();
  if (!term) return;

  setStatus(`Searching for "${term}"...`);
  try {
    const stations = await searchStations(term);
    renderStations(stations);
    setStatus(`${stations.length} result(s) for "${term}"`);
  } catch (err) {
    setStatus(`Error: ${err.message}`);
  }
}

// Initialize
initMap("map", { onClick: handleMapClick });

searchBtn.addEventListener("click", handleSearch);
searchInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter") handleSearch();
});
