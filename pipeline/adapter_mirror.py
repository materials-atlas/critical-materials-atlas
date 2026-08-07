# -*- coding: utf-8 -*-
"""MIRROR layer: reconstruct a 'dark' country's trade from what its PARTNERS report, tagged
is_mirror=True. This is the move for countries that suppress or don't publish — China (gallium/
germanium after the 2023 export controls), Russia (no detail since 2022), DRC (weak statistics).
Here it runs over reconciled BACI, so it mirrors BACI's own figures — but the MECHANISM is the point:
applied to raw Comtrade when a country goes dark, the partner-side sum is the only signal there is,
and it's exactly what TDM cannot give you when a primary source blanks out."""
import os, re, csv, io, zipfile
import schema, concordance
from adapter_base import Adapter, num

DARK = {'CHN': 'China', 'COD': 'Dem. Rep. of the Congo', 'RUS': 'Russian Federation'}
ISO3_NUM = {iso3: num_ for num_, iso3 in schema.NUM2ISO3.items()}   # reverse the BACI lookup


class MirrorAdapter(Adapter):
    key = 'mirror'
    freq = 'A'
    note = 'dark-country trade reconstructed from partner reports (China/Russia/DRC)'
    ZIP = os.path.join(schema.ROOT, 'raw', 'baci', 'BACI_HS17_V202601.zip')

    def discover(self):
        z = zipfile.ZipFile(self.ZIP)
        return sorted(int(m.group(1)) for m in (re.search(r'_Y(\d{4})_', n) for n in z.namelist()) if m)

    def pull(self, period):
        z = zipfile.ZipFile(self.ZIP)
        return z, next(n for n in z.namelist() if f'_Y{period}_' in n)

    def normalize(self, raw, period):
        z, member = raw
        crit = concordance.tracked_hs6_set()
        dark = {ISO3_NUM[iso]: iso for iso in DARK if iso in ISO3_NUM}   # {baci_num: iso3}
        with z.open(member) as fh:
            r = csv.reader(io.TextIOWrapper(fh, 'utf8'))
            next(r)  # header t,i,j,k,v,q  (exporter i, importer j)
            for t, i, j, k, v, q in r:
                if k not in crit:
                    continue
                mat = concordance.material_for(k, 6)
                # dark country as IMPORTER: reconstruct its imports from partner (exporter i) reports
                if j in dark:
                    d = dark[j]
                    yield schema.row(source=self.key, freq=self.freq, period=int(t),
                        reporter=d, reporter_name=DARK[d],
                        partner=schema.NUM2ISO3.get(i, i), partner_name=schema.NUM2NAME.get(i, i),
                        flow='import', hs6=k, native_code=k, code_level=6, material=mat,
                        value_usd=num(v, 1000), qty_kg=num(q, 1000), is_mirror=True)
                # dark country as EXPORTER: reconstruct its exports from partner (importer j) reports
                if i in dark:
                    d = dark[i]
                    yield schema.row(source=self.key, freq=self.freq, period=int(t),
                        reporter=d, reporter_name=DARK[d],
                        partner=schema.NUM2ISO3.get(j, j), partner_name=schema.NUM2NAME.get(j, j),
                        flow='export', hs6=k, native_code=k, code_level=6, material=mat,
                        value_usd=num(v, 1000), qty_kg=num(q, 1000), is_mirror=True)
