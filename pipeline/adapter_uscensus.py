# -*- coding: utf-8 -*-
"""DEEP layer: US Census International Trade — HS-6, monthly, values already USD. Needs a FREE API key
(env CENSUS_API_KEY or pipeline/.census_key, gitignored). Census can't batch commodities and the
unfiltered all-HS6 call times out, so we query ONE call per (flow, commodity) for the latest month(s)
and read all countries. Country = Census name -> ISO3 best-effort. Values GEN_VAL_MO / ALL_VAL_MO (USD)."""
import os, json, time, datetime, urllib.request, urllib.error
import schema, concordance
from adapter_base import Adapter, num

IMP = "https://api.census.gov/data/timeseries/intltrade/imports/hs"
EXP = "https://api.census.gov/data/timeseries/intltrade/exports/hs"


def _load_key():
    k = os.environ.get('CENSUS_API_KEY', '')
    if not k:
        p = os.path.join(schema.ROOT, 'pipeline', '.census_key')   # gitignored, never committed
        if os.path.exists(p):
            k = open(p).read().strip()
    return k


KEY = _load_key()

_NAME2ISO = {v.upper(): k for k, v in schema.ISO3_NAME.items()}
_NAME2ISO.update({
    'CHINA': 'CHN', 'KOREA, SOUTH': 'KOR', 'KOREA, REPUBLIC OF': 'KOR', 'TAIWAN': 'TWN',
    'RUSSIA': 'RUS', 'VIETNAM': 'VNM', 'CZECH REPUBLIC': 'CZE', 'CONGO (KINSHASA)': 'COD',
    'CONGO (DEMOCRATIC REPUBLIC)': 'COD', 'UNITED KINGDOM': 'GBR', 'GERMANY': 'DEU',
    'NETHERLANDS': 'NLD', 'JAPAN': 'JPN', 'FRANCE': 'FRA', 'BRAZIL': 'BRA', 'CANADA': 'CAN',
    'MEXICO': 'MEX', 'INDIA': 'IND', 'AUSTRALIA': 'AUS', 'BELGIUM': 'BEL', 'ITALY': 'ITA',
    'SPAIN': 'ESP', 'SOUTH AFRICA': 'ZAF', 'CHILE': 'CHL', 'PERU': 'PER', 'KAZAKHSTAN': 'KAZ',
})


def _get(url, tries=4):
    for _ in range(tries):
        try:
            resp = urllib.request.urlopen(
                urllib.request.Request(url, headers={'User-Agent': 'critical-materials-atlas/phase2'}), timeout=60)
        except urllib.error.HTTPError as e:
            if e.code in (429, 503):
                time.sleep(4); continue
            return None                      # 400/404 etc. -> treat as no data
        except urllib.error.URLError:
            time.sleep(4); continue
        raw = resp.read()
        if not raw:                          # HTTP 204 = no data for that month/commodity
            return None
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return None
    return None


class USCensusAdapter(Adapter):
    key = 'uscensus'
    freq = 'M'
    note = 'US Census — HS-6, monthly, needs free API key'
    WINDOW = 1   # latest month (widen later; Census can't batch, so calls = 31 codes x window x 2 flows)
    PROBE = '282200'   # cobalt: reliably traded, used to find the latest published month

    def _months(self, latest, n):
        y, m, out = latest // 100, latest % 100, []
        for _ in range(n):
            out.append(y * 100 + m)
            m -= 1
            if m < 1:
                m, y = 12, y - 1
        return out

    def discover(self):
        d0 = datetime.date.today()
        y, m = d0.year, d0.month
        for _ in range(18):
            cand = f"{y}-{m:02d}"
            if _get(f"{IMP}?get=CTY_CODE,GEN_VAL_MO&COMM_LVL=HS6&I_COMMODITY={self.PROBE}&time={cand}&key={KEY}"):
                return [int(cand.replace('-', ''))]
            m -= 1
            if m < 1:
                m, y = 12, y - 1
        return [int(f"{d0.year}{d0.month:02d}")]

    def pull(self, period):
        codes = sorted(concordance.tracked_hs6_set())
        months = self._months(period, self.WINDOW)
        rows = []
        for base, cvar, vvar, flow in ((IMP, 'I_COMMODITY', 'GEN_VAL_MO', 'import'),
                                        (EXP, 'E_COMMODITY', 'ALL_VAL_MO', 'export')):
            for code in codes:
                for pm in months:
                    tm = f"{pm//100}-{pm%100:02d}"
                    d = _get(f"{base}?get=CTY_CODE,CTY_NAME,{cvar},{vvar}&COMM_LVL=HS6&{cvar}={code}&time={tm}&key={KEY}")
                    if not d or len(d) < 2:
                        continue
                    h = {name: i for i, name in enumerate(d[0])}
                    for r in d[1:]:
                        rows.append((pm, flow, code, r[h['CTY_NAME']], num(r[h[vvar]])))
                    time.sleep(0.2)
        return rows

    def normalize(self, raw, period):
        for pm, flow, code, cty_name, val in raw:
            iso = _NAME2ISO.get((cty_name or '').upper())
            if not iso:                       # drops "TOTAL FOR ALL COUNTRIES" and region aggregates
                continue
            yield schema.row(
                source=self.key, freq=self.freq, period=pm,
                reporter='USA', reporter_name='United States',
                partner=iso, partner_name=cty_name.title(),
                flow=flow, hs6=code, native_code=code, code_level=6,
                material=concordance.material_for(code, 6),
                value_usd=val, qty_kg=None,   # Census quantity units are commodity-specific; omit for v1
                is_mirror=False)
