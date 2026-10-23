#!/usr/bin/env python3
"""
get_data.py - Wildlife Observations in Australia (FIT3179 DV2)

Downloads PRE-AGGREGATED counts from the Atlas of Living Australia (ALA)
occurrence API and writes every data file the web page needs into ../data/.
No individual records are downloaded, so the page stays small and fast.

Run from the repository root:
    python -m pip install requests
    python scripts/get_data.py

Takes about 10-20 minutes the first time (around 200 small API queries).
Every response is cached in scripts/.cache/, so re-running is instant.
Delete scripts/.cache/ to force fresh data.

Sources written to data/query_log.csv (every URL + access time) for your
metadata and for the interview.
"""
import csv
import datetime as dt
import hashlib
import json
import sys
import time
from collections import defaultdict
from pathlib import Path

try:
    import requests
except ImportError:
    sys.exit("Please run:  python -m pip install requests")

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
CACHE = ROOT / "scripts" / ".cache"
DATA.mkdir(exist_ok=True)
CACHE.mkdir(exist_ok=True)

API = "https://api.ala.org.au/occurrences/occurrences/search"
HEADERS = {"User-Agent": "FIT3179-DV2 student project (educational, non-commercial)"}
YEAR = 2025                    # latest complete calendar year
TREND_START = 2010
STATE_FIELD = "cl22"           # ALA spatial layer: Australian States and Territories
STATES = ["New South Wales", "Victoria", "Queensland", "South Australia",
          "Western Australia", "Tasmania", "Northern Territory",
          "Australian Capital Territory"]
# The five groups used in the seasonal radial chart and bin-map dropdown.
GROUPS = {
    "Birds":    'class:"Aves"',
    "Frogs":    'class:"Amphibia"',
    "Insects":  'class:"Insecta"',
    "Reptiles": 'class:"Reptilia"',
    "Fungi":    'kingdom:"Fungi"',
}
CAPITALS = [  # city, lat, lon (city centre, Geoscience Australia gazetteer values rounded)
    ("Sydney", -33.87, 151.21), ("Melbourne", -37.81, 144.96),
    ("Brisbane", -27.47, 153.03), ("Perth", -31.95, 115.86),
    ("Adelaide", -34.93, 138.60), ("Hobart", -42.88, 147.33),
    ("Darwin", -12.46, 130.84), ("Canberra", -35.28, 149.13),
]
RADIUS_KM = 50
CANE_TOAD = 'species:"Rhinella marina"'
WA_BORDER_LON = 129.0

# Keywords that identify community (citizen-science) data resources in ALA.
# The script writes data/resource_types.csv so you can check and correct them.
PUBLIC_KEYWORDS = [
    "inaturalist", "ebird", "frogid", "birdata", "birdlife", "naturemapr",
    "questagame", "reef life survey", "redmap", "climatewatch", "ispot",
    "aussie bird count", "butterflies australia", "wildlife spotter",
    "canberra nature map", "echidna", "platypus", "great koala count",
    "bowerbird", "flickr", "biocollect", "citizen", "community",
    "sightings", "atlas of life", "koala count", "backyard", "bioblitz",
]

LOG = []


# ----------------------------------------------------------------------------
# API helpers
# ----------------------------------------------------------------------------
def query(params):
    """GET the ALA occurrence search API with caching and retries."""
    p = {"q": "*:*", "pageSize": 0, "qualityProfile": "ALA"}
    p.update(params)
    url = requests.Request("GET", API, params=p).prepare().url
    cache_file = CACHE / (hashlib.md5(url.encode()).hexdigest() + ".json")
    if cache_file.exists():
        return json.loads(cache_file.read_text(encoding="utf-8"))
    for attempt in range(6):
        try:
            r = requests.get(url, headers=HEADERS, timeout=180)
            if r.status_code == 200:
                js = r.json()
                cache_file.write_text(json.dumps(js), encoding="utf-8")
                LOG.append((dt.datetime.now().isoformat(timespec="seconds"), url))
                time.sleep(0.4)  # be polite to the public API
                return js
            print(f"  HTTP {r.status_code}, retrying ...")
        except requests.RequestException as e:
            print(f"  {type(e).__name__}, retrying ...")
        time.sleep(4 * (attempt + 1))
    sys.exit(f"\nALA did not respond after several tries:\n{url}\n"
             "Check your internet connection and run the script again "
             "(finished queries are cached).")


