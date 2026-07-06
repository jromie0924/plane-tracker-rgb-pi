import json
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest
from botocore.exceptions import ClientError

# Patch boto3 before the handler imports so module-level calls
# (boto3.resource(...).Table(...), boto3.client("ssm")) don't try to hit AWS.
_resource_patcher = patch("boto3.resource", MagicMock())
_client_patcher = patch("boto3.client", MagicMock())
_resource_patcher.start()
_client_patcher.start()

from api import handler  # noqa: E402

_resource_patcher.stop()
_client_patcher.stop()


VALID_KEY = "secret-key-abc123"


@pytest.fixture
def mock_table():
  """Override handler._table with a MagicMock for the test scope."""
  mock = MagicMock()
  with patch.object(handler, "_table", mock):
    yield mock


@pytest.fixture
def mock_expected_key():
  """Bypass SSM by stubbing _expected_key directly; clear the warm cache."""
  handler._api_key_cache = {"value": None, "fetched_at": 0.0}
  with patch.object(handler, "_expected_key", return_value=VALID_KEY) as m:
    yield m


def make_event(query_params=None, origin=None, headers=None):
  evt_headers = dict(headers or {})
  if origin:
    evt_headers["origin"] = origin
  return {
    "queryStringParameters": query_params or {},
    "headers": evt_headers,
  }


# --- auth ---

def test_missing_key_returns_403(mock_table, mock_expected_key):
  event = make_event({"callsign": "UAL123"})
  response = handler.lambda_handler(event, None)
  assert response["statusCode"] == 403


def test_wrong_key_returns_403(mock_table, mock_expected_key):
  event = make_event({"key": "wrong", "callsign": "UAL123"})
  response = handler.lambda_handler(event, None)
  assert response["statusCode"] == 403


def test_empty_key_returns_403(mock_table, mock_expected_key):
  event = make_event({"key": "", "callsign": "UAL123"})
  response = handler.lambda_handler(event, None)
  assert response["statusCode"] == 403


def test_ssm_failure_fails_closed(mock_table):
  handler._api_key_cache = {"value": None, "fetched_at": 0.0}
  with patch.object(handler, "_expected_key", side_effect=Exception("ssm down")):
    event = make_event({"key": "anything", "callsign": "UAL123"})
    response = handler.lambda_handler(event, None)
    assert response["statusCode"] == 403


# --- input validation ---

def test_missing_callsign_returns_400(mock_table, mock_expected_key):
  event = make_event({"key": VALID_KEY})
  response = handler.lambda_handler(event, None)
  assert response["statusCode"] == 400
  assert "callsign" in json.loads(response["body"])["error"].lower()


def test_callsign_is_uppercased(mock_table, mock_expected_key):
  mock_table.query.return_value = {"Items": []}
  event = make_event({"key": VALID_KEY, "callsign": "ual123"})
  response = handler.lambda_handler(event, None)
  assert response["statusCode"] == 200
  assert json.loads(response["body"])["callsign"] == "UAL123"


def test_bad_timestamp_returns_400(mock_table, mock_expected_key):
  event = make_event({"key": VALID_KEY, "callsign": "UAL123", "timestamp": "not-a-date"})
  response = handler.lambda_handler(event, None)
  assert response["statusCode"] == 400


def test_iso_timestamp_accepted(mock_table, mock_expected_key):
  mock_table.query.return_value = {"Items": []}
  event = make_event({
    "key": VALID_KEY,
    "callsign": "UAL123",
    "timestamp": "2026-05-20T14:30:00",
  })
  response = handler.lambda_handler(event, None)
  assert response["statusCode"] == 200


def test_epoch_ms_digits_timestamp_accepted(mock_table, mock_expected_key):
  mock_table.query.return_value = {"Items": []}
  event = make_event({
    "key": VALID_KEY,
    "callsign": "UAL123",
    "timestamp": "1747750200000",
  })
  response = handler.lambda_handler(event, None)
  assert response["statusCode"] == 200


# --- query behavior ---

def test_query_without_timestamp_returns_items(mock_table, mock_expected_key):
  items = [{"callsign": "UAL123", "timestamp": Decimal("1700000000000")}]
  mock_table.query.return_value = {"Items": items}
  event = make_event({"key": VALID_KEY, "callsign": "UAL123"})
  response = handler.lambda_handler(event, None)
  body = json.loads(response["body"])
  assert response["statusCode"] == 200
  assert body["count"] == 1
  assert body["window_minutes"] is None
  assert body["items"][0]["callsign"] == "UAL123"


def test_query_with_timestamp_sets_window_minutes(mock_table, mock_expected_key):
  mock_table.query.return_value = {"Items": []}
  event = make_event({
    "key": VALID_KEY,
    "callsign": "UAL123",
    "timestamp": "2026-05-20T14:30:00",
  })
  response = handler.lambda_handler(event, None)
  body = json.loads(response["body"])
  assert response["statusCode"] == 200
  assert body["window_minutes"] == handler.WINDOW_MINUTES


def test_filter_engine_collapses_clustered_results(mock_table, mock_expected_key):
  """End-to-end: items within 15 minutes of each other reduce to the newest of each cluster."""
  base = 1_700_000_000_000
  items = [
    {"callsign": "UAL123", "timestamp": Decimal(base)},
    {"callsign": "UAL123", "timestamp": Decimal(base + 60 * 1000)},        # 1 min after base
    {"callsign": "UAL123", "timestamp": Decimal(base + 30 * 60 * 1000)},   # 30 min after base
  ]
  mock_table.query.return_value = {"Items": items}
  event = make_event({"key": VALID_KEY, "callsign": "UAL123"})
  response = handler.lambda_handler(event, None)
  body = json.loads(response["body"])
  # Two clusters survive: the +30m point, and the newest of the {base, base+1m} cluster.
  assert body["count"] == 2
  timestamps = [item["timestamp"] for item in body["items"]]
  assert timestamps == [base + 30 * 60 * 1000, base + 60 * 1000]


