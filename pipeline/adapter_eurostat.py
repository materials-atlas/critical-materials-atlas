# -*- coding: utf-8 -*-
"""DEEP layer: Eurostat Comext detailed — EU-27, CN-8, monthly, free. The 8-digit that splits the
HS-6 bundles (gallium 81129289 vs germanium 81129295), ~2 years fresher than BACI."""
import os, re, csv, urllib.request
import py7zr
import schema, concordance, fx
from adapter_base import Adapter, num

_DIR = "https://ec.europa.eu/eurostat/api/dissemination/files?dir=comext%2FCOMEXT_DATA%2FPRODUCTS"
_FILE = "https://ec.europa.eu/eurostat/api/dissemination/files?file=comext%2FCOMEXT_DATA%2FPRODUCTS%2F"


class EurostatAdapter(Adapter):
    key = 'eurostat'
    freq = 'M'
    note = 'Eurostat Comext detailed — EU-27, CN-8, monthly, free'
    DATA = os.path.join(schema.ROOT, 'pipeline', 'data')

    def _fetch(self, url, timeout=180):
        req = urllib.request.Request(url, headers={'User-Agent': 'critical-materials-atlas/phase1'})
        return urllib.request.urlopen(req, timeout=timeout).read()   # urllib follows the 302

    def discover(self):
        listing = self._fetch(_DIR).decode('utf8', 'replace')
        return sorted(int(m) for m in set(re.findall(r'full_partxixu_v2_(\d{6})\.7z', listing)))

    def pull(self, period):
        dat = os.path.join(self.DATA, 'comext_tmp', f'full_partxixu{period}.dat')
        if not os.path.exists(dat):
            z = os.path.join(self.DATA, f'comext_{period}.7z')
            if not os.path.exists(z):
                open(z, 'wb').write(self._fetch(_FILE + f'full_partxixu_v2_{period}.7z'))
            with py7zr.SevenZipFile(z) as a:
                a.extractall(os.path.join(self.DATA, 'comext_tmp'))
        return dat

    def normalize(self, raw, period):
        flowmap = {'1': 'import', '2': 'export'}
        with open(raw, encoding='utf8', errors='replace') as f:
            for r in csv.DictReader(f):
                nc = r['PRODUCT_NC']
                if not concordance.hs6_tracked(nc[:6]):
                    continue
                rep = schema.iso3(r['REPORTER'])
                par = schema.iso3(r['PARTNER'])
                yield schema.row(
                    source=self.key, freq=self.freq, period=int(r['PERIOD']),
                    reporter=rep, reporter_name=schema.cname(rep),
                    partner=par, partner_name=schema.cname(par),
                    flow=flowmap.get(r['FLOW'], r['FLOW']),
                    hs6=nc[:6], native_code=nc, code_level=8,
                    material=concordance.material_for(nc, 8),
                    value_usd=(lambda e: e * fx.eur_to_usd(int(r['PERIOD'])) if e is not None else None)(num(r['VALUE_EUR'])),
                    qty_kg=num(r['QUANTITY_KG']),
                    is_mirror=False)
