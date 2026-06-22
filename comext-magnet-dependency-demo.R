# ============================================================================
#  EU rare-earth-magnet import dependency — naive vs. origin-corrected
#  Portfolio demo pipeline (public Eurostat Comext data only)
# ----------------------------------------------------------------------------
#  Purpose: show that the "obvious" supplier ranking is wrong because of the
#  Rotterdam/Antwerp quasi-transit effect (consignment != origin), and that
#  handling it correctly changes the dependency picture.
#
#  Scope:   Extra-EU IMPORTS of CN 8505 11 10
#           ("permanent magnets of metal, containing Nd/Pr/Dy/Sm" = rare-earth)
#           Annual, ~2015–latest. EU27 as reporter (sum of member states).
#
#  NOTE ON SOURCES (verified June 2026):
#   - Comext DETAILED (CN8) data is NOT served by the standard SDMX web API,
#     so the eurostat / restatapi R packages CANNOT pull it. Use either:
#       (a) the Comext bulk download facility (annual/monthly CSV/zip), or
#       (b) the dedicated Comext endpoint (must filter, full download disabled):
#           https://ec.europa.eu/eurostat/api/comext/dissemination/sdmx/2.1/
#   - Aggregated trade (HS2-4) IS in the standard API -> good for cross-checks
#     via the `eurostat` package.
#
#  Items marked  ## VERIFY  need confirming against the live data before a
#  client-facing run (exact file URLs, field names, code-break year).
# ============================================================================

library(data.table)
# install.packages(c("data.table","ggplot2","arrow")) if needed
library(ggplot2)

# ---- 0. CONFIG -------------------------------------------------------------
cfg <- list(
  product_cn8   = "85051110",     # rare-earth permanent magnets
  product_cn6   = "850511",       # fallback for pre-split years (see §1b)
  product_label = "Rare-earth permanent magnets (NdFeB/SmCo)",
  years         = 2015:2024,      ## VERIFY latest complete year available
  flow          = 1L,             # 1 = imports, 2 = exports (Comext convention) ## VERIFY
  reporter_set  = "EU27",         # aggregate EU27 reporters
  out_dir       = "out"
)
dir.create(cfg$out_dir, showWarnings = FALSE)

# ---- 1. ACQUIRE ------------------------------------------------------------
# Two real options. (a) bulk facility is the most reliable for detailed data.

# (a) Bulk download facility — annual detailed files.
#     Browse/confirm the exact file names + URL pattern here:
#     https://ec.europa.eu/eurostat/databrowser/bulk?selectedTab=fileComext
#     Instructions PDF: .../comext/bulk_download/Instructions...pdf
download_comext_year <- function(year, dest_dir = "raw") {
  dir.create(dest_dir, showWarnings = FALSE)
  ## VERIFY exact file naming (e.g. "full<year>52.7z" or similar) on the bulk page
  url  <- sprintf("https://ec.europa.eu/eurostat/api/dissemination/files?file=comext/COMEXT_DATA/PRODUCTS/full%d52.7z", year) ## VERIFY
  dest <- file.path(dest_dir, sprintf("comext_%d.7z", year))
  if (!file.exists(dest)) download.file(url, dest, mode = "wb")
  dest  # then extract with archive::archive_extract() or system 7z, read the .dat/.csv
}

# (b) Dedicated Comext API endpoint (filtered query, returns SDMX/CSV).
#     Build the dataflow + key from the metadata; example shape only:
#     <base>/data/DS-045409/...?format=csv&... ## VERIFY dataflow id + dimension keys
comext_api_base <- "https://ec.europa.eu/eurostat/api/comext/dissemination/sdmx/2.1"

# For the scaffold we assume a long table `raw` with at least these columns
# after reading + light renaming:
#   reporter (declarant), partner, partner_origin, product, year, flow,
#   value_eur, qty_kg, flag  (flag carries confidentiality/estimation markers)
# load_raw() <- your reader for the chosen option above.  ## IMPLEMENT

# ---- 1b. CODE CONTINUITY ---------------------------------------------------
# The rare-earth-specific line 85051110 was introduced only recently; earlier
# years only have CN6 850511 (all metal magnets lumped). For pre-split years
# either (i) stop the rare-earth series at the introduction year, or
# (ii) show 850511 with an explicit break annotation. Do NOT silently splice.
SPLIT_YEAR <- 2022L  ## VERIFY exact year the EU CN introduced 85051110

