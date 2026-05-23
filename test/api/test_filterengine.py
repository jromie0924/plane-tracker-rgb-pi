from decimal import Decimal

from api.filterengine import FilterEngine, MIN_TIME_SEPARATION_MINUTES


MIN_SEP_MS = MIN_TIME_SEPARATION_MINUTES * 60 * 1000


def f(ts, callsign='UAL123'):
  return {'timestamp': ts, 'callsign': callsign}


# --- trivial inputs ---

def test_empty_input_returns_empty_list():
  assert FilterEngine.filter_flights([]) == []


def test_single_flight_returned_unchanged():
  flights = [f(1_000_000)]
  assert FilterEngine.filter_flights(flights) == flights


# --- separation window behavior ---

def test_two_flights_within_window_keeps_only_newest():
  older = f(1_000_000)
  newer = f(1_000_000 + 5 * 60 * 1000)  # 5 min after older
  result = FilterEngine.filter_flights([older, newer])
  assert result == [newer]


def test_two_flights_outside_window_keeps_both_newest_first():
  older = f(1_000_000)
  newer = f(1_000_000 + 20 * 60 * 1000)  # 20 min after older
  result = FilterEngine.filter_flights([older, newer])
  assert [item['timestamp'] for item in result] == [newer['timestamp'], older['timestamp']]


def test_flights_exactly_at_window_boundary_kept():
  """Check is >=, so exactly MIN_SEP_MS apart should keep both."""
  older = f(1_000_000)
  newer = f(1_000_000 + MIN_SEP_MS)
  result = FilterEngine.filter_flights([older, newer])
  assert len(result) == 2


def test_flights_one_ms_under_boundary_keeps_only_newest():
  older = f(1_000_000)
  newer = f(1_000_000 + MIN_SEP_MS - 1)
  result = FilterEngine.filter_flights([older, newer])
  assert result == [newer]


# --- clustering ---

def test_tight_cluster_collapses_to_newest():
  base = 1_000_000_000
  flights = [f(base), f(base + 1000), f(base + 2000), f(base + 3000)]
  result = FilterEngine.filter_flights(flights)
  assert result == [f(base + 3000)]


def test_multiple_clusters_each_collapses_to_its_newest():
  base = 1_000_000_000
  # Cluster A: a1 and a2 within 5 minutes of each other.
  a1 = f(base)
  a2 = f(base + 5 * 60 * 1000)
  # Cluster B: 30 minutes after a2 (so well outside the window), b1 + b2 within
  # 2 minutes of each other.
  b1 = f(a2['timestamp'] + 30 * 60 * 1000)
  b2 = f(b1['timestamp'] + 2 * 60 * 1000)

  result = FilterEngine.filter_flights([a1, a2, b1, b2])

  # Newest of each cluster: b2 (newest in B), a2 (newest in A).
  assert [item['timestamp'] for item in result] == [b2['timestamp'], a2['timestamp']]


def test_unsorted_input_handled_correctly():
  """Sort is internal — caller order shouldn't matter."""
  base = 1_000_000_000
  flights = [
    f(base + 30 * 60 * 1000),
    f(base),
    f(base + 5 * 60 * 1000),
    f(base + 60 * 60 * 1000),
  ]
  result = FilterEngine.filter_flights(flights)
  # Sorted desc: 60m, 30m, 5m, 0.
  #   60m kept; 30m: 60-30=30 >= 15 → kept; 5m: 30-5=25 >= 15 → kept; 0: 5-0=5 < 15 → dropped.
  assert [item['timestamp'] for item in result] == [
    base + 60 * 60 * 1000,
    base + 30 * 60 * 1000,
    base + 5 * 60 * 1000,
  ]


# --- types from DynamoDB ---

def test_decimal_timestamps_supported():
  """DynamoDB returns numeric attrs as Decimal; arithmetic should still work."""
  older = {'timestamp': Decimal('1000000'), 'callsign': 'UAL1'}
  newer = {'timestamp': Decimal('1000000') + Decimal(MIN_SEP_MS), 'callsign': 'UAL1'}
  result = FilterEngine.filter_flights([older, newer])
  assert len(result) == 2


# --- non-mutation / preservation ---

def test_does_not_mutate_input_list_order():
  a = f(1_000_000)
  b = f(2_000_000)
  c = f(3_000_000)
  original = [a, b, c]
  FilterEngine.filter_flights(original)
  assert original == [a, b, c]


def test_preserves_full_flight_dicts():
  flight = {
    'timestamp': 1_000_000,
    'callsign': 'UAL123',
    'lat': 41.8,
    'lon': -87.6,
    'extra': 'data',
  }
  result = FilterEngine.filter_flights([flight])
  assert result == [flight]
