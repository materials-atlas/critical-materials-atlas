"""Extract clean EV and broad vehicle-component trade baskets from BACI."""
from __future__ import annotations

import csv, io, json, os, zipfile
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HERE = os.path.dirname(os.path.abspath(__file__))
COUNTRIES = os.path.join(ROOT, "raw", "baci", "country_codes_V202601.csv")
OUT = os.path.join(HERE, "out", "ev_trade.json")
BATCHES = [("HS02", range(2002, 2017), "BACI_HS02_V202601.zip", "BACI_HS02_Y{year}_V202601.csv"), ("HS17", range(2017, 2025), "BACI_HS17_V202601.zip", "BACI_HS17_Y{year}_V202601.csv")]
GROUPS = {
    "passenger_cars": {"title": "All passenger cars", "prefixes": ["8703"], "vintages": ["HS02", "HS17"], "boundary": "All powertrains; a long-run comparator, not an EV measure."},
    "battery_electric_cars": {"title": "Battery-electric cars", "codes": ["870380"], "vintages": ["HS17"], "boundary": "Clean BEV code available here only from 2017."},
    "plugin_hybrid_cars": {"title": "Plug-in-hybrid cars", "codes": ["870360", "870370"], "vintages": ["HS17"], "boundary": "Spark- and compression-ignition PHEVs; clean codes available here only from 2017."},
    "lithium_ion_batteries": {"title": "Lithium-ion accumulators", "codes": ["850760"], "vintages": ["HS17"], "boundary": "Cells, modules and packs for vehicles, storage and other uses."},
    "static_converters": {"title": "Static converters", "codes": ["850440"], "vintages": ["HS02", "HS17"], "boundary": "Includes inverters, rectifiers and power supplies for vehicle and non-vehicle uses."},
}
FORCE_ISO={"490":"TW","516":"NA"}; FORCE_NAME={"TW":"Taiwan","NA":"Namibia"}

def maps():
    iso,names={},{}
    with open(COUNTRIES,encoding="utf-8") as h:
        for r in csv.DictReader(h):
            code=(r.get("country_iso2") or "").strip()
            if code and code!="NA": iso[r["country_code"].strip()]=code; names[code]=(r.get("country_name") or code).strip()
    iso.update(FORCE_ISO); names.update(FORCE_NAME); return iso,names

HS17_EXACT = {
    "870380": ["battery_electric_cars"],
    "870360": ["plugin_hybrid_cars"],
    "870370": ["plugin_hybrid_cars"],
    "850760": ["lithium_ion_batteries"],
    "850440": ["static_converters"],
}
HS02_EXACT = {"850440": ["static_converters"]}


def matching_groups(code, vintage):
    groups = list((HS17_EXACT if vintage == "HS17" else HS02_EXACT).get(code, ()))
    if code.startswith("8703"):
        groups.append("passenger_cars")
    return groups

def empty(): return {"exp":defaultdict(float),"imp":defaultdict(float),"usd":0.0,"tonnes":0.0,"flows":0}
def top(values,total,names):
    return [{"iso":k,"name":names.get(k,k),"value_usd":round(v),"share":round(v/total,4)} for k,v in sorted(values.items(),key=lambda x:-x[1])[:8]] if total else []

def extract():
    iso,names=maps(); bag={y:{g:empty() for g in GROUPS} for _,ys,_,_ in BATCHES for y in ys}; vint={y:hs for hs,ys,_,_ in BATCHES for y in ys}
    for hs,years,archive,member in BATCHES:
        with zipfile.ZipFile(os.path.join(ROOT,"raw","baci",archive)) as z:
            for year in years:
                print("reading",year,hs,flush=True)
                with z.open(member.format(year=year)) as raw:
                    h=io.TextIOWrapper(raw,encoding="utf-8",newline=""); next(h)
                    for line in h:
                        p=line.split(",")
                        if len(p)<6: continue
                        groups=matching_groups(p[3],hs)
                        if not groups: continue
                        ex,im=iso.get(p[1]),iso.get(p[2])
                        if not ex or not im or ex==im: continue
                        try: usd=float(p[4])*1000
                        except ValueError: continue
                        if usd<=0: continue
                        try: tonnes=float(p[5]) if p[5].strip() not in ("","NA","nan") else 0
                        except ValueError: tonnes=0
                        for g in groups:
                            r=bag[year][g]; r["exp"][ex]+=usd; r["imp"][im]+=usd; r["usd"]+=usd; r["tonnes"]+=max(0,tonnes); r["flows"]+=1
    out={"source":"CEPII BACI V202601, based on UN Comtrade","years":sorted(bag),"vintage":{str(y):vint[y] for y in bag},"groups":GROUPS,"years_data":{},"series":{}}
    for y in out["years"]:
        out["years_data"][str(y)]={}
        for g,spec in GROUPS.items():
            available=vint[y] in spec["vintages"]; r=bag[y][g]; total=r["usd"]
            out["years_data"][str(y)][g]={"available":available,"world_usd":round(total) if available else None,"world_tonnes":round(r["tonnes"],1) if available else None,"china_export_share":round(r["exp"].get("CN",0)/total,4) if total else None,"exporters":top(r["exp"],total,names),"importers":top(r["imp"],total,names)}
    for g in GROUPS: out["series"][g]=[{"year":y,**out["years_data"][str(y)][g]} for y in out["years"] if out["years_data"][str(y)][g]["available"]]
    os.makedirs(os.path.dirname(OUT),exist_ok=True)
    with open(OUT,"w",encoding="utf-8") as h: json.dump(out,h,ensure_ascii=False,indent=2); h.write("\n")
    print("WROTE",OUT)
    for g,rows in out["series"].items(): print(g,rows[0]["year"],"->",rows[-1]["year"],f"${rows[-1]['world_usd']/1e9:.2f}B")

if __name__=="__main__": extract()
