from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, Request, Response
from sqlmodel import Session, create_engine

from antenna.config import settings
from antenna.db import get_connection
from antenna.routers import contours, lookup, stations


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    # SQLModel engine for station/contour metadata queries
    engine = create_engine(
        f"sqlite:///{settings.db_path}", connect_args={"check_same_thread": False}
    )

    app.state.engine = engine

    yield

    engine.dispose()


app = FastAPI(
    title="Antenna",
    description="A radio station API powered by FCC broadcast data",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(stations.router)
app.include_router(contours.router)
app.include_router(lookup.router)


@app.middleware("http")
async def db_session_middleware(request: Request, call_next) -> Response:
    """Provide a SQLModel session and per-request raw connection."""
    raw_conn = get_connection(settings.db_path, readonly=True)
    try:
        with Session(request.app.state.engine) as session:
            request.state.db_session = session
            request.state.raw_conn = raw_conn
            return await call_next(request)
    finally:
        raw_conn.close()


@app.exception_handler(httpx.HTTPStatusError)
async def upstream_error_handler(request: Request, exc: httpx.HTTPStatusError) -> Response:
    from fastapi.responses import JSONResponse

    return JSONResponse(
        status_code=502,
        content={
            "detail": "FCC upstream API error",
            "upstream_status": exc.response.status_code,
        },
    )


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
