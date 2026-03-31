"""Models representing raw FCC API response shapes."""

from pydantic import BaseModel


class FCCContourPoint(BaseModel):
    """A single contour point from the FCC Entity API response."""

    x: float  # longitude
    y: float  # latitude
    z: float
    distance: float
    haat: float | None = None
    erp: float | None = None
    azimuth: float


class FCCContourProperties(BaseModel):
    """Properties from a single feature in the FCC Entity API response."""

    callsign: str = ""
    facility_id: int = 0
    application_id: int = 0
    service: str = ""
    station_class: str | None = None
    antenna_lat: float = 0.0
    antenna_lon: float = 0.0
    field: float = 0.0
    erp: float = 0.0
    channel: int = 0
    rcamsl: float = 0.0
    nradial: int = 0
    contourData: list[FCCContourPoint] = []


class FCCContourGeometry(BaseModel):
    type: str
    coordinates: list[list[list[list[float]]]]  # MultiPolygon


class FCCContourFeature(BaseModel):
    type: str = "Feature"
    geometry: FCCContourGeometry
    properties: FCCContourProperties


class FCCEntityResponse(BaseModel):
    type: str = "FeatureCollection"
    features: list[FCCContourFeature]


class FCCFacilityResult(BaseModel):
    """A single facility from the publicfiles.fcc.gov search API."""

    id: str
    callSign: str
    service: str
    rfChannel: str | None = None
    frequency: str | None = None
    status: str = ""
    communityCity: str = ""
    communityState: str = ""
    partyName: str = ""
    licenseExpirationDate: str | None = None


class FCCFacilitySearchResponse(BaseModel):
    """Parsed response from publicfiles.fcc.gov facility search."""

    fm_facilities: list[FCCFacilityResult] = []
    am_facilities: list[FCCFacilityResult] = []
