"""Download and parse FM/AM station data from FCC query APIs."""

import logging

import httpx
from sqlmodel import Session

from antenna.config import settings
from antenna.models.stations import Station
from antenna.sync.parsers import dms_to_decimal, parse_pipe_float, parse_pipe_int

logger = logging.getLogger(__name__)

# FCC query URLs return all stations as pipe-delimited text with list=4
_FM_QUERY = f"{settings.fcc_fm_query_url}?state=&call=&city=&ession=&n=0&list=4&type=N"
_AM_QUERY = f"{settings.fcc_am_query_url}?state=&call=&city=&ession=&n=0&list=4&type=N"


def download_station_data() -> tuple[str, str]:
    """Download FM and AM station data from FCC query APIs (~22 MB total)."""
    logger.info("Downloading FM station data from %s", settings.fcc_fm_query_url)
    fm_resp = httpx.get(_FM_QUERY, timeout=120.0)
    fm_resp.raise_for_status()
    logger.info("FM query: %d bytes, %d lines", len(fm_resp.text), fm_resp.text.count("\n"))

    logger.info("Downloading AM station data from %s", settings.fcc_am_query_url)
    am_resp = httpx.get(_AM_QUERY, timeout=120.0)
    am_resp.raise_for_status()
    logger.info("AM query: %d bytes, %d lines", len(am_resp.text), am_resp.text.count("\n"))

    return fm_resp.text, am_resp.text


def parse_and_insert_stations(
    session: Session, fm_text: str, am_text: str
) -> tuple[int, dict[str, int]]:
    """Parse FM and AM query results and insert stations.

    FM query fields (pipe-delimited, 41 fields):
      [1] callsign  [2] frequency  [3] service  [4] channel
      [7] station_class  [9] status  [10] city  [11] state
      [13] application_id  [14] erp_h_kw  [15] erp_v_kw
      [16] haat_h  [17] haat_v  [18] facility_id
      [19] lat_dir  [20] lat_deg  [21] lat_min  [22] lat_sec
      [23] lon_dir  [24] lon_deg  [25] lon_min  [26] lon_sec
      [27] licensee  [31] rcamsl  [38] lms_app_uuid

    AM query fields (pipe-delimited, 35 fields):
      Same layout through [27], [32] lms_app_uuid

    Returns (count, lms_app_uuid→facility_id mapping).
    """
    lms_app_to_facility: dict[str, int] = {}

    # Deduplicate by facility_id — keep LIC records over CP/STA,
    # and collect all LMS UUIDs for contour matching.
    stations_by_id: dict[int, Station] = {}
    status_priority = {"LIC": 0, "LICEN": 0, "STA": 1, "CP": 2}

    # Parse FM stations
    for line in fm_text.strip().split("\n"):
        fields = line.split("|")
        if len(fields) < 28:
            continue

        station = _parse_fm_line(fields)
        if station is None:
            continue

        existing = stations_by_id.get(station.facility_id)
        if existing is not None:
            existing_pri = status_priority.get(existing.license_status or "", 3)
            new_pri = status_priority.get(station.license_status or "", 3)
            if new_pri > existing_pri:
                continue  # Keep the higher-priority record

        stations_by_id[station.facility_id] = station

        # Build LMS UUID mapping for FM contour matching
        if len(fields) > 38:
            lms_uuid = fields[38].strip()
            if lms_uuid:
                lms_app_to_facility[lms_uuid] = station.facility_id

    logger.info("Parsed %d unique FM stations", len(stations_by_id))
    fm_count = len(stations_by_id)

    # Parse AM stations
    for line in am_text.strip().split("\n"):
        fields = line.split("|")
        if len(fields) < 28:
            continue

        station = _parse_am_line(fields)
        if station is None:
            continue

        existing = stations_by_id.get(station.facility_id)
        if existing is not None:
            existing_pri = status_priority.get(existing.license_status or "", 3)
            new_pri = status_priority.get(station.license_status or "", 3)
            if new_pri > existing_pri:
                continue

        stations_by_id[station.facility_id] = station

    am_count = len(stations_by_id) - fm_count
    logger.info("Parsed %d unique AM stations", am_count)

    # Bulk insert all stations
    count = 0
    for station in stations_by_id.values():
        session.add(station)
        count += 1
        if count % 1000 == 0:
            session.commit()
            logger.info("Inserted %d stations", count)

    session.commit()
    logger.info("Finished: inserted %d stations total", count)
    return count, lms_app_to_facility


