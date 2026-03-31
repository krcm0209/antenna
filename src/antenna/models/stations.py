from sqlmodel import Field, SQLModel


class Station(SQLModel, table=True):
    __tablename__ = "stations"

    facility_id: int = Field(primary_key=True)
    callsign: str = Field(index=True)
    service: str = Field(index=True)
    frequency: float = Field(index=True)
    channel: int | None = None
    station_class: str | None = None
    erp_kw: float | None = None
    haat_m: float | None = None
    rcamsl_m: float | None = None
    antenna_lat: float
    antenna_lon: float
    city: str | None = None
    state: str | None = Field(default=None, index=True)
    licensee: str | None = None
    license_status: str | None = None
    application_id: int | None = None
    file_number: str | None = None
