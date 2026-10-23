# Millions of Eyes: Wildlife Observations in Australia

FIT3179 Data Visualisation 2, Monash University
Kevin Zaw, October 2026

Live page: https://kevin-zaw.github.io/wildlife-dv2-initial/

A data story about wildlife sightings shared by the public in Australia, and how they end up being used for science. Built with Vega-Lite and Vega.

## Data

- Atlas of Living Australia: wildlife records, downloaded as totals with `scripts/get_data.py` (CC BY 4.0)
- Australian Bureau of Statistics: state population, December 2025 (CC BY 4.0)
- Natural Earth: state boundaries (public domain)
- Queensland Museum: cane toad release date

## Files

- `index.html` – the page
- `css/style.css` – layout and fonts
- `js/main.js` – embeds each chart with `vegaEmbed`
- `specs/` – the JSON spec for each chart
- `data/` – data files used by the charts
- `scripts/get_data.py` – script used to download the ALA data

## Running locally

The charts load data files, so the page has to be served rather than opened directly:

    python -m http.server 8000

Then go to http://localhost:8000

## Use of AI

Claude (Anthropic) was used to help plan the story, draft chart specifications and the data script, and check grammar. All data, design and text were checked and edited by me.
