/** Leaflet map management — contour rendering, markers, click handling. */

let map;
let contourLayer;
let markerLayer;
let clickMarker;

export function initMap(elementId, { onClick } = {}) {
  map = L.map(elementId).setView([39.8, -98.5], 4); // Center of continental US

  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution: "&copy; OpenStreetMap contributors",
    maxZoom: 19,
  }).addTo(map);

  contourLayer = L.featureGroup().addTo(map);
  markerLayer = L.layerGroup().addTo(map);

  if (onClick) {
    map.on("click", (e) => onClick(e.latlng.lat, e.latlng.lng));
  }

  return map;
}

export function setClickMarker(lat, lon) {
  if (clickMarker) map.removeLayer(clickMarker);
  clickMarker = L.circleMarker([lat, lon], {
    radius: 8,
    color: "#e63946",
    fillColor: "#e63946",
    fillOpacity: 0.8,
  }).addTo(map);
}

export function clearContours() {
  contourLayer.clearLayers();
}

const CONTOUR_COLORS = [
  "#2196f3", "#4caf50", "#ff9800", "#9c27b0", "#00bcd4",
  "#f44336", "#8bc34a", "#ff5722", "#673ab7", "#009688",
];

let colorIndex = 0;

export function addContour(geojson, { label, facilityId } = {}) {
  const color = CONTOUR_COLORS[colorIndex % CONTOUR_COLORS.length];
  colorIndex++;

  const layer = L.geoJSON(geojson, {
    style: { color, weight: 2, fillOpacity: 0.15 },
  });

  if (label) {
    layer.bindTooltip(label, { sticky: true });
  }

  contourLayer.addLayer(layer);
  return layer;
}

export function resetColorIndex() {
  colorIndex = 0;
}

export function fitToContours() {
  if (contourLayer.getLayers().length > 0) {
    map.fitBounds(contourLayer.getBounds(), { padding: [20, 20] });
  }
}
