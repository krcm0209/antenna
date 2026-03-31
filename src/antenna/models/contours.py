from pydantic import BaseModel
from sqlmodel import Field, SQLModel


class Contour(SQLModel, table=True):
    """Contour record (non-geometry columns managed by SQLModel).

    The `geom` geometry column is managed via raw SpatiaLite SQL
    since SQLModel doesn't support spatial column types.
    """

    __tablename__ = "contours"

    id: int | None = Field(default=None, primary_key=True)
    facility_id: int = Field(foreign_key="stations.facility_id", index=True)
    application_id: int | None = None
    service_type: str
    field_strength: float | None = None
    erp_kw: float | None = None
    contour_data: str | None = None  # JSON: 360-point array


# --- API response models (not DB tables) ---


class ContourPoint(BaseModel):
    """A single point on the contour boundary (one per degree of azimuth)."""

    azimuth: float
    latitude: float
    longitude: float
    distance_km: float
    haat_m: float
    erp_kw: float


class GeoJSONPolygon(BaseModel):
    """GeoJSON Polygon geometry."""

    type: str = "Polygon"
    coordinates: list[list[list[float]]]


class ContourResponse(BaseModel):
    facility_id: int
    service_type: str
    field_strength: float | None = None
    erp_kw: float | None = None
    geometry: GeoJSONPolygon
    contour_points: list[ContourPoint] | None = None
