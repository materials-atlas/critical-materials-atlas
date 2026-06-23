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
  list(label = "niobium",   code = "72029300",
       title = "Ferro-niobium (CN 7202 93 00)",
       note  = "A near-monopoly, but on Brazil, not China: Brazil supplies ~84% of EU ferro-niobium (the additive for high-strength steel), with Canada the rest. The naive view points at the Netherlands (~49%, a Rotterdam clearing artefact); the origin is Brazil."),
  list(label = "boron",     code = "25280000",
       title = "Natural borates (CN 2528 00 00)",
       note  = "The most concentrated dependency in the atlas - and it is Turkey, not China: Turkey supplies ~98% of EU natural-borate imports (HHI 0.96). The naive view is scattered across member states (none above ~20%); the corrected view is almost a single bar."),
  list(label = "lithium",   code = "28369100",
       title = "Lithium carbonate (CN 2836 91 00)",
       note  = "The battery metal - a concentrated dependency, but NOT on China: Chile supplies ~75% (the South American 'lithium triangle'), with the US and Argentina behind. The naive view blames the Netherlands and Germany (clearing hubs); the origin is South America."),
  list(label = "antimony",  code = "81101000",
       title = "Antimony, unwrought (CN 8110 10 00)",
       note  = "The method's acid test: the naive view says France and Belgium (~37% each); the corrected view reveals Tajikistan at ~69%, with China barely present. Proof this is not a China-finding machine - it surfaces whatever origin the transit data hides."),
  list(label = "platinum",  code = "71101100",
       title = "Platinum, unwrought (CN 7110 11 00)",
       note  = "Platinum-group metals - autocatalysts and the hydrogen economy. A concentrated non-China dependency: South Africa ~57%, with the UK and US behind. The naive view points at Germany (~43%); the origin is South Africa."),
  list(label = "palladium", code = "71102100",
       title = "Palladium, unwrought (CN 7110 21 00)",
       note  = "Platinum's sister PGM, and the sharpest naive trap in the atlas: the member-state view says Germany ~60% (a refining/clearing hub that mines no PGM), while the true origin is South Africa ~40% and Russia ~20% - the latter a live sanctions exposure for autocatalysts."),
  list(label = "fluorspar", code = "25292200",
       title = "Fluorspar, >97% CaF2 (CN 2529 22 00)",
       note  = "Feedstock for hydrofluoric acid and refrigerants. A diversified non-China dependency: Mexico ~42% and South Africa ~36%, while the naive view blames Italy (~51%). Mexico is an origin that appears nowhere in the member-state picture."),
  list(label = "titanium",  code = "81082000",
       title = "Titanium, unwrought (CN 8108 20 00)",
       note  = "Aerospace-grade titanium, post-Russia. The naive view says France (~40%); the corrected view shows Kazakhstan (~33%) and the US (~25%) - the sponge supply that replaced Russia after 2022. A recognised strategic metal sourced from Central Asia, invisible in the member-state view."),
  list(label = "silicon",   code = "28046900",
       title = "Silicon, < 99.99% (CN 2804 69 00)",
       note  = "A critical material where the EU is genuinely diversified: origin is Norway (~47%), Brazil and Iceland - not a dependency risk. The naive view still misleads (Germany 44%), but the honest finding here is 'no concentration'. Included to show the method measures rather than confirms."),
  list(label = "feldspar",  code = "25291000",
       title = "Feldspar (CN 2529 10 00)",
       note  = "The atlas's second near-monopoly on Turkey: ~84% of EU feldspar (ceramics and glass) is Turkish. The naive view blames Spain and Italy (~45%/34%); the origin is overwhelmingly Turkey."),
  list(label = "vanadium",  code = "72029200",
       title = "Ferro-vanadium (CN 7202 92 00)",
       note  = "A steel- and battery-metal dependency on South Africa (~53%) and South Korea (~32%), China a distant third (~15%). The naive view points at the Netherlands (~35%); the origin is South Africa."),
  list(label = "manganese", code = "26020000",
       title = "Manganese ore (CN 2602 00 00)",
       note  = "An African dependency the member-state view erases: Gabon ~51% and South Africa ~41%, while the naive view blames France (~42%). Gabon appears nowhere in the importing-country picture."),
  list(label = "bauxite",   code = "26060000",
       title = "Aluminium ores / bauxite (CN 2606 00 00)",
       note  = "The feedstock for aluminium: Guinea ~59%, then Brazil. The naive view points at Ireland (~35%, the Aughinish alumina refinery) - a processing artefact, not the origin, which is Guinea."),
  list(label = "phosphate", code = "25101000",
       title = "Phosphate rock (CN 2510 10 00)",
       note  = "Fertiliser feedstock: Russia ~41% and Morocco ~27%, with the naive view split across the Netherlands and Belgium (~33%/31%, the Antwerp/Rotterdam fertiliser hubs). The Russia share is a live sanctions exposure."),
  list(label = "baryte",    code = "25111000",
       title = "Baryte (CN 2511 10 00)",
       note  = "Drilling-fluid weighting agent: China ~53% and Morocco ~30%. The naive view is scattered across the Netherlands and Italy (~25%/24%); the origin is China."),
  list(label = "arsenic",   code = "28048000",
       title = "Arsenic (CN 2804 80 00)",
       note  = "A concentrated China dependency (~86%), used in semiconductors and alloys. The naive view scatters it across the Netherlands and Germany; the origin is overwhelmingly China."),
  list(label = "beryllium", code = "81121200",
       title = "Beryllium, unwrought (CN 8112 12 00)",
       note  = "The atlas's one perfect monopoly - and it is the US, not China: ~100% of EU beryllium imports originate in the United States. The naive view points at Spain and France (refining/clearing); the origin is singular."),
  list(label = "hafnium",   code = "81123100",
       title = "Hafnium, unwrought (CN 8112 31 00)",
       note  = "The sharpest naive trap in the atlas: the member-state view says Germany ~88%, while the true origin is the US (~60%) and China (~21%). A nuclear- and superalloy-grade metal almost entirely hidden behind one clearing country."),
  list(label = "strontium", code = "28369200",
       title = "Strontium carbonate (CN 2836 92 00)",
       note  = "A Japan-led dependency: ~75% of EU strontium-carbonate imports are Japanese, China ~14%. The naive view is scattered across Italy and Austria; the origin is Japan."),
  list(label = "phosphorus",code = "28047010",
       title = "Phosphorus (CN 2804 70 10)",
       note  = "Elemental phosphorus comes mainly from Vietnam (~64%) and China (~25%). The naive view blames Germany and Italy (~49%/40%); the origin is South-East Asian."),
  list(label = "tantalum",  code = "81032000",
       title = "Tantalum, unwrought (CN 8103 20 00)",
       note  = "Processed tantalum is diversified across China (~37%), Japan and the US - the naive view blames Germany (~42%). Unlike the mined ore (DRC/Rwanda), the refined metal comes from the processors."),
  list(label = "cokingcoal",code = "27011210",
       title = "Coking coal (CN 2701 12 10)",
       note  = "An allied dependency: the US and Australia supply ~44% each, Canada behind. The naive view blames Germany and the Netherlands (the coal ports); the origins are friendly."),
  list(label = "helium",    code = "28042910",
       title = "Helium (CN 2804 29 10)",
       note  = "A diversified gas dependency: Algeria ~37%, Qatar ~31% and the US ~21%. The naive view splits across Germany and France; the origins are North African, Gulf and American."),
  list(label = "copper",    code = "74031100",
       title = "Refined copper cathodes (CN 7403 11 00)",
       note  = "Chile ~39%, then the DRC and Congo. The naive view says Italy (~31%); the true origins are South American and Central African mines - diversified, with a notable DRC share."),
  list(label = "nickel",    code = "75021000",
       title = "Nickel, unwrought (CN 7502 10 00)",
       note  = "A diversified, lower-risk dependency: Norway ~33%, Canada and Russia behind. The naive view points at the Netherlands (~39%); origin is spread across friendly producers - no single chokepoint.")
)

