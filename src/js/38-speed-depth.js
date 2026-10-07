  /* ================= Fart: knopmätare + snittfart =================
     Everything here stays on the phone -- nothing is written to the
     database. */
  var KN_PER_MS = 1.943844;                 // 1 m/s in knots
  var UNDERWAY_MS = 0.8 / KN_PER_MS;        // slower than 0.8 kn = drifting / GPS jitter, not "on the move"
  var MAX_PLAUSIBLE_MS = 25 / KN_PER_MS;    // faster than 25 kn = a GPS jump, ignored
  var speedFixes = [];   // recent fixes {t, lat, lon, acc} (last ~20 s)
  var speedSamples = []; // recent speeds {t, v} in m/s (last ~10 s)
  function resetSpeedTracking(){ speedFixes = []; speedSamples = []; }
  if (rotState && rotState.speed){ speedFixes = rotState.speed.f || []; speedSamples = rotState.speed.s || []; } // knot meter keeps going through a rotation

  // Called for every position (real GPS or demo). Prefers the speed the GPS
  // chip itself reports (accurate even at trolling speed); otherwise works
  // it out from how far we moved over the last ~6 s, treating movement
  // smaller than the GPS accuracy as standing still.
  function recordSpeed(lat, lon, accM, speedMs){
    var now = Date.now();
    var prev = speedFixes.length ? speedFixes[speedFixes.length - 1] : null;
    speedFixes.push({ t: now, lat: lat, lon: lon, acc: accM || 15 });
    while (speedFixes.length && now - speedFixes[0].t > 20000) speedFixes.shift();
    var v = (typeof speedMs === 'number' && isFinite(speedMs) && speedMs >= 0) ? speedMs : null;
    if (v === null){
      var base = null;
      for (var i = speedFixes.length - 2; i >= 0; i--){
        if (now - speedFixes[i].t >= 6000){ base = speedFixes[i]; break; }
      }
      if (!base) base = prev;
      if (base && now > base.t){
        var d = haversineKm(base.lat, base.lon, lat, lon) * 1000;
        var noise = Math.max(base.acc, accM || 15) * 0.5;
        v = d <= noise ? 0 : d / ((now - base.t) / 1000);
      }
    }
    if (v === null || v > MAX_PLAUSIBLE_MS) return;
    speedSamples.push({ t: now, v: v });
    while (speedSamples.length && now - speedSamples[0].t > 10000) speedSamples.shift();
    if (prev){
      var dt = (now - prev.t) / 1000;
      if (dt > 0 && dt <= 30 && v >= UNDERWAY_MS) addUnderway(v * dt, dt);
    }
    updateSpeedPill();
  }
  // What the knot meter shows: the average of the last ~8 s. No new position
  // for that long means we're not moving (phones send fewer fixes when still).
  function currentSpeedKn(){
    var now = Date.now(), sum = 0, n = 0;
    speedSamples.forEach(function(x){ if (now - x.t <= 8000){ sum += x.v; n++; } });
    if (!n) return 0;
    var kn = sum / n * KN_PER_MS;
    return kn < 0.3 ? 0 : kn;
  }
  /* ---- which way you're going: the arrow in your GPS dot ----
     Uses the heading the GPS chip reports while moving when there is one,
     otherwise the direction from a recent position that's clearly far enough
     behind you (~6 m+, so GPS jitter doesn't spin it). Only updated while
     you're under way (knot meter 0,8 kn or more); when you stop it keeps
     pointing the last way you went -- remembered on the phone, so it's the
     same after a restart or a rotation. (Before the very first trip: north.) */
  var HEADING_KEY = 'ffmap_last_heading_v1';
  var headingDeg = 0;
  try { var savedHdg = parseFloat(localStorage.getItem(HEADING_KEY)); if (isFinite(savedHdg)) headingDeg = savedHdg; } catch(e){}
  var arrowAngle = null, lastHeadingSave = 0;
  var MOVING_KN = 0.8;
  function bearingDeg(lat1, lon1, lat2, lon2){
    var r = Math.PI / 180, p1 = lat1 * r, p2 = lat2 * r, dl = (lon2 - lon1) * r;
    var y = Math.sin(dl) * Math.cos(p2);
    var x = Math.cos(p1) * Math.sin(p2) - Math.sin(p1) * Math.cos(p2) * Math.cos(dl);
    return (Math.atan2(y, x) / r + 360) % 360;
  }
  function updateHeading(lat, lon, gpsHeading){
    if (currentSpeedKn() >= MOVING_KN){
      var h = (typeof gpsHeading === 'number' && isFinite(gpsHeading) && gpsHeading >= 0) ? gpsHeading : null;
      if (h === null){
        for (var i = speedFixes.length - 2; i >= 0; i--){
          var f = speedFixes[i];
          if (haversineKm(f.lat, f.lon, lat, lon) * 1000 >= Math.max(6, (f.acc || 15) * 0.5)){ h = bearingDeg(f.lat, f.lon, lat, lon); break; }
        }
      }
      if (h !== null){
        headingDeg = h;
        var now = Date.now();
        if (now - lastHeadingSave > 3000){ lastHeadingSave = now; try { localStorage.setItem(HEADING_KEY, headingDeg.toFixed(1)); } catch(e){} }
      }
    }
    drawHeadingArrow();
  }
  function drawHeadingArrow(){
    var arrow = document.getElementById('dotArrow');
    if (arrowAngle === null){
      arrowAngle = headingDeg; // first time: point the right way at once, no swing from north
      arrow.style.transition = 'none';
      arrow.style.transform = 'rotate(' + arrowAngle.toFixed(1) + 'deg)';
      void arrow.offsetWidth;
      arrow.style.transition = '';
      return;
    }
    arrowAngle += ((headingDeg - arrowAngle) % 360 + 540) % 360 - 180; // the short way round
    arrow.style.transform = 'rotate(' + arrowAngle.toFixed(1) + 'deg)';
  }
  /* ---- depth ("Djup"): under you, and at any spot ----
     A grid over the map image (lakes/<id>/depth_*.txt, size in lake.json),
     one byte per cell = depth / step (Regnaren: 0-10 m in 4 cm steps -- its
     map's own data stops at 10 m, so deeper = "10+"); 255 = land, and runs
     of land are packed (251, count lo, count hi), all base64. Fetched at
     start (the service worker keeps it for offline starts), unpacked once. */
  var DEPTH_W = LAKE.depth.w, DEPTH_H = LAKE.depth.h, DEPTH_STEP = LAKE.depth.step;
  var DEPTH_B64 = null;
  var depthGrid = null;
  function fetchDepthGrid(){
    fetch(lakeUrl(LAKE_DIR + LAKE.depth.file)).then(function(r){ return r.ok ? r.text() : null; }).then(function(t){
      if (!t) return;
      DEPTH_B64 = t.trim();
      if (typeof updateProbeText === 'function') updateProbeText();
      if (typeof updateSpeedPill === 'function') updateSpeedPill();
      if (typeof shoreDraw === 'function') shoreDraw();   // (Strandlinje needs the lake's outline)
    }).catch(function(e){ console.warn('djupdata', e); });
  }
  fetchDepthGrid();
  function loadDepthGrid(){
    if (depthGrid) return depthGrid;
    if (!DEPTH_B64) return null; // (still on its way)
    try {
      var bin = atob(DEPTH_B64), g = new Uint8Array(DEPTH_W * DEPTH_H), j = 0;
      for (var i = 0; i < bin.length; i++){
        var v = bin.charCodeAt(i);
        if (v === 251 || v === 253){ // a run of land (255) / of lake without depth data (252)
          var n = bin.charCodeAt(i + 1) | (bin.charCodeAt(i + 2) << 8); g.fill(v === 251 ? 255 : 252, j, j + n); j += n; i += 2;
        }
        else g[j++] = v;
      }
      depthGrid = g;
    } catch(e){ console.warn('djupdata', e); }
    return depthGrid;
  }
  // the grid that things for the whole lake are worked out on (Kartanalys, Vind och lä, the route): at most ~1,5 M
  // cells -- a bigger lake's depth cells are taken 2x2 (4x4 ...) together. Mälaren: 3,9 M cells of 10 m -> 1 M of 20 m
  // (it crashed the phone, tools/PLAN_MINNE.md); the other lakes: the depth grid itself. The depth (lodet) stays exact.
  var GRID_MAX = 1.5e6, workGridC = null;
  function gridStep(){ for (var k = 1; (DEPTH_W / k) * (DEPTH_H / k) > GRID_MAX; k *= 2); return k; }
  function workGrid(){              // -> { g (like the depth grid: depth steps, 252 lake without depth, 255 land), W, H, k }
    if (workGridC) return workGridC;
    var g = loadDepthGrid(); if (!g) return null;
    var k = gridStep();
    if (k === 1) return (workGridC = { g: g, W: DEPTH_W, H: DEPTH_H, k: 1 });
    var W = Math.ceil(DEPTH_W / k), H = Math.ceil(DEPTH_H / k), o = new Uint8Array(W * H);
    for (var y = 0; y < H; y++) for (var x = 0; x < W; x++){
      var n = 0, nl = 0, nw = 0, s = 0;
      for (var yy = y * k; yy < Math.min(DEPTH_H, y * k + k); yy++) for (var xx = x * k; xx < Math.min(DEPTH_W, x * k + k); xx++){
        var v = g[yy * DEPTH_W + xx]; n++; if (v !== 255){ nl++; if (v <= 250){ nw++; s += v; } }
      }
      // mostly land: land; half or more with depth: their mean depth; else lake without depth
      o[y * W + x] = nl * 2 < n ? 255 : nw * 2 >= n ? Math.round(s / nw) : 252;
    }
    return (workGridC = { g: o, W: W, H: H, k: k });
  }
  function depthAtImgPx(x, y){
    var g = loadDepthGrid();
    if (!g) return null;
    var gx = x / IMG_W * DEPTH_W - 0.5, gy = y / IMG_H * DEPTH_H - 0.5;
    var x0 = Math.floor(gx), y0 = Math.floor(gy), fx = gx - x0, fy = gy - y0;
    var sum = 0, wsum = 0;
    for (var dy = 0; dy <= 1; dy++) for (var dx = 0; dx <= 1; dx++){
      var xi = x0 + dx, yi = y0 + dy;
      if (xi < 0 || yi < 0 || xi >= DEPTH_W || yi >= DEPTH_H) continue;
      var v = g[yi * DEPTH_W + xi];
      if (v > 250) continue; // land (255), or lake without depth data (252)
      var w = (dx ? fx : 1 - fx) * (dy ? fy : 1 - fy);
      sum += v * w; wsum += w;
    }
    if (wsum < 0.2) return null; // (on land / no depth data / outside the map)
    return sum / wsum * DEPTH_STEP;
  }
  // lake or land? The lake = Genesis' data + the lake's outline from OpenStreetMap
  // (Lantmäteriet), so this also knows the parts nobody has logged a depth for.
  function isLakeAtImgPx(x, y){
    var g = loadDepthGrid();
    if (!g) return false;
    var xi = Math.floor(x / IMG_W * DEPTH_W), yi = Math.floor(y / IMG_H * DEPTH_H);
    if (xi < 0 || yi < 0 || xi >= DEPTH_W || yi >= DEPTH_H) return false;
    return g[yi * DEPTH_W + xi] !== 255;
  }

