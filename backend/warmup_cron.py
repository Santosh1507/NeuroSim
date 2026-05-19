"""Render cron job worker — warms up the in-memory cache.

Runs on a */5 * * * * schedule via render.yaml.
Sends a GET request to the API's warmup endpoint to preload
recent analyses into the in-memory cache after a cold restart.

Environment:
  API_BASE_URL — the public URL of the web service (e.g. https://neurosim-api.onrender.com)
"""

import os
import sys
import urllib.request
import urllib.error


def main():
    base_url = os.environ.get("API_BASE_URL", "")
    if not base_url:
        print("[WARMUP] API_BASE_URL not set — skipping warmup")
        sys.exit(0)

    url = f"{base_url.rstrip('/')}/api/warmup"
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=10) as resp:
            body = resp.read().decode()
            print(f"[WARMUP] {resp.status} — {body}")
    except urllib.error.HTTPError as e:
        print(f"[WARMUP] HTTP {e.code} — {e.read().decode()}")
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"[WARMUP] URL error: {e.reason}")
        sys.exit(1)


if __name__ == "__main__":
    main()
