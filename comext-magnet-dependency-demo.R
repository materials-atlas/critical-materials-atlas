# EU rare-earth-magnet import dependency: naive (member state) vs corrected (origin).
# Base R only - no package installs. Reads raw/ CSVs (fetched by download_data.ps1),
# writes out/ CSVs + headline PNG. Validated 2023-2024: China ~92% value, ~90% tonnage.
#
# Method: extra-EU imports of CN 8505 11 10. For extra-EU imports the Comext partner
# field IS the country of origin, so corrected supplier view = partner. The Rotterdam
# effect is a member-state artefact (goods cleared in NL/BE, bound elsewhere), so the
# "by importing member state" panel is the trap. Aggregate codes (EU, EA, EXT_*, INT_*,
# WORLD, *_2020) are dropped or totals double-count. CN 8505 11 10 exists from 2023.

product <- "85051110"; raw_dir <- "raw"; out_dir <- "out"
dir.create(out_dir, showWarnings = FALSE)
eu27 <- c("AT","BE","BG","HR","CY","CZ","DK","EE","FI","FR","DE","EL","GR","HU",
          "IE","IT","LV","LT","LU","MT","NL","PL","PT","RO","SK","SI","ES","SE")
is_aggregate <- function(x) grepl("EU|EA|EXT|INT|WORLD|TOTAL|_", x)
rd <- function(p){ if(!file.exists(p)) return(NULL)
  z <- read.csv(p, stringsAsFactors = FALSE)
  z$OBS_VALUE <- suppressWarnings(as.numeric(z$OBS_VALUE)); z[!is.na(z$OBS_VALUE),] }

val <- rd(file.path(raw_dir, paste0("magnets_", product, "_value.csv")))
qty <- rd(file.path(raw_dir, paste0("magnets_", product, "_qty.csv")))
if (is.null(val)) stop("Value file missing in raw/ - run download_data.ps1 first.")

ot <- function(df,y){ d <- df[df$TIME_PERIOD==y & !is_aggregate(df$partner) & !(df$partner %in% eu27),]
  a <- aggregate(OBS_VALUE ~ partner, d, sum); a[order(-a$OBS_VALUE),] }
mt <- function(df,y){ d <- df[df$TIME_PERIOD==y & df$reporter %in% eu27 & !is_aggregate(df$reporter),]
  a <- aggregate(OBS_VALUE ~ reporter, d, sum); a[order(-a$OBS_VALUE),] }

oa <- NULL; ma <- NULL; su <- NULL
for (y in sort(unique(val$TIME_PERIOD))) {
  ov <- ot(val,y); names(ov)[2] <- "value_eur"
  oq <- ot(qty,y); names(oq)[2] <- "q"
  ov <- merge(ov, oq, by="partner", all.x=TRUE); ov$tonnes <- ov$q/10; ov$q <- NULL
  ov$year <- y; vt <- sum(ov$value_eur); qt <- sum(ov$tonnes, na.rm=TRUE)
  ov$value_share <- round(100*ov$value_eur/vt,2); ov$qty_share <- round(100*ov$tonnes/qt,2)
  oa <- rbind(oa, ov[order(-ov$value_eur), c("year","partner","value_eur","tonnes","value_share","qty_share")])
  ms <- mt(val,y); names(ms)[2] <- "value_eur"; ms$year <- y
  ms$value_share <- round(100*ms$value_eur/sum(ms$value_eur),2)
  ma <- rbind(ma, ms[order(-ms$value_eur), c("year","reporter","value_eur","value_share")])
  cv <- ov$value_share[ov$partner=="CN"]; if(!length(cv)) cv <- 0
  cq <- ov$qty_share[ov$partner=="CN"];   if(!length(cq)) cq <- NA
  su <- rbind(su, data.frame(year=y, total_eur=vt, china_val=cv, china_qty=cq,
              hhi_val=round(sum((ov$value_eur/vt)^2),3),
              hhi_qty=round(sum((ov$tonnes/qt)^2, na.rm=TRUE),3)))
}
write.csv(oa,"out/origin_shares.csv",row.names=FALSE)
write.csv(ma,"out/ms_shares.csv",row.names=FALSE)
write.csv(su,"out/summary.csv",row.names=FALSE)

yL <- max(su$year); oc <- head(oa[oa$year==yL,],6); mc <- head(ma[ma$year==yL,],6)
png(paste0("out/headline_",yL,".png"), width=1000, height=450)
par(mfrow=c(1,2), mar=c(4,6,4,1))
barplot(rev(mc$value_share), names.arg=rev(mc$reporter), horiz=TRUE, las=1, col="grey70",
        xlab="% of MS imports", main=paste("NAIVE: by member state",yL))
barplot(rev(oc$value_share), names.arg=rev(oc$partner), horiz=TRUE, las=1, col="firebrick",
        xlab="% of extra-EU imports", main=paste("CORRECTED: by origin",yL))
dev.off()
cat("\n=== SUMMARY ===\n"); print(su)
