MIN_TIME_SEPARATION_MINUTES = 15

class FilterEngine:

  @staticmethod
  def filter_flights(flights: list[dict]) -> list[dict]:
    min_sep_ms = MIN_TIME_SEPARATION_MINUTES * 60 * 1000
    flights = sorted(flights, key=lambda flight: flight['timestamp'], reverse=True)
    flights_filtered: list[dict] = []
    compare = None

    for flight in flights:
      if compare is None or compare - flight['timestamp'] >= min_sep_ms:
        flights_filtered.append(flight)
        compare = flight['timestamp']

    return flights_filtered