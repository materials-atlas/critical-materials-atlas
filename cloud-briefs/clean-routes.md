# The clean-route restructure

Repo: `materials-atlas/critical-materials-atlas` (public, self-contained).

The long-run intent, in the author's words: McKinsey-style clean routes, and eventually CMS-style
editing for non-engineers, on a static site that stays free and hard to break. This job is the first
half: the routes.

Pages are served at paths like `/revisions`, `/export-controls`, `/scrap`, while internal links mix
`page.html` and bare `page`. The job is one coherent scheme, applied everywhere, breaking nothing for
a reader or a search engine.

Constraints, all of which must hold:

- The site is GitHub Pages behind Cloudflare. There is no server-side rewrite; the scheme must work as
  static files.
- **Every currently live URL must keep working.** The site is indexed (Search Console, sitemap,
  robots) and cited from Zenodo DOIs and from posts on X. A dead link is a worse outcome than an ugly
  one. Redirect stubs are acceptable if they carry `<link rel="canonical">` and a meta refresh.
- `sitemap.xml`, `robots.txt`, the canonicals from `add_canonicals.py`, the index from
  `build_search_index.py` and the `check_head` guard must all agree with the new scheme.
- Chain pages are rendered by `chain-assets/chainview.js` from JSON: check its link building, not just
  the HTML.
- **Do not restructure page CONTENT.** This is routing only.

Deliver: the scheme written down in one short document; the redirects; updated post-passes; a
`check.py` guard (injection-tested) that fails if a page is reachable at a path the scheme disallows or
if a live URL loses its redirect; and a list of every URL whose form changed.

## House rules (non-negotiable)

- `check.py` must pass. Any guard you add must be verified by INJECTION: break the thing it guards,
  confirm the guard fails, restore it, confirm it passes. Report that you did this.
- Never run `runner.py --force`. If you rebuild a page, the runner reruns the post-passes
  (`add_canonicals.py`, `add_head.py`, `clean_links.py`, `build_search_index.py`).
- Determinism: no `hash()`, no set/dict iteration order, no unseeded randomness.
- Deliver a PULL REQUEST, never a push to `main`. The PR description must carry the numbers, the
  verdict, and what you did not do.
- Money and tonnes are separate measures, and SINCE 2026-10-02 THE CUBE CARRIES BOTH. The old
  instruction "out/cube.parquet is tonnage-based" is no longer true and would make you read
  euros as tonnes. Use `currency_denom`: USD, EUR, or `_T` where the row is physical. Chain
  JSONs are still value-based. State the basis in every figure.
- THE CUBE IS NOW BILATERAL, on the IMF BPM6 structure (see `DSD_BPM6.md`). Two consequences
  you must respect or your numbers will be wrong:
    * `counterpart_area` holds BOTH totals and their components - `W1` is a country total
      against all partners, an ISO3 code is one bilateral partner. SUMMING ACROSS IT DOUBLE
      COUNTS. The same is true of `country_iso3`, where USGS and IEA file a `WLD` row beside
      the countries inside it.
    * Do not hand-roll an aggregate. `cube_query.totals(material, measure, scope, ref=...)`
      is the one way, and it REQUIRES both scopes precisely so this cannot be forgotten. It
      refuses mixes rather than guessing.
- Never sum sources for one flow. Never treat a zero declaration as a declaration.
- A negative result is a result. If the page's claim survives, say so plainly and change only the
  wording that needed it. Do not manufacture findings to justify the run.
- Do not touch anything relating to `BOP_extraction` or `rbop-archive`.
- Every source you cite, you open first. Never cite from memory.
