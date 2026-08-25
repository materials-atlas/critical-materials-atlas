# Aerospace chain — enrichment plan (working doc, not for publishing)

**Purpose.** The research library is raw material, not a bibliography to display. Each source is a *recipe*: what they did (method), what they measured (data), what they found (finding). This doc maps each source to something we can **reproduce on our own data** to make the aerospace chain richer and more detailed. We cite the sources later; here we mine them for methods.

**How to read each entry.**
- **They did** — the method / measurement in the source.
- **We reproduce** — the same technique applied to our data (BACI, USGS/BGS, production series).
- **Yields** — the concrete new element in the chain record (a stat, a hop detail, a panel, a metric).
- **Needs** — what's required to execute (a full-text read, a new data pull, a firm-level census).

---

## Stage ① Rhenium — the scarce superalloy element

**USGS MCS — Rhenium** · *They did:* report rhenium as a by-product of Cu–Mo roasting, 80% into superalloys, 75% import reliance. · *We reproduce:* compute a **by-product coupling coefficient** — rhenium output as a fixed fraction of the copper/moly it rides on — to show supply is inelastic to rhenium price. · *Yields:* a new stat ("~X g Re per t Mo") + a hop note explaining why "mine more rhenium" is not a lever. · *Needs:* USGS Re + Mo + Cu production series (have via MCS).

**Assessment of supply interruption of rhenium (ScienceDirect)** · *They did:* build supply-interruption indicators from historical price shocks + estimate recoverable rhenium from in-service stock (industrial ecology). · *We reproduce:* an **in-service stock estimate** — rhenium locked in the global installed base of turbine blades, and what fraction is recoverable at end-of-life. · *Yields:* a "recyclable stock" panel — a second supply source the mine-centric view misses. · *Needs:* full-text read for their stock/flow coefficients.

**Review of rhenium extraction & recycling (Minerals Engineering)** · *They did:* survey primary/secondary recovery routes and yields. · *We reproduce:* a **recovery-route table** (route → typical yield → maturity) feeding the "break the chokepoint" decision layer. · *Yields:* a substitution/recovery angle for the breakout page. · *Needs:* full-text for yields.

## Stage ② Titanium — sponge to aerospace-qualified metal

**USGS MCS — Titanium** · *They did:* separate sponge tonnage from aerospace-qualified metal; import reliance >95%, Japan 82%. · *We reproduce:* formalise **two distinct measures** in the record — "sponge production" vs "aerospace-qualified supply" — with numbers, not just prose. · *Yields:* splits one hop into two measured columns; the chain already argues this qualitatively — this quantifies it.

**Argus — aerospace-approved sponge** · *They did:* 89 kt qualified (JP/KZ/SA) vs 220 kt uncertified Chinese; 83% capacity utilisation. · *We reproduce:* a **"qualified vs total" ratio** and a **capacity-utilisation** metric for the sponge stage. · *Yields:* two new stats that make "China ~71% but almost none qualified" numeric.

**BIS Titanium supply-chain assessment** · *They did:* an **industrial-base survey** — count single/sole-source inputs, capacity, financial health, firm by firm. · *We reproduce:* a **qualified-supplier count per stage** (the concentration is firm-count, not country-share). · *Yields:* a "# of qualified suppliers" metric per hop — the atlas's core "capability not geology" claim, measured. · *Needs:* firm-level list (partly in the report + trade press).

**Vulnerability Analysis on the Titanium Supply Chain — network approach (Northeastern)** · *They did:* model the chain as a **network of nodes** (sponge/ingot/mill), simulate removing a node (TIMET), measure downstream demand not met. · *We reproduce:* a **node-disruption chokepoint score** — model our chain's stages as nodes, knock out the binding stage (single-crystal casting, or a top supplier), compute downstream loss. · *Yields:* a **quantified chokepoint index** — turns "the chokepoint walks downstream" from a claim into a number. **Highest-value item.** · *Needs:* full-text for their model spec; adapt to our hop graph.

**Life Cycle Assessment of Titanium (Georgia Tech)** · *They did:* embodied-energy / material intensity per stage + TRL/MRL of substitutes (HSCR steel). · *We reproduce:* a **material/energy-intensity dimension** per stage and a **substitution-readiness** tag. · *Yields:* a physical-intensity overlay + a substitution column for the decision layer. · *Needs:* full-text for inventory numbers.

