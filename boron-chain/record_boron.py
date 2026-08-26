"""Evidence JSON for the boron / borates chain pilot. Uniform schema. Public sources.
A fourth geological chain — Turkey's borate reserves. Run: python record_boron.py
"""
from __future__ import annotations
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out", "boron_chain.json")

SRC = {
    "usgs_boron": {"title": "USGS Mineral Commodity Summaries 2026 — Boron", "year": 2026, "url": "https://pubs.usgs.gov/periodicals/mcs2026/mcs2026-boron.pdf"},
    "eti_maden": {"title": "Eti Maden (Turkey) — world boron reserves & production", "year": 2024, "url": "https://www.etimaden.gov.tr/en"},
    "bgs_wms": {"title": "BGS, World Mineral Statistics — borates", "year": 2024, "url": "https://www2.bgs.ac.uk/mineralsuk/statistics/worldStatistics.html"},
    "baci": {"title": "CEPII BACI V202601, based on UN Comtrade", "year": 2026, "url": "https://www.cepii.fr/CEPII/en/bdd_modele/bdd_modele_item.asp?id=37"},
}

CHAIN = {
    "title": "Boron chain",
    "chokepoint": {"product": "Fibreglass · fertilizer · magnets", "stage": "Reserves", "mechanism": "geological", "physics": "Turkey's borate basins (tincal, colemanite) are a geological rarity concentrated in one region and can't be relocated; its state producer Eti Maden claims ~73% of world reserves, though USGS publishes no consistent world total", "holder": "Turkey", "share": "~73% (co. est.)", "control": "—", "conf": "estimate"},
    "published": True,
    "related": [{"href": "../magnet-chain/magnet-chain.html", "label": "Rare-earth magnet chain"}, {"href": "../phosphate-food-chain/phosphate-food-chain.html", "label": "Phosphate / food chain"}, {"href": "../steel-alloys-chain/steel-alloys-chain.html", "label": "Steel-alloys chain"}],
    "accent": "#8a6a4a",
    "eyebrow": "Product-chain pilot · one country's rock",
    "h1": "Two countries hold the world's boron — and one of them holds most of it",
    "deck": "Boron, mined as borates, is in fibreglass and glass, in fertilizer as an essential micronutrient, in "
            "heat-resistant borosilicate, in detergents — and it is the 'B' in neodymium magnets. Almost all of it "
            "comes from just two places: Turkey, which holds the world's largest borate reserves, and a single large mine "
            "in California. It is a chokepoint written into the geology.",
    "byline": "borate ore (Turkey largest reserves + US) ≠ boric acid / borax ≠ fibreglass · fertilizer · borosilicate · NdFeB",
    "correction": "Boron is one of the atlas's few genuinely geological chokepoints. Turkey holds the world's largest "
                  "borate reserves — an exceptional geological endowment mined by the state producer Eti Maden, which claims "
                  "~73% of the world, though USGS publishes no consistent world reserves total — and "
                  "the United States adds a single large California operation (Rio Tinto's Boron mine). Between them "
                  "they supply most of the world. Unlike a smelter or a fab, this concentration cannot be rebuilt "
                  "elsewhere: the borate deposits are where they are.",
    "stats": [
        {"v": "~73%*", "l": "of world borate reserves per Turkey's Eti Maden (*company estimate; USGS gives no world total)", "conf": "estimate"},
        {"v": "duopoly", "l": "Turkey (Eti Maden) and the US (one California mine) supply most of the world", "conf": "measured"},
        {"v": "glass + fibreglass", "l": "the largest use — plus fertilizer, borosilicate, detergents", "conf": "measured"},
        {"v": "NdFeB", "l": "boron is the 'B' in neodymium-iron-boron permanent magnets", "conf": "measured"},
    ],
    "hops": [
        {"n": "1 · Borate ore", "t": "tincal, colemanite, ulexite — Turkey holds the largest reserves, plus California"},
        {"n": "2 · Refine", "t": "processed to borax, boric acid and boron oxides"},
        {"n": "3 · Compounds", "t": "the traded forms feeding glass, agriculture, ceramics, chemicals"},
        {"n": "4 · End use", "t": "fibreglass/glass, fertilizer micronutrient, borosilicate, detergents, magnets"},
    ],
    "sections": [
        {"h2": "1 · A chokepoint in the ground", "panels": [
            {"kind": "big", "h3": "Where the boron is", "big": "~73%*", "conf": "estimate",
             "text": "Turkey's borate basins are a geological rarity. Its state producer Eti Maden claims ~73% of world "
                     "reserves (*a company estimate — USGS publishes no consistent world reserves total). The only other "
                     "major source is a single large open-pit mine in Boron, California; a handful of smaller producers "
                     "(Chile, Argentina, Russia, China) supply the rest. This is not a built concentration that capital "
                     "can relocate — it is where the deposits happen to be, like phosphate or the platinum-group Bushveld.",
             "note": "Eti Maden (company estimate). USGS Boron 2025 states world reserves cannot be consistently totalled."},
            {"kind": "text", "h3": "Why that makes it different",
             "text": "Because boron's concentration is geological, the response is not 'build a plant elsewhere' but the "
                     "geological toolkit: substitution where possible, recycling (limited), and managing dependence on "
                     "two suppliers. It joins phosphate, PGMs and niobium as the handful of chains where the mine truly "
                     "is the chokepoint — and geology is why.",
             "flag": "a fourth geological chokepoint"},
        ]},
        {"h2": "2 · The many things boron quietly enables", "panels": [
            {"kind": "cards", "h3": "Where boron goes", "cards": [
                {"t": "Glass & fibreglass", "d": "The largest use: borosilicate glass (heat- and shock-resistant) and the glass fibre in insulation and composites."},
                {"t": "Fertilizer", "d": "An essential plant micronutrient — boron-deficient soils need it, tying boron to food (see the phosphate chain)."},
                {"t": "Magnets & more", "d": "The 'B' in NdFeB permanent magnets (see the magnet chain), plus detergents, ceramics, and neutron shielding in nuclear."},
            ]},
        ]},
        {"h2": "3 · A stable, quiet dependency", "panels": [
            {"kind": "text", "h3": "Concentrated, but not weaponised",
             "text": "Unlike gallium or antimony, boron has not been turned into an export lever — Turkey and the US "
                     "supply a broad, price-stable market, and demand is spread across many undramatic uses. The risk "
                     "is structural rather than acute: a near-duopoly on a material embedded in glass, agriculture and "
                     "magnets, held in place by geology rather than by policy. Worth knowing precisely because it is so "
                     "easy to overlook.",
             "flag": "structural, not a lever — yet"},
        ]},
    ],
    "trade_intro": "BACI carries natural borates (252800) and boron oxides / boric acid (281000), which together show "
                   "the Turkey-plus-US concentration at the raw and first-refined stages. Read the shares below as that "
                   "borate trade — the geological duopoly is visible here more directly than in most atlas chains.",
    "method": [
        {"stage": "Reserves", "lens": "Eti Maden (company est.); USGS gives no world total", "why": "Turkey's exceptional borate geology — a geological chokepoint"},
        {"stage": "Supply", "lens": "Turkey + US production", "why": "a near-duopoly by geology"},
        {"stage": "Use", "lens": "USGS end-use", "why": "glass/fibreglass leads; fertilizer + magnets tie it across the atlas"},
        {"stage": "Trade", "lens": "BACI 252800 borates + 281000 boron oxides", "why": "shows the duopoly directly — flagged context"},
    ],
    "sources": SRC,
}

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w", encoding="utf-8") as fh:
    json.dump(CHAIN, fh, ensure_ascii=False, indent=2)
print("wrote", os.path.relpath(OUT, HERE), "- boron, Turkey reserves (Eti Maden ~73pct est.) (geological, 4th); glass/fertilizer/NdFeB")
