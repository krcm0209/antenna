CREATE TABLE stations (
    facility_id    INTEGER PRIMARY KEY,
    callsign       TEXT NOT NULL,
    service        TEXT NOT NULL,
    frequency      REAL NOT NULL,
    channel        INTEGER,
    station_class  TEXT,
    erp_kw         REAL,
    haat_m         REAL,
    rcamsl_m       REAL,
    antenna_lat    REAL NOT NULL,
    antenna_lon    REAL NOT NULL,
    city           TEXT,
    state          TEXT,
    licensee       TEXT,
    license_status TEXT,
    application_id INTEGER,
    file_number    TEXT
);

CREATE INDEX idx_stations_callsign ON stations (callsign);
CREATE INDEX idx_stations_service ON stations (service);
CREATE INDEX idx_stations_state ON stations (state);
CREATE INDEX idx_stations_frequency ON stations (frequency);

CREATE TABLE contours (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    facility_id    INTEGER NOT NULL REFERENCES stations(facility_id),
    application_id INTEGER,
    service_type   TEXT NOT NULL,
    field_strength REAL,
    erp_kw         REAL,
    contour_data   TEXT
);

CREATE INDEX idx_contours_facility ON contours (facility_id);
