from typing import Any

import httpx
from aiolimiter import AsyncLimiter

from antenna.config import settings

# 6 requests per 60 seconds to FCC APIs
fcc_rate_limiter = AsyncLimiter(
    settings.fcc_rate_limit_requests,
    settings.fcc_rate_limit_period,
)


class FCCClient:
    """Async HTTP client for FCC APIs with rate limiting."""

    def __init__(self) -> None:
        self.http = httpx.AsyncClient(timeout=30.0)

    async def get_json(self, url: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        async with fcc_rate_limiter:
            response = await self.http.get(url, params=params)
        response.raise_for_status()
        return response.json()

    async def get_text(self, url: str, params: dict[str, Any] | None = None) -> str:
        async with fcc_rate_limiter:
            response = await self.http.get(url, params=params)
        response.raise_for_status()
        return response.text

    async def get_bytes(self, url: str) -> bytes:
        async with fcc_rate_limiter:
            response = await self.http.get(url)
        response.raise_for_status()
        return response.content

    async def close(self) -> None:
        await self.http.aclose()
