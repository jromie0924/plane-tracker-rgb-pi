# Flight Query API

A read-only HTTP API over the `tracker_log` DynamoDB table. One endpoint —
`GET /flights` — returns logged flights for a callsign, optionally narrowed to
a time window.

Access is gated by a **shared key** passed in the `key` query parameter. The
expected value lives in an SSM parameter; the Lambda fetches it (with a short
warm-cache) and compares against the request. This isn't real security — it
just keeps the table from being trivially hammered by anyone who finds the URL.

## Layout

| File | Purpose |
|------|---------|
| `handler.py` | Lambda function — key check, query, JSON response. |
| `template.yaml` | SAM template — Lambda + REST API + IAM. |
| `requirements.txt` | `tzdata`, so IANA zone names always resolve. |

## API

`GET /flights`

| Param | Required | Notes |
|-------|----------|-------|
| `key` | yes | Shared secret. Must match the SSM parameter value. |
| `callsign` | yes | Flight identifier, e.g. `UAL123`. Upper-cased before lookup. |
| `timestamp` | no | Human time; results limited to ±`WindowMinutes` around it. |

`timestamp` accepts ISO-8601 (`2026-05-20`, `2026-05-20T14:30:00`,
`2026-05-20T14:30:00-05:00`) or raw epoch-milliseconds. A value with **no
offset** is interpreted in `DefaultTimezone` (UTC unless overridden).

Response: `{ callsign, count, window_minutes, more_available, items: [...] }`,
most recent first, capped at `MaxItems`.

### Examples

```bash
# all recent entries for a callsign
curl "$API/flights?key=$KEY&callsign=UAL123"

# entries within ~15 min of a time
curl "$API/flights?key=$KEY&callsign=UAL123&timestamp=2026-05-20T14:30:00"
```

## Deploy

Prerequisites: the AWS SAM CLI, and AWS credentials for the account/region
holding the table (**us-east-2**).

```bash
cd api
sam build
sam deploy --guided      # first time; writes samconfig.toml
```

Accept `us-east-2` as the region. The stack prints the `ApiUrl` output.
Later deploys: `sam build && sam deploy`.

## Key

The expected key lives in SSM parameter `/plane-tracker/api/key`. It is
**not** managed by the template, so deploys never overwrite it. Create it
once with any opaque value (a UUID is fine):

```bash
aws ssm put-parameter \
  --name /plane-tracker/api/key \
  --region us-east-2 --type String \
  --value "$(uuidgen)"
```

To rotate, run the same command with `--overwrite`. The Lambda caches the
value for `KEY_CACHE_TTL` seconds (default 60), so a rotation takes effect
within a minute without a redeploy.

## Tuning (stack parameters)

| Parameter | Default | |
|-----------|---------|--|
| `WindowMinutes` | 15 | half-window each side of a timestamp |
| `MaxItems` | 50 | cap on callsign-only results |
| `DefaultTimezone` | UTC | e.g. `America/Chicago` for local-time input |
| `ThrottleRateLimit` / `ThrottleBurstLimit` | 5 / 10 | API throttle — keeps the request rate under the 1-2 RCU table's ceiling |

## Custom domain (optional, later)

To put your own domain on the API:

1. Request a free **ACM certificate** for the domain, in **us-east-2** (this
   is a REGIONAL API, so the cert must live in the same region).
2. API Gateway → Custom domain names → create, attach the cert, map it to
   this API + stage.
3. Add a DNS record (CNAME, or alias) from your domain to the API Gateway
   target domain name.

No charge for the custom domain or the certificate. It can also be wired into
`template.yaml` later via the `Domain` property on `AWS::Serverless::Api`.

## Cost

Effectively free at personal volume: Lambda stays within the free tier,
DynamoDB reads draw on provisioned capacity (no per-request charge), and
standard SSM parameters are free. The only ongoing line item is API Gateway
REST requests at $3.50/million — cents per month.
