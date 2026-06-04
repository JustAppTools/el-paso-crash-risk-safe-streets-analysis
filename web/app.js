const SERVICES = {
  collisions:
    "https://devapps.fehrandpeers.com/devgis/rest/services/DA/El_Paso_Dashboard_Data/FeatureServer/1",
  cityBoundary:
    "https://devapps.fehrandpeers.com/devgis/rest/services/DA/El_Paso_Dashboard_Data/FeatureServer/2",
  mvHin:
    "https://devapps.fehrandpeers.com/devgis/rest/services/DA/El_Paso_Dashboard_Data/FeatureServer/7",
  bpHin:
    "https://devapps.fehrandpeers.com/devgis/rest/services/DA/El_Paso_Dashboard_Data/FeatureServer/8",
  equity:
    "https://devapps.fehrandpeers.com/devgis/rest/services/DA/El_Paso_Dashboard_Data/FeatureServer/11",
  predictive:
    "https://devapps.fehrandpeers.com/devgis/rest/services/DA/El_Paso_Predictive_Modeling/FeatureServer/0",
  busStops: "https://gis.elpasotexas.gov/dev/rest/services/OpenData/BusStops/FeatureServer/0",
  schools: "https://gis.elpasotexas.gov/dev/rest/services/OpenData/Schools/FeatureServer/0",
  bikeLanes: "https://gis.elpasotexas.gov/dev/rest/services/Streets/BikeLanes/FeatureServer/0",
};

const COLLISION_FIELDS = [
  "OBJECTID",
  "year",
  "crash_mode",
  "crash_mode_2",
  "crash_sev_id",
  "ksi",
  "death_cnt",
  "sus_serious_injry_cnt",
  "col_bic_cnt",
  "col_ped_cnt",
  "bike_accident",
  "ped_accident",
  "rpt_street_name",
  "rpt_street_sfx",
  "street_name",
  "crash_time_group",
  "posted_speed_group",
  "dui",
  "hit_and_run",
  "latitude",
  "longitude",
].join(",");

const state = {
  collisions: [],
  years: [],
  layers: {},
  toggles: {
    heat: true,
    ksi: false,
    vru: false,
    mvHin: true,
    bpHin: true,
    predictive: false,
    equity: false,
    context: false,
  },
  loading: {},
  activePreset: "overview",
};

const DEFAULT_TOGGLES = {
  heat: true,
  ksi: false,
  vru: false,
  mvHin: true,
  bpHin: true,
  predictive: false,
  equity: false,
  context: false,
};

const PRESETS = {
  overview: {
    title: "Overview mode",
    text: "Start with crash density and HIN corridors. This keeps the citywide safety pattern readable.",
    toggles: DEFAULT_TOGGLES,
  },
  points: {
    title: "Crash Points mode",
    text: "Shows KSI and bike/ped crashes for inspecting individual crash concentrations and overlap.",
    toggles: { ...DEFAULT_TOGGLES, ksi: true, vru: true },
  },
  equity: {
    title: "Equity context mode",
    text: "Adds equity/DAC areas to compare safety corridors with disadvantaged-community context.",
    toggles: { ...DEFAULT_TOGGLES, equity: true },
  },
  systemic: {
    title: "Systemic network mode",
    text: "Adds predictive and local context layers for deeper screening. Use after the overview pattern is clear.",
    toggles: { ...DEFAULT_TOGGLES, predictive: true, context: true },
  },
  custom: {
    title: "Custom layer view",
    text: "Manual layer selections are active. Reduce optional layers if the map starts to feel visually crowded.",
    toggles: DEFAULT_TOGGLES,
  },
};

const el = {
  statusDot: document.getElementById("statusDot"),
  statusText: document.getElementById("statusText"),
  metricCrashes: document.getElementById("metricCrashes"),
  metricKsi: document.getElementById("metricKsi"),
  metricVru: document.getElementById("metricVru"),
  metricFatal: document.getElementById("metricFatal"),
  yearFilter: document.getElementById("yearFilter"),
  modeFilter: document.getElementById("modeFilter"),
  topStreetList: document.getElementById("topStreetList"),
  streetSubtitle: document.getElementById("streetSubtitle"),
  lastUpdated: document.getElementById("lastUpdated"),
  insightTitle: document.getElementById("insightTitle"),
  insightText: document.getElementById("insightText"),
};