eur <- function(x) ifelse(x >= 1e9, sprintf("EUR %.2fB", x/1e9),
                   ifelse(x >= 1e6, sprintf("EUR %.1fM", x/1e6), sprintf("EUR %.0f", x)))

# Render the three PNGs for one product; return an HTML <section> string.
render_product <- function(p) {
  val <- read_comext(file.path(raw_dir, paste0(p$label, "_", p$code, "_value.csv")))
  qty <- read_comext(file.path(raw_dir, paste0(p$label, "_", p$code, "_qty.csv")))
  if (is.null(val)) { message("skip ", p$label, " - run download_data.ps1"); return(NULL) }
  t <- build_tables(val, qty); oa <- t$origin; ma <- t$ms; su <- t$summary
  su <- su[su$year <= HEADLINE_YEAR, ]; oa <- oa[oa$year <= HEADLINE_YEAR, ]; ma <- ma[ma$year <= HEADLINE_YEAR, ]
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

  ud <- val[["LAST.UPDATE"]]   # Comext SDMX-CSV carries a "LAST UPDATE" dd/mm/yy column
  updated <- if (is.null(ud)) NULL else
    format(suppressWarnings(max(as.Date(substr(ud, 1, 8), "%d/%m/%y"), na.rm = TRUE)), "%Y-%m-%d")

  # Rich per-material record consumed by the interactive front-end (out/data.json).
  list(
    label = p$label, title = p$title, note = p$note, year = yL,
    hhi = sL$hhi_val, total_eur = round(sL$total_eur), china_val = sL$china_val,
    china_qty = if (is.na(sL$china_qty)) NULL else sL$china_qty,
    top_partner = oc$partner[1], top_share = oc$value_share[1],
    china = identical(oc$partner[1], "CN"), updated = updated,
    origins = lapply(seq_len(nrow(oc)), function(i)
      list(c = oc$partner[i], v = oc$value_share[i], q = oc$qty_share[i], eur = round(oc$value_eur[i]))),
    naive = lapply(seq_len(nrow(mc)), function(i)
      list(c = mc$reporter[i], v = mc$value_share[i])),
    trend = lapply(seq_len(nrow(su)), function(i)
      list(y = su$year[i], cn = su$china_val[i]))
  )
}

