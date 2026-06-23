# build_static.R - regenerate the no-install offline deliverable from current code.
# Base R only. Sources dependency_core.R, reads raw/, and writes index.html at the repo
# root (so GitHub Pages serves it at the site URL) plus per-product PNGs in out/
# (<label>_headline / _trend / _vq) that the page references. Browse-only viewers see all
# products without running anything.
# Run:  Rscript build_static.R

raw_dir <- "raw"; out_dir <- "out"
dir.create(out_dir, showWarnings = FALSE)
source("dependency_core.R")

# Narrative order: headline case first, then the two export-control metals.
products <- list(
  list(label = "magnets",   code = "85051110",
       title = "Rare-earth permanent magnets (CN 8505 11 10)",
       note  = "Near-total concentration: China at ~93% of value, HHI ~0.86. The next origins (Philippines, Vietnam, Japan) are each under 3%."),
  list(label = "magnesium", code = "81041100",
       title = "Magnesium, unwrought (CN 8104 11 00)",
       note  = "China ~92% by value, ~95% by tonnage. The naive view blames the Netherlands (44%) - a Rotterdam clearing artefact; the true origin is China."),
  list(label = "germanium", code = "81129295",
       title = "Germanium (CN 8112 92 95)",
       note  = "The cleanest member-state trap: the naive view points at Belgium (Umicore's Antwerp refining hub - a processing/transit artefact), while the corrected view shows China at ~83%."),
  list(label = "graphite",  code = "25049000",
       title = "Natural graphite (CN 2504 90 00)",
       note  = "China ~82%. Topical: graphite is the EV-battery anode, and China imposed export licensing in December 2023. The naive view points at Germany; Madagascar and Brazil supply more tonnage than value."),
  list(label = "gallium",   code = "81129289",
       title = "Gallium (CN 8112 92 89)",
       note  = "Watch the export controls: China's origin share fell 96.8% (2022) -> 85% (2023) -> 68% (2024) as Canada and Russia stepped in - the July-2023 controls visible directly in the customs record."),
  list(label = "tungsten",  code = "81019400",
       title = "Tungsten, unwrought (CN 8101 94 00)",
       note  = "China is the largest origin (~58% value, ~73% tonnage) but not alone - Britain supplies ~22%. Even here the naive view (Germany 55%) misstates who the EU relies on."),
  list(label = "cobalt",    code = "28220000",
       title = "Cobalt oxides & hydroxides (CN 2822 00 00)",
       note  = "The refined-cobalt dependency (the metal alone is diversified): China supplies ~62% of EU cobalt-oxide imports - the battery-cathode precursor. The naive view blames Belgium (~43%, Umicore's refining/clearing hub again); the origin is China, with the UK behind."),
  list(label = "lithium",   code = "28369100",
       title = "Lithium carbonate (CN 2836 91 00)",
       note  = "The battery metal - a concentrated dependency, but NOT on China: Chile supplies ~75% (the South American 'lithium triangle'), with the US and Argentina behind. The naive view blames the Netherlands and Germany (clearing hubs); the origin is South America."),
  list(label = "antimony",  code = "81101000",
       title = "Antimony, unwrought (CN 8110 10 00)",
       note  = "The method's acid test: the naive view says France and Belgium (~37% each); the corrected view reveals Tajikistan at ~69%, with China barely present. Proof this is not a China-finding machine - it surfaces whatever origin the transit data hides."),
  list(label = "platinum",  code = "71101100",
       title = "Platinum, unwrought (CN 7110 11 00)",
       note  = "Platinum-group metals - autocatalysts and the hydrogen economy. A concentrated non-China dependency: South Africa ~57%, with the UK and US behind. The naive view points at Germany (~43%); the origin is South Africa."),
  list(label = "titanium",  code = "81082000",
       title = "Titanium, unwrought (CN 8108 20 00)",
       note  = "Aerospace-grade titanium, post-Russia. The naive view says France (~40%); the corrected view shows Kazakhstan (~33%) and the US (~25%) - the sponge supply that replaced Russia after 2022. A recognised strategic metal sourced from Central Asia, invisible in the member-state view."),
  list(label = "silicon",   code = "28046900",
       title = "Silicon, < 99.99% (CN 2804 69 00)",
       note  = "A critical material where the EU is genuinely diversified: origin is Norway (~47%), Brazil and Iceland - not a dependency risk. The naive view still misleads (Germany 44%), but the honest finding here is 'no concentration'. Included to show the method measures rather than confirms.")
)

eur <- function(x) ifelse(x >= 1e9, sprintf("EUR %.2fB", x/1e9),
                   ifelse(x >= 1e6, sprintf("EUR %.1fM", x/1e6), sprintf("EUR %.0f", x)))

