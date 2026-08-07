# -*- coding: utf-8 -*-
"""WIDE layer: CEPII BACI HS17 — mirror-reconciled, ~200 reporters, world, HS-6, annual.
The comparable research base every deep/mirror layer sits on top of."""
import os, re, csv, io, zipfile
import schema, concordance
from adapter_base import Adapter, num


class BACIAdapter(Adapter):
    key = 'baci'
    freq = 'A'
    note = 'CEPII BACI HS17 — reconciled, world, HS-6, annual'
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
        with z.open(member) as fh:
            r = csv.reader(io.TextIOWrapper(fh, 'utf8'))
            next(r)  # header t,i,j,k,v,q
            for t, i, j, k, v, q in r:
                if k not in crit:
                    continue
                yield schema.row(
                    source=self.key, freq=self.freq, period=int(t),
                    reporter=schema.NUM2ISO3.get(i, i), reporter_name=schema.NUM2NAME.get(i, i),
                    partner=schema.NUM2ISO3.get(j, j), partner_name=schema.NUM2NAME.get(j, j),
                    flow='export',                       # BACI is directional exporter -> importer
                    hs6=k, native_code=k, code_level=6,
                    material=concordance.material_for(k, 6),
                    value_usd=num(v, 1000),              # BACI value is in kUSD
                    qty_kg=num(q, 1000),                 # BACI qty is in tonnes
                    is_mirror=False)