const map = L.map("map", {
  center: [31.79, -106.43],
  preferCanvas: true,
  zoom: 11,
  zoomControl: false,
});

L.control.zoom({ position: "bottomright" }).addTo(map);

L.tileLayer("https://{s}.basemaps.cartocdn.com/light_nolabels/{z}/{x}/{y}{r}.png", {
  attribution:
    '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="https://carto.com/attributions">CARTO</a>',
  maxZoom: 19,
}).addTo(map);

map.createPane("labelPane");
map.getPane("labelPane").style.zIndex = 650;
map.getPane("labelPane").style.pointerEvents = "none";

L.tileLayer("https://{s}.basemaps.cartocdn.com/light_only_labels/{z}/{x}/{y}{r}.png", {
  attribution: "",
  maxZoom: 19,
  opacity: 0.95,
  pane: "labelPane",
}).addTo(map);

const canvasRenderer = L.canvas({ padding: 0.35 });
let pointResizeTimer;

function setStatus(text, kind = "loading") {
  el.statusText.textContent = text;
  el.statusDot.classList.toggle("ready", kind === "ready");
  el.statusDot.classList.toggle("error", kind === "error");
}

function formatNumber(value) {
  return new Intl.NumberFormat("en-US").format(value || 0);
}

function arcgisQueryUrl(serviceUrl, params = {}) {
  const query = new URLSearchParams({
    where: "1=1",
    outFields: "*",
    returnGeometry: "true",
    f: "geojson",
    ...params,
  });
  return `${serviceUrl}/query?${query.toString()}`;
}

async function fetchJson(url) {
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`${response.status} ${response.statusText}`);
  }
  return response.json();
}

async function fetchArcgisGeoJson(serviceUrl, params = {}) {
  return fetchJson(arcgisQueryUrl(serviceUrl, params));
}

async function fetchPagedFeatures(serviceUrl, params = {}, pageSize = 2000) {
  let offset = 0;
  const features = [];

  while (true) {
    const page = await fetchArcgisGeoJson(serviceUrl, {
      resultOffset: offset,
      resultRecordCount: pageSize,
      ...params,
    });

    features.push(...(page.features || []));
    if (!page.exceededTransferLimit && (page.features || []).length < pageSize) break;

    offset += pageSize;
    setStatus(`Loading collisions... ${formatNumber(features.length)} records`);
  }

  return {
    type: "FeatureCollection",
    features,
  };
}

function isKsi(feature) {
  const p = feature.properties || {};
  return Number(p.ksi || 0) > 0 || Number(p.death_cnt || 0) > 0 || Number(p.sus_serious_injry_cnt || 0) > 0;
}

function isFatal(feature) {
  const p = feature.properties || {};
  return Number(p.death_cnt || 0) > 0;
}

function isVru(feature) {
  const p = feature.properties || {};
  const mode = `${p.crash_mode || ""} ${p.crash_mode_2 || ""}`.toUpperCase();
  return (
    mode.includes("PED") ||
    mode.includes("BIKE") ||
    mode.includes("BICYCLE") ||
    Number(p.col_ped_cnt || 0) > 0 ||
    Number(p.col_bic_cnt || 0) > 0 ||
    String(p.ped_accident || "").toUpperCase() === "Y" ||
    String(p.bike_accident || "").toUpperCase() === "Y"
  );
}

function displayStreet(feature) {
  const p = feature.properties || {};
  const reportStreet = [p.rpt_street_name, p.rpt_street_sfx].filter(Boolean).join(" ").trim();
  return reportStreet || p.street_name || "Unknown street";
}

function filteredCollisions() {
  const year = el.yearFilter.value;
  const mode = el.modeFilter.value;

  return state.collisions.filter((feature) => {
    const p = feature.properties || {};
    if (year !== "all" && String(p.year) !== year) return false;
    if (mode === "ksi" && !isKsi(feature)) return false;
    if (mode === "vru" && !isVru(feature)) return false;
    if (mode === "fatal" && !isFatal(feature)) return false;
    return true;
  });
}

function popupForCollision(feature) {
  const p = feature.properties || {};
  const label = isFatal(feature) ? "Fatal crash" : isKsi(feature) ? "KSI crash" : isVru(feature) ? "Bike/Ped crash" : "Crash";
  return `
    <span class="popup-title">${label}</span>
    <span class="popup-row">${displayStreet(feature)}</span>
    <span class="popup-row">Year: ${p.year || "Unknown"}</span>
    <span class="popup-row">Mode: ${p.crash_mode || p.crash_mode_2 || "Unknown"}</span>
    <span class="popup-row">Speed group: ${p.posted_speed_group || "Unknown"}</span>
  `;
}

function pointRadius(kind, feature) {
  const zoom = map.getZoom();
  const zoomScale = Math.max(0.7, Math.min(1.15, zoom / 12));

  if (kind === "ksi") {
    return (isFatal(feature) ? 4.2 : 3.0) * zoomScale;
  }

  return 2.6 * zoomScale;
}

function updateCrashLayers() {
  const features = filteredCollisions();
  const heatPoints = [];
  const ksiFeatures = [];
  const vruFeatures = [];

  features.forEach((feature) => {
    const coordinates = feature.geometry && feature.geometry.coordinates;
    if (!coordinates) return;
    const [lng, lat] = coordinates;
    if (!Number.isFinite(lat) || !Number.isFinite(lng)) return;

    const intensity = isFatal(feature) ? 1.0 : isKsi(feature) ? 0.8 : isVru(feature) ? 0.45 : 0.18;
    heatPoints.push([lat, lng, intensity]);
    if (isKsi(feature)) ksiFeatures.push(feature);
    if (isVru(feature)) vruFeatures.push(feature);
  });

  if (state.layers.heat) map.removeLayer(state.layers.heat);
  state.layers.heat = L.heatLayer(heatPoints, {
    blur: 24,
    gradient: {
      0.18: "#f0d56b",
      0.55: "#f0a23a",
      0.8: "#d9483b",
      1.0: "#8d1c23",
    },
    max: 1,
    radius: 22,
  });

  if (state.layers.ksi) map.removeLayer(state.layers.ksi);
  state.layers.ksi = L.geoJSON(
    {
      type: "FeatureCollection",
      features: ksiFeatures,
    },
    {
      pointToLayer: (feature, latlng) =>
        L.circleMarker(latlng, {
          color: "#8d1c23",
          fillColor: isFatal(feature) ? "#8d1c23" : "#d9483b",
          fillOpacity: isFatal(feature) ? 0.74 : 0.58,
          radius: pointRadius("ksi", feature),
          renderer: canvasRenderer,
          weight: 0.8,
        }),
      onEachFeature: (feature, layer) => layer.bindPopup(popupForCollision(feature)),
    },
  );

  if (state.layers.vru) map.removeLayer(state.layers.vru);
  state.layers.vru = L.geoJSON(
    {
      type: "FeatureCollection",
      features: vruFeatures,
    },
    {
      pointToLayer: (feature, latlng) =>
        L.circleMarker(latlng, {
          color: "#0e5f56",
          fillColor: "#1f9a8a",
          fillOpacity: 0.54,
          radius: pointRadius("vru", feature),
          renderer: canvasRenderer,
          weight: 0.8,
        }),
      onEachFeature: (feature, layer) => layer.bindPopup(popupForCollision(feature)),
    },
  );

  applyLayerVisibility();
  updateMetrics(features);
}

function updateMetrics(features) {
  const ksi = features.filter(isKsi).length;
  const vru = features.filter(isVru).length;
  const fatal = features.filter(isFatal).length;

  el.metricCrashes.textContent = formatNumber(features.length);
  el.metricKsi.textContent = formatNumber(ksi);
  el.metricVru.textContent = formatNumber(vru);
  el.metricFatal.textContent = formatNumber(fatal);

  const byStreet = new Map();
  features.forEach((feature) => {
    const street = displayStreet(feature);
    byStreet.set(street, (byStreet.get(street) || 0) + 1);
  });

  const top = [...byStreet.entries()]
    .sort((a, b) => b[1] - a[1])
    .slice(0, 4);

  el.topStreetList.innerHTML = top
    .map(([street, count]) => `<li><strong>${street}</strong><span class="street-count">${formatNumber(count)} crashes</span></li>`)
    .join("");

  el.streetSubtitle.textContent = `${formatNumber(features.length)} filtered crashes`;
}

function makeLineLayer(data, color, weight = 4, opacity = 0.78) {
  return L.geoJSON(data, {
    style: (feature) => {
      const p = feature.properties || {};
      const joinCount = Number(p.Join_Count || p.Col_Cnt || p.Wtd_Col_All || 0);
      return {
        color,
        opacity,
        weight: Math.min(weight + joinCount * 0.18, 10),
      };
    },
    onEachFeature: (feature, layer) => {
      const p = feature.properties || {};
      layer.bindPopup(`
        <span class="popup-title">${p.STREETNAME || p.street_name || "Street segment"}</span>
        <span class="popup-row">${p.CLASS_CLEAN || "Roadway context"}</span>
        <span class="popup-row">Speed: ${p.SPEED || p.crash_speed_limit || "Unknown"}</span>
      `);
    },
  });
}

function makePointLayer(data, color, radius) {
  return L.geoJSON(data, {
    pointToLayer: (feature, latlng) =>
      L.circleMarker(latlng, {
        color,
        fillColor: color,
        fillOpacity: 0.5,
        radius,
        renderer: canvasRenderer,
        weight: 1,
      }),
  });
}

function makeEquityLayer(data) {
  return L.geoJSON(data, {
    style: (feature) => {
      const score = Number((feature.properties || {}).Perc_Equity_Rank_Scores || 0);
      return {
        color: "#7057a6",
        fillColor: score > 80 ? "#7057a6" : "#9a82c8",
        fillOpacity: score > 80 ? 0.12 : 0.06,
        opacity: 0.32,
        weight: 1,
      };
    },
  });
}

function syncControlsFromState() {
  document.querySelectorAll("[data-layer-toggle]").forEach((input) => {
    const key = input.dataset.layerToggle;
    input.checked = Boolean(state.toggles[key]);
  });

  document.querySelectorAll("[data-preset]").forEach((button) => {
    button.classList.toggle("active", button.dataset.preset === state.activePreset);
  });

  const preset = PRESETS[state.activePreset] || PRESETS.overview;
  el.insightTitle.textContent = preset.title;
  el.insightText.textContent = preset.text;

  document.querySelectorAll("[data-legend]").forEach((item) => {
    const key = item.dataset.legend;
    item.hidden = !Boolean(state.toggles[key]);
  });
}

function applyLayerVisibility() {
  const layerKeys = ["heat", "mvHin", "bpHin", "ksi", "vru", "predictive", "equity"];

  layerKeys.forEach((key) => {
    const layer = state.layers[key];
    if (!layer) return;
    const shouldShow = Boolean(state.toggles[key]);
    const isShown = map.hasLayer(layer);
    if (shouldShow && !isShown) map.addLayer(layer);
    if (!shouldShow && isShown) map.removeLayer(layer);
  });

  ["mvHin", "bpHin", "ksi", "vru"].forEach((key) => {
    const layer = state.layers[key];
    if (layer && map.hasLayer(layer) && layer.bringToFront) layer.bringToFront();
  });

  ["schools", "busStops", "bikeLanes"].forEach((key) => {
    const layer = state.layers[key];
    if (!layer) return;
    const isShown = map.hasLayer(layer);
    if (state.toggles.context && !isShown) map.addLayer(layer);
    if (!state.toggles.context && isShown) map.removeLayer(layer);
  });

  syncControlsFromState();
}

async function ensureOptionalLayer(key) {
  if (state.layers[key] || state.loading[key]) return state.loading[key];

  if (key === "predictive") {
    state.loading[key] = fetchPagedFeatures(SERVICES.predictive, {
      outFields:
        "OBJECTID,STREETNAME,CLASS_CLEAN,Network_ID,ColBic_Cnt_Int,ColPed_Cnt_Int,NoBkPed_Cnt_Int,Wtd_ColBic_Int,Wtd_ColPed_Int,Wtd_NoBkPed_Int",
    }).then((data) => {
      state.layers.predictive = makeLineLayer(data, "#7057a6", 1.25, 0.18);
    });
  }

  if (key === "equity") {
    state.loading[key] = fetchArcgisGeoJson(SERVICES.equity).then((data) => {
      state.layers.equity = makeEquityLayer(data);
    });
  }

  if (key === "context") {
    state.loading[key] = Promise.all([
      fetchPagedFeatures(SERVICES.busStops, { outFields: "OBJECTID,STOP_NAME" }),
      fetchArcgisGeoJson(SERVICES.schools, { outFields: "OBJECTID,NAME" }),
      fetchArcgisGeoJson(SERVICES.bikeLanes),
    ]).then(([busStops, schools, bikeLanes]) => {
      state.layers.busStops = makePointLayer(busStops, "#2f6fb2", 2.4);
      state.layers.schools = makePointLayer(schools, "#487b3f", 4);
      state.layers.bikeLanes = makeLineLayer(bikeLanes, "#f0a23a", 1.25, 0.36);
    });
  }

  await state.loading[key];
  state.loading[key] = null;
  return null;
}