# Render the three PNGs for one product; return an HTML <section> string.
render_product <- function(p) {
  val <- read_comext(file.path(raw_dir, paste0(p$label, "_", p$code, "_value.csv")))
  qty <- read_comext(file.path(raw_dir, paste0(p$label, "_", p$code, "_qty.csv")))
  if (is.null(val)) { message("skip ", p$label, " - run download_data.ps1"); return(NULL) }
  t <- build_tables(val, qty); oa <- t$origin; ma <- t$ms; su <- t$summary
  yL <- max(su$year); oc <- head(oa[oa$year == yL, ], 6); mc <- head(ma[ma$year == yL, ], 6)
  sL <- su[su$year == yL, ]

  hp <- file.path(out_dir, paste0(p$label, "_headline.png"))
  png(hp, width = 1000, height = 430); par(mfrow = c(1, 2), mar = c(4, 6, 4, 1))
  barplot(rev(mc$value_share), names.arg = rev(mc$reporter), horiz = TRUE, las = 1,
          col = "grey70", xlab = "% of MS imports", main = paste("NAIVE: by member state", yL))
  barplot(rev(oc$value_share), names.arg = rev(oc$partner), horiz = TRUE, las = 1,
          col = "firebrick", xlab = "% of extra-EU imports", main = paste("CORRECTED: by origin", yL))
  dev.off()

  tp <- file.path(out_dir, paste0(p$label, "_trend.png"))
  png(tp, width = 1000, height = 360); par(mar = c(4, 5, 3, 1))
  plot(su$year, su$china_val, type = "o", pch = 19, col = "firebrick", lwd = 2, ylim = c(0, 100),
       xaxt = "n", xlab = NA, ylab = "China share (%)", main = "China share of extra-EU origin over time")
  lines(su$year, su$china_qty, type = "o", pch = 17, col = "grey40", lwd = 2)
  axis(1, at = su$year); legend("bottomleft", c("value", "tonnage"),
       col = c("firebrick", "grey40"), pch = c(19, 17), lwd = 2, bty = "n")
  dev.off()

  vp <- file.path(out_dir, paste0(p$label, "_vq.png"))
  png(vp, width = 1000, height = 360); par(mar = c(4, 6, 3, 1))
  m <- t(as.matrix(oc[, c("value_share", "qty_share")])); colnames(m) <- oc$partner
  barplot(m[, rev(seq_len(ncol(m)))], beside = TRUE, horiz = TRUE, las = 1,
          col = c("firebrick", "grey60"), xlab = "% share",
          main = paste("Value vs tonnage share by origin", yL))
  legend("bottomright", c("value", "tonnage"), fill = c("firebrick", "grey60"), bty = "n")
  dev.off()

  rows <- paste0("<tr><td>", oc$partner, "</td><td class='n'>",
    formatC(oc$value_eur, format = "d", big.mark = " "), "</td><td class='n'>",
    formatC(round(oc$tonnes, 1), format = "f", digits = 1, big.mark = " "), "</td><td class='n'>",
    sprintf("%.1f%%", oc$value_share), "</td><td class='n'>",
    sprintf("%.1f%%", oc$qty_share), "</td></tr>", collapse = "\n")
  cq <- if (is.na(sL$china_qty)) "-" else sprintf("%.1f%%", sL$china_qty)

  sec <- paste0(
'<section><h2>', p$title, '</h2>
<p class="note">', p$note, '</p>
<div class="kpis">
 <div class="kpi"><div class="v">', sprintf("%.1f%%", sL$china_val), '</div><div class="l">China (value)</div></div>
 <div class="kpi"><div class="v">', cq, '</div><div class="l">China (tonnage)</div></div>
 <div class="kpi"><div class="v">', sprintf("%.2f", sL$hhi_val), '</div><div class="l">HHI (value)</div></div>
 <div class="kpi"><div class="v">', eur(sL$total_eur), '</div><div class="l">Total extra-EU (', yL, ')</div></div>
</div>
<img src="out/', p$label, '_headline.png" alt="naive vs corrected">
<div class="two"><img src="out/', p$label, '_trend.png" alt="trend"><img src="out/', p$label, '_vq.png" alt="value vs tonnage"></div>
<table><thead><tr><th>Origin</th><th class="n">Value (EUR)</th><th class="n">Tonnes</th><th class="n">Value %</th><th class="n">Tonnage %</th></tr></thead>
<tbody>', rows, '</tbody></table></section>')

  top <- oc[1, ]
  ud <- val[["LAST.UPDATE"]]   # Comext SDMX-CSV carries a "LAST UPDATE" dd/mm/yy column
  updated <- if (is.null(ud)) as.Date(NA) else
    suppressWarnings(max(as.Date(substr(ud, 1, 8), "%d/%m/%y"), na.rm = TRUE))
  ov <- data.frame(
    mat = paste0(toupper(substr(p$label, 1, 1)), substr(p$label, 2, nchar(p$label))),
    partner = top$partner, share = top$value_share,
    china = identical(top$partner, "CN"),
    dyear = yL, updated = updated, stringsAsFactors = FALSE)
  list(section = sec, ov = ov)
}

# Render each product, then build the one-glance overview from their top origins.
results <- Filter(Negate(is.null), lapply(products, render_product))

ovs <- do.call(rbind, lapply(results, `[[`, "ov"))
ovs <- ovs[order(ovs$share), ]
png(file.path(out_dir, "overview.png"), width = 1000, height = 470)
par(mar = c(4, 9.5, 3, 1))
bp <- barplot(ovs$share, horiz = TRUE, las = 1, xlim = c(0, 105),
        names.arg = paste0(ovs$mat, "  (", ovs$partner, ")"),
        col = ifelse(ovs$china, "firebrick", "steelblue"),
        xlab = "% of extra-EU imports from the single largest origin (2024)",
        main = "EU critical-material dependency, by true origin")
text(ovs$share, bp, labels = sprintf(" %.0f%%", ovs$share), pos = 4, xpd = TRUE, cex = 0.85)
legend("bottomright", c("China", "other origin"), fill = c("firebrick", "steelblue"), bty = "n")
dev.off()

maxYear     <- max(ovs$dyear)
dataUpdated <- format(suppressWarnings(max(ovs$updated, na.rm = TRUE)), "%d %b %Y")
genDate     <- format(Sys.Date(), "%d %b %Y")

sections <- paste(vapply(results, `[[`, character(1), "section"), collapse = "\n")

html <- paste0(
'<!doctype html><html lang="en"><head><meta charset="utf-8">
<title>EU import dependency - corrected for the Rotterdam effect (Comext)</title>
<style>
 body{font-family:system-ui,Segoe UI,Arial,sans-serif;max-width:1000px;margin:2rem auto;padding:0 1rem;color:#1a1a1a;line-height:1.5}
 h1{font-size:1.6rem;margin-bottom:.2rem} .sub{color:#555;margin-top:0;margin-bottom:.1rem}
 .stamp{font-size:.8rem;color:#888;margin:.1rem 0 .7rem}
 h2{font-size:1.15rem;margin-top:.4rem} section{border-top:2px solid #eee;padding-top:1.2rem;margin-top:2rem}
 .kpis{display:flex;gap:.6rem;flex-wrap:wrap;margin:.8rem 0}
 .kpi{flex:1;min-width:130px;border:1px solid #ddd;border-radius:8px;padding:.6rem;text-align:center}
 .kpi .v{font-size:1.4rem;font-weight:700;color:firebrick} .kpi .l{font-size:.72rem;color:#555}
 img{max-width:100%;height:auto;border:1px solid #eee;border-radius:6px;margin:.3rem 0}
 .two{display:flex;gap:.6rem;flex-wrap:wrap} .two img{flex:1;min-width:320px}
 table{border-collapse:collapse;width:100%;font-size:.88rem;margin:.5rem 0} th,td{padding:.3rem .55rem;border-bottom:1px solid #eee;text-align:left}
 td.n,th.n{text-align:right} .note{color:#444} .intro{background:#faf6f6;border-left:3px solid firebrick;padding:.7rem 1rem;border-radius:0 6px 6px 0}
 footer{margin-top:2rem;font-size:.8rem;color:#777;border-top:1px solid #eee;padding-top:.8rem} a{color:firebrick}
</style></head><body>
<h1>Who does the EU really depend on?</h1>
<p class="sub">Extra-EU import dependency across twelve critical raw materials, corrected for the Rotterdam/Antwerp transit effect. Source: Eurostat Comext (public).</p>
<p class="stamp">Data through ', maxYear, ' &middot; Eurostat Comext (DS-045409) dataset updated ', dataUpdated, ' &middot; page generated ', genDate, '</p>
<p class="intro"><b>Naive</b> rankings by importing member state measure where goods are customs-cleared, not where they come from - distorted by the NL/BE port effect. <b>Corrected</b> rankings treat the EU as one entity and rank by country of origin (for extra-EU flows the Comext partner field is the origin). <b>Across all twelve materials the constant is that the naive view is wrong</b> - China is the true origin for seven; the rest reveal dependencies the naive view hides (lithium on Chile, antimony on Tajikistan, platinum on South Africa, titanium on Kazakhstan), and silicon on Norway where the EU is genuinely fine. The gap between the two panels is the whole point.</p>
<h2>The landscape at a glance</h2>
<img src="out/overview.png" alt="dependency overview - each material by its single largest true origin">
<p class="note">Each bar is one material&#39;s single largest true origin and its share of 2024 extra-EU imports. Red = China; blue = another country. The naive member-state view hides every one of these.</p>
', sections, '
<footer>Generated by build_static.R from public Eurostat Comext data (DS-045409). Method note: <a href="methodology.html">methodology.html</a>. Independent demo - not affiliated with any institution.</footer>
</body></html>')
writeLines(html, "index.html")  # repo root, so GitHub Pages serves it at the site URL
cat("Wrote index.html (root) + out/overview.png +", length(results) * 3, "per-product PNGs for:",
    paste(vapply(results, function(x) tolower(x$ov$mat), character(1)), collapse = ", "), "\n")