def test_empty_query_result_returns_empty_items(mock_table, mock_expected_key):
  mock_table.query.return_value = {"Items": []}
  event = make_event({"key": VALID_KEY, "callsign": "UAL123"})
  response = handler.lambda_handler(event, None)
  body = json.loads(response["body"])
  assert response["statusCode"] == 200
  assert body["count"] == 0
  assert body["items"] == []


def test_throttle_returns_429(mock_table, mock_expected_key):
  mock_table.query.side_effect = ClientError(
    {"Error": {"Code": "ProvisionedThroughputExceededException", "Message": "throttled"}},
    "Query",
  )
  event = make_event({"key": VALID_KEY, "callsign": "UAL123"})
  response = handler.lambda_handler(event, None)
  assert response["statusCode"] == 429


def test_other_client_error_returns_502(mock_table, mock_expected_key):
  mock_table.query.side_effect = ClientError(
    {"Error": {"Code": "InternalServerError", "Message": "boom"}},
    "Query",
  )
  event = make_event({"key": VALID_KEY, "callsign": "UAL123"})
  response = handler.lambda_handler(event, None)
  assert response["statusCode"] == 502


def test_more_available_true_when_last_evaluated_key_present(mock_table, mock_expected_key):
  mock_table.query.return_value = {
    "Items": [],
    "LastEvaluatedKey": {"callsign": "UAL123", "timestamp": Decimal("1700000000000")},
  }
  event = make_event({"key": VALID_KEY, "callsign": "UAL123"})
  response = handler.lambda_handler(event, None)
  assert json.loads(response["body"])["more_available"] is True


def test_more_available_false_when_no_last_evaluated_key(mock_table, mock_expected_key):
  mock_table.query.return_value = {"Items": []}
  event = make_event({"key": VALID_KEY, "callsign": "UAL123"})
  response = handler.lambda_handler(event, None)
  assert json.loads(response["body"])["more_available"] is False


def test_decimal_values_serialized_as_numbers(mock_table, mock_expected_key):
  items = [{
    "callsign": "UAL123",
    "timestamp": Decimal("1700000000000"),
    "lat": Decimal("41.8781"),
    "alt": Decimal("15000"),
  }]
  mock_table.query.return_value = {"Items": items}
  event = make_event({"key": VALID_KEY, "callsign": "UAL123"})
  response = handler.lambda_handler(event, None)
  body = json.loads(response["body"])
  assert body["items"][0]["timestamp"] == 1700000000000
  assert body["items"][0]["lat"] == 41.8781
  assert body["items"][0]["alt"] == 15000


# --- CORS ---

def test_cors_allowlisted_origin_is_echoed(mock_table, mock_expected_key):
  mock_table.query.return_value = {"Items": []}
  event = make_event({"key": VALID_KEY, "callsign": "UAL123"}, origin="https://example.com")
  response = handler.lambda_handler(event, None)
  assert response["headers"]["Access-Control-Allow-Origin"] == "https://example.com"
  assert response["headers"].get("Vary") == "Origin"


def test_cors_unlisted_origin_is_not_echoed(mock_table, mock_expected_key):
  mock_table.query.return_value = {"Items": []}
  event = make_event({"key": VALID_KEY, "callsign": "UAL123"}, origin="https://evil.com")
  response = handler.lambda_handler(event, None)
  assert "Access-Control-Allow-Origin" not in response["headers"]


def test_cors_headers_present_on_error_responses(mock_table, mock_expected_key):
  # Auth failure path still needs CORS so the browser surfaces the real 403.
  event = make_event({"callsign": "UAL123"}, origin="https://example.com")
  response = handler.lambda_handler(event, None)
  assert response["statusCode"] == 403
  assert response["headers"]["Access-Control-Allow-Origin"] == "https://example.com"


def test_cors_wildcard_allows_any_origin(mock_table, mock_expected_key):
  mock_table.query.return_value = {"Items": []}
  with patch.object(handler, "CORS_ALLOWED_ORIGINS", ["*"]):
    event = make_event({"key": VALID_KEY, "callsign": "UAL123"}, origin="https://anything.com")
    response = handler.lambda_handler(event, None)
    assert response["headers"]["Access-Control-Allow-Origin"] == "*"


def test_no_origin_header_no_cors_headers(mock_table, mock_expected_key):
  mock_table.query.return_value = {"Items": []}
  event = make_event({"key": VALID_KEY, "callsign": "UAL123"})
  response = handler.lambda_handler(event, None)
  assert "Access-Control-Allow-Origin" not in response["headers"]


# --- SSM key caching ---

def test_expected_key_cached_across_calls(mock_table):
  """A second call inside the cache TTL should not re-query SSM."""
  handler._api_key_cache = {"value": None, "fetched_at": 0.0}
  mock_ssm = MagicMock()
  mock_ssm.get_parameter.return_value = {"Parameter": {"Value": VALID_KEY}}
  with patch.object(handler, "_ssm", mock_ssm):
    mock_table.query.return_value = {"Items": []}
    event = make_event({"key": VALID_KEY, "callsign": "UAL123"})
    handler.lambda_handler(event, None)
    handler.lambda_handler(event, None)
    assert mock_ssm.get_parameter.call_count == 1
