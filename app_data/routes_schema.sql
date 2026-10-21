-- Schema for the local route database, built from the VRS standing data
-- published at https://vrs-standing-data.adsb.lol (routes.csv.gz, airports.csv.gz).
--
-- This script is run against a fresh temp file on every rebuild, which is then
-- swapped into place with os.replace(). It intentionally uses plain CREATE TABLE
-- (not IF NOT EXISTS) so running it against an existing database fails loudly.

-- Bump this when the schema changes so an older database gets rebuilt.
PRAGMA user_version = 2;

-- One row per airport, from airports.csv.
-- code is the key route_stops refers to. It's the ICAO code for all but a
-- handful of airports that have none, where it holds the IATA code instead.
CREATE TABLE airports (
  code          TEXT PRIMARY KEY,
  icao          TEXT,
  iata          TEXT,
  name          TEXT NOT NULL,
  location      TEXT,
  country_iso2  TEXT,
  lat           REAL NOT NULL,
  lon           REAL NOT NULL,
  alt_feet      REAL
) WITHOUT ROWID;

-- One row per stop on a route, from routes.csv's AirportCodes column
-- (e.g. KLAX-KDEN-KJFK becomes seq 0, 1, 2).
-- seq 0 is the origin and the highest seq is the final destination.
-- The airline is derived from the callsign, so it isn't stored here.
CREATE TABLE route_stops (
  callsign      TEXT NOT NULL,
  seq           INTEGER NOT NULL,
  airport_code  TEXT NOT NULL,
  PRIMARY KEY (callsign, seq)
) WITHOUT ROWID;

-- Each source file this database was built from, keyed by file name
-- (e.g. 'routes.csv.gz'). Stored here rather than in a separate cache file so it's
-- swapped in atomically with the data it describes.
-- etag lets an unchanged file come back as a cheap 304. The ETag can change when the
-- contents haven't (it's derived from the file's modified time), so sha256 of the
-- decompressed contents is what decides whether the data actually changed.
-- checked_at is the last time the file was downloaded or confirmed unchanged.
CREATE TABLE source_files (
  name          TEXT PRIMARY KEY,
  etag          TEXT,
  sha256        TEXT NOT NULL,
  checked_at    INTEGER NOT NULL  -- unix epoch seconds
) WITHOUT ROWID;
