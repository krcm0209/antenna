import math
from enum import StrEnum

from fastapi import APIRouter, Query, Request

from antenna.models.lookup import LookupResponse, StationAtLocation

router = APIRouter(prefix="/lookup", tags=["lookup"])


class ServiceType(StrEnum):
    FM = "FM"
    AM = "AM"


class SortBy(StrEnum):
    distance = "distance"
    frequency = "frequency"
    signal = "signal"


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the great-circle distance between two points in km."""
    r = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    )
    return r * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _estimate_signal_dbm(erp_kw: float, frequency_mhz: float, distance_km: float) -> float | None:
    """Estimate received signal strength using free-space path loss.

    FSPL (dB) = 20·log10(d_km) + 20·log10(f_MHz) + 32.45
    Received (dBm) = ERP (dBm) - FSPL
    """
    if erp_kw is None or erp_kw <= 0 or frequency_mhz <= 0 or distance_km <= 0:
        return None
    erp_dbm = 10 * math.log10(erp_kw) + 60  # kW → dBm
    fspl = 20 * math.log10(distance_km) + 20 * math.log10(frequency_mhz) + 32.45
    return round(erp_dbm - fspl, 1)


@router.get("/at-location")
def stations_at_location(
    request: Request,
    lat: float = Query(ge=-90, le=90),
    lon: float = Query(ge=-180, le=180),
    service: ServiceType | None = Query(default=None, description="Filter by service type"),
    sort_by: SortBy = Query(default=SortBy.distance, description="Sort results by field"),
) -> LookupResponse:
    """Find all stations whose broadcast contour covers the given GPS coordinates."""
    raw_conn = request.state.raw_conn

    rows = raw_conn.execute(
        """SELECT s.facility_id, s.callsign, s.service, s.frequency,
                  s.station_class, s.erp_kw, s.city, s.state,
                  s.antenna_lat, s.antenna_lon
           FROM contours c
           JOIN stations s ON s.facility_id = c.facility_id
           WHERE c.ROWID IN (
               SELECT ROWID FROM SpatialIndex
               WHERE f_table_name = 'contours' AND f_geometry_column = 'geom'
               AND search_frame = MakePoint(?, ?, 4326)
           )
           AND Contains(c.geom, MakePoint(?, ?, 4326))""",
        (lon, lat, lon, lat),
    ).fetchall()

    fm_services = {"FM", "FX", "FS", "FL", "FB"}
    stations = []
    for row in rows:
        raw_svc = row["service"]
        svc = "FM" if raw_svc in fm_services else raw_svc
        if service is not None and svc != service:
            continue

        distance = round(_haversine_km(lat, lon, row["antenna_lat"], row["antenna_lon"]), 2)
        freq = row["frequency"]
        erp = row["erp_kw"]
        signal = _estimate_signal_dbm(erp, freq, distance)

        stations.append(
            StationAtLocation(
                facility_id=row["facility_id"],
                callsign=row["callsign"],
                service=svc,
                frequency=freq,
                station_class=row["station_class"],
                erp_kw=erp,
                city=row["city"],
                state=row["state"],
                distance_km=distance,
                estimated_signal_dbm=signal,
            )
        )

    if sort_by == SortBy.distance:
        stations.sort(key=lambda s: s.distance_km)
    elif sort_by == SortBy.frequency:
        stations.sort(key=lambda s: s.frequency)
    elif sort_by == SortBy.signal:
        # Strongest signal first; stations without signal estimate go last
        stations.sort(key=lambda s: s.estimated_signal_dbm if s.estimated_signal_dbm is not None else float("-inf"), reverse=True)

    return LookupResponse(latitude=lat, longitude=lon, stations=stations)
