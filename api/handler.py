"""
Read-only query endpoint for the plane-tracker DynamoDB flight log.

Exposes GET /flights with query parameters:
  callsign   (required)  Flight identifier, e.g. UAL123.
  timestamp  (optional)  A human-readable time. When given, results are
                         limited to a +/- WINDOW_MINUTES window around it.

Access is restricted by source IP: the caller's address must fall within
one of the CIDRs stored in the SSM parameter named by ALLOWED_IPS_PARAM.

Responses carry CORS headers for any browser origin listed in the
CORS_ALLOWED_ORIGINS environment variable (comma-separated; "*" for any).
"""

import ipaddress
import json
import logging
import os
import time
from datetime import datetime, timezone
from decimal import Decimal
from zoneinfo import ZoneInfo

import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

TABLE_NAME = os.environ["TABLE_NAME"]
ALLOWED_IPS_PARAM = os.environ["ALLOWED_IPS_PARAM"]
WINDOW_MINUTES = int(os.environ.get("WINDOW_MINUTES", "15"))
MAX_ITEMS = int(os.environ.get("MAX_ITEMS", "50"))
ALLOWLIST_CACHE_TTL = int(os.environ.get("ALLOWLIST_CACHE_TTL", "60"))
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

# Cache the allowlist across warm invocations so we don't hit SSM every request.
_allowlist = {"networks": None, "fetched_at": 0.0}


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


def _allowed_networks():
    """Load (and briefly cache) the CIDR allowlist from SSM Parameter Store."""
    now = time.time()
    if (
        _allowlist["networks"] is not None
        and now - _allowlist["fetched_at"] < ALLOWLIST_CACHE_TTL
    ):
        return _allowlist["networks"]

    raw = _ssm.get_parameter(Name=ALLOWED_IPS_PARAM)["Parameter"]["Value"]
    networks = [
        ipaddress.ip_network(token.strip(), strict=False)
        for token in raw.split(",")
        if token.strip()
    ]
    _allowlist["networks"] = networks
    _allowlist["fetched_at"] = now
    return networks


def _ip_allowed(source_ip):
    try:
        addr = ipaddress.ip_address(source_ip)
    except ValueError:
        return False
    try:
        networks = _allowed_networks()
    except Exception:
        # Fail closed: if the allowlist can't be read, deny.
        logger.exception("Could not load IP allowlist from SSM.")
        return False
    return any(addr in net for net in networks)


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
    source_ip = (
        event.get("requestContext", {}).get("identity", {}).get("sourceIp", "")
    )
    if not _ip_allowed(source_ip):
        logger.warning("Rejected request from %s", source_ip or "<unknown>")
        return _response(403, {"error": "Forbidden"})

    params = event.get("queryStringParameters") or {}

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

    items = result.get("Items", [])
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
