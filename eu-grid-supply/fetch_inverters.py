# -*- coding: utf-8 -*-
"""Supplement to export-controls/fetch_comext_ec.py for the inverter line of the EU grid-supply study.

CN 85044086 (inverters > 7.5 kVA) exists only 2023-2025. Before 2023 the same line was 85044088
(same description, excluding telecom/ADP inverters); from 2026 inverters are split by function instead,
85044084 (with maximum power point tracking, i.e. solar) and 85044087 (without), at any power. This
fetches 85044088 for 2019-2022 and 85044084/85044087 for 2026 into eu-grid-supply/eu_data_inverters/,
using the same Comext monthly files and filters. Network fetcher: the runner must never run it.
Usage: python eu-grid-supply/fetch_inverters.py
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), 'export-controls'))
import fetch_comext_ec as f  # noqa: E402

f.OUTDIR = os.path.join(HERE, 'eu_data_inverters')
f.TMP = os.path.join(HERE, '_comext_tmp')
f.LOG = os.path.join(f.OUTDIR, 'fetch.log')
f.PREFIXES = ['85044088', '85044084', '85044087']

if __name__ == '__main__':
    sys.argv = [sys.argv[0], '--start', '201901', '--end', '202212']
    f.main()
    sys.argv = [sys.argv[0], '--start', '202601', '--end', '202607']
    f.main()