function setupFilters() {
  Object.assign(state.toggles, DEFAULT_TOGGLES);
  state.activePreset = "overview";
  syncControlsFromState();

  state.years = [...new Set(state.collisions.map((feature) => feature.properties && feature.properties.year))]
    .filter(Boolean)
    .sort((a, b) => a - b);

  state.years.forEach((year) => {
    const option = document.createElement("option");
    option.value = String(year);
    option.textContent = String(year);
    el.yearFilter.append(option);
  });

  el.yearFilter.addEventListener("change", updateCrashLayers);
  el.modeFilter.addEventListener("change", updateCrashLayers);

  document.querySelectorAll("[data-preset]").forEach((button) => {
    button.addEventListener("click", async (event) => {
      const presetKey = event.currentTarget.dataset.preset;
      const preset = PRESETS[presetKey] || PRESETS.overview;
      state.activePreset = presetKey;
      Object.assign(state.toggles, preset.toggles);

      const optionalKeys = ["predictive", "equity", "context"].filter((key) => state.toggles[key]);
      if (optionalKeys.length) {
        setStatus("Loading selected context layers...");
        await Promise.all(optionalKeys.map((key) => ensureOptionalLayer(key)));
        setStatus("Ready: live safety layers loaded", "ready");
      }

      applyLayerVisibility();
    });
  });

  document.querySelectorAll("[data-layer-toggle]").forEach((input) => {
    input.addEventListener("change", async (event) => {
      const key = event.currentTarget.dataset.layerToggle;
      state.toggles[key] = event.currentTarget.checked;
      state.activePreset = "custom";
      if (event.currentTarget.checked && ["predictive", "equity", "context"].includes(key)) {
        setStatus(`Loading ${event.currentTarget.parentElement.textContent.trim()}...`);
        await ensureOptionalLayer(key);
        setStatus("Ready: live safety layers loaded", "ready");
      }
      applyLayerVisibility();
    });
  });
}

async function initialize() {
  try {
    Object.assign(state.toggles, DEFAULT_TOGGLES);
    state.activePreset = "overview";
    syncControlsFromState();
    setStatus("Loading public safety layers...");

    const [boundary, collisions, mvHin, bpHin] =
      await Promise.all([
        fetchArcgisGeoJson(SERVICES.cityBoundary),
        fetchPagedFeatures(SERVICES.collisions, {
          outFields: COLLISION_FIELDS,
        }),
        fetchArcgisGeoJson(SERVICES.mvHin),
        fetchArcgisGeoJson(SERVICES.bpHin),
      ]);

    state.layers.boundary = L.geoJSON(boundary, {
      style: {
        color: "#172638",
        fillOpacity: 0,
        opacity: 0.72,
        weight: 2,
      },
    }).addTo(map);

    state.collisions = collisions.features || [];
    state.layers.mvHin = makeLineLayer(mvHin, "#d9483b", 4, 0.82);
    state.layers.bpHin = makeLineLayer(bpHin, "#1f9a8a", 4, 0.86);

    map.on("zoomend", () => {
      window.clearTimeout(pointResizeTimer);
      pointResizeTimer = window.setTimeout(updateCrashLayers, 80);
    });

    setupFilters();
    updateCrashLayers();
    map.fitBounds(
      [
        [31.61, -106.6],
        [31.96, -106.17],
      ],
      { padding: [22, 22] },
    );

    setStatus("Ready: live safety layers loaded", "ready");
    el.lastUpdated.textContent = `${formatNumber(state.collisions.length)} public crash records loaded from Vision Zero services`;
  } catch (error) {
    setStatus(`Layer load failed: ${error.message}`, "error");
    console.error(error);
  }
}

initialize();
