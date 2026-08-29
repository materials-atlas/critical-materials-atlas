"""Evidence JSON for the germanium chain pilot. Uniform schema. Public sources.
Shared chainview renderer, per-figure confidence tags. Run: python record_germanium.py
"""
from __future__ import annotations
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out", "germanium_chain.json")

SRC = {
    "usgs_germanium": {"title": "USGS Mineral Commodity Summaries 2026 — Germanium", "year": 2026, "url": "https://pubs.usgs.gov/periodicals/mcs2026/mcs2026-germanium.pdf"},
    "csis_gege": {"title": "CSIS, China's gallium and germanium export controls", "year": 2023, "url": "https://www.csis.org/analysis/chinas-gallium-and-germanium-export-controls"},
    "bgs_wms": {"title": "BGS, World Mineral Statistics — germanium", "year": 2024, "url": "https://www2.bgs.ac.uk/mineralsuk/statistics/worldStatistics.html"},
    "baci": {"title": "CEPII BACI V202601, based on UN Comtrade", "year": 2026, "url": "https://www.cepii.fr/CEPII/en/bdd_modele/bdd_modele_item.asp?id=37"},
}

CHAIN = {
    "title": "Germanium chain",
    "chokepoint": {"product": "IR optics · fibre", "stage": "Recovery", "mechanism": "byproduct", "physics": "By-product of zinc residues + coal fly ash — can't scale on its own; USGS states producers do not publicly report germanium output, so the share is an estimate", "holder": "China", "share": "~85% (est.)", "control": "Jul 2023", "conf": "estimate"},
    "published": True,
    "related": [{"href": "../gallium-chain/gallium-chain", "label": "Gallium chain"}, {"href": "../fibre-optics-chain/fibre-optics-chain", "label": "Fibre-optics chain"}, {"href": "../defence-chain/defence-chain", "label": "Defence chain"}, {"href": "../displays-indium-chain/displays-indium-chain", "label": "Displays / indium chain"}],
    "accent": "#5a7a5a",
    "eyebrow": "Product-chain pilot · the infrared metal",
    "h1": "Gallium's twin — the infrared metal China controls with the same lever",
    "deck": "Germanium is the metal that lets you see in the dark and carries light down a fibre. It is a by-product of "
            "zinc refining and coal fly ash — no one mines it on purpose — and China produces most of it. In July 2023 "
            "China placed germanium under export licensing alongside gallium: the same by-product trap, the same lever, "
            "the same week.",
    "byline": "zinc residue / coal ash ≠ by-product germanium (China ~85%+) ≠ high-purity Ge / GeO2 ≠ IR optics · fibre · catalysts",
    "correction": "Germanium is gallium's mirror image and shares its playbook. It cannot be mined on its own — it is "
                  "recovered in tiny amounts from zinc refining and coal fly ash — and China produces the majority. Its "
                  "critical roles are infrared optics (thermal imaging and night-vision, a defence use), the "
                  "light-guiding core of optical fibre, PET-plastic polymerisation catalysts and space solar cells. "
                  "China's July 2023 export controls named germanium and gallium together for exactly this reason.",
    "stats": [
        {"v": "~85%+", "l": "China's share of world germanium production (USGS: output not publicly reported — an estimate)", "conf": "estimate"},
        {"v": "Jul 2023", "l": "export-controlled alongside gallium — the same lever, the same week", "conf": "measured"},
        {"v": "IR + fibre", "l": "infrared optics (night-vision / thermal) and optical-fibre cores", "conf": "measured"},
        {"v": "by-product", "l": "recovered from zinc residues and coal fly ash — can't scale alone", "conf": "measured"},
    ],
    "hops": [
        {"n": "1 · Host", "t": "zinc refining residues and coal fly ash — germanium rides along in trace amounts"},
        {"n": "2 · By-product extraction", "t": "germanium recovered and purified to high purity — China ~85%+"},
        {"n": "3 · Ge / GeO2", "t": "high-purity germanium metal, germanium dioxide, and optical-grade crystals"},
        {"n": "4 · Uses", "t": "infrared lenses, optical-fibre cores, PET catalysts, space photovoltaic cells"},
    ],
    "sections": [
        {"h2": "1 · The same by-product trap, the same lever", "panels": [
            {"kind": "big", "h3": "Where germanium comes from", "big": "~85%+ China", "conf": "estimate",
             "text": "Germanium is not mined; it is recovered from the residues of zinc smelting and from coal fly ash, "
                     "so its supply is coupled to zinc and coal, not to germanium demand. China installed the recovery "
                     "capacity at scale and now produces the majority. When it placed germanium under export licensing "
                     "in July 2023 — the same day as gallium — it turned that concentration into a lever on optics and "
                     "chips (see the gallium chain).",
             "note": "USGS MCS 2026; CSIS."},
            {"kind": "text", "h3": "Coupled, so hard to scale",
             "text": "As with gallium, indium and helium, you cannot simply make more germanium: output is bounded by "
                     "how much zinc is refined and coal burned, and by who bothers to recover it. Western zinc "
                     "refineries can recover germanium but many stopped when Chinese supply was cheaper — so the fix is "
                     "restarting recovery circuits, which takes capital and time.",
             "flag": "coupled to zinc and coal, not to demand"},
        ]},
        {"h2": "2 · Seeing in the dark, and guiding light", "panels": [
            {"kind": "text", "h3": "Infrared optics — a defence use", "conf": "measured",
             "text": "Germanium is transparent to infrared light, which makes it the standard lens and window material "
                     "for thermal-imaging and night-vision systems — a directly military application, alongside "
                     "civilian uses like firefighting and industrial sensing. Its concentration is therefore a "
                     "defence-supply concern as much as an industrial one (see the defence chain).",
             "note": "USGS: infrared optics is a leading germanium use.", "flag": "the metal that sees heat"},
            {"kind": "text", "h3": "The core of optical fibre",
             "text": "Germanium dioxide dopes the core of optical fibre to raise its refractive index and guide light "
                     "with minimal loss — the physical basis of the internet's backbone (see the fibre-optics chain). "
                     "It also catalyses PET-plastic production and boosts efficiency in space-grade solar cells. Small "
                     "tonnage, outsized reach.",
             "flag": "small tonnage, backbone role"},
        ]},
        {"h2": "3 · The response", "panels": [
            {"kind": "text", "h3": "Recovery and recycling, slowly",
             "text": "Because germanium is recoverable from existing zinc and coal streams and is efficiently recycled "
                     "from optical and electronic scrap, the chokepoint is rebuildable — the US, Europe and others are "
                     "moving to reopen recovery and stockpile. But qualifying optical- and defence-grade germanium "
                     "takes time, so the July-2023 lever bites in the interim, just as it does for gallium.",
             "flag": "a built chokepoint, rebuildable slowly"},
        ]},
    ],
    "trade_intro": "Germanium has no clean HS6 line — unwrought germanium sits in the shared 811292 'other minor "
                   "metals' basket with gallium and indium, so its trade cannot be isolated (the same limit the atlas "
                   "flags for gallium and indium). The table below shows that basket only as flagged context.",
    "method": [
        {"stage": "Source", "lens": "USGS germanium share", "why": "~85%+ China; a by-product of zinc/coal"},
        {"stage": "Policy", "lens": "Jul-2023 export licensing", "why": "the lever, named with gallium"},
        {"stage": "Uses", "lens": "IR / fibre / catalyst literature", "why": "infrared optics + fibre cores — qualitative"},
        {"stage": "Trade", "lens": "BACI 811292 basket", "why": "germanium not separable from gallium/indium — flagged context"},
    ],
    "sources": SRC,
}

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w", encoding="utf-8") as fh:
    json.dump(CHAIN, fh, ensure_ascii=False, indent=2)
print("wrote", os.path.relpath(OUT, HERE), "- germanium, ~60pct China (est.) by-product; Jul-2023 controls; IR optics + fibre")
