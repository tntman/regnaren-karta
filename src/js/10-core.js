(function(){
  "use strict";

  /* ---------- lakes ------------------------------------------------
     Every lake has its own folder lakes/<id>/ (map pictures, depth data,
     thumbnails, detail tiles) and a lake.json that the build embeds here.
     One page serves all lakes: the chosen lake is remembered on the phone
     (?lake=<id> in the address picks one directly); switching lakes in the
     menu reloads the page with the new one. Waypoints, boats and settings
     in Firestore are tagged with the lake id, so lakes never mix. */
  var LAKES = __LAKES__;
  var LAKE_KEY = 'ffmap_lake_v1';
  var LAKE_ID = (function(){
    function known(id){ return LAKES.some(function(l){ return l.id === id; }); }
    var want = null;
    try { var m = /[?&]lake=([a-z0-9_-]+)/.exec(location.search); if (m) want = m[1]; } catch(e){}
    if (!known(want)){ try { want = localStorage.getItem(LAKE_KEY); } catch(e){} }
    return known(want) ? want : LAKES[0].id;
  })();
  try { localStorage.setItem(LAKE_KEY, LAKE_ID); } catch(e){}
  var LAKE = LAKES.filter(function(l){ return l.id === LAKE_ID; })[0];
  var LAKE_DIR = 'lakes/' + LAKE_ID + '/';
  // Hooks for the app (src/js/11-native.js on the branch "app" replaces them) -- on the web they do nothing.
  // Don't remove them. lakeUrl: every lake file is loaded through it; lakeImgError: a map picture / detail
  // piece that failed -- true = the app dealt with it, skip the usual handling.
  function lakeUrl(p){ return p; }
  function lakeImgError(el){ return false; }
  // Per-lake storage key. Regnaren (the first lake) keeps its old key, so
  // nothing already saved on anyone's phone is lost.
  function lakeKey(legacy, name){ return LAKE_ID === 'regnaren' ? legacy : 'lake_' + LAKE_ID + '_' + name; }

  /* ---------- Testläge = Demo Mode (tools/NOTES_TESTLAGE.md) ----------
     Decided once, when the page loads (switching Demo Mode reloads the page). In the test mode
     everything shared goes to a separate Firebase project (FIREBASE_CONFIG, 14-spots.js) and the
     phone's copies of shared data have their own keys (testKey), so test and real never mix.
     Demo Mode switches itself off after 15 min (32-demo.js) -- an old start time = off. */
  var DEMO_KEY = 'regnaren_demo_mode_v1', DEMO_SINCE_KEY = 'regnaren_demo_since_v1', DEMO_MAX_MS = 15 * 60 * 1000;
  var TEST_MODE = false;
  try {
    TEST_MODE = localStorage.getItem(DEMO_KEY) === '1' && Date.now() - (+localStorage.getItem(DEMO_SINCE_KEY) || 0) < DEMO_MAX_MS;
    if (!TEST_MODE && localStorage.getItem(DEMO_KEY) === '1'){ localStorage.setItem(DEMO_KEY, '0'); localStorage.removeItem(DEMO_SINCE_KEY); }
  } catch(e){}
  function testKey(k){ return TEST_MODE ? k + '_test' : k; }

  /* ---------- geo referencing --------------------------------------
     A lake's map image is a crop of a standard Web-Mercator slippy-tile
     canvas (256px tiles) at geo.zoom: the crop's top-left corner is at
     global pixel (originX, originY) and it was geo.fullW px wide at full
     resolution. The web-served image is a uniformly downscaled copy of
     that same crop, so a single scale factor (IMG_W / fullW) relates the
     two pixel spaces. ------- */
  var TILE = 256;
  var MAX_ZOOM = 18.6;                  // how far you can zoom in, the same on every lake
  var ZOOM = LAKE.geo.zoom;
  var ORIGIN_X = LAKE.geo.originX, ORIGIN_Y = LAKE.geo.originY;
  var FULLRES_W = LAKE.geo.fullW;
  var IMG_W = LAKE.geo.imgW, IMG_H = LAKE.geo.imgH; // natural size of the map pictures
  var S = IMG_W / FULLRES_W;
  var N_TILES = Math.pow(2, ZOOM);
  var ORIG_METERS_PER_PX = LAKE.geo.metersPerPx; // at full native resolution
  var WEB_METERS_PER_PX = ORIG_METERS_PER_PX / S;
  var LAKE_CENTER_LAT = LAKE.center[0], LAKE_CENTER_LON = LAKE.center[1];

  function latLonToImgPx(lat, lon){
    var xGlobal = (lon + 180) / 360 * N_TILES * TILE;
    var latRad = lat * Math.PI / 180;
    var yGlobal = (1 - Math.log(Math.tan(latRad) + 1/Math.cos(latRad)) / Math.PI) / 2 * N_TILES * TILE;
    var xFull = xGlobal - ORIGIN_X;
    var yFull = yGlobal - ORIGIN_Y;
    return { x: xFull * S, y: yFull * S };
  }

  function imgPxToLatLon(x, y){
    var xFull = x / S, yFull = y / S;
    var xGlobal = xFull + ORIGIN_X;
    var yGlobal = yFull + ORIGIN_Y;
    var lon = xGlobal / (N_TILES * TILE) * 360 - 180;
    var yr = yGlobal / (N_TILES * TILE);
    var lat = Math.atan(Math.sinh(Math.PI * (1 - 2 * yr))) * 180 / Math.PI;
    return { lat: lat, lon: lon };
  }

  // the lake's name wherever the page shows it
  document.getElementById('lakeTitle').textContent = LAKE.name.toUpperCase();
  document.getElementById('mapImg').alt = 'Djupkarta över sjön ' + LAKE.name;
  document.getElementById('wxTitle').textContent = 'Väder vid ' + LAKE.name;
  document.getElementById('wxCard').setAttribute('aria-label', 'Väder vid ' + LAKE.name);

  function haversineKm(lat1, lon1, lat2, lon2){
    var R = 6371;
    var dLat = (lat2 - lat1) * Math.PI / 180;
    var dLon = (lon2 - lon1) * Math.PI / 180;
    var a = Math.sin(dLat/2)*Math.sin(dLat/2) +
            Math.cos(lat1*Math.PI/180)*Math.cos(lat2*Math.PI/180)*
            Math.sin(dLon/2)*Math.sin(dLon/2);
    return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
  }

