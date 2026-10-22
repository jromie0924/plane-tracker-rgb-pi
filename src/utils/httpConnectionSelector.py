import http.client

import config
from config import DataSource


def getHttpConnectionType(url: str, timeout: int):
  match config.ADSB_DATA_SOURCE:
    case DataSource.API:
      return http.client.HTTPSConnection(host=url, timeout=timeout)
    case DataSource.FEEDER:
      return http.client.HTTPConnection(host=url, timeout=timeout)
    case _:
      raise Exception("Invalid ADSB data source provided.")