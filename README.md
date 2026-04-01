# Antenna

A radio station API powered by FCC broadcast data. Given a set of GPS coordinates, Antenna tells you every FM and AM station you can pick up — sorted by distance, frequency, or estimated signal strength.

Built for road-trippers who want to know what's on the dial.

## Quickstart

### Prerequisites

- Python 3.14+
- [uv](https://docs.astral.sh/uv/)
- `libsqlite3-mod-spatialite` (SpatiaLite extension for spatial queries)

### Install dependencies

```sh
uv sync
```

### Build the database

Antenna pulls station and contour data from FCC public APIs. Run the sync to build a local SQLite database:

```sh
uv run python -m antenna.sync
```

This downloads ~22 MB of station data from the FCC FM/AM query APIs and ~65 MB of FM contour geometry. Takes about 2 minutes.

### Start the server

```sh
uv run fastapi dev src/antenna/main.py
```

The API will be available at `http://localhost:8000` with interactive docs at `http://localhost:8000/docs`.

## API

### `GET /lookup/at-location`

The main endpoint. Find all stations whose broadcast contour covers a GPS location.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `lat` | float | yes | Latitude (-90 to 90) |
| `lon` | float | yes | Longitude (-180 to 180) |
| `service` | string | no | Filter by `FM` or `AM`. Omit for both. |
| `sort_by` | string | no | `distance` (default), `frequency`, or `signal` |

**Example:**

```
GET /lookup/at-location?lat=33.878&lon=-84.136&service=FM&sort_by=signal
```

**Response:**

```json
{
  "latitude": 33.878,
  "longitude": -84.136,
  "stations": [
    {
      "facility_id": 11710,
      "callsign": "WSBB-FM",
      "service": "FM",
      "frequency": 95.5,
      "station_class": "C1",
      "erp_kw": 100,
      "city": "DORAVILLE",
      "state": "GA",
      "distance_km": 22.59,
      "estimated_signal_dbm": -12.3
    }
  ]
}
```

The `estimated_signal_dbm` field uses a free-space path loss model to estimate received signal strength based on the station's ERP, frequency, and distance from the queried location.

### `GET /stations/search/{term}`

Search stations by facility ID, callsign prefix, or licensee name.

### `GET /stations/fm`

List FM stations with optional filters: `state`, `freq_min`, `freq_max`, `callsign`, `station_class`, `limit`.

### `GET /stations/am`

List AM stations with the same filters as above.

### `GET /contours/{facility_id}`

Get the broadcast contour geometry (GeoJSON polygon) for a station.

### `GET /health`

Returns `{"status": "ok"}`.

## Data sources

Antenna pulls from three FCC data sources during sync:

| Source | What it provides | Size |
|--------|-----------------|------|
| [FM Query API](https://transition.fcc.gov/fcc-bin/fmq) | FM station metadata (callsign, frequency, coordinates, ERP, etc.) | ~13 MB |
| [AM Query API](https://transition.fcc.gov/fcc-bin/amq) | AM station metadata | ~10 MB |
| [FM Contour Bulk Data](https://transition.fcc.gov/bureaus/mb/databases/map/FM_service_contour_current.zip) | 360-point broadcast contour polygons for FM stations | ~65 MB |

AM contours are fetched on-demand from the [FCC Entity API](https://geo.fcc.gov/api/contours) since no bulk download is available.

## Docker

```sh
docker build --target production -t antenna .
docker run -p 8080:8080 antenna
```

Note: the `fcc.db` file must exist before building the image. Run the sync first.

## Infrastructure

GCP infrastructure is managed with [Pulumi](https://www.pulumi.com/) in the `infra/` directory. It provisions:

- Cloud Run service with IAP (Identity-Aware Proxy)
- Artifact Registry (Docker repo)
- Cloud Storage bucket (FCC database)
- Service account for GitHub Actions
- Workload Identity Federation (OIDC, no static keys)
- Required GCP APIs

```sh
cd infra
pulumi up
```

Stack outputs provide the values needed for GitHub Actions secrets (`GCP_PROJECT_ID`, `GCP_WIF_PROVIDER`, `GCP_SERVICE_ACCOUNT`, `GCP_FCC_DB_BUCKET`).

## CI/CD

GitHub Actions workflows in `.github/workflows/`:

| Workflow | Trigger | What it does |
|----------|---------|--------------|
| `ci.yml` | Push/PR to main | Lint (ruff), type check (ty), test (pytest) |
| `release.yml` | Push to main | Maintains a release PR via release-please |
| `deploy.yml` | Release published or manual | Downloads `fcc.db` from GCS, builds image, deploys to Cloud Run |
| `sync.yml` | Weekly (Monday 06:00 UTC) or manual | Rebuilds `fcc.db` from FCC APIs, preserves AM contours, uploads to GCS |
| `seed-am.yml` | Manual (one-time) | Batched initial seed of AM contours across 7 parallel jobs |

## Authentication (IAP)

Access is controlled by [Identity-Aware Proxy](https://cloud.google.com/iap) on Cloud Run (free, no load balancer). IAP is enabled via Pulumi; user access is managed in the GCP Console:

1. **OAuth consent screen**: APIs & Services > OAuth consent screen > External > add your email as test user
2. **Enable IAP**: Security > Identity-Aware Proxy > toggle on for the `antenna` Cloud Run service
3. **Grant access**: Add Gmail addresses with the `IAP-secured Web App User` role

## Dashboard

The web dashboard is served at `/dashboard` (root `/` redirects there). Features:

- Click the map to find all stations covering a location
- View broadcast contour overlays on the map
- Search stations by callsign, facility ID, or licensee
- Filter by FM/AM and sort by distance, frequency, or signal strength

## Development

```sh
uv sync --group dev              # app + dev tools
uv sync --all-groups             # include infra (Pulumi) deps
uv run ruff check src/           # lint
uv run ty check src/             # type check
uv run fastapi dev src/antenna/main.py  # dev server with auto-reload
```
