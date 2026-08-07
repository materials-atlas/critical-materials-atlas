# -*- coding: utf-8 -*-
"""Monthly currency->USD from the ECB reference rates (free, no key), so any-currency source converts at
the ACTUAL rate for each month rather than a fixed constant. ECB quotes each currency PER EUR, so
X->USD = (USD per EUR) / (X per EUR). Cached per currency; falls back to the nearest earlier month."""
import os, csv, urllib.request
import schema

_URL = "https://data-api.ecb.europa.eu/service/data/EXR/M.{ccy}.EUR.SP00.A?format=csvdata&startPeriod=2000-01"
_cache = {}   # currency -> {YYYYMM: units-of-currency per EUR}


def _rates(ccy):
    if ccy in _cache:
        return _cache[ccy]
    path = os.path.join(schema.ROOT, 'pipeline', 'data', f'fx_{ccy.lower()}_eur.csv')
    if not os.path.exists(path):
        open(path, 'wb').write(urllib.request.urlopen(_URL.format(ccy=ccy), timeout=60).read())
    r = {}
    for row in csv.DictReader(open(path, encoding='utf8')):
        tp, v = row.get('TIME_PERIOD'), row.get('OBS_VALUE')
        if tp and v:
            try:
                r[int(tp.replace('-', ''))] = float(v)
            except ValueError:
                pass
    _cache[ccy] = r
    return r


def _at(rates, period):
    if period in rates:
        return rates[period]
    earlier = [p for p in rates if p <= period]
    return rates[max(earlier)] if earlier else (rates[min(rates)] if rates else None)


def eur_to_usd(period):
    return _at(_rates('USD'), period) or schema.EUR_USD


def to_usd(value, period, currency):
    """Convert `value` (in `currency`, for month YYYYMM) to USD via ECB EUR crosses."""
    if value is None:
        return None
    if currency == 'USD':
        return value
    usd_eur = eur_to_usd(period)
    if currency == 'EUR':
        return value * usd_eur
    ccy_eur = _at(_rates(currency), period)      # units of `currency` per EUR
    return value * usd_eur / ccy_eur if ccy_eur else None