def total(fq=()):
    return int(query({"fq": list(fq)}).get("totalRecords", 0))


def facet(field, fq=(), flimit=-1, **extra):
    """Return [(label, count), ...] for one facet field, largest first."""
    params = {"fq": list(fq), "facets": field, "flimit": flimit, "fsort": "count"}
    params.update(extra)
    js = query(params)
    out = []
    for fr in js.get("facetResults", []):
        if fr.get("fieldName") not in (field, None) and len(js["facetResults"]) > 1:
            continue
        for item in fr.get("fieldResult", []):
            label = item.get("label") or item.get("fieldValue") or item.get("i18nCode")
            if label in (None, "", "Not supplied") or label.endswith(".novalue"):
                continue
            out.append((label, int(item.get("count", 0))))
    return sorted(out, key=lambda x: -x[1])


def distinct(field, fq=(), **extra):
    """Number of distinct values of a field (e.g. species) for a query."""
    return len(facet(field, fq, flimit=-1, **extra))


def write_csv(name, header, rows):
    with open(DATA / name, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)
    print(f"  wrote data/{name} ({len(rows)} rows)")


def yfq(year):
    return f"year:{year}"


MONTH_ABBR = ["jan", "feb", "mar", "apr", "may", "jun",
              "jul", "aug", "sep", "oct", "nov", "dec"]


def month_num(label):
    """ALA returns months as numbers or as names ('10', 'Oct', 'October')."""
    s = str(label).strip()
    if s.isdigit():
        return int(s)
    return MONTH_ABBR.index(s[:3].lower()) + 1


def step(msg):
    print(f"\n== {msg}")


# ----------------------------------------------------------------------------
# 1. Records per year per source  ->  Chart 1 (line) + contributor types
# ----------------------------------------------------------------------------
step(f"1/10  Records per year by data source, {TREND_START}-{YEAR}")
by_year = {y: facet("dataResourceName", [yfq(y)]) for y in range(TREND_START, YEAR + 1)}
overall = defaultdict(int)
for rows in by_year.values():
    for label, n in rows:
        overall[label] += n
TOP5 = [k for k, _ in sorted(overall.items(), key=lambda x: -x[1])[:5]]
ORDER = {name: i + 1 for i, name in enumerate(TOP5)}
ORDER["All other sources"] = 6          # same order (and colours) in Charts 1 and 3
rows = []
for y, res in by_year.items():
    agg = defaultdict(int)
    for label, n in res:
        agg[label if label in TOP5 else "All other sources"] += n
    rows += [(y, s, n, ORDER[s]) for s, n in agg.items()]
write_csv("year_source.csv", ["year", "source", "records", "order"], rows)
year_totals = {y: sum(n for _, n in res) for y, res in by_year.items()}