# ---- 2. CLEAN / FILTER -----------------------------------------------------
prep <- function(raw) {
  dt <- as.data.table(raw)
  dt <- dt[product %in% c(cfg$product_cn8, cfg$product_cn6) &
             flow == cfg$flow &
             year %in% cfg$years]

  # Confidential / suppressed flows: keep, flag, never drop silently.
  dt[, confidential := grepl("conf|suppress|: ", flag, ignore.case = TRUE)] ## VERIFY flag codes

  # Extra-EU only (partner outside EU27): the quasi-transit story is about
  # extra-EU imports cleared via NL/BE. ## VERIFY partner geo coding (ISO vs Comext)
  dt[, extra_eu := !(partner %in% eu27_codes())]
  dt[, value_eur := as.numeric(value_eur)]
  dt[]
}

eu27_codes <- function() c("AT","BE","BG","HR","CY","CZ","DK","EE","FI","FR",
  "DE","GR","HU","IE","IT","LV","LT","LU","MT","NL","PL","PT","RO","SK","SI",
  "ES","SE")  ## VERIFY coding scheme used in your Comext extract

# ---- 3. NAIVE vs CORRECTED ATTRIBUTION ------------------------------------
# NAIVE   : aggregate extra-EU imports by reported trading PARTNER
#           (= country of consignment/dispatch). This is what a generalist does
#           and it inflates NL/BE because of goods transiting Rotterdam/Antwerp.
# CORRECTED: aggregate by COUNTRY OF ORIGIN. Comext extra-EU imports record an
#           origin concept distinct from consignment — using it strips out the
#           transit distortion. ## VERIFY which dimension carries origin in your extract.
build_views <- function(dt) {
  naive <- dt[extra_eu == TRUE,
              .(value_eur = sum(value_eur, na.rm = TRUE)),
              by = .(year, country = partner)]

  corrected <- dt[extra_eu == TRUE,
                  .(value_eur = sum(value_eur, na.rm = TRUE)),
                  by = .(year, country = partner_origin)]  ## origin field

  list(naive = naive, corrected = corrected)
}

# ---- 4. DEPENDENCY METRICS -------------------------------------------------
# Per year: top-supplier shares + a concentration index (HHI) + single biggest
# partner share. HHI in [0,1]; >0.25 is "highly concentrated" — a clean,
# defensible headline number for a "how exposed are we" question.
metrics <- function(view) {
  tot <- view[, .(total = sum(value_eur)), by = year]
  view <- merge(view, tot, by = "year")
  view[, share := value_eur / total]
  list(
    shares = view[order(year, -share)],
    hhi    = view[, .(hhi = sum(share^2)), by = year],
    top1   = view[order(year, -share), .SD[1], by = year][
               , .(year, top_country = country, top_share = share)]
  )
}

# ---- 5. ASSEMBLE + EXPORT --------------------------------------------------
# run <- function() {
#   raw <- load_raw()                 ## IMPLEMENT (option a or b above)
#   dt  <- prep(raw)
#   v   <- build_views(dt)
#   mn  <- metrics(v$naive); mc <- metrics(v$corrected)
#
#   # Clean, documented client dataset:
#   arrow::write_parquet(dt, file.path(cfg$out_dir, "magnets_clean.parquet"))
#   fwrite(mn$shares, file.path(cfg$out_dir, "shares_naive.csv"))
#   fwrite(mc$shares, file.path(cfg$out_dir, "shares_corrected.csv"))
#
#   # THE headline chart: naive vs corrected top-supplier share, latest year.
#   latest <- max(cfg$years)
#   comp <- rbind(
#     cbind(view = "By trading partner (naive)",   mn$shares[year == latest]),
#     cbind(view = "By country of origin (corrected)", mc$shares[year == latest])
#   )
#   p <- ggplot(comp[share > 0.02],
#               aes(reorder(country, share), share, fill = view)) +
#        geom_col(position = "dodge") + coord_flip() +
#        scale_y_continuous(labels = scales::percent) +
#        labs(title = sprintf("EU import dependence — %s, %d", cfg$product_label, latest),
#             subtitle = "Naive partner view overstates NL/BE (Rotterdam effect); origin view corrects it",
#             x = NULL, y = "Share of extra-EU import value", fill = NULL)
#   ggsave(file.path(cfg$out_dir, "naive_vs_corrected.png"), p, width = 9, height = 5, dpi = 150)
#   invisible(list(dt = dt, naive = mn, corrected = mc))
# }
# run()

# ---- 6. NEXT: DASHBOARD ----------------------------------------------------
# Wrap §5 outputs in a Quarto dashboard (format: dashboard) or a small Shiny app:
#   - Tab 1: naive-vs-corrected headline (the "wow")
#   - Tab 2: 10-year trend of top-supplier + HHI concentration
#   - Tab 3: methodology note (consignment vs origin, code break, confidential flags)
# Parameterise `product_cn8` so the same pipeline re-points to any product
# = the basis of a maintained, refreshable client deliverable + retainer.
