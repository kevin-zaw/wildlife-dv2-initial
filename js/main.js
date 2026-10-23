// main.js - draws every chart on the page.
//
// vegaEmbed(where, spec, options) is the Vega-Embed library function.
//   where   = the <div> on the page, found by its id (e.g. "#c1")
//   spec    = the JSON file that describes the chart (in the /specs folder)
//   options = settings shared by every chart (below)

// Shared look for all charts, so fonts and colours match the web page.
const config = {
  font: "Atkinson Hyperlegible, Verdana, sans-serif",
  background: null,                         // transparent: page colour shows through
  view: { stroke: null },                   // no box around each chart
  axis: { labelFontSize: 12, titleFontSize: 12, gridColor: "#E1E7E1" },
  legend: { labelFontSize: 12, titleFontSize: 12 }
};

const options = { actions: false, renderer: "svg", config: config };

vegaEmbed("#c1", "specs/01_sources_line.vl.json", options);
vegaEmbed("#c2", "specs/02_waffle.vl.json", options);
vegaEmbed("#c3", "specs/03_source_mix.vl.json", options);
vegaEmbed("#c4", "specs/04_choropleth.vl.json", options);
vegaEmbed("#c5", "specs/05_binmap.vl.json", options);
vegaEmbed("#c6", "specs/06_propsymbol.vl.json", options);
vegaEmbed("#c7", "specs/07_treemap.vg.json", options);   // the only Vega (not Vega-Lite) chart
vegaEmbed("#c8", "specs/08_bump.vl.json", options);
vegaEmbed("#c9", "specs/09_heatmap.vl.json", options);
vegaEmbed("#c10", "specs/10_radial.vl.json", options);
vegaEmbed("#c11", "specs/11_canetoad_dotmap.vl.json", options);
vegaEmbed("#c12", "specs/12_dumbbell.vl.json", options);
