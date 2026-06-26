# The origin gap — one finding from the atlas

**Headline:** across 32 critical raw materials, **import-origin statistics systematically overstate the
geographic diversification of true supply.** In **19 of 32** materials (2024 reconciled BACI trade), the
top *exporter* is not the top *miner*. The country a customs ledger records as the source is, more often
than not, a refinery or a hub standing in front of the mine.

Reproduce: [`reconcile/findings.py`](reconcile/findings.py) → [`reconcile/results/findings.json`](reconcile/results/findings.json).
Interactive: the atlas's **Table** view (the **⚠** flag, the **origin gap** in each material's detail) and
any country's **dependency report**.

## The measure

For each material, in the same year:

> **origin gap = (top exporter's share of world trade) − (that same country's share of world mine output)**

A large positive gap means a country sells far more of the material than it digs out of the ground — it is
*processing or trans-shipping* someone else's ore. It is the single number behind the atlas's thesis: **the
refiner is not the source.**

## Where the gap is largest (2024)

| Material | Top exporter | exports | it mines | **gap** | Actual lead miner |
|---|---|--:|--:|--:|---|
| Beryllium, unwrought | Kazakhstan | 89% | 0% | **+89pp** | United States (65%) |
| Strontium carbonate | Germany | 60% | 0% | **+60pp** | Spain (30%) |
| Lithium carbonate | Chile | 75% | 22% | **+53pp** | Australia (52%) |
| Bauxite / aluminium ore | Guinea | 72% | 25% | **+47pp** | Australia (27%) |
| Phosphorus | Vietnam | 47% | 12% | **+35pp** | China (70%) |
| Titanium, unwrought | Japan | 34% | 0% | **+34pp** | China (32%) |
| Cobalt oxides & hydroxides | Finland | 29% | 0% | **+29pp** | DR Congo (76%) |
| Tantalum, unwrought | United States | 22% | 0% | **+22pp** | DR Congo (40%) |
| Nickel, unwrought | Norway | 18% | 0% | **+18pp** | Indonesia (60%) |

In **4 of 32** materials a country that mines **under 5%** of the world supply nonetheless **exports over
25%** of it — a near-pure refiner/hub effect.

## The twist: the illusion is not only China's

The intuitive story is "China hides behind refineries." The data only half-supports it. For many materials
China is *both* the lead miner and the lead exporter — its chokehold is largely **genuine**, not an
accounting artefact. The materials where exporter and miner diverge are instead fronted by **industrial
refiners and entrepôts**: Finland for Congolese cobalt, Japan for (largely Chinese-mined) titanium sponge,
Germany for Spanish strontium, Norway for Indonesian nickel, the United States for Congolese tantalum.

So the corrective cuts two ways. It deflates apparent dependence on *refiner* countries (a German strontium
"supply" is Spanish rock); and it reveals that a genuinely concentrated upstream — DR Congo cobalt,
Indonesian nickel, Chinese rare earths — is *more* concentrated than the diversified-looking trade ledger
suggests, because the ore is laundered through several different refiners before it ships.

## What this is and isn't

- **It is** a like-for-like comparison of two public measures (CEPII-BACI reconciled trade shares; USGS
  mine-production shares), per material, every year 2018–2024.
- **It isn't** a claim that the refiner adds no value, nor that the trade form equals the mined form: some
  gap is legitimate — Finland really does export *refined* cobalt chemicals, which sit under a different
  product than mined cobalt. The gap measures **where customs would mislead you about origin**, not fraud.
- gallium / germanium / hafnium share one HS6 code (811292) and cannot be separated in trade; flagged
  throughout.

## Why it matters

Supply-risk and friend-shoring policy is often written off *import-origin* tables. This finding says those
tables, taken at face value, **misidentify the chokepoint** in a majority of critical materials — sometimes
flattering a refiner, sometimes hiding how concentrated the real mine base is. The fix is cheap: reconcile
the bilateral trade, then subtract the mine layer. That is what this atlas does.

*Independent work, public data only (USGS, IEA, UN Comtrade via CEPII BACI). Figures approximate and
rounded; read each row as an overlay of two different measures, not one observed pipeline.*
