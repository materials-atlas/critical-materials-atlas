# Shared core for the EU trade-dependency demo. Base R only - no package installs.
# Sourced by BOTH the batch pipeline (comext-magnet-dependency-demo.R) and the Shiny
# app (app.R), so the naive-vs-corrected method has a single source of truth.
#
# Method: extra-EU imports of a CN product. For extra-EU imports the Comext partner
# field IS the country of origin, so the corrected supplier view = partner. The
# Rotterdam effect is a member-state artefact (goods cleared in NL/BE, bound elsewhere),
# so the "by importing member state" panel is the trap. Aggregate codes (EU, EA, EXT_*,
# INT_*, WORLD, *_2020) are dropped on BOTH reporter and partner or totals double-count.

eu27 <- c("AT","BE","BG","HR","CY","CZ","DK","EE","FI","FR","DE","EL","GR","HU",
          "IE","IT","LV","LT","LU","MT","NL","PL","PT","RO","SK","SI","ES","SE")

is_aggregate <- function(x) grepl("EU|EA|EXT|INT|WORLD|TOTAL|_", x)

# Read a Comext SDMX-CSV file; coerce OBS_VALUE numeric; drop non-numeric (": " etc).
read_comext <- function(p) {
  if (!file.exists(p)) return(NULL)
  z <- read.csv(p, stringsAsFactors = FALSE)
  z$OBS_VALUE <- suppressWarnings(as.numeric(z$OBS_VALUE))
  z[!is.na(z$OBS_VALUE), ]
}

# CORRECTED view: extra-EU imports by country of origin (partner), EU-27 reporters only.
origin_tab <- function(df, y) {
  d <- df[df$TIME_PERIOD == y & df$reporter %in% eu27 &
            !is_aggregate(df$partner) & !(df$partner %in% eu27), ]
  a <- aggregate(OBS_VALUE ~ partner, d, sum); a[order(-a$OBS_VALUE), ]
}

# NAIVE view: by importing member state (reporter) - the Rotterdam trap.
ms_tab <- function(df, y) {
  d <- df[df$TIME_PERIOD == y & df$reporter %in% eu27 & !is_aggregate(df$reporter), ]
  a <- aggregate(OBS_VALUE ~ reporter, d, sum); a[order(-a$OBS_VALUE), ]
}

# Build per-year origin / member-state / summary tables from a value+quantity pair.
# QUANTITY_IN_100KG -> tonnes = /10. Returns list(origin, ms, summary).
build_tables <- function(val, qty) {
  oa <- NULL; ma <- NULL; su <- NULL
  for (y in sort(unique(val$TIME_PERIOD))) {
    ov <- origin_tab(val, y); names(ov)[2] <- "value_eur"
    oq <- origin_tab(qty, y); names(oq)[2] <- "q"
    ov <- merge(ov, oq, by = "partner", all.x = TRUE)
    ov$tonnes <- ov$q / 10; ov$q <- NULL
    ov$year <- y; vt <- sum(ov$value_eur); qt <- sum(ov$tonnes, na.rm = TRUE)
    ov$value_share <- round(100 * ov$value_eur / vt, 2)
    ov$qty_share   <- round(100 * ov$tonnes / qt, 2)
    oa <- rbind(oa, ov[order(-ov$value_eur),
                       c("year","partner","value_eur","tonnes","value_share","qty_share")])
    ms <- ms_tab(val, y); names(ms)[2] <- "value_eur"; ms$year <- y
    ms$value_share <- round(100 * ms$value_eur / sum(ms$value_eur), 2)
    ma <- rbind(ma, ms[order(-ms$value_eur), c("year","reporter","value_eur","value_share")])
    cv <- ov$value_share[ov$partner == "CN"]; if (!length(cv)) cv <- 0
    cq <- ov$qty_share[ov$partner == "CN"];   if (!length(cq)) cq <- NA
    su <- rbind(su, data.frame(year = y, total_eur = vt, china_val = cv, china_qty = cq,
                  hhi_val = round(sum((ov$value_eur / vt)^2), 3),
                  hhi_qty = round(sum((ov$tonnes / qt)^2, na.rm = TRUE), 3)))
  }
  list(origin = oa, ms = ma, summary = su)
}

# Discover downloaded products in a raw/ dir from "<label>_<code>_value.csv" filenames.
# Returns a data.frame(label, code, value_file, qty_file) for pairs that have both.
discover_products <- function(raw_dir = "raw") {
  vf <- list.files(raw_dir, pattern = "_value\\.csv$", full.names = FALSE)
  out <- NULL
  for (f in vf) {
    m <- regmatches(f, regexec("^(.*)_([0-9]+)_value\\.csv$", f))[[1]]
    if (length(m) != 3) next
    qf <- sub("_value\\.csv$", "_qty.csv", f)
    if (!file.exists(file.path(raw_dir, qf))) next
    out <- rbind(out, data.frame(label = m[2], code = m[3],
                                 value_file = f, qty_file = qf, stringsAsFactors = FALSE))
  }
  out
}
