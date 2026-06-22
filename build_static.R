# build_static.R - regenerate the no-install offline deliverable from current code.
# Base R only. Sources dependency_core.R, reads raw/, writes out/dashboard.html plus the
# three committed PNGs (headline / trend / value_vs_qty) that the HTML references.
# Run:  Rscript build_static.R

product <- "85051110"; raw_dir <- "raw"; out_dir <- "out"
dir.create(out_dir, showWarnings = FALSE)
source("dependency_core.R")

val <- read_comext(file.path(raw_dir, paste0("magnets_", product, "_value.csv")))
qty <- read_comext(file.path(raw_dir, paste0("magnets_", product, "_qty.csv")))
if (is.null(val)) stop("Value file missing in raw/ - run download_data.ps1 first.")

tabs <- build_tables(val, qty)
oa <- tabs$origin; ma <- tabs$ms; su <- tabs$summary
yL <- max(su$year)
oc <- head(oa[oa$year == yL, ], 6)
mc <- head(ma[ma$year == yL, ], 6)
sL <- su[su$year == yL, ]

# --- headline.png : naive (member state) vs corrected (origin) -----------------
png(file.path(out_dir, "headline.png"), width = 1000, height = 450)
par(mfrow = c(1, 2), mar = c(4, 6, 4, 1))
barplot(rev(mc$value_share), names.arg = rev(mc$reporter), horiz = TRUE, las = 1,
        col = "grey70", xlab = "% of MS imports", main = paste("NAIVE: by member state", yL))
barplot(rev(oc$value_share), names.arg = rev(oc$partner), horiz = TRUE, las = 1,
        col = "firebrick", xlab = "% of extra-EU imports", main = paste("CORRECTED: by origin", yL))
dev.off()

# --- trend.png : China origin share over time ----------------------------------
png(file.path(out_dir, "trend.png"), width = 1000, height = 420)
par(mar = c(4, 5, 4, 1))
plot(su$year, su$china_val, type = "o", pch = 19, col = "firebrick", lwd = 2,
     ylim = c(0, 100), xaxt = "n", xlab = NA, ylab = "China share (%)",
     main = "China share of extra-EU origin over time")
lines(su$year, su$china_qty, type = "o", pch = 17, col = "grey40", lwd = 2)
axis(1, at = su$year)
legend("bottomleft", c("value", "tonnage"), col = c("firebrick", "grey40"),
       pch = c(19, 17), lwd = 2, bty = "n")
dev.off()

# --- value_vs_qty.png : value vs tonnage share by origin, latest year ----------
png(file.path(out_dir, "value_vs_qty.png"), width = 1000, height = 420)
par(mar = c(4, 6, 4, 1))
m <- t(as.matrix(oc[, c("value_share", "qty_share")])); colnames(m) <- oc$partner
barplot(m[, rev(seq_len(ncol(m)))], beside = TRUE, horiz = TRUE, las = 1,
        col = c("firebrick", "grey60"), xlab = "% share",
        main = paste("Value vs tonnage share by origin", yL))
legend("bottomright", c("value", "tonnage"), fill = c("firebrick", "grey60"), bty = "n")
dev.off()

# --- dashboard.html : self-contained page referencing the three PNGs -----------
esc <- function(x) x
rows <- paste0(
  "<tr><td>", oc$partner, "</td><td class='n'>",
  formatC(oc$value_eur, format = "d", big.mark = " "), "</td><td class='n'>",
  formatC(round(oc$tonnes, 1), format = "f", digits = 1, big.mark = " "), "</td><td class='n'>",
  sprintf("%.1f%%", oc$value_share), "</td><td class='n'>",
  sprintf("%.1f%%", oc$qty_share), "</td></tr>", collapse = "\n")

html <- paste0(
'<!doctype html><html lang="en"><head><meta charset="utf-8">
<title>EU import dependency - rare-earth magnets (Comext)</title>
<style>
 body{font-family:system-ui,Segoe UI,Arial,sans-serif;max-width:980px;margin:2rem auto;padding:0 1rem;color:#1a1a1a;line-height:1.5}
 h1{font-size:1.5rem} h2{font-size:1.1rem;margin-top:2rem;border-top:1px solid #eee;padding-top:1rem}
 .kpis{display:flex;gap:.75rem;flex-wrap:wrap;margin:1rem 0}
 .kpi{flex:1;min-width:150px;border:1px solid #ddd;border-radius:8px;padding:.7rem;text-align:center}
 .kpi .v{font-size:1.5rem;font-weight:700;color:firebrick} .kpi .l{font-size:.75rem;color:#555}
 img{max-width:100%;height:auto;border:1px solid #eee;border-radius:6px}
 table{border-collapse:collapse;width:100%;font-size:.9rem} th,td{padding:.35rem .6rem;border-bottom:1px solid #eee;text-align:left}
 td.n,th.n{text-align:right} .note{font-size:.85rem;color:#555} footer{margin-top:2rem;font-size:.8rem;color:#777}
</style></head><body>
<h1>Who does the EU really depend on for rare-earth magnets?</h1>
<p>Extra-EU imports of CN <b>8505 11 10</b> (rare-earth permanent magnets), corrected for the
Rotterdam/Antwerp transit effect. The <b>naive</b> view ranks by importing member state and is
distorted by goods cleared in NL/BE but bound elsewhere; the <b>corrected</b> view ranks by country
of origin. Source: Eurostat Comext, public data. Latest year: ', yL, '.</p>
<div class="kpis">
 <div class="kpi"><div class="v">', sprintf("%.1f%%", sL$china_val), '</div><div class="l">China share (value)</div></div>
 <div class="kpi"><div class="v">', sprintf("%.1f%%", sL$china_qty), '</div><div class="l">China share (tonnage)</div></div>
 <div class="kpi"><div class="v">', sprintf("%.2f", sL$hhi_val), '</div><div class="l">Concentration (HHI value)</div></div>
 <div class="kpi"><div class="v">', sprintf("EUR %.2fB", sL$total_eur/1e9), '</div><div class="l">Total extra-EU imports</div></div>
</div>
<h2>Naive vs corrected</h2>
<p class="note">The naive panel spreads dependence across member states; the corrected panel reveals a single origin.</p>
<img src="headline.png" alt="Naive vs corrected">
<h2>China share over time</h2><img src="trend.png" alt="Trend">
<h2>Value vs tonnage by origin (', yL, ')</h2><img src="value_vs_qty.png" alt="Value vs tonnage">
<h2>Top origins, ', yL, '</h2>
<table><thead><tr><th>Origin</th><th class="n">Value (EUR)</th><th class="n">Tonnes</th><th class="n">Value %</th><th class="n">Tonnage %</th></tr></thead>
<tbody>', rows, '</tbody></table>
<p class="note">Method: for extra-EU imports the Comext partner field is the country of origin. Bloc
aggregates (EU, EA, EA21, EU27_2020, EXT_*, INT_*, WORLD, *_2020) are dropped on both reporter and
partner, or origin totals double-count (~4.6x inflation while shares stay ~92%). CN 8505 11 10
exists only from 2023.</p>
<footer>Generated by build_static.R from public Eurostat Comext data. Independent demo - not affiliated with any institution.</footer>
</body></html>')
writeLines(html, file.path(out_dir, "dashboard.html"))

cat("Wrote out/dashboard.html + headline.png + trend.png + value_vs_qty.png for", yL, "\n")
