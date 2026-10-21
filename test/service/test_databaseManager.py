import gzip
import os
import sqlite3
import sys
import threading
import time
import pytest
from unittest.mock import patch, MagicMock
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))
import services.databaseManager as database_manager
from services.databaseManager import DatabaseManager, AIRPORTS_FILE, ROUTES_FILE

AIRPORTS_CSV = (
  'Code,Name,ICAO,IATA,Location,CountryISO2,Latitude,Longitude,AltitudeFeet\n'
  'KLAX,Los Angeles International Airport,KLAX,LAX,Los Angeles,US,33.942501,-118.407997,125\n'
  'KDEN,Denver International Airport,KDEN,DEN,Denver,US,39.861698,-104.672997,5431\n'
  'KJFK,John F Kennedy International Airport,KJFK,JFK,New York,US,40.639801,-73.7789,13\n'
  'FOA,Foula Airport,,FOA,Foula,GB,60.121,-2.052,150\n'
)
ROUTES_CSV = (
  'Callsign,Code,Number,AirlineCode,AirportCodes\n'
  'UAL1234,UAL,1234,UAL,KLAX-KDEN-KJFK\n'
  'DAL5,DAL,5,DAL,KJFK-KLAX\n'
)


@pytest.fixture
def mock_config():
  with patch('services.databaseManager.config') as mock_config:
    mock_config.APP_NAME = 'test_app'
    mock_config.ROUTE_DATA_URL = 'test_url'
    mock_config.ROUTE_DATA_REFRESH_DAYS = 7
    mock_config.ADSB_USER_AGENT = 'test-agent'
    yield mock_config


@pytest.fixture
def db_paths(mock_config, tmp_path):
  db_file = str(tmp_path / 'routes.db')
  mock_config.ROUTE_DB_FILE = db_file
  with patch.object(database_manager, 'TEMP_DB_FILE', f'{db_file}.tmp'):
    yield db_file


@pytest.fixture
def manager(mock_config, db_paths):
  # Fresh singleton per test
  DatabaseManager._instance = None
  yield DatabaseManager()
  DatabaseManager._instance = None


def fetch_returning(responses):
  '''Builds a _fetch stand-in that returns responses[(name, etag)] and records each call.'''
  calls = []
  def fetch(name, etag):
    calls.append((name, etag))
    return responses[(name, etag)]
  fetch.calls = calls
  return fetch


def build_database(manager, airports_etag='"a1"', routes_etag='"r1"'):
  fetch = fetch_returning({
    (AIRPORTS_FILE, None): (AIRPORTS_CSV, airports_etag),
    (ROUTES_FILE, None): (ROUTES_CSV, routes_etag),
  })
  with patch.object(manager, '_fetch', side_effect=fetch):
    manager.rebuild()


def query(db_file, sql, params=()):
  conn = sqlite3.connect(db_file)
  try:
    return conn.execute(sql, params).fetchall()
  finally:
    conn.close()


# needs_rebuild

def test_needs_rebuild_when_database_missing(manager):
  assert manager.needs_rebuild() is True


def test_needs_rebuild_false_after_successful_build(manager):
  build_database(manager)
  manager._last_rebuild_attempt = 0  # ignore the retry delay

  assert manager.needs_rebuild() is False


def test_needs_rebuild_when_upstream_check_is_due(manager, db_paths):
  build_database(manager)
  manager._last_rebuild_attempt = 0
  eight_days_ago = int(time.time()) - 8 * 24 * 60 * 60
  conn = sqlite3.connect(db_paths)
  with conn:
    conn.execute('UPDATE source_files SET checked_at = ?', (eight_days_ago,))
  conn.close()

  assert manager.needs_rebuild() is True


def test_needs_rebuild_when_schema_version_is_old(manager, db_paths):
  build_database(manager)
  manager._last_rebuild_attempt = 0
  conn = sqlite3.connect(db_paths)
  conn.execute('PRAGMA user_version = 0')
  conn.close()

  assert manager.needs_rebuild() is True


def test_needs_rebuild_when_file_is_not_a_database(manager, db_paths):
  with open(db_paths, 'w') as f:
    f.write('not a database ' * 10)

  assert manager.needs_rebuild() is True


def test_needs_rebuild_false_while_rebuild_running(manager):
  manager._rebuild_lock.acquire()
  try:
    assert manager.needs_rebuild() is False
  finally:
    manager._rebuild_lock.release()


def test_needs_rebuild_false_within_retry_delay_after_failure(manager):
  with patch.object(manager, '_fetch', side_effect=RuntimeError('no network')):
    manager.rebuild()

  # Database is still missing, but it was just attempted
  assert manager.needs_rebuild() is False


# retry backoff

def fail_rebuild(manager, times):
  with patch.object(manager, '_fetch', side_effect=RuntimeError('no network')):
    for _ in range(times):
      manager.rebuild()


