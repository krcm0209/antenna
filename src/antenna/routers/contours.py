import json

from fastapi import APIRouter, HTTPException, Request

from antenna.models.contours import ContourPoint, ContourResponse, GeoJSONPolygon

router = APIRouter(prefix="/contours", tags=["contours"])


@router.get("/{facility_id}")
def get_contour(request: Request, facility_id: int) -> ContourResponse:
    """Get the broadcast contour polygon for a station."""
    raw_conn = request.state.raw_conn

    row = raw_conn.execute(
        """SELECT c.facility_id, c.service_type, c.field_strength, c.erp_kw,
                  c.contour_data, AsGeoJSON(c.geom) as geojson
           FROM contours c
           WHERE c.facility_id = ?
           LIMIT 1""",
        (facility_id,),
    ).fetchone()

    if row is None:
        raise HTTPException(status_code=404, detail=f"No contour found for facility {facility_id}")

    geojson_str = row["geojson"]
    if geojson_str is None:
        raise HTTPException(status_code=404, detail=f"No geometry for facility {facility_id}")

    geojson_dict = json.loads(geojson_str)
    geometry = GeoJSONPolygon(
        type=geojson_dict["type"],
        coordinates=geojson_dict["coordinates"],
    )

    contour_points = None
    if row["contour_data"]:
        raw_points = json.loads(row["contour_data"])
        contour_points = [
            ContourPoint(
                azimuth=p["azimuth"],
                latitude=p["latitude"],
                longitude=p["longitude"],
                distance_km=p["distance"],
                haat_m=p["haat"],
                erp_kw=p["erp"],
            )
            for p in raw_points
        ]

    return ContourResponse(
        facility_id=row["facility_id"],
        service_type=row["service_type"],
        field_strength=row["field_strength"],
        erp_kw=row["erp_kw"],
        geometry=geometry,
        contour_points=contour_points,
    )
