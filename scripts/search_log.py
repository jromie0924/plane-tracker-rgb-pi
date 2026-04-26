import argparse
import json
import os
import sys

LOG_PATH = os.path.join(os.path.dirname(__file__), '..', 'tracker_log', 'log.json')

def get_data() -> dict:
  try:
    with open(LOG_PATH, 'r') as file:
      data = json.load(file)
      return data
  except FileNotFoundError:
    return None


if __name__ == '__main__':
  parser = argparse.ArgumentParser()
  parser.add_argument('--callsign', type=str)
  args = parser.parse_args()
  
  callsign = args.callsign
  data = get_data()
  
  if data:
    entry = data.get(callsign)
    if entry:
      print(json.dumps(entry, indent=2))
    else:
      print(f"Entry not found for callsign {callsign}.")
  else:
    print("No data found.")