const map = L.map("map", { zoomControl: true }).setView([41.26, -96.03], 11);

L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
  maxZoom: 19,
  attribution: '&copy; OpenStreetMap contributors',
}).addTo(map);

const ramps = {
  mismatch: ["#eff3f0", "#c9dfd7", "#f0d58f", "#df8d63", "#b8483a"],
  opportunity: ["#f2f0ea", "#d7e7df", "#9ecdbd", "#55a78e", "#167b6d"],
  equity: ["#f7f1f4", "#e5cdd8", "#c99bb3", "#a76486", "#7a3658"],
  income: ["#f2f4f7", "#d7e2ee", "#a9c5dc", "#6f9fc3", "#2c729f"],
  rent: ["#f6f1ea", "#e6d2b5", "#d6ad74", "#bd7f38", "#8d5424"],
  ratio: ["#f1f3f4", "#d8e2da", "#b6cda8", "#82ad6e", "#4f7d44"],
};

const layerConfig = {
  spatial_mismatch_score_custom: {
    label: "Spatial Mismatch Score",
    colors: ramps.mismatch,
    format: (v) => formatNumber(v, 1),
    note: "Higher values indicate more severe mismatch.",
  },
  opportunity_access_index: {
    label: "Opportunity Access Index",
    colors: ramps.opportunity,
    format: (v) => formatNumber(v, 1),
    note: "Higher values indicate stronger access to opportunity.",
  },
  poverty_rate: {
    label: "Poverty Rate",
    colors: ramps.equity,
    format: formatPercent,
    note: "ACS poverty universe; null when ACS is unavailable.",
  },
  unemployment_rate: {
    label: "Unemployment Rate",
    colors: ramps.equity,
    format: formatPercent,
    note: "ACS unemployed divided by civilian labor force.",
  },
  households_without_vehicles: {
    label: "Households without Vehicles",
    colors: ramps.equity,
    format: (v) => formatNumber(v, 0),
    note: "ACS households reporting no available vehicle.",
  },
  people_of_color_share: {
    label: "Race/Ethnicity Context",
    colors: ramps.equity,
    format: formatPercent,
    note: "Share of residents who are not non-Hispanic white.",
  },
  median_rent: {
    label: "Median Rent",
    colors: ramps.rent,
    format: formatDollars,
    note: "ACS median gross rent.",
  },
  median_household_income: {
    label: "Median Household Income",
    colors: ramps.income,
    format: formatDollars,
    note: "ACS median household income.",
  },
  transit_access_flag: {
    label: "Transit Access",
    categorical: true,
    note: "GTFS stop and route proximity when GTFS is supplied.",
  },
  jobs_worker_ratio: {
    label: "Jobs-Worker Ratio",
    colors: ramps.ratio,
    format: (v) => formatNumber(v, 2),
    note: "Workplace jobs divided by resident workers.",
  },
};

let tractLayer;
let tractData;
let activeMetric = "spatial_mismatch_score_custom";
let searchedGeoid = "";

function formatNumber(value, digits = 0) {
  const number = Number(value);
  if (!Number.isFinite(number)) return "No data";
  return number.toLocaleString(undefined, { maximumFractionDigits: digits, minimumFractionDigits: digits });
}

function formatDollars(value) {
  const number = Number(value);
  if (!Number.isFinite(number)) return "No data";
  return `$${number.toLocaleString(undefined, { maximumFractionDigits: 0 })}`;
}

function formatPercent(value) {
  const number = Number(value);
  if (!Number.isFinite(number)) return "No data";
  return `${(number * 100).toLocaleString(undefined, { maximumFractionDigits: 1 })}%`;
}

function formatFlag(value) {
  if (value === true || value === "True" || value === "true") return "Access";
  if (value === false || value === "False" || value === "false") return "Weak access";
  return "No data";
}

function metricValues(metric) {
  return tractData.features
    .map((feature) => feature.properties[metric])
    .filter((value) => value !== null && value !== undefined && value !== "")
    .map((value) => Number(value))
    .filter((value) => Number.isFinite(value));
}

function quantileBreaks(values) {
  const sorted = [...values].sort((a, b) => a - b);
  const quantile = (q) => sorted[Math.min(sorted.length - 1, Math.floor(q * (sorted.length - 1)))];
  return [quantile(0.2), quantile(0.4), quantile(0.6), quantile(0.8)];
}

function colorForValue(value, metric) {
  if (metric === "transit_access_flag") {
    if (value === true || value === "True" || value === "true") return "#167b6d";
    if (value === false || value === "False" || value === "false") return "#b8483a";
    return "#d8dee5";
  }

  const config = layerConfig[metric] || layerConfig.spatial_mismatch_score_custom;
  const values = metricValues(metric);
  if (!values.length || value === null || value === undefined || value === "") return "#d8dee5";
  const breaks = quantileBreaks(values);
  const number = Number(value);
  const index = breaks.findIndex((breakValue) => number <= breakValue);
  return config.colors[index === -1 ? config.colors.length - 1 : index];
}

function styleFeature(feature) {
  const isSearched = searchedGeoid && feature.properties.GEOID === searchedGeoid;
  return {
    color: isSearched ? "#17212b" : "#ffffff",
    weight: isSearched ? 3 : 1,
    fillColor: colorForValue(feature.properties[activeMetric], activeMetric),
    fillOpacity: isSearched ? 0.94 : 0.8,
  };
}

function tooltipHtml(props) {
  const rows = [
    ["Mismatch", formatNumber(props.spatial_mismatch_score_custom, 1)],
    ["Opportunity", formatNumber(props.opportunity_access_index, 1)],
    ["Jobs", formatNumber(props.total_jobs, 0)],
    ["Resident workers", formatNumber(props.resident_workers, 0)],
    ["Jobs-worker ratio", formatNumber(props.jobs_worker_ratio, 2)],
    ["Poverty", formatPercent(props.poverty_rate)],
    ["No vehicle HH", formatNumber(props.households_without_vehicles, 0)],
    ["Transit", formatFlag(props.transit_access_flag)],
  ];
  return `
    <div class="tooltip-title">${props.tract_name || "Tract"} <span>${props.GEOID}</span></div>
    ${rows.map(([label, value]) => `<div class="tooltip-row"><span>${label}</span><strong>${value}</strong></div>`).join("")}
  `;
}

function updateLegend() {
  const legend = document.getElementById("legend");
  const config = layerConfig[activeMetric] || layerConfig.spatial_mismatch_score_custom;

  if (activeMetric === "transit_access_flag") {
    legend.innerHTML = `
      ${legendRows([["#167b6d", "Transit access"], ["#b8483a", "Weak transit access"], ["#d8dee5", "No GTFS / no data"]])}
      <p class="legend-note">${config.note}</p>
    `;
    return;
  }

  const values = metricValues(activeMetric);
  if (!values.length) {
    legend.innerHTML = `${legendRows([["#d8dee5", "No data available"]])}<p class="legend-note">${config.note}</p>`;
    return;
  }

  const breaks = quantileBreaks(values);
  const labels = [
    `<= ${config.format(breaks[0])}`,
    `${config.format(breaks[0])} - ${config.format(breaks[1])}`,
    `${config.format(breaks[1])} - ${config.format(breaks[2])}`,
    `${config.format(breaks[2])} - ${config.format(breaks[3])}`,
    `> ${config.format(breaks[3])}`,
  ];
  legend.innerHTML = `${legendRows(config.colors.map((color, index) => [color, labels[index]]))}<p class="legend-note">${config.note}</p>`;
}

function legendRows(rows) {
  return rows.map(([color, label]) => `<div class="legend-row"><span class="swatch" style="background:${color}"></span><span>${label}</span></div>`).join("");
}

function average(values) {
  const clean = values
    .filter((value) => value !== null && value !== undefined && value !== "")
    .map(Number)
    .filter(Number.isFinite);
  if (!clean.length) return null;
  return clean.reduce((sum, value) => sum + value, 0) / clean.length;
}

function maxBy(props, field) {
  const candidates = props.filter((row) => Number.isFinite(Number(row[field])));
  if (!candidates.length) return null;
  return candidates.reduce((best, row) => Number(row[field]) > Number(best[field]) ? row : best);
}

function updateKpis() {
  const props = tractData.features.map((feature) => feature.properties);
  const sum = (field) => props.reduce((total, row) => total + (Number(row[field]) || 0), 0);
  const high = props.filter((row) => row.spatial_mismatch_tier === "Higher").length;
  const transitKnown = props.filter((row) => row.transit_access_flag === true || row.transit_access_flag === false);
  const weakTransit = transitKnown.filter((row) => row.transit_access_flag === false).length;
  const highestMismatch = maxBy(props, "spatial_mismatch_score_custom");
  const highestOpportunity = maxBy(props, "opportunity_access_index");

  document.getElementById("kpiJobs").textContent = formatNumber(sum("total_jobs"), 0);
  document.getElementById("kpiWorkers").textContent = formatNumber(sum("resident_workers"), 0);
  document.getElementById("kpiAvgMismatch").textContent = formatNumber(average(props.map((row) => row.spatial_mismatch_score_custom)), 1);
  document.getElementById("kpiAvgOpportunity").textContent = formatNumber(average(props.map((row) => row.opportunity_access_index)), 1);
  document.getElementById("kpiHighShare").textContent = props.length ? `${((high / props.length) * 100).toFixed(1)}%` : "No data";
  document.getElementById("kpiWeakTransit").textContent = transitKnown.length ? `${((weakTransit / transitKnown.length) * 100).toFixed(1)}%` : "No data";
  document.getElementById("kpiHighestMismatch").textContent = highestMismatch ? `${highestMismatch.tract_name} (${formatNumber(highestMismatch.spatial_mismatch_score_custom, 1)})` : "No data";
  document.getElementById("kpiHighestOpportunity").textContent = highestOpportunity ? `${highestOpportunity.tract_name} (${formatNumber(highestOpportunity.opportunity_access_index, 1)})` : "No data";
}

function renderLayer() {
  if (tractLayer) map.removeLayer(tractLayer);
  tractLayer = L.geoJSON(tractData, {
    style: styleFeature,
    onEachFeature: (feature, layer) => {
      layer.bindTooltip(tooltipHtml(feature.properties), { sticky: true, direction: "auto" });
      layer.on("click", () => {
        searchedGeoid = feature.properties.GEOID;
        document.getElementById("tractSearch").value = feature.properties.GEOID;
        renderLayer();
      });
    },
  }).addTo(map);
  updateLegend();
}

function showStatus(message) {
  const status = document.getElementById("status");
  status.textContent = message;
  status.hidden = false;
}

document.getElementById("layerSelect").addEventListener("change", (event) => {
  activeMetric = event.target.value;
  renderLayer();
});

document.getElementById("tractSearch").addEventListener("input", (event) => {
  const query = event.target.value.trim().toLowerCase();
  const match = tractData.features.find((feature) => {
    const props = feature.properties;
    return props.GEOID.toLowerCase().includes(query) || String(props.tract_name || "").toLowerCase().includes(query);
  });
  searchedGeoid = query && match ? match.properties.GEOID : "";
  if (match) map.fitBounds(L.geoJSON(match).getBounds(), { maxZoom: 13 });
  renderLayer();
});

fetch("../outputs/geojson/tract_mismatch.geojson")
  .then((response) => {
    if (!response.ok) throw new Error(`GeoJSON not found: ${response.status}`);
    return response.json();
  })
  .then((data) => {
    tractData = data;
    renderLayer();
    updateKpis();
    if (data.features.length) map.fitBounds(tractLayer.getBounds(), { padding: [20, 20] });
  })
  .catch((error) => {
    showStatus(`Could not load outputs/geojson/tract_mismatch.geojson. Run the Python workflow, then serve the project root locally. ${error.message}`);
  });