def _parse_fm_line(fields: list[str]) -> Station | None:
    """Parse a single FM query result line into a Station."""
    facility_id = parse_pipe_int(fields[18])
    if facility_id is None:
        return None

    service = fields[3].strip()
    if not service:
        return None

    lat = _parse_lat_lon(fields, lat_dir=19, lat_deg=20, lat_min=21, lat_sec=22)
    lon = _parse_lat_lon(fields, lat_dir=23, lat_deg=24, lat_min=25, lat_sec=26)
    if lat is None or lon is None:
        return None

    freq = _parse_frequency(fields[2])
    erp = parse_pipe_float(fields[14]) or parse_pipe_float(fields[15])
    haat = parse_pipe_float(fields[16]) or parse_pipe_float(fields[17])
    rcamsl = parse_pipe_float(fields[31]) if len(fields) > 31 else None

    return Station(
        facility_id=facility_id,
        callsign=fields[1].strip(),
        service=service,
        frequency=freq or 0.0,
        channel=parse_pipe_int(fields[4]),
        station_class=fields[7].strip() or None,
        erp_kw=erp,
        haat_m=haat,
        rcamsl_m=rcamsl,
        antenna_lat=lat,
        antenna_lon=lon,
        city=fields[10].strip() or None,
        state=fields[11].strip() or None,
        licensee=fields[27].strip() or None,
        license_status=fields[9].strip() or None,
        application_id=parse_pipe_int(fields[13]),
        file_number=fields[13].strip() or None,
    )


def _parse_am_line(fields: list[str]) -> Station | None:
    """Parse a single AM query result line into a Station."""
    facility_id = parse_pipe_int(fields[18])
    if facility_id is None:
        return None

    lat = _parse_lat_lon(fields, lat_dir=19, lat_deg=20, lat_min=21, lat_sec=22)
    lon = _parse_lat_lon(fields, lat_dir=23, lat_deg=24, lat_min=25, lat_sec=26)
    if lat is None or lon is None:
        return None

    freq = _parse_frequency(fields[2])
    erp = parse_pipe_float(fields[14])

    return Station(
        facility_id=facility_id,
        callsign=fields[1].strip(),
        service=fields[3].strip() or "AM",
        frequency=freq or 0.0,
        channel=parse_pipe_int(fields[4]),
        station_class=fields[7].strip() or None,
        erp_kw=erp,
        haat_m=None,  # AM query doesn't provide HAAT in same format
        rcamsl_m=None,
        antenna_lat=lat,
        antenna_lon=lon,
        city=fields[10].strip() or None,
        state=fields[11].strip() or None,
        licensee=fields[27].strip() or None,
        license_status=fields[9].strip() or None,
        application_id=parse_pipe_int(fields[13]),
        file_number=fields[13].strip() or None,
    )


def _parse_lat_lon(
    fields: list[str], *, lat_dir: int, lat_deg: int, lat_min: int, lat_sec: int
) -> float | None:
    """Parse DMS coordinates from field indices."""
    deg = parse_pipe_int(fields[lat_deg])
    min_ = parse_pipe_int(fields[lat_min])
    sec = parse_pipe_float(fields[lat_sec])
    if deg is None or min_ is None or sec is None:
        return None

    decimal = dms_to_decimal(deg, min_, sec)
    direction = fields[lat_dir].strip()
    if direction in ("S", "W"):
        decimal = -decimal
    return decimal


def _parse_frequency(value: str) -> float | None:
    """Parse frequency from FCC format like '88.1  MHz' or '530   kHz'."""
    token = value.strip().split()[0] if value.strip() else ""
    if not token:
        return None
    try:
        freq = float(token)
    except ValueError:
        return None
    # Convert kHz to MHz for AM stations
    if "kHz" in value:
        freq = freq / 1000.0
    return freq