**USW Section 232 petition (TIMET)** · *They did:* document a **single-domestic-producer failure point**. · *We reproduce:* a **single-point-of-failure flag** per stage (is there a last-one-standing producer?). · *Yields:* a boolean/■ flag on hops that have a single critical producer.

**JRC — Closing the loop (titanium)** · *They did:* compute **import-to-export ratios** (6:1 products, 10:1 sponge) as a dependency measure. · *We reproduce:* import/export ratio **per traded good from BACI** — cheap, we already hold the data. · *Yields:* a "dependency ratio" column on every trade row. **Quick win.**

**MINING.com / AeroTime / Oregon Group / Metalnomist / AlloyIndex** · *They did:* report data points — China ~69–74% sponge; global capacity 410 kt, output 320 kt; certification lead time ~a decade; China 34% minerals / 67% sponge / 55% pigment; Chinese aerospace-grade exports projected 1 kt→10 kt by 2030. · *We reproduce:* ingest as **dated observations** and add a **"qualification lag ~10 yr"** annotation to the qualified-supply hop. · *Yields:* time-points for a small history + a lead-time note explaining why diversification is slow. · *Needs:* treat as secondary (flag confidence).

## Stage ③ Single-crystal blade casting — the gap

*No country-level data exists.* · *Reproduce the BIS/market-profile method instead:* a **firm-level census** of qualified casters (Precision Castparts, Doncasters, and the OEMs' in-house foundries). · *Yields:* a **"# of qualified casters worldwide"** metric — the concentration made concrete where no trade code can. · *Needs:* build the census from company/trade-press profiles (no dataset exists — this is original).

## Stage ④ Jet engines & OEM concentration

**Mordor / Simple Flying / GlobeNewswire** · *They did:* report OEM shares — GE 55% (incl. CFM), P&W 26%, RR 18%; four groups ~80%. · *We reproduce:* compute an **HHI concentration index** for the engine stage from these shares. · *Yields:* a single concentration number for the most-concentrated stage. · *Needs:* seek **FAA/EASA type-certificate holder counts** as a primary replacement for trade-press shares.

## Across the chain — frameworks to reproduce

**EU CRM 2023 (Economic Importance × Supply Risk)** · *We reproduce:* the **EI × SR formula per stage** using our production/trade data → a **criticality index** for each hop, not just for the material overall.

**USGS 2025 methodology (supply-disruption scenarios)** · *We reproduce:* a simplified **single-supplier-disruption scenario** for the chain (remove top supplier of the binding stage; estimate impact) — mirrors their 1,200-scenario model at chain scale.

**CSIS volumes** · *They did:* catalogue policy responses (domestic development, processing/recycling, partnerships). · *We reproduce:* map each to a **"break the chokepoint" action** in the decision layer.

**CEPII BACI** · The data engine — already the chain's trade source. Extend it to power the **dependency ratios** and **HHI** above.

---

## Priority shortlist (highest value / lowest cost first)

1. **Dependency ratios from BACI** (JRC method) — we already have the data; add import/export ratio to every trade row. *Cheap.*
2. **Qualified-vs-tonnage split + capacity utilisation** (USGS/Argus) — makes "71% but unqualified" numeric. *Cheap.*
3. **Node-disruption chokepoint score** (Northeastern) — turns the headline thesis into a number. *Medium; needs full-text.*
4. **Qualified-supplier / caster counts** (BIS + firm census) — the "capability not geology" claim, measured. *Medium; original census.*
5. **Criticality index per stage** (EU EI×SR). *Medium.*
6. **By-product coupling coefficient** (rhenium) + **HHI** for engines. *Cheap-ish.*

## Full-text reads / data pulls still needed
- Northeastern thesis & Georgia Tech LCA — for exact model/inventory coefficients.
- Firm-level caster census — no dataset exists; build from profiles.
- FAA/EASA type-certificate holder counts — primary engine-share data.
- Rhenium in-service stock/flow coefficients (ScienceDirect supply-interruption paper).

## Reusability across the 58 chains
Most of these are **generic reproducible methods**, not aerospace-specific: dependency ratios, HHI, criticality index, node-disruption score, single-point-of-failure flags, by-product coupling. Building them once as chain-record fields + a small compute step lets every chain gain the same richer layer — the same way the library format generalised.
