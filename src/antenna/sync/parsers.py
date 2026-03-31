"""Parsers for FCC pipe-delimited data formats."""


def dms_to_decimal(degrees: int, minutes: int, seconds: float) -> float:
    """Convert degrees/minutes/seconds to decimal degrees."""
    return degrees + minutes / 60 + seconds / 3600


def parse_pipe_float(value: str) -> float | None:
    """Parse a float from FCC pipe-delimited fields.

    FCC fields often have trailing units like '5.2    kW' or '415.0   '.
    Split on whitespace and take the first token.
    """
    token = value.strip().split()[0] if value.strip() else ""
    if not token:
        return None
    try:
        return float(token)
    except ValueError:
        return None


def parse_pipe_int(value: str) -> int | None:
    """Parse an int from FCC pipe-delimited fields."""
    token = value.strip().split()[0] if value.strip() else ""
    if not token:
        return None
    try:
        return int(token)
    except ValueError:
        return None
