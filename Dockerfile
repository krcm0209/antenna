FROM python:3.14-slim AS build

RUN apt-get update \
    && apt-get install -y --no-install-recommends libsqlite3-mod-spatialite \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-workspace

COPY README.md .
COPY src/ src/
RUN uv sync --frozen --no-dev --no-editable

# Collect mod_spatialite and all its transitive shared library deps
# into /spatialite-libs for a clean COPY into the final image.
RUN mkdir /spatialite-libs && \
    SPATIALITE=$(find /usr/lib -name "mod_spatialite.so" | head -1) && \
    cp "$SPATIALITE" /spatialite-libs/ && \
    ldd "$SPATIALITE" | awk '/=>/{print $3}' | sort -u | while read lib; do \
        cp --dereference "$lib" /spatialite-libs/; \
    done


FROM build AS dev

CMD ["sleep", "infinity"]


FROM gcr.io/distroless/cc-debian13 AS production

COPY --from=build /usr/local/bin/python3.14 /usr/local/bin/python3.14
COPY --from=build /usr/local/lib/python3.14/ /usr/local/lib/python3.14/
COPY --from=build /usr/local/lib/libpython3.14.so* /usr/local/lib/

COPY --from=build /spatialite-libs/ /usr/lib/spatialite/

COPY --from=build /app /app
COPY fcc.db /app/

ENV VIRTUAL_ENV="/app/.venv"
ENV PATH="/app/.venv/bin:/usr/local/bin:$PATH"
ENV PYTHONPATH="/app/.venv/lib/python3.14/site-packages"
ENV LD_LIBRARY_PATH="/usr/lib/spatialite:/usr/local/lib"
ENV FCC_API_SPATIALITE_PATH="/usr/lib/spatialite/mod_spatialite"

WORKDIR /app
EXPOSE 8080

ENTRYPOINT ["/usr/local/bin/python3.14", "-m", "uvicorn", "antenna.main:app", "--host", "0.0.0.0", "--port", "8080"]
