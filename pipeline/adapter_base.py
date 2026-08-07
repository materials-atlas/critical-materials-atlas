# -*- coding: utf-8 -*-
"""The adapter contract. Every source is a subclass implementing discover/pull/normalize; run()
wires them together and gates the output through schema.validate before it can enter the database.
Adding a country = one new subclass in isolation — nothing else changes. This is what makes the
project AI-parallel and survivable over a long, unhurried build."""
import schema


def num(x, scale=1.0):
    """Safe float (handles '', 'NA', None) with optional scaling to canonical units."""
    try:
        return float(x) * scale
    except (TypeError, ValueError):
        return None


class Adapter:
    key = None       # unique source id, e.g. 'baci'
    freq = None      # 'A' (annual) or 'M' (monthly)
    note = ''        # one-line human description

    def discover(self):
        """Return the sorted list of available periods (ints: YYYY or YYYYMM)."""
        raise NotImplementedError

    def pull(self, period):
        """Return raw source material for one period (a handle, path, or rows)."""
        raise NotImplementedError

    def normalize(self, raw, period):
        """Yield canonical rows (schema.row(...)) — the only place source quirks live."""
        raise NotImplementedError

    def run(self, period=None):
        try:
            if period is None:
                periods = self.discover()
                if not periods:                    # a flaky source must not crash the whole build
                    return {'source': self.key, 'freq': self.freq, 'period': None,
                            'rows': [], 'ok': False, 'problems': ['discover() returned no periods']}
                period = periods[-1]
            rows = list(self.normalize(self.pull(period), period))
        except Exception as e:
            return {'source': self.key, 'freq': self.freq, 'period': period,
                    'rows': [], 'ok': False, 'problems': [f'{type(e).__name__}: {e}']}
        ok, problems = schema.validate(rows, self.key)
        return {'source': self.key, 'freq': self.freq, 'period': period,
                'rows': rows, 'ok': ok, 'problems': problems}
