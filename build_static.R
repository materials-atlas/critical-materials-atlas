# build_static.R - regenerate the no-install offline deliverable from current code.
# Base R only. Sources dependency_core.R, reads raw/, and writes out/index.html plus
# per-product PNGs (<label>_headline / _trend / _vq) that the page references.
# Browse-only viewers (e.g. on GitHub) see all products without running anything.
# Run:  Rscript build_static.R

raw_dir <- "raw"; out_dir <- "out"
dir.create(out_dir, showWarnings = FALSE)
source("dependency_core.R")

# Narrative order: headline case first, then the two export-control metals.
products <- list(
  list(label = "magnets",   code = "85051110",
       title = "Rare-earth permanent magnets (CN 8505 11 10)",
       note  = "Near-total concentration: one origin at ~93% of value, HHI ~0.86. The next origins (Philippines, Vietnam, Japan) are each under 3%."),
  list(label = "germanium", code = "81129295",
       title = "Germanium (CN 8112 92 95)",
       note  = "The cleanest member-state trap: the naive view points at Belgium (Umicore's Antwerp refining hub - a processing/transit artefact), while the corrected view shows China at ~83%."),
  list(label = "gallium",   code = "81129289",
       title = "Gallium (CN 8112 92 89)",
       note  = "Watch the export controls: China's origin share fell 96.8% (2022) -> 85% (2023) -> 68% (2024) as Canada and Russia stepped in - the July-2023 controls visible directly in the customs record.")
)

eur <- function(x) ifelse(x >= 1e9, sprintf("EUR %.2fB", x/1e9),
                   ifelse(x >= 1e6, sprintf("EUR %.1fM", x/1e6), sprintf("EUR %.0f", x)))

# Render the three PNGs for one product; return an HTML <section> string.
render_product <- function(p) {
  val <- read_comext(file.path(raw_dir, paste0(p$label, "_", p$code, "_value.csv")))
  qty <- read_comext(file.path(raw_dir, paste0(p$label, "_", p$code, "_qty.csv")))
  if (is.null(val)) { message("skip ", p$label, " - run download_data.ps1"); return("") }
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

  paste0(
'<section><h2>', p$title, '</h2>
<p class="note">', p$note, '</p>
<div class="kpis">
 <div class="kpi"><div class="v">', sprintf("%.1f%%", sL$china_val), '</div><div class="l">China (value)</div></div>
 <div class="kpi"><div class="v">', cq, '</div><div class="l">China (tonnage)</div></div>
 <div class="kpi"><div class="v">', sprintf("%.2f", sL$hhi_val), '</div><div class="l">HHI (value)</div></div>
 <div class="kpi"><div class="v">', eur(sL$total_eur), '</div><div class="l">Total extra-EU (', yL, ')</div></div>
</div>
<img src="', p$label, '_headline.png" alt="naive vs corrected">
<div class="two"><img src="', p$label, '_trend.png" alt="trend"><img src="', p$label, '_vq.png" alt="value vs tonnage"></div>
<table><thead><tr><th>Origin</th><th class="n">Value (EUR)</th><th class="n">Tonnes</th><th class="n">Value %</th><th class="n">Tonnage %</th></tr></thead>
<tbody>', rows, '</tbody></table></section>')
}

sections <- paste(vapply(products, render_product, character(1)), collapse = "\n")

html <- paste0(
'<!doctype html><html lang="en"><head><meta charset="utf-8">
<title>EU import dependency - corrected for the Rotterdam effect (Comext)</title>
<style>
 body{font-family:system-ui,Segoe UI,Arial,sans-serif;max-width:1000px;margin:2rem auto;padding:0 1rem;color:#1a1a1a;line-height:1.5}
 h1{font-size:1.6rem;margin-bottom:.2rem} .sub{color:#555;margin-top:0}
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
<p class="sub">Extra-EU import dependency for critical products, corrected for the Rotterdam/Antwerp transit effect. Source: Eurostat Comext (public).</p>
<p class="intro"><b>Naive</b> rankings by importing member state measure where goods are customs-cleared, not where they come from - distorted by the NL/BE port effect. <b>Corrected</b> rankings treat the EU as one entity and rank by country of origin (for extra-EU flows the Comext partner field is the origin). The gap between the two panels below is the whole point.</p>
', sections, '
<footer>Generated by build_static.R from public Eurostat Comext data (DS-045409). Method note: <a href="../methodology.html">methodology.html</a>. Independent demo - not affiliated with any institution.</footer>
</body></html>')
writeLines(html, file.path(out_dir, "index.html"))
cat("Wrote out/index.html +", length(products) * 3, "PNGs for:",
    paste(vapply(products, function(p) p$label, character(1)), collapse = ", "), "\n")