def test_retry_delay_doubles_after_each_consecutive_failure(manager):
  base = database_manager.REBUILD_RETRY_SECONDS
  delays = []
  for _ in range(4):
    fail_rebuild(manager, 1)
    delays.append(manager._retry_delay())

  assert delays == [base, base * 2, base * 4, base * 8]


def test_retry_delay_is_capped(manager):
  fail_rebuild(manager, 50)

  assert manager._retry_delay() == database_manager.REBUILD_RETRY_MAX_SECONDS


def test_retry_delay_resets_after_success(manager):
  fail_rebuild(manager, 3)
  build_database(manager)

  assert manager._consecutive_failures == 0
  assert manager._retry_delay() == database_manager.REBUILD_RETRY_SECONDS


def test_retry_delay_resets_when_data_unchanged(manager):
  build_database(manager)
  fail_rebuild(manager, 3)

  fetch = fetch_returning({
    (AIRPORTS_FILE, '"a1"'): (None, '"a1"'),
    (ROUTES_FILE, '"r1"'): (None, '"r1"'),
  })
  with patch.object(manager, '_fetch', side_effect=fetch):
    manager.rebuild()

  assert manager._consecutive_failures == 0


def test_needs_rebuild_waits_for_backed_off_delay(manager):
  fail_rebuild(manager, 2)  # next retry in 2x the base delay
  base = database_manager.REBUILD_RETRY_SECONDS

  manager._last_rebuild_attempt = time.time() - base * 1.5
  assert manager.needs_rebuild() is False

  manager._last_rebuild_attempt = time.time() - base * 2.5
  assert manager.needs_rebuild() is True


# rebuild

def test_rebuild_creates_database(manager, db_paths):
  build_database(manager)

  assert os.path.isfile(db_paths)
  assert not os.path.exists(f'{db_paths}.tmp')
  assert query(db_paths, 'PRAGMA user_version') == [(manager._schema_version,)]
  assert query(db_paths, 'SELECT seq, airport_code FROM route_stops WHERE callsign = ? ORDER BY seq', ('UAL1234',)) == [
    (0, 'KLAX'), (1, 'KDEN'), (2, 'KJFK'),
  ]
  assert query(db_paths, 'SELECT name, etag FROM source_files ORDER BY name') == [
    (AIRPORTS_FILE, '"a1"'), (ROUTES_FILE, '"r1"'),
  ]


def test_rebuild_keys_airport_without_icao_by_code(manager, db_paths):
  build_database(manager)

  assert query(db_paths, 'SELECT code, icao, iata FROM airports WHERE code = ?', ('FOA',)) == [('FOA', None, 'FOA')]


def test_rebuild_skips_airports_with_invalid_coordinates(manager, db_paths):
  bad_airports = AIRPORTS_CSV + 'XXXX,Broken Airport,XXXX,,Nowhere,US,not-a-number,0,0\n'
  fetch = fetch_returning({
    (AIRPORTS_FILE, None): (bad_airports, '"a1"'),
    (ROUTES_FILE, None): (ROUTES_CSV, '"r1"'),
  })
  with patch.object(manager, '_fetch', side_effect=fetch):
    manager.rebuild()

  assert query(db_paths, 'SELECT COUNT(*) FROM airports') == [(4,)]


def test_rebuild_sends_stored_etags_and_keeps_database_when_unchanged(manager, db_paths):
  build_database(manager)
  stale = int(time.time()) - 8 * 24 * 60 * 60
  conn = sqlite3.connect(db_paths)
  with conn:
    conn.execute('UPDATE source_files SET checked_at = ?', (stale,))
  conn.close()
  inode_before = os.stat(db_paths).st_ino

  fetch = fetch_returning({
    (AIRPORTS_FILE, '"a1"'): (None, '"a1"'),
    (ROUTES_FILE, '"r1"'): (None, '"r1"'),
  })
  with patch.object(manager, '_fetch', side_effect=fetch):
    manager.rebuild()

  assert fetch.calls == [(AIRPORTS_FILE, '"a1"'), (ROUTES_FILE, '"r1"')]
  assert os.stat(db_paths).st_ino == inode_before  # not replaced
  checked = [row[0] for row in query(db_paths, 'SELECT checked_at FROM source_files')]
  assert all(c > stale for c in checked)


def test_rebuild_skips_build_when_etag_changed_but_contents_did_not(manager, db_paths):
  build_database(manager)
  inode_before = os.stat(db_paths).st_ino

  # Both files come back 200 with new ETags, but identical contents
  fetch = fetch_returning({
    (AIRPORTS_FILE, '"a1"'): (AIRPORTS_CSV, '"a2"'),
    (ROUTES_FILE, '"r1"'): (ROUTES_CSV, '"r2"'),
  })
  with patch.object(manager, '_fetch', side_effect=fetch):
    manager.rebuild()

  assert os.stat(db_paths).st_ino == inode_before  # not replaced
  # New ETags are recorded so the next check can get a 304
  assert query(db_paths, 'SELECT name, etag FROM source_files ORDER BY name') == [
    (AIRPORTS_FILE, '"a2"'), (ROUTES_FILE, '"r2"'),
  ]


