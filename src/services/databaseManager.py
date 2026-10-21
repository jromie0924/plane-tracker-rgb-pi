import csv
import gzip
import hashlib
import http.client
import io
import logging
import os
import sqlite3
import threading
import time

from http import HTTPStatus

import config


logger = logging.getLogger(config.APP_NAME)

TEMP_DB_FILE = f'{config.ROUTE_DB_FILE}.tmp'
SCHEMA_FILE = 'app_data/routes_schema.sql'

AIRPORTS_FILE = 'airports.csv.gz'
ROUTES_FILE = 'routes.csv.gz'
SOURCE_FILES = (AIRPORTS_FILE, ROUTES_FILE)

# Minimum time between rebuild attempts, so a failing download (e.g. no network)
# isn't retried on every grab cycle. Doubles after each consecutive failure, up to
# REBUILD_RETRY_MAX_SECONDS, and resets once a rebuild succeeds.
REBUILD_RETRY_SECONDS = 15 * 60
REBUILD_RETRY_MAX_SECONDS = 12 * 60 * 60


# Reads the schema version (PRAGMA user_version) declared in the schema file,
# by running it against a throwaway in-memory database. This keeps the version
# defined in one place instead of duplicating it here.
def _read_schema_version() -> int:
  with open(SCHEMA_FILE, 'r') as f:
    schema = f.read()
  conn = sqlite3.connect(':memory:')
  try:
    conn.executescript(schema)
    return conn.execute('PRAGMA user_version').fetchone()[0]
  finally:
    conn.close()


def _content_hash(text: str) -> str:
  return hashlib.sha256(text.encode('utf-8')).hexdigest()


# Yields rows for the airports table from airports.csv, skipping (and counting)
# any row without usable coordinates.
def _airport_rows(airports_csv: str, skipped: dict):
  for row in csv.DictReader(io.StringIO(airports_csv)):
    try:
      yield (
        row['Code'],
        row['ICAO'] or None,
        row['IATA'] or None,
        row['Name'],
        row['Location'] or None,
        row['CountryISO2'] or None,
        float(row['Latitude']),
        float(row['Longitude']),
        float(row['AltitudeFeet']) if row['AltitudeFeet'] else None,
      )
    except (KeyError, ValueError):
      skipped['airports'] += 1


# Yields rows for the route_stops table from routes.csv, one per airport in the
# AirportCodes column (e.g. KLAX-KDEN-KJFK yields seq 0, 1, 2).
def _route_stop_rows(routes_csv: str, skipped: dict):
  for row in csv.DictReader(io.StringIO(routes_csv)):
    callsign = (row.get('Callsign') or '').strip()
    airport_codes = (row.get('AirportCodes') or '').strip()
    if not callsign or not airport_codes:
      skipped['routes'] += 1
      continue
    for seq, airport_code in enumerate(airport_codes.split('-')):
      yield (callsign, seq, airport_code)


