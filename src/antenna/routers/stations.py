from fastapi import APIRouter, Query, Request
from sqlmodel import col, select

from antenna.models.stations import Station

router = APIRouter(prefix="/stations", tags=["stations"])


@router.get("/search/{term}")
def search_stations(request: Request, term: str) -> list[Station]:
    """Search stations by callsign, facility ID, or licensee name."""
    session = request.state.db_session

    # Try as facility ID first
    try:
        fac_id = int(term)
        station = session.get(Station, fac_id)
        if station:
            return [station]
    except ValueError:
        pass

    # Search by callsign (exact or prefix)
    results = session.exec(
        select(Station).where(col(Station.callsign).startswith(term.upper())).limit(50)
    ).all()
    if results:
        return list(results)

    # Search by licensee name (contains)
    results = session.exec(
        select(Station).where(col(Station.licensee).contains(term)).limit(50)
    ).all()
    return list(results)


@router.get("/fm")
def list_fm_stations(
    request: Request,
    state: str | None = None,
    freq_min: float | None = Query(None, ge=87.5, le=108.0),
    freq_max: float | None = Query(None, ge=87.5, le=108.0),
    callsign: str | None = None,
    station_class: str | None = None,
    limit: int = Query(100, ge=1, le=1000),
) -> list[Station]:
    """List FM stations with optional filters."""
    session = request.state.db_session
    query = select(Station).where(col(Station.service).in_(["FM", "FX", "FL", "FB"]))

    if state:
        query = query.where(Station.state == state.upper())
    if freq_min is not None:
        query = query.where(Station.frequency >= freq_min)
    if freq_max is not None:
        query = query.where(Station.frequency <= freq_max)
    if callsign:
        query = query.where(col(Station.callsign).startswith(callsign.upper()))
    if station_class:
        query = query.where(Station.station_class == station_class.upper())

    query = query.limit(limit)
    return list(session.exec(query).all())


@router.get("/am")
def list_am_stations(
    request: Request,
    state: str | None = None,
    freq_min: float | None = Query(None, ge=530, le=1700),
    freq_max: float | None = Query(None, ge=530, le=1700),
    callsign: str | None = None,
    station_class: str | None = None,
    limit: int = Query(100, ge=1, le=1000),
) -> list[Station]:
    """List AM stations with optional filters."""
    session = request.state.db_session
    query = select(Station).where(Station.service == "AM")

    if state:
        query = query.where(Station.state == state.upper())
    if freq_min is not None:
        query = query.where(Station.frequency >= freq_min)
    if freq_max is not None:
        query = query.where(Station.frequency <= freq_max)
    if callsign:
        query = query.where(col(Station.callsign).startswith(callsign.upper()))
    if station_class:
        query = query.where(Station.station_class == station_class.upper())

    query = query.limit(limit)
    return list(session.exec(query).all())
