"""
Read-only query endpoint for the plane-tracker DynamoDB flight log.

Exposes GET /flights with query parameters:
  key        (required)  Shared secret. Must match the value stored in the
                         SSM parameter named by API_KEY_PARAM.
  callsign   (required)  Flight identifier, e.g. UAL123.
  timestamp  (optional)  A human-readable time. When given, results are
                         limited to a +/- WINDOW_MINUTES window around it.

Responses carry CORS headers for any browser origin listed in the
CORS_ALLOWED_ORIGINS environment variable (comma-separated; "*" for any).
"""

import json
import logging
import os
import secrets
import time
from datetime import datetime, timezone
from decimal import Decimal
from zoneinfo import ZoneInfo

import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError

from filterengine import FilterEngine

logger = logging.getLogger()
logger.setLevel(logging.INFO)

TABLE_NAME = os.environ["TABLE_NAME"]
API_KEY_PARAM = os.environ["API_KEY_PARAM"]
WINDOW_MINUTES = int(os.environ.get("WINDOW_MINUTES", "15"))
MAX_ITEMS = int(os.environ.get("MAX_ITEMS", "50"))
KEY_CACHE_TTL = int(os.environ.get("KEY_CACHE_TTL", "60"))
DEFAULT_TZ = os.environ.get("DEFAULT_TZ", "UTC")
CORS_ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.environ.get("CORS_ALLOWED_ORIGINS", "").split(",")
    if origin.strip()
]

try:
    _default_tz = ZoneInfo(DEFAULT_TZ)
except Exception:
    logger.warning("Unknown DEFAULT_TZ %r; falling back to UTC.", DEFAULT_TZ)
    _default_tz = timezone.utc

_table = boto3.resource("dynamodb").Table(TABLE_NAME)
_ssm = boto3.client("ssm")

# Cache the expected key across warm invocations so we don't hit SSM every request.
_api_key_cache = {"value": None, "fetched_at": 0.0}


class _DecimalEncoder(json.JSONEncoder):
    """DynamoDB returns numbers as Decimal, which json can't serialize."""

    def default(self, o):
        if isinstance(o, Decimal):
            return int(o) if o == o.to_integral_value() else float(o)
        return super().default(o)


def _response(status, body):
    return {
        "statusCode": status,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body, cls=_DecimalEncoder),
    }


def _request_origin(event):
    """Pull the browser Origin header off the request, if present."""
    headers = event.get("headers") or {}
    return headers.get("origin") or headers.get("Origin")


def _cors_headers(origin):
    """CORS headers to merge into a response, echoing an allowlisted origin."""
    if "*" in CORS_ALLOWED_ORIGINS:
        return {"Access-Control-Allow-Origin": "*"}
    if origin and origin in CORS_ALLOWED_ORIGINS:
        return {"Access-Control-Allow-Origin": origin, "Vary": "Origin"}
    return {}


def _expected_key():
    """Load (and briefly cache) the expected API key from SSM Parameter Store."""
    now = time.time()
    if (
        _api_key_cache["value"] is not None
        and now - _api_key_cache["fetched_at"] < KEY_CACHE_TTL
    ):
        return _api_key_cache["value"]

    value = _ssm.get_parameter(Name=API_KEY_PARAM)["Parameter"]["Value"].strip()
    _api_key_cache["value"] = value
    _api_key_cache["fetched_at"] = now
    return value


def _key_ok(supplied):
    if not supplied:
        return False
    try:
        expected = _expected_key()
    except Exception:
        # Fail closed: if the key can't be read, deny.
        logger.exception("Could not load API key from SSM.")
        return False
    return secrets.compare_digest(supplied, expected)


def _parse_timestamp_to_ms(raw):
    """Parse a human timestamp (or raw epoch-ms digits) to epoch milliseconds."""
    raw = raw.strip()
    if raw.isdigit():
        return int(raw)
    dt = datetime.fromisoformat(raw)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=_default_tz)
    return int(dt.timestamp() * 1000)


def _handle(event, context):
    params = event.get("queryStringParameters") or {}

    if not _key_ok((params.get("key") or "").strip()):
        logger.warning("Rejected request: bad or missing key")
        return _response(403, {"error": "Forbidden"})

    callsign = (params.get("callsign") or "").strip().upper()
    if not callsign:
        return _response(400, {"error": "Missing required query parameter: callsign"})

    timestamp_raw = params.get("timestamp")
    if timestamp_raw:
        try:
            center_ms = _parse_timestamp_to_ms(timestamp_raw)
        except ValueError:
            return _response(
                400,
                {
                    "error": (
                        f"Could not parse timestamp {timestamp_raw!r}. "
                        "Use ISO-8601, e.g. 2026-05-20T14:30:00."
                    )
                },
            )
        half = WINDOW_MINUTES * 60 * 1000
        key_condition = Key("callsign").eq(callsign) & Key("timestamp").between(
            center_ms - half, center_ms + half
        )
    else:
        key_condition = Key("callsign").eq(callsign)

    try:
        result = _table.query(
            KeyConditionExpression=key_condition,
            ScanIndexForward=False,  # most recent first
            Limit=MAX_ITEMS,
        )
    except ClientError as e:
        code = e.response["Error"]["Code"]
        if code == "ProvisionedThroughputExceededException":
            logger.warning("DynamoDB query throttled for %s.", callsign)
            return _response(429, {"error": "Database throttled - retry shortly."})
        logger.exception("DynamoDB query failed.")
        return _response(502, {"error": "Database query failed."})

    items = FilterEngine.filter_flights(result.get("Items", []))
    return _response(
        200,
        {
            "callsign": callsign,
            "count": len(items),
            "window_minutes": WINDOW_MINUTES if timestamp_raw else None,
            "more_available": "LastEvaluatedKey" in result,
            "items": items,
        },
    )


def lambda_handler(event, context):
    """Entrypoint: run the query, then attach CORS headers to the result.

    Headers go on every response (including 403/4xx/5xx) so the browser
    surfaces the real status instead of masking it as a CORS failure.
    """
    response = _handle(event, context)
    cors = _cors_headers(_request_origin(event))
    if cors:
        response.setdefault("headers", {}).update(cors)
    return response
