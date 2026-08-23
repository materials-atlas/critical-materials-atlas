"""Extract broad electrolyser-material and equipment trade context from BACI."""
from __future__ import annotations

import csv, io, json, os, zipfile
from collections import defaultdict

ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); HERE=os.path.dirname(os.path.abspath(__file__))
COUNTRIES=os.path.join(ROOT,"raw","baci","country_codes_V202601.csv"); OUT=os.path.join(HERE,"out","electrolyser_trade.json")
BATCHES=[("HS02",range(2002,2017),"BACI_HS02_V202601.zip","BACI_HS02_Y{year}_V202601.csv"),("HS17",range(2017,2025),"BACI_HS17_V202601.zip","BACI_HS17_Y{year}_V202601.csv")]
GROUPS={
 "electrolysis_equipment":{"title":"Electroplating/electrolysis equipment","codes":["854330"],"boundary":"Includes electroplating, electrophoresis and other electrolysis apparatus; not a clean water-electrolyser code."},
 "iridium_group":{"title":"Unwrought/powder iridium, osmium and ruthenium","codes":["711041"],"boundary":"Groups three PGMs and all end uses; does not isolate iridium or PEM catalysts."},
 "nickel_plate":{"title":"Nickel plates, sheets, strip and foil","codes":["750610","750620"],"boundary":"Nickel and nickel-alloy flat products for all industries."},
 "static_converters":{"title":"Static converters","codes":["850440"],"boundary":"Rectifiers and power supplies for electrolysers and many unrelated uses."},
}
CODE_GROUP={c:g for g,s in GROUPS.items() for c in s["codes"]}; FORCE_ISO={"490":"TW","516":"NA"}; FORCE_NAME={"TW":"Taiwan","NA":"Namibia"}
def maps():
 iso,names={},{}
 with open(COUNTRIES,encoding="utf-8") as h:
  for r in csv.DictReader(h):
   c=(r.get("country_iso2") or "").strip()
   if c and c!="NA": iso[r["country_code"].strip()]=c; names[c]=(r.get("country_name") or c).strip()
 iso.update(FORCE_ISO); names.update(FORCE_NAME); return iso,names
def empty(): return {"exp":defaultdict(float),"imp":defaultdict(float),"usd":0.0,"tonnes":0.0}
def top(v,total,names): return [{"iso":k,"name":names.get(k,k),"value_usd":round(x),"share":round(x/total,4)} for k,x in sorted(v.items(),key=lambda z:-z[1])[:8]] if total else []
def extract():
 iso,names=maps(); bag={y:{g:empty() for g in GROUPS} for _,ys,_,_ in BATCHES for y in ys}; vint={y:hs for hs,ys,_,_ in BATCHES for y in ys}
 for hs,years,archive,member in BATCHES:
  with zipfile.ZipFile(os.path.join(ROOT,"raw","baci",archive)) as z:
   for year in years:
    print("reading",year,hs,flush=True)
    with z.open(member.format(year=year)) as raw:
     h=io.TextIOWrapper(raw,encoding="utf-8",newline=""); next(h)
     for line in h:
      p=line.split(","); g=CODE_GROUP.get(p[3]) if len(p)>=6 else None
      if not g: continue
      ex,im=iso.get(p[1]),iso.get(p[2])
      if not ex or not im or ex==im: continue
      try: usd=float(p[4])*1000
      except ValueError: continue
      if usd<=0: continue
      try: tonnes=float(p[5]) if p[5].strip() not in ("","NA","nan") else 0
      except ValueError: tonnes=0
      r=bag[year][g]; r["exp"][ex]+=usd; r["imp"][im]+=usd; r["usd"]+=usd; r["tonnes"]+=max(0,tonnes)
 out={"source":"CEPII BACI V202601, based on UN Comtrade","years":sorted(bag),"vintage":{str(y):vint[y] for y in bag},"groups":GROUPS,"years_data":{},"series":{}}
 for y in out["years"]:
  out["years_data"][str(y)]={}
  for g in GROUPS:
   r=bag[y][g]; total=r["usd"]; shares=[x/total for x in r["exp"].values()] if total else []
   out["years_data"][str(y)][g]={"world_usd":round(total),"world_tonnes":round(r["tonnes"],1),"china_export_share":round(r["exp"].get("CN",0)/total,4) if total else None,"export_hhi":round(sum(x*x for x in shares),4) if total else None,"exporters":top(r["exp"],total,names),"importers":top(r["imp"],total,names)}
 for g in GROUPS: out["series"][g]=[{"year":y,**out["years_data"][str(y)][g]} for y in out["years"]]
 os.makedirs(os.path.dirname(OUT),exist_ok=True)
 with open(OUT,"w",encoding="utf-8") as h: json.dump(out,h,ensure_ascii=False,indent=2);h.write("\n")
 print("WROTE",OUT)
 for g,rows in out["series"].items(): print(g,f"${rows[0]['world_usd']/1e9:.2f}B -> ${rows[-1]['world_usd']/1e9:.2f}B")
if __name__=="__main__": extract()
