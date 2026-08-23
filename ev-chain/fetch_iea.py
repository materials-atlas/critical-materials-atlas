"""Refresh the two official IEA world historical series used by the EV pilot."""
from __future__ import annotations

import os
import urllib.parse
import urllib.request


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
API = "https://api.iea.org/evs/"


def fetch(parameter, filename):
    query = urllib.parse.urlencode({"parameter": parameter, "mode": "Cars", "category": "Historical", "region": "World", "csv": "true"})
    target = os.path.join(ROOT, "raw", filename)
    request = urllib.request.Request(f"{API}?{query}", headers={"User-Agent": "critical-materials-atlas/ev-pilot"})
    with urllib.request.urlopen(request, timeout=60) as response:
        payload = response.read()
    if not payload.startswith(b"region,category,parameter"):
        raise SystemExit(f"Unexpected IEA response for {parameter}")
    with open(target, "wb") as handle:
        handle.write(payload)
    print("WROTE", target, len(payload), "bytes")


if __name__ == "__main__":
    fetch("EV sales", "iea_ev_sales_2026.csv")
    fetch("EV stock", "iea_ev_stock_2026.csv")
