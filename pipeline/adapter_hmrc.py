# -*- coding: utf-8 -*-
"""DEEP layer: UK HMRC Overseas Trade Statistics — CN-8, monthly, keyless OData API. Values are GBP
(converted via ECB GBP crosses). HMRC splits flows EU/non-EU (1/3 = imports, 2/4 = exports); we merge.
The API restricts $orderby/$select/in and rate-limits, so we use only eq/or/and filters + $expand and
back off on rejection."""
import time, json, urllib.request, urllib.error, urllib.parse
import schema, concordance, fx
from adapter_base import Adapter, num

BASE = "https://api.uktradeinfo.com/OTS"
_PAUSE = 4
FLOWMAP = {1: 'import', 3: 'import', 2: 'export', 4: 'export'}


def _get(url, tries=6):
    for _ in range(tries):
        try:
            raw = urllib.request.urlopen(
                urllib.request.Request(url, headers={'User-Agent': 'critical-materials-atlas/phase2'}), timeout=60).read()
        except urllib.error.HTTPError as e:
            if e.code in (429, 403, 503):
                time.sleep(_PAUSE); continue
            raise
        try:
            return json.loads(raw)
        except json.JSONDecodeError:      # HMRC returns a plain-text "rejected" body when throttled
            time.sleep(_PAUSE); continue
    return {'value': []}


class HMRCAdapter(Adapter):
    key = 'hmrc'
    freq = 'M'
    note = 'UK HMRC OTS — CN-8, monthly, keyless OData'
    WINDOW = 24   # months back from latest

    def _codes(self):
        return [int(c['code']) for c in
                json.load(open(schema.ROOT + r'\pipeline\critical_codes.json', encoding='utf8'))['codes']
                if len(c['code']) == 8 and c['code'].isdigit()]

    def _query(self, filt):
        rows, url = [], BASE + "?$filter=" + urllib.parse.quote(filt) + "&$expand=Country"
        while url:
            d = _get(url)
            rows += d.get('value', [])
            url = d.get('@odata.nextLink')
            if url:
                time.sleep(_PAUSE)
        return rows

    def discover(self):
        rows = self._query("CommodityId eq 72029300 and MonthId ge 202301")
        return sorted({r['MonthId'] for r in rows}) or [202401]

    def pull(self, period):
        y, m = period // 100, period % 100
        start = (y - self.WINDOW // 12) * 100 + m
        codes = self._codes()
        # chunk the OR-list to keep URLs sane
        out = []
        for i in range(0, len(codes), 12):
            chunk = codes[i:i + 12]
            filt = "(" + " or ".join(f"CommodityId eq {c}" for c in chunk) + f") and MonthId ge {start}"
            out += self._query(filt)
            time.sleep(_PAUSE)
        return out

    def normalize(self, raw, period):
        for r in raw:
            nc = str(r['CommodityId'])
            if len(nc) != 8 or not concordance.hs6_tracked(nc[:6]):
                continue
            c = r.get('Country') or {}
            iso2 = c.get('CountryCodeAlpha')
            partner = schema.iso3(iso2) if iso2 else 'n/a'   # n/a = HMRC's suppressed "Confidential Country"
            yield schema.row(
                source=self.key, freq=self.freq, period=int(r['MonthId']),
                reporter='GBR', reporter_name='United Kingdom',
                partner=partner, partner_name=c.get('CountryName', iso2),
                flow=FLOWMAP.get(r['FlowTypeId'], 'export'),
                hs6=nc[:6], native_code=nc, code_level=8,
                material=concordance.material_for(nc, 8),
                value_usd=fx.to_usd(num(r.get('Value')), int(r['MonthId']), 'GBP'),
                qty_kg=num(r.get('NetMass')),
                is_mirror=False)
