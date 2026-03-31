from pydantic import BaseModel


class StationAtLocation(BaseModel):
    facility_id: int
    callsign: str
    service: str
    frequency: float
    station_class: str | None = None
    erp_kw: float | None = None
    city: str | None = None
    state: str | None = None
    distance_km: float
    estimated_signal_dbm: float | None = None


class LookupResponse(BaseModel):
    latitude: float
    longitude: float
    stations: list[StationAtLocation]
