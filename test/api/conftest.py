"""Shared setup for api tests.

Sets env vars that handler.py reads at import time, and adds the project
root to sys.path so `from api.<x> import ...` resolves.
"""

import os
import sys

os.environ.setdefault("TABLE_NAME", "test_table")
os.environ.setdefault("API_KEY_PARAM", "/test/api_key")
os.environ.setdefault("WINDOW_MINUTES", "15")
os.environ.setdefault("MAX_ITEMS", "50")
os.environ.setdefault("KEY_CACHE_TTL", "60")
os.environ.setdefault("DEFAULT_TZ", "UTC")
os.environ.setdefault("CORS_ALLOWED_ORIGINS", "https://example.com,https://other.com")

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