# ----------------------------------------------------------------------------
# 2. Contributor type in YEAR  ->  Chart 2 (waffle)
# ----------------------------------------------------------------------------
step(f"2/10  Community vs institutional records, {YEAR}")
types_file = DATA / "resource_types.csv"
manual = {}
if types_file.exists():  # keep any corrections you made by hand
    with open(types_file, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            manual[r["resource"]] = r["type"]
res_year = by_year[YEAR]
type_rows, type_tot = [], defaultdict(int)
for label, n in res_year:
    guess = "Community" if any(k in label.lower() for k in PUBLIC_KEYWORDS) else "Institutions"
    t = manual.get(label, guess)
    type_rows.append((label, n, t))
    type_tot[t] += n
write_csv("resource_types.csv", ["resource", "records", "type"], type_rows)
grand = sum(type_tot.values()) or 1
pct = {t: type_tot[t] / grand * 100 for t in ("Community", "Institutions")}
squares = {t: int(pct[t]) for t in pct}                 # largest-remainder rounding
for t in sorted(pct, key=lambda t: -(pct[t] - int(pct[t])))[: 100 - sum(squares.values())]:
    squares[t] += 1
waffle = []
for t in ("Community", "Institutions"):
    waffle += [(len(waffle) + i, t, round(pct[t], 1)) for i in range(squares[t])]
write_csv("waffle.csv", ["id", "type", "pct"], waffle)

# ----------------------------------------------------------------------------
# 3. Records per state + per capita, and state x source  ->  Charts 3, 4
# ----------------------------------------------------------------------------
step(f"3/10  Records per state, {YEAR}")
pop = {}
with open(DATA / "population.csv", encoding="utf-8") as f:
    for r in csv.DictReader(f):
        pop[r["state"]] = (r["code"], int(r["population"]))
state_counts = dict(facet(STATE_FIELD, [yfq(YEAR)]))
if not any(s in state_counts for s in STATES):
    print("  cl22 returned no states - falling back to stateProvince")
    STATE_FIELD = "stateProvince"
    state_counts = dict(facet(STATE_FIELD, [yfq(YEAR)]))
rows = []
for s in STATES:
    code, p = pop[s]
    n = state_counts.get(s, 0)
    rows.append((s, code, n, p, round(n / p * 1000, 1)))
write_csv("state_rate.csv", ["state", "code", "records", "population", "rate"], rows)
state_rate = {r[0]: r for r in rows}

state_src = {s: facet("dataResourceName", [yfq(YEAR), f'{STATE_FIELD}:"{s}"']) for s in STATES}
rows = []
for s, res in state_src.items():
    agg = defaultdict(int)
    for label, n in res:
        agg[label if label in TOP5 else "All other sources"] += n
    rows += [(s, pop[s][0], src, n, ORDER[src]) for src, n in agg.items()]
write_csv("state_source.csv", ["state", "code", "source", "records", "order"], rows)

# ----------------------------------------------------------------------------
# 4. 1-degree grid, all records and per group  ->  Chart 5 (bin map)
# ----------------------------------------------------------------------------
step(f"4/10  1-degree grid of records, {YEAR}")
cells = defaultdict(lambda: {"All": 0, **{g: 0 for g in GROUPS}})
def add_grid(key, fq):
    for label, n in facet("point-1", fq):
        try:
            a, b = (float(v) for v in label.split(","))
        except ValueError:
            continue
        lat, lon = (a, b) if a < 0 else (b, a)          # tolerate either order
        if -44.5 <= lat <= -9 and 112 <= lon <= 154.5:
            cells[(lat, lon)][key] += n
add_grid("All", [yfq(YEAR)])
for g, q in GROUPS.items():
    add_grid(g, [yfq(YEAR), q])
if not cells:
    sys.exit("The point-1 grid facet returned nothing. Tell your tutor/Claude; "
             "the rest of the data is cached.")
features = []
for (lat, lon), props in sorted(cells.items()):
    h = 0.5
    ring = [[lon - h, lat - h], [lon - h, lat + h], [lon + h, lat + h],
            [lon + h, lat - h], [lon - h, lat - h]]          # clockwise, as d3-geo requires
    features.append({"type": "Feature", "properties": {"lat": lat, "lon": lon, **props},
                     "geometry": {"type": "Polygon", "coordinates": [ring]}})
(DATA / "grid.geojson").write_text(
    json.dumps({"type": "FeatureCollection", "features": features}, separators=(",", ":")),
    encoding="utf-8")
print(f"  wrote data/grid.geojson ({len(features)} cells)")

# ----------------------------------------------------------------------------
# 5. Capital cities (50 km radius)  ->  Chart 6 (proportional symbols)
# ----------------------------------------------------------------------------
step(f"5/10  Records and species within {RADIUS_KM} km of each capital, {YEAR}")
rows = []
for city, lat, lon in CAPITALS:
    sp = {"lat": lat, "lon": lon, "radius": RADIUS_KM}
    n = int(query({"fq": [yfq(YEAR)], **sp}).get("totalRecords", 0))
    k = distinct("species", [yfq(YEAR)], **sp)
    rows.append((city, lat, lon, n, k))
write_csv("capitals.csv", ["city", "lat", "lon", "records", "species"], rows)
capital_total = sum(r[3] for r in rows)

# ----------------------------------------------------------------------------
# 6. Taxonomy (kingdom -> class)  ->  Chart 7 (treemap)
# ----------------------------------------------------------------------------
step(f"6/10  Records by kingdom and class, {YEAR}")
KINGDOM_NAMES = {"Animalia": "Animals", "Plantae": "Plants", "Fungi": "Fungi",
                 "Chromista": "Seaweeds & kin", "Protozoa": "Protozoa",
                 "Bacteria": "Bacteria"}
CLASS_NAMES = {
    "Aves": "Birds", "Insecta": "Insects", "Magnoliopsida": "Flowering plants",
    "Liliopsida": "Grasses, lilies & orchids", "Mammalia": "Mammals",
    "Reptilia": "Reptiles", "Amphibia": "Frogs", "Arachnida": "Spiders & kin",
    "Agaricomycetes": "Mushrooms & brackets", "Actinopterygii": "Bony fishes",
    "Gastropoda": "Snails & slugs", "Polypodiopsida": "Ferns", "Pinopsida": "Conifers",
    "Malacostraca": "Crabs, prawns & slaters", "Lecanoromycetes": "Lichens",
    "Bryopsida": "Mosses", "Anthozoa": "Corals & anemones",
    "Elasmobranchii": "Sharks & rays", "Chondrichthyes": "Sharks & rays",
    "Bivalvia": "Clams & oysters", "Florideophyceae": "Red seaweeds",
    "Phaeophyceae": "Brown seaweeds", "Ulvophyceae": "Green seaweeds",
    "Diplopoda": "Millipedes", "Chilopoda": "Centipedes", "Echinoidea": "Sea urchins",
    "Asteroidea": "Sea stars", "Cephalopoda": "Octopus & squid",
    "Ascidiacea": "Sea squirts", "Polychaeta": "Bristle worms", "Hydrozoa": "Hydroids",
    "Scyphozoa": "Jellyfish", "Myxomycetes": "Slime moulds",
    "Marchantiopsida": "Liverworts", "Cycadopsida": "Cycads",
    "Lycopodiopsida": "Clubmosses", "Collembola": "Springtails",
    "Ophiuroidea": "Brittle stars", "Holothuroidea": "Sea cucumbers",
    "Sordariomycetes": "Flask fungi", "Dothideomycetes": "Sooty moulds & kin",
    "Pezizomycetes": "Cup fungi", "Clitellata": "Earthworms & leeches",
    "Polyplacophora": "Chitons", "Hexanauplia": "Barnacles & copepods",
    "Thecostraca": "Barnacles", "Demospongiae": "Sponges", "Cubozoa": "Box jellyfish",
    "Bacillariophyceae": "Diatoms", "Merostomata": "Horseshoe crabs",
}
kingdoms = facet("kingdom", [yfq(YEAR)])
rows = [("root", "", "All records", "", "", "")]
leaves = []
for k, kn in kingdoms:
    if k not in KINGDOM_NAMES or kn < 1:
        continue
    rows.append((k, "root", KINGDOM_NAMES[k], k, "", ""))
    classes = facet("class", [yfq(YEAR), f'kingdom:"{k}"'])
    classed = sum(n for _, n in classes)
    for c, n in classes:
        leaves.append((k, c, n))
    if kn - classed > 0:
        leaves.append((k, "__unclassified__", kn - classed))
leaves.sort(key=lambda x: -x[2])
keep, other = leaves[:28], defaultdict(int)
for k, c, n in leaves[28:]:
    other[k] += n
for k, c, n in keep:
    if c == "__unclassified__":
        other[k] += n
        continue
    rows.append((f"{k}/{c}", k, CLASS_NAMES.get(c, c), k, c, n))
for k, n in other.items():
    rows.append((f"{k}/other", k, f"Other {KINGDOM_NAMES[k].lower()}", k, "", n))
write_csv("taxonomy.csv", ["id", "parent", "name", "kingdom", "scientific", "records"], rows)
all_year = total([yfq(YEAR)])
birds_year = next((n for k, c, n in leaves if c == "Aves"), 0)

# ----------------------------------------------------------------------------
# 7. Month x year  ->  Chart 9 (heatmap)
# ----------------------------------------------------------------------------
step("7/10  Records per month, 2016-" + str(YEAR))
rows = []
for y in range(2016, YEAR + 1):
    for label, n in facet("month", [yfq(y)]):
        rows.append((y, month_num(label), n))
write_csv("month_year.csv", ["year", "month", "records"], rows)

# ----------------------------------------------------------------------------
# 8. Seasonal fingerprint per group  ->  Chart 10 (radial small multiples)
# ----------------------------------------------------------------------------
step(f"8/10  Monthly records per group, 2021-{YEAR} (five-year average pattern)")
rows = []
for g, q in GROUPS.items():
    for label, n in facet("month", [f"year:[2021 TO {YEAR}]", q]):
        rows.append((g, month_num(label), n))
write_csv("month_group.csv", ["group", "month", "records"], rows)

# ----------------------------------------------------------------------------
# 9. Top 10 species per year  ->  Chart 8 (bump chart)
# ----------------------------------------------------------------------------
step("9/10  Ten most-recorded species per year, 2016-" + str(YEAR))
ranks, names = [], {}
for y in range(2016, YEAR + 1):
    for r, (sp, n) in enumerate(facet("species", [yfq(y)], flimit=10), start=1):
        ranks.append((y, sp, r, n))
        names.setdefault(sp, None)
CLASS_GROUP = {"Aves": "Birds", "Amphibia": "Frogs", "Insecta": "Insects",
               "Reptilia": "Reptiles", "Mammalia": "Mammals"}
group_of = {}
for sp in names:
    v = facet("vernacularName", [f'species:"{sp}"'], flimit=1)
    names[sp] = v[0][0].strip().title() if v else sp
    c = facet("class", [f'species:"{sp}"'], flimit=1)
    k = facet("kingdom", [f'species:"{sp}"'], flimit=1)
    cls = c[0][0] if c else ""
    kin = k[0][0] if k else ""
    group_of[sp] = CLASS_GROUP.get(cls, "Fungi" if kin == "Fungi" else
                                   "Plants" if kin == "Plantae" else "Other animals")
write_csv("species_rank.csv", ["year", "species", "common_name", "group", "rank", "records"],
          [(y, sp, names[sp], group_of[sp], r, n) for y, sp, r, n in ranks])

# Species recorded per state, 2015 vs YEAR  ->  Chart 12 (dumbbell)
rows = []
for s in STATES:
    a = distinct("species", [yfq(2015), f'{STATE_FIELD}:"{s}"'])
    b = distinct("species", [yfq(YEAR), f'{STATE_FIELD}:"{s}"'])
    rows.append((s, pop[s][0], a, b))
write_csv("species_state.csv", ["state", "code", "y2015", f"y{YEAR}"], rows)
species_state = rows

# ----------------------------------------------------------------------------
# 10. Cane toad: first year recorded in each 0.1-degree cell  ->  Chart 11
# ----------------------------------------------------------------------------
step("10/10  Cane toad records, 1935-" + str(YEAR) + " (one query per year)")
first = {}
toad_years = [y for y, n in facet("year", [CANE_TOAD]) if n > 0]
for y in sorted(int(v) for v in toad_years if str(v).isdigit() and 1935 <= int(v) <= YEAR):
    for label, n in facet("point-0.1", [CANE_TOAD, yfq(y)]):
        try:
            a, b = (float(v) for v in label.split(","))
        except ValueError:
            continue
        lat, lon = (a, b) if a < 0 else (b, a)
        if -45 <= lat <= -9 and 112 <= lon <= 155 and (lat, lon) not in first:
            first[(lat, lon)] = y
rows = [(lat, lon, y) for (lat, lon), y in sorted(first.items(), key=lambda x: x[1])]
write_csv("canetoad.csv", ["lat", "lon", "first_year"], rows)
wa_years = [y for (lat, lon), y in first.items() if lon < WA_BORDER_LON]
notes = [(145.8, -17.1, "Released in north Queensland, 1935", "")]
if wa_years:
    wa = min(wa_years)
    notes.append((126.8, -13.4, f"First recorded in Western Australia: {wa}", ""))
write_csv("canetoad_notes.csv", ["lon", "lat", "text", "anchor"], notes)

# Choropleth class breaks: quartiles of the eight state rates, rounded to
# two significant figures so the legend is easy to read (Week 8: classification).
def nice(v):
    if v <= 0:
        return 0
    from math import floor, log10
    m = 10 ** (floor(log10(v)) - 1)
    return int(round(v / m) * m)
rates = sorted(r[4] for r in state_rate.values())
breaks = []
for qtl in (0.25, 0.5, 0.75):
    i = qtl * (len(rates) - 1)
    lo, hi = rates[int(i)], rates[min(int(i) + 1, len(rates) - 1)]
    b = nice(lo + (hi - lo) * (i - int(i)))
    if not breaks or b > breaks[-1]:
        breaks.append(b)
print(f"  suggested choropleth class breaks (copy into specs/04 if data changes): {breaks}")

# ----------------------------------------------------------------------------
# Summary numbers used in the text of the page
# ----------------------------------------------------------------------------
step("Writing data/summary.json and data/query_log.csv")
species_year = distinct("species", [yfq(YEAR)])
top_rate = max(state_rate.values(), key=lambda r: r[4])
low_rate = min(state_rate.values(), key=lambda r: r[4])
month_names = ["January", "February", "March", "April", "May", "June", "July",
               "August", "September", "October", "November", "December"]
yr_rows = [r for r in csv.reader(open(DATA / "month_year.csv")) if r[0] == str(YEAR)]
peak_month = month_names[int(max(yr_rows, key=lambda r: int(r[2]))[1]) - 1] if yr_rows else ""
top_sp = [r for r in ranks if r[0] == YEAR and r[2] == 1]
fmt = lambda n: f"{n:,}"
summary = {
    "year": YEAR,
    "records_year": fmt(all_year),
    "records_year_millions": f"{all_year / 1e6:.1f} million",
    "species_year": fmt(species_year),
    "community_pct": f"{round(pct['Community'])}%",
    "community_per100": str(squares["Community"]),
    "records_2015": fmt(year_totals.get(2015, 0)),
    "growth_2015": f"{year_totals[YEAR] / year_totals[2015]:.1f}" if year_totals.get(2015) else "",
    "top_source": TOP5[0] if TOP5 else "",
    "top_rate_state": top_rate[0], "top_rate": fmt(round(top_rate[4])),
    "low_rate_state": low_rate[0], "low_rate": fmt(round(low_rate[4])),
    "capitals_pct": f"{round(capital_total / all_year * 100)}%" if all_year else "",
    "birds_pct": f"{round(birds_year / all_year * 100)}%" if all_year else "",
    "top_species_year": names[top_sp[0][1]] if top_sp else "",
    "peak_month": peak_month,
    "toad_cells": fmt(len(first)),
    "toad_first_wa_year": str(min(wa_years)) if wa_years else "",
    "grid_cells": fmt(len(features)),
    "rate_breaks": breaks,
    "accessed": dt.date.today().strftime("%-d %B %Y") if sys.platform != "win32"
                else dt.date.today().strftime("%#d %B %Y"),
}
(DATA / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
old = []
if (DATA / "query_log.csv").exists():
    with open(DATA / "query_log.csv", encoding="utf-8") as f:
        old = list(csv.reader(f))[1:]
write_csv("query_log.csv", ["accessed", "url"], old + LOG)
print("\nDone. Key numbers:")
for k, v in summary.items():
    print(f"  {k:22s} {v}")
print("\nNext: check data/resource_types.csv, fix any wrong 'type' values, "
      "then run this script again (it re-uses the cache).")