# The latest Comext annual year is provisional - recent figures are revised upward for
# months - so the atlas headlines the latest COMPLETE year = one before the global latest.
# This keeps every panel on the same year and never publishes a partial figure.
.all_years <- unlist(lapply(products, function(p) {
  f <- file.path(raw_dir, paste0(p$label, "_", p$code, "_value.csv"))
  if (file.exists(f)) unique(read.csv(f, stringsAsFactors = FALSE)$TIME_PERIOD)
}))
HEADLINE_YEAR <- max(.all_years) - 1
cat("Headline year:", HEADLINE_YEAR, "(latest", max(.all_years), "dropped as provisional)\n")

# Render each product, then build the one-glance overview from their top origins.
results <- Filter(Negate(is.null), lapply(products, render_product))

short <- function(s) paste0(toupper(substr(s, 1, 1)), substr(s, 2, nchar(s)))
ovs <- data.frame(
  mat     = vapply(results, function(r) short(r$label), character(1)),
  partner = vapply(results, function(r) r$top_partner, character(1)),
  share   = vapply(results, function(r) r$top_share, numeric(1)),
  china   = vapply(results, function(r) isTRUE(r$china), logical(1)),
  stringsAsFactors = FALSE)
ovs <- ovs[order(ovs$share), ]
png(file.path(out_dir, "overview.png"), width = 1000, height = 120 + 24 * nrow(ovs))
par(mar = c(4, 9.5, 3, 1))
bp <- barplot(ovs$share, horiz = TRUE, las = 1, xlim = c(0, 105),
        names.arg = paste0(ovs$mat, "  (", ovs$partner, ")"),
        col = ifelse(ovs$china, "firebrick", "steelblue"),
        xlab = paste0("% of extra-EU imports from the single largest origin (", HEADLINE_YEAR, ")"),
        main = "EU critical-material dependency, by true origin")
text(ovs$share, bp, labels = sprintf(" %.0f%%", ovs$share), pos = 4, xpd = TRUE, cex = 0.85)
legend("bottomright", c("China", "other origin"), fill = c("firebrick", "steelblue"), bty = "n")
dev.off()

# Machine-readable data for the interactive front-end (index.html fetches out/data.json).
upds <- Filter(Negate(is.null), lapply(results, function(r) r$updated))
dataUpdated <- if (length(upds)) format(max(as.Date(unlist(upds))), "%d %b %Y") else format(Sys.Date(), "%d %b %Y")
payload <- list(
  generated    = format(Sys.Date(), "%d %b %Y"),
  dataUpdated  = dataUpdated,
  headlineYear = HEADLINE_YEAR,
  materials    = results)
writeLines(jsonlite::toJSON(payload, auto_unbox = TRUE, null = "null", digits = 4),
           file.path(out_dir, "data.json"))
cat("Wrote out/data.json + out/overview.png +", length(results) * 3, "per-product PNGs for",
    length(results), "materials.\n")
