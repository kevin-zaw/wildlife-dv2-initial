# Millions of Eyes: Wildlife Observations in Australia

FIT3179 Data Visualisation 2, Monash University. Author: YOUR NAME, October 2026.

A single-page data story built with Vega-Lite 5 and Vega 5 about wildlife observations shared by the public and how they feed scientific research.

## What is already real, and what you must download

| File | Status |
|---|---|
| `data/population.csv` | Real data: ABS, *National, state and territory population, December 2025* (released 18 June 2026), population at 31 Dec 2025. The release table is in thousands, so values are rounded to the nearest 100. |
| `data/aus_states.topojson` | Real data: Natural Earth Admin-1, 1:50m, public domain. Jervis Bay Territory removed, simplified with mapshaper (10 KB). |
| Every other file in `data/` | **Created by `scripts/get_data.py`** from the Atlas of Living Australia API. The page shows "could not load" boxes until you run it. |

## 1. Download the data (about 15 minutes, once)

You need Python 3.9+ ([python.org](https://www.python.org/downloads/)). Open a terminal in this folder:

```
python -m pip install requests
python scripts/get_data.py
```

- It prints progress for 10 steps and ends with a list of key numbers. Those numbers are also saved in `data/summary.json`, and the page fills them into the text automatically.
- Results are cached in `scripts/.cache/`. If the internet drops, just run it again and it continues where it stopped.
- **Then** open `data/resource_types.csv` in Excel. Every data source has been auto-labelled `Community` or `Institutions`. Check the top 30 rows (look any source up on https://collections.ala.org.au if unsure), fix wrong labels, save as CSV, and run the script again. It re-uses the cache and only rebuilds the files.
- The page text and chart specs contain the 2025 numbers directly. If you re-download and the numbers change, update them by hand (the script prints suggested choropleth class breaks).

## 2. Preview locally

Charts load data files, so double-clicking `index.html` will not work. Use one of:

- VS Code → right-click `index.html` → **Open with Live Server**
- or in a terminal: `python -m http.server 8000`, then open http://localhost:8000

## 3. Check the words against YOUR data (important)

The following sentences are claims that the data should support. Read each chart and reword any title or sentence that does not match:

- Chart 3 title: "Every state relies on a different mix of sources"
- Chart 5 title: "Sightings hug the coast while the interior stays blank"
- Chart 10 intro: seasonal behaviour of frogs, insects and fungi
- Chart 12 title: "More species are being recorded than a decade ago"
- Hero and Chart 2: check `community_per100` is sensible after you fix `resource_types.csv`

Also replace every `YOUR NAME` / `YOUR ID` in `index.html` and this README. If you are at the Malaysia campus, un-comment the Malaysia paragraph in the "Your turn" section of `index.html`.

## 4. Publish on GitHub Pages

1. Create a **public** repository on GitHub (e.g. `wildlife-dv2`).
2. Upload every file and folder here, **except** `scripts/.cache/` (already excluded by `.gitignore` if you use Git or GitHub Desktop).
3. Repository → **Settings → Pages → Deploy from a branch → main → / (root) → Save**.
4. After 1–3 minutes your page is at `https://YOUR-USERNAME.github.io/wildlife-dv2/`. Test it in an **incognito** window.
5. Scan your hand-drawn sketch to PDF, save it as `sketch/DV2_sketch.pdf`, and upload it. It will be at `https://YOUR-USERNAME.github.io/wildlife-dv2/sketch/DV2_sketch.pdf`.

GitHub Pages is case-sensitive: keep every file name lowercase exactly as it is.

## Chart list (12 charts, 9 advanced idioms, 4 map idioms)

| # | Spec file | Idiom | Advanced? |
|---|---|---|---|
| 1 | `01_sources_line.vl.json` | Multi-line chart | Basic |
| 2 | `02_waffle.vl.json` | Waffle chart | Yes |
| 3 | `03_source_mix.vl.json` | 100% stacked bar chart | Basic |
| 4 | `04_choropleth.vl.json` | Choropleth map | Yes (map) |
| 5 | `05_binmap.vl.json` | Bin map with dropdown | Yes (map) |
| 6 | `06_propsymbol.vl.json` | Proportional symbol map | Yes (map) |
| 7 | `07_treemap.vg.json` | Treemap (Vega) | Yes |
| 8 | `08_bump.vl.json` | Bump chart | Yes |
| 9 | `09_heatmap.vl.json` | Heatmap | Yes |
| 10 | `10_radial.vl.json` | Radial (polar area) small multiples | Yes |
| 11 | `11_canetoad_dotmap.vl.json` | Dot map with year slider | Yes (map) |
| 12 | `12_dumbbell.vl.json` | Dumbbell chart | Basic |

All maps: Albers equal-area conic, standard parallels 18°S and 36°S, rotated to 132°E.

## Optional: all-government boundaries

To replace Natural Earth with ABS boundaries: download *States and Territories (STE) 2021, GDA2020 Shapefile* from the ABS "ASGS Edition 3 digital boundary files" page, drop the zip on https://mapshaper.org, and run in the console:

```
-filter 'STE_CODE21 != "9"'
-filter 'this.isNull === false'
-simplify 2% keep-shapes
-each 'code = {"1":"NSW","2":"VIC","3":"QLD","4":"SA","5":"WA","6":"TAS","7":"NT","8":"ACT"}[STE_CODE21]; name = STE_NAME21'
-filter-fields code,name
-rename-layers states
-o format=topojson aus_states.topojson
```

Replace `data/aus_states.topojson` with the result and update the boundary credit in the page footer.

## Licence and credits

Data: Atlas of Living Australia (CC BY 4.0), Australian Bureau of Statistics (CC BY 4.0), Natural Earth (public domain), Queensland Museum. Use of AI: Claude (Anthropic) helped plan the story, draft the chart specifications and data script, and check grammar; all data, design and text were checked and edited by the author.