class DatabaseManager:
  _instance = None
  _lock = threading.Lock()

  def __new__(cls):
    with cls._lock:
      if not cls._instance:
        cls._instance = super(DatabaseManager, cls).__new__(cls)
      return cls._instance

  def __init__(self):
    if hasattr(self, '_initialized'):
      return
    self._initialized = True

    self._schema_version = _read_schema_version()
    self._rebuild_lock = threading.Lock()
    self._last_rebuild_attempt = 0.0
    self._consecutive_failures = 0

    if self._database_is_current():
      logger.info(f'Route database found at {config.ROUTE_DB_FILE} (schema v{self._schema_version}).')
    else:
      logger.info(f'Route database missing or outdated at {config.ROUTE_DB_FILE}; it will be rebuilt.')

  # Cheap, local-only check (no network) for whether rebuild() should be run.
  # True if the database is missing or outdated, or the route data hasn't been
  # checked for changes in ROUTE_DATA_REFRESH_DAYS.
  def needs_rebuild(self) -> bool:
    if self._rebuild_lock.locked():
      return False  # a rebuild is already running

    if time.time() - self._last_rebuild_attempt < self._retry_delay():
      return False

    return not self._database_is_current() or self._upstream_check_is_due()

  # Downloads the route data and rebuilds the database if it has changed.
  # Blocking; run it on its own thread. If another rebuild is already running,
  # this returns immediately. Errors are logged rather than raised, and leave
  # the existing database untouched.
  def rebuild(self):
    if not self._rebuild_lock.acquire(blocking=False):
      logger.debug('Route database rebuild already in progress.')
      return

    try:
      self._last_rebuild_attempt = time.time()
      self._rebuild()
      self._consecutive_failures = 0
    except Exception as e:
      self._consecutive_failures += 1
      logger.error(f'Route database rebuild failed ({self._consecutive_failures} in a row): {e}. '
                   f'Retrying in {self._retry_delay() / 60:.0f} minutes.', exc_info=True)
    finally:
      self._rebuild_lock.release()

  # Time to wait after the last rebuild attempt before trying again:
  # REBUILD_RETRY_SECONDS, doubled for each consecutive failure after the first,
  # capped at REBUILD_RETRY_MAX_SECONDS.
  def _retry_delay(self) -> float:
    if self._consecutive_failures <= 1:
      return REBUILD_RETRY_SECONDS
    doublings = self._consecutive_failures - 1
    if REBUILD_RETRY_SECONDS * 2 ** min(doublings, 32) >= REBUILD_RETRY_MAX_SECONDS:
      return REBUILD_RETRY_MAX_SECONDS
    return REBUILD_RETRY_SECONDS * 2 ** doublings

  def _rebuild(self):
    # Only use what's stored if the existing database is usable; otherwise a 304
    # would leave us with nothing to build from.
    stored = self._stored_sources() if self._database_is_current() else {}

    downloads = {name: self._fetch(name, stored.get(name, (None, None))[0]) for name in SOURCE_FILES}

    # A file has changed only if it was downloaded and its contents differ from what
    # the database was built from. A new ETag on its own doesn't count.
    changed = [name for name, (body, _) in downloads.items()
               if body is not None and _content_hash(body) != stored.get(name, (None, None))[1]]

    if not changed:
      self._mark_checked({name: etag for name, (_, etag) in downloads.items()})
      logger.info('Route data unchanged since last check.')
      return

    logger.info(f'Route data changed ({", ".join(changed)}); rebuilding.')

    # The database is rebuilt from scratch. Any file that came back unchanged (304)
    # is downloaded again to rebuild from.
    for name, (body, _) in downloads.items():
      if body is None:
        downloads[name] = self._fetch(name, None)

    self._build(downloads)

  # Fetches a source file, returning (decoded csv text, etag). If etag is given and
  # the file hasn't changed, the server replies 304 and this returns (None, etag).
  def _fetch(self, name: str, etag: str | None, timeout=30):
    headers = {'User-Agent': config.ADSB_USER_AGENT}
    if etag:
      headers['If-None-Match'] = etag

    conn = None
    try:
      conn = http.client.HTTPSConnection(config.ROUTE_DATA_URL, timeout=timeout)
      conn.request('GET', f'/{name}', headers=headers)
      response = conn.getresponse()

      if response.status == HTTPStatus.NOT_MODIFIED:
        response.read()
        return None, etag

      if response.status != HTTPStatus.OK:
        raise RuntimeError(f'Error getting {name}. Response code: {response.status}.')

      body = gzip.decompress(response.read()).decode('utf-8-sig')
      return body, response.getheader('ETag')

    finally: # always release the socket, including on the early returns above
      if conn is not None:
        conn.close()

  # Builds a new database in TEMP_DB_FILE from the downloaded files, then swaps it
  # into place. Readers never see a partially built database.
  def _build(self, downloads: dict):
    started = time.time()

    if os.path.exists(TEMP_DB_FILE):
      os.remove(TEMP_DB_FILE)

    with open(SCHEMA_FILE, 'r') as f:
      schema = f.read()

    skipped = {'airports': 0, 'routes': 0}
    conn = sqlite3.connect(TEMP_DB_FILE)
    try:
      # The temp file is thrown away if anything fails, so skip journaling and
      # per-write syncing; it's flushed to disk once below, before the swap.
      conn.execute('PRAGMA journal_mode = OFF')
      conn.execute('PRAGMA synchronous = OFF')
      conn.executescript(schema)

      with conn:
        conn.executemany('INSERT INTO airports VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
                         _airport_rows(downloads[AIRPORTS_FILE][0], skipped))
        conn.executemany('INSERT INTO route_stops VALUES (?, ?, ?)',
                         _route_stop_rows(downloads[ROUTES_FILE][0], skipped))
        conn.executemany('INSERT INTO source_files VALUES (?, ?, ?, ?)',
                         [(name, etag, _content_hash(body), int(started)) for name, (body, etag) in downloads.items()])

      airport_count = conn.execute('SELECT COUNT(*) FROM airports').fetchone()[0]
      stop_count = conn.execute('SELECT COUNT(*) FROM route_stops').fetchone()[0]
    finally:
      conn.close()

    # Make sure the new file is fully on disk before it replaces the old one, so a
    # power cut can't leave a half-written database in place.
    with open(TEMP_DB_FILE, 'rb') as f:
      os.fsync(f.fileno())
    os.replace(TEMP_DB_FILE, config.ROUTE_DB_FILE)

    if skipped['airports'] or skipped['routes']:
      logger.warning(f'Skipped {skipped["airports"]} airport and {skipped["routes"]} route rows with missing or invalid data.')
    logger.info(f'Rebuilt route database with {airport_count} airports and {stop_count} route stops '
                f'in {time.time() - started:.1f}s.')

  # A database is current if it exists, is a readable SQLite file, and was built
  # with the current schema version. A partially built database never ends up at
  # ROUTE_DB_FILE (it's only swapped in once complete), so these checks are enough.
  def _database_is_current(self) -> bool:
    if not os.path.isfile(config.ROUTE_DB_FILE):
      return False

    try:
      # Read-only, so this can never create or modify the file
      conn = sqlite3.connect(f'file:{config.ROUTE_DB_FILE}?mode=ro', uri=True)
      try:
        version = conn.execute('PRAGMA user_version').fetchone()[0]
      finally:
        conn.close()
    except sqlite3.DatabaseError as e:
      logger.warning(f'Route database at {config.ROUTE_DB_FILE} is unreadable: {e}')
      return False

    if version != self._schema_version:
      logger.info(f'Route database schema is v{version}, expected v{self._schema_version}.')
      return False

    return True

  # True if any source file hasn't been checked for changes in ROUTE_DATA_REFRESH_DAYS.
  def _upstream_check_is_due(self) -> bool:
    try:
      conn = sqlite3.connect(f'file:{config.ROUTE_DB_FILE}?mode=ro', uri=True)
      try:
        count, oldest = conn.execute('SELECT COUNT(*), MIN(checked_at) FROM source_files').fetchone()
      finally:
        conn.close()
    except sqlite3.DatabaseError:
      return True

    if count < len(SOURCE_FILES):
      return True

    return time.time() - oldest >= config.ROUTE_DATA_REFRESH_DAYS * 24 * 60 * 60

  # Returns {name: (etag, sha256)} for the source files the database was built from.
  def _stored_sources(self) -> dict:
    try:
      conn = sqlite3.connect(f'file:{config.ROUTE_DB_FILE}?mode=ro', uri=True)
      try:
        return {name: (etag, sha256) for name, etag, sha256 in
                conn.execute('SELECT name, etag, sha256 FROM source_files').fetchall()}
      finally:
        conn.close()
    except sqlite3.DatabaseError:
      return {}

  # Records that the source files were checked and are unchanged, along with their
  # latest ETags so the next check can get a 304 for them.
  def _mark_checked(self, etags: dict):
    now = int(time.time())
    conn = sqlite3.connect(config.ROUTE_DB_FILE)
    try:
      with conn:
        conn.executemany('UPDATE source_files SET etag = ?, checked_at = ? WHERE name = ?',
                         [(etag, now, name) for name, etag in etags.items()])
    finally:
      conn.close()