def test_rebuild_stores_content_hashes(manager, db_paths):
  build_database(manager)

  hashes = dict(query(db_paths, 'SELECT name, sha256 FROM source_files'))
  assert hashes[AIRPORTS_FILE] == database_manager._content_hash(AIRPORTS_CSV)
  assert hashes[ROUTES_FILE] == database_manager._content_hash(ROUTES_CSV)


def test_rebuild_refetches_unchanged_file_when_other_changed(manager, db_paths):
  build_database(manager)

  new_routes = ROUTES_CSV + 'AAL9,AAL,9,AAL,KDEN-KJFK\n'
  fetch = fetch_returning({
    (AIRPORTS_FILE, '"a1"'): (None, '"a1"'),
    (ROUTES_FILE, '"r1"'): (new_routes, '"r2"'),
    (AIRPORTS_FILE, None): (AIRPORTS_CSV, '"a1"'),
  })
  with patch.object(manager, '_fetch', side_effect=fetch):
    manager.rebuild()

  assert (AIRPORTS_FILE, None) in fetch.calls
  assert query(db_paths, 'SELECT COUNT(*) FROM route_stops WHERE callsign = ?', ('AAL9',)) == [(2,)]
  assert query(db_paths, 'SELECT etag FROM source_files WHERE name = ?', (ROUTES_FILE,)) == [('"r2"',)]


def test_rebuild_failure_keeps_existing_database(manager, db_paths):
  build_database(manager)
  inode_before = os.stat(db_paths).st_ino

  with patch.object(manager, '_fetch', side_effect=RuntimeError('Response code: 500')):
    manager.rebuild()  # logged, not raised

  assert os.stat(db_paths).st_ino == inode_before
  assert query(db_paths, 'SELECT COUNT(*) FROM route_stops') == [(5,)]


def test_rebuild_returns_immediately_when_already_running(manager):
  manager._rebuild_lock.acquire()
  try:
    with patch.object(manager, '_fetch') as mock_fetch:
      manager.rebuild()
    mock_fetch.assert_not_called()
  finally:
    manager._rebuild_lock.release()


def test_concurrent_rebuilds_only_run_once(manager):
  started = threading.Event()
  release = threading.Event()
  fetch_count = 0

  def slow_fetch(name, etag):
    nonlocal fetch_count
    fetch_count += 1
    started.set()
    release.wait(timeout=5)
    return {AIRPORTS_FILE: (AIRPORTS_CSV, '"a1"'), ROUTES_FILE: (ROUTES_CSV, '"r1"')}[name]

  with patch.object(manager, '_fetch', side_effect=slow_fetch):
    first = threading.Thread(target=manager.rebuild)
    first.start()
    started.wait(timeout=5)
    manager.rebuild()  # should return immediately while the first is still running
    release.set()
    first.join(timeout=5)

  assert fetch_count == 2  # one per source file, from the first rebuild only


# _fetch

@pytest.fixture
def mock_https_connection():
  with patch('services.databaseManager.http.client.HTTPSConnection') as mock_https_connection:
    yield mock_https_connection


def make_response(status, body=b'', etag=None):
  response = MagicMock()
  response.status = status
  response.read.return_value = body
  response.getheader.side_effect = lambda name: etag if name == 'ETag' else None
  return response


def test_fetch_decompresses_body_and_returns_etag(manager, mock_https_connection):
  body = gzip.compress(('﻿' + AIRPORTS_CSV).encode('utf-8'))  # upstream files start with a BOM
  mock_https_connection.return_value.getresponse.return_value = make_response(200, body, '"a1"')

  text, etag = manager._fetch(AIRPORTS_FILE, None)

  assert text == AIRPORTS_CSV
  assert etag == '"a1"'
  headers = mock_https_connection.return_value.request.call_args.kwargs['headers']
  assert 'If-None-Match' not in headers


def test_fetch_sends_etag_and_returns_none_when_not_modified(manager, mock_https_connection):
  mock_https_connection.return_value.getresponse.return_value = make_response(304)

  text, etag = manager._fetch(ROUTES_FILE, '"r1"')

  assert text is None
  assert etag == '"r1"'
  headers = mock_https_connection.return_value.request.call_args.kwargs['headers']
  assert headers['If-None-Match'] == '"r1"'


def test_fetch_raises_on_error_status_and_closes_connection(manager, mock_https_connection):
  mock_https_connection.return_value.getresponse.return_value = make_response(500)

  with pytest.raises(RuntimeError):
    manager._fetch(ROUTES_FILE, None)

  mock_https_connection.return_value.close.assert_called_once()
