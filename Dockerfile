FROM python:3.14-slim AS base

RUN apt-get update \
    && apt-get install -y --no-install-recommends libsqlite3-mod-spatialite \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

ENV PATH="/root/.local/bin:$PATH"

WORKDIR /app

CMD ["sleep", "infinity"]

FROM base AS production

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY src/ src/
COPY fcc.db .

EXPOSE 8080

CMD ["uv", "run", "fastapi", "run", "src/antenna/main.py", "--host", "0.0.0.0", "--port", "8080"]
