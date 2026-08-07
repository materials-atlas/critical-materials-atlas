# -*- coding: utf-8 -*-
"""DEEP layer: Brazil Comex Stat — NCM-8, monthly, keyless POST API, values already FOB in USD.
Brazil is the niobium chokepoint (~90% of world supply). Rate-limited (~1 req/10s), so we batch every
critical-material NCM into ONE call per flow and retry on 429. Country names are Portuguese -> ISO3 via
the official PAIS reference table."""
import os, csv, json, time, urllib.request, urllib.error
import schema, concordance
from adapter_base import Adapter

API = 'https://api-comexstat.mdic.gov.br/general'
PAIS_URL = 'https://balanca.economia.gov.br/balanca/bd/tabelas/PAIS.csv'
_PAUSE = 13   # API allows ~1 request / 10s; stay clear of it


def _post(body, timeout=60, tries=5):
    data = json.dumps(body).encode()
    for _ in range(tries):
        try:
            req = urllib.request.Request(API, data=data, method='POST',
                headers={'Content-Type': 'application/json', 'User-Agent': 'critical-materials-atlas/phase2'})
            d = json.load(urllib.request.urlopen(req, timeout=timeout))
        except urllib.error.HTTPError as e:
            if e.code == 429:
                time.sleep(_PAUSE); continue
            raise
        if isinstance(d.get('error'), dict) and d['error'].get('code') == 429:
            time.sleep(_PAUSE); continue
        return d
    return {'data': {'list': []}}   # gave up after retries — empty, the validation gate will catch it


class ComexStatAdapter(Adapter):
    key = 'comexstat'
    freq = 'M'
    note = 'Brazil Comex Stat — NCM-8, monthly, USD FOB, keyless'
    WINDOW = 12   # months back from the latest available

    def _pais_map(self):
        cache = os.path.join(schema.ROOT, 'pipeline', 'data', 'pais.csv')
        if not os.path.exists(cache):
            open(cache, 'wb').write(urllib.request.urlopen(PAIS_URL, timeout=60).read())
        m = {}
        for r in csv.DictReader(open(cache, encoding='latin-1'), delimiter=';'):
            iso = (r.get('CO_PAIS_ISOA3') or '').strip()
            if iso and iso != 'ZZZ':
                for nm in (r.get('NO_PAIS'), r.get('NO_PAIS_ING')):
                    if nm:
                        m[nm.strip()] = iso
        return m

    def _ncm_candidates(self):
        cands = set()
        for c in json.load(open(os.path.join(schema.ROOT, 'pipeline', 'critical_codes.json'), encoding='utf8'))['codes']:
            cands.add(c['code'])          # exact code (matches Brazil NCM for HS-based lines, e.g. niobium 72029300)
            cands.add(c['hs6'] + '00')    # the .00 subline where Brazil doesn't subdivide (e.g. gallium 81129200)
        return sorted(cands)

    def discover(self):
        d = _post({"flow": "export", "monthDetail": True, "period": {"from": "2024-01", "to": "2026-12"},
                   "filters": [{"filter": "ncm", "values": ["72029300"]}],
                   "details": ["country", "ncm"], "metrics": ["metricFOB"]})
        periods = sorted({int(r['year'] + r['monthNumber']) for r in d.get('data', {}).get('list', [])})
        return periods or [202606]   # fallback if the probe was rate-limited/empty

    def pull(self, period):
        # monthDetail queries must stay WITHIN a calendar year, so pull the current year (Jan..latest)
        # plus the previous full year — one same-year request per (year, flow).
        y, m = period // 100, period % 100
        ncm = self._ncm_candidates()
        windows = [(y - 1, f"{y-1}-01", f"{y-1}-12"), (y, f"{y}-01", f"{y}-{m:02d}")]
        out = []
        for _yr, pfrom, pto in windows:
            for flow in ('export', 'import'):
                time.sleep(_PAUSE)
                d = _post({"flow": flow, "monthDetail": True, "period": {"from": pfrom, "to": pto},
                           "filters": [{"filter": "ncm", "values": ncm}],
                           "details": ["country", "ncm"], "metrics": ["metricFOB", "metricKG"]})
                for r in d['data']['list']:
                    r['_flow'] = flow
                    out.append(r)
        return out

    def normalize(self, raw, period):
        pais = self._pais_map()
        for r in raw:
            nc = r['coNcm']
            if not concordance.hs6_tracked(nc[:6]):
                continue
            yield schema.row(
                source=self.key, freq=self.freq, period=int(r['year'] + r['monthNumber']),
                reporter='BRA', reporter_name='Brazil',
                partner=pais.get(r['country'], r['country']), partner_name=r['country'],
                flow=r['_flow'], hs6=nc[:6], native_code=nc, code_level=8,
                material=concordance.material_for(nc, 8),
                value_usd=float(r['metricFOB']) if r.get('metricFOB') else None,
                qty_kg=float(r['metricKG']) if r.get('metricKG') else None,
                is_mirror=False)
