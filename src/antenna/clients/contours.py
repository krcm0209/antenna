from antenna.clients.base import FCCClient
from antenna.config import settings
from antenna.models.fcc_responses import FCCEntityResponse


async def fetch_entity_contour(
    client: FCCClient,
    *,
    callsign: str | None = None,
    facility_id: int | None = None,
    service_type: str = "fm",
) -> FCCEntityResponse:
    """Fetch contour from FCC Entity API and parse into typed response."""
    params: dict[str, str | int] = {"serviceType": service_type}
    if callsign:
        params["callsign"] = callsign
    elif facility_id is not None:
        params["facilityId"] = facility_id
    else:
        msg = "Either callsign or facility_id is required"
        raise ValueError(msg)

    url = f"{settings.fcc_contours_base_url}/entity.json"
    data = await client.get_json(url, params=params)
    return FCCEntityResponse.model_validate(data)
