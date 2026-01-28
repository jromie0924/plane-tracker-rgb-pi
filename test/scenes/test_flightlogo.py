import json
import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../src")))

import scenes.flightlogo as flightlogo


def test_record_missing_logo_creates_and_increments(tmp_path, monkeypatch):
  missing_dir = tmp_path / "missing_logos"
  missing_file = missing_dir / "missing_logos.json"

  monkeypatch.setattr(flightlogo, "MISSING_LOGOS_DIR", str(missing_dir))
  monkeypatch.setattr(flightlogo, "MISSING_LOGOS_FILE", str(missing_file))

  flightlogo._record_missing_logo("ABC")
  assert missing_file.exists()

  with open(missing_file, "r", encoding="utf-8") as file:
    data = json.load(file)
  assert data == {"ABC": 1}

  flightlogo._record_missing_logo("ABC")
  with open(missing_file, "r", encoding="utf-8") as file:
    data = json.load(file)
  assert data == {"ABC": 2}

  flightlogo._record_missing_logo("DEF")
  with open(missing_file, "r", encoding="utf-8") as file:
    data = json.load(file)
  assert data == {"ABC": 2, "DEF": 1}
