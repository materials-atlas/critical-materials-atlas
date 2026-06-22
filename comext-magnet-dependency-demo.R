# EU rare-earth-magnet import dependency: naive (member state) vs corrected (origin).
# Base R only - no package installs. Reads raw/ CSVs (fetched by download_data.ps1),
# writes out/ CSVs + headline PNG. Validated 2023-2024: China ~92% value, ~91% tonnage.
# The naive-vs-corrected method lives in dependency_core.R (shared with the Shiny app).

product <- "85051110"; raw_dir <- "raw"; out_dir <- "out"
dir.create(out_dir, showWarnings = FALSE)
source("dependency_core.R")

val <- read_comext(file.path(raw_dir, paste0("magnets_", product, "_value.csv")))
qty <- read_comext(file.path(raw_dir, paste0("magnets_", product, "_qty.csv")))
if (is.null(val)) stop("Value file missing in raw/ - run download_data.ps1 first.")

tabs <- build_tables(val, qty)
write.csv(tabs$origin,  "out/origin_shares.csv", row.names = FALSE)
write.csv(tabs$ms,      "out/ms_shares.csv",     row.names = FALSE)
write.csv(tabs$summary, "out/summary.csv",       row.names = FALSE)

su <- tabs$summary
yL <- max(su$year)
oc <- head(tabs$origin[tabs$origin$year == yL, ], 6)
mc <- head(tabs$ms[tabs$ms$year == yL, ], 6)
png(paste0("out/headline_", yL, ".png"), width = 1000, height = 450)
par(mfrow = c(1, 2), mar = c(4, 6, 4, 1))
barplot(rev(mc$value_share), names.arg = rev(mc$reporter), horiz = TRUE, las = 1, col = "grey70",
        xlab = "% of MS imports", main = paste("NAIVE: by member state", yL))
barplot(rev(oc$value_share), names.arg = rev(oc$partner), horiz = TRUE, las = 1, col = "firebrick",
        xlab = "% of extra-EU imports", main = paste("CORRECTED: by origin", yL))
dev.off()
cat("\n=== SUMMARY ===\n"); print(su)
