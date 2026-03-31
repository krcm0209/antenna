from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    db_path: Path = Path("fcc.db")

    # FCC API base URLs
    fcc_contours_base_url: str = "https://geo.fcc.gov/api/contours"
    fcc_facility_search_url: str = "https://publicfiles.fcc.gov/api/service/facility/search"
    fcc_fm_query_url: str = "https://transition.fcc.gov/fcc-bin/fmq"
    fcc_am_query_url: str = "https://transition.fcc.gov/fcc-bin/amq"

    # FCC bulk data URLs
    fcc_fm_contour_bulk_url: str = (
        "https://transition.fcc.gov/bureaus/mb/databases/map/FM_service_contour_current.zip"
    )
    fcc_lms_dump_url: str = (
        "https://enterpriseefiling.fcc.gov/dataentry/api/download/dbfile/Current_LMS_Dump.zip"
    )

    # SpatiaLite extension path
    spatialite_path: str = "mod_spatialite"

    # Rate limiting for FCC API calls (during sync)
    fcc_rate_limit_requests: int = 6
    fcc_rate_limit_period: float = 60.0

    model_config = {"env_prefix": "FCC_API_"}


settings = Settings()
