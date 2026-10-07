  /* ---- route by water (for the lead line: "how far / how long by boat") ----
     A coarse grid over the lake (~9 m cells; a cell is water if any of its
     depth-grid cells is lake, so narrow sounds stay open). For a target, one
     Dijkstra run gives every water cell its distance by water to the target;
     after that the route from wherever the boat is is just "walk downhill",
     so it's redone for free on every GPS fix. Close to the shore costs a bit
     more, so the route keeps a few metres off land where it can. */
  var RT = null;            // {rf, w, h, water, cost, cellM}
  function routeGrid(){
    if (RT) return RT;
    var g = loadDepthGrid(); if (!g) return null;
    var cellM0 = WEB_METERS_PER_PX * IMG_W / DEPTH_W;
    var rf = Math.max(gridStep(), Math.round(9 / cellM0));   // (a big lake: coarser, see workGrid)
    var w = Math.ceil(DEPTH_W / rf), h = Math.ceil(DEPTH_H / rf);
    var water = new Uint8Array(w * h);
    for (var y = 0; y < DEPTH_H; y++) for (var x = 0; x < DEPTH_W; x++)
      if (g[y * DEPTH_W + x] !== 255) water[Math.floor(y / rf) * w + Math.floor(x / rf)] = 1;
    // distance to land (in cells, chamfer 1/1.4), for "keep off the shore"
    var d = new Float32Array(w * h), BIG = 1e6, i;
    for (i = 0; i < w * h; i++) d[i] = water[i] ? BIG : 0;
    function relax(i, j, c){ if (d[j] + c < d[i]) d[i] = d[j] + c; }
    for (y = 0; y < h; y++) for (x = 0; x < w; x++){ i = y * w + x; if (!d[i]) continue;
      if (x > 0) relax(i, i - 1, 1); if (y > 0){ relax(i, i - w, 1); if (x > 0) relax(i, i - w - 1, 1.4); if (x < w - 1) relax(i, i - w + 1, 1.4); } }
    for (y = h - 1; y >= 0; y--) for (x = w - 1; x >= 0; x--){ i = y * w + x; if (!d[i]) continue;
      if (x < w - 1) relax(i, i + 1, 1); if (y < h - 1){ relax(i, i + w, 1); if (x < w - 1) relax(i, i + w + 1, 1.4); if (x > 0) relax(i, i + w - 1, 1.4); } }
    var cost = new Float32Array(w * h);
    for (i = 0; i < w * h; i++) cost[i] = water[i] ? 1 + 1.5 / (1 + d[i]) : 0;
    RT = { rf: rf, w: w, h: h, water: water, cost: cost, cellM: cellM0 * rf };
    return RT;
  }
  function rtCell(x, y){ var R = RT; return { cx: Math.floor(x / IMG_W * DEPTH_W / R.rf), cy: Math.floor(y / IMG_H * DEPTH_H / R.rf) }; }
  function rtImg(cx, cy){ var R = RT; return { x: (cx + 0.5) * R.rf * IMG_W / DEPTH_W, y: (cy + 0.5) * R.rf * IMG_H / DEPTH_H }; }
  function rtNearestWater(c, maxR){      // the closest water cell (ring by ring), or null
    var R = RT;
    for (var r = 0; r <= maxR; r++) for (var dy = -r; dy <= r; dy++) for (var dx = -r; dx <= r; dx++){
      if (Math.max(Math.abs(dx), Math.abs(dy)) !== r) continue;
      var x = c.cx + dx, y = c.cy + dy;
      if (x >= 0 && y >= 0 && x < R.w && y < R.h && R.water[y * R.w + x]) return { cx: x, cy: y };
    }
    return null;
  }
  var rtField = null;       // {key, dist: Float32Array (m), tx, ty}
  function routeFieldTo(x, y){
    if (!routeGrid()) return null;
    var key = Math.round(x) + ',' + Math.round(y);
    if (rtField && rtField.key === key) return rtField;
    var R = RT, t = rtNearestWater(rtCell(x, y), 12); // (a lead line on the shore: the nearest water, up to ~100 m)
    if (!t) { rtField = { key: key, dist: null }; return rtField; }
    var n = R.w * R.h, dist = new Float32Array(n).fill(Infinity);
    // Dijkstra with a binary heap (8 neighbours)
    // (a cell can be queued more than once -- stale entries are skipped -- so the heap grows as needed)
    var hi = [], hp = [], hn = 0, popP = 0;
    function push(i, p){ var k = hn++; while (k > 0){ var q = (k - 1) >> 1; if (hp[q] <= p) break; hi[k] = hi[q]; hp[k] = hp[q]; k = q; } hi[k] = i; hp[k] = p; }
    function pop(){ var top = hi[0]; popP = hp[0]; var li = hi[--hn], lp = hp[hn], k = 0;
      while (true){ var c = 2 * k + 1; if (c >= hn) break; if (c + 1 < hn && hp[c + 1] < hp[c]) c++; if (hp[c] >= lp) break; hi[k] = hi[c]; hp[k] = hp[c]; k = c; }
      hi[k] = li; hp[k] = lp; return top; }
    var s = t.cy * R.w + t.cx; dist[s] = 0; push(s, 0);
    var DX = [1, -1, 0, 0, 1, 1, -1, -1], DY = [0, 0, 1, -1, 1, -1, 1, -1], DL = [1, 1, 1, 1, 1.4142, 1.4142, 1.4142, 1.4142];
    while (hn){
      var i = pop();
      if (popP > dist[i]) continue;          // stale: a shorter way here was already found
      var di = dist[i], ix = i % R.w, iy = (i - ix) / R.w;
      for (var k = 0; k < 8; k++){
        var x2 = ix + DX[k], y2 = iy + DY[k];
        if (x2 < 0 || y2 < 0 || x2 >= R.w || y2 >= R.h) continue;
        var j = y2 * R.w + x2; if (!R.water[j]) continue;
        var nd = di + DL[k] * R.cellM * (R.cost[i] + R.cost[j]) / 2;
        if (nd < dist[j]){ dist[j] = nd; push(j, dist[j]); }   // (queue the stored float32 value: queueing the float64 made
                                                                // "stale?" true when it rounded down -- the search stopped)
      }
    }
    rtField = { key: key, dist: dist, tx: t.cx, ty: t.cy };
    return rtField;
  }
  function waterLineClear(a, b){         // a straight line between two cells stays on water?
    var R = RT, n = Math.ceil(Math.max(Math.abs(b.cx - a.cx), Math.abs(b.cy - a.cy)) * 2) || 1;
    for (var k = 0; k <= n; k++){
      var x = Math.round(a.cx + (b.cx - a.cx) * k / n), y = Math.round(a.cy + (b.cy - a.cy) * k / n);
      if (!R.water[y * R.w + x]) return false;
    }
    return true;
  }
  // the route from (fx, fy) to the target of routeFieldTo(tx, ty), in map-image px, and its length (m)
  function routeFrom(fx, fy, tx, ty){
    var F = routeFieldTo(tx, ty);
    if (!F || !F.dist) return null;
    var R = RT, s = rtNearestWater(rtCell(fx, fy), 6);
    if (!s || !isFinite(F.dist[s.cy * R.w + s.cx])) return null;   // no way there by water
    var cells = [s], c = s, guard = R.w * R.h;
    while ((c.cx !== F.tx || c.cy !== F.ty) && guard--){      // downhill to the target
      var best = null, bd = F.dist[c.cy * R.w + c.cx];
      for (var dy = -1; dy <= 1; dy++) for (var dx = -1; dx <= 1; dx++){
        var x = c.cx + dx, y = c.cy + dy;
        if ((dx || dy) && x >= 0 && y >= 0 && x < R.w && y < R.h && F.dist[y * R.w + x] < bd){ bd = F.dist[y * R.w + x]; best = { cx: x, cy: y }; }
      }
      if (!best) break;
      cells.push(best); c = best;
    }
    // straighten: keep only the corners needed to stay on water
    var pts = [cells[0]], a = 0;
    while (a < cells.length - 1){
      var b = cells.length - 1;
      while (b > a + 1 && !waterLineClear(cells[a], cells[b])) b--;
      pts.push(cells[b]); a = b;
    }
    var img = pts.map(function(p){ return rtImg(p.cx, p.cy); });
    img[0] = { x: fx, y: fy }; img[img.length - 1] = { x: tx, y: ty };   // exactly from you to the lead line
    var m = 0;
    for (var k = 1; k < img.length; k++) m += Math.hypot(img[k].x - img[k - 1].x, img[k].y - img[k - 1].y) * WEB_METERS_PER_PX;
    return { pts: img, meters: m };
  }
  function depthAtLatLon(lat, lon){ var p = latLonToImgPx(lat, lon); return depthAtImgPx(p.x, p.y); }
  // (for the tests and tools/help_anim.py: depth / lake at a place, and screen <-> place)
  window.__ffGeo = {
    depthAt: depthAtLatLon,
    lake: function(lat, lon){ var p = latLonToImgPx(lat, lon); return isLakeAtImgPx(p.x, p.y); },
    screenOf: function(lat, lon){ var p = latLonToImgPx(lat, lon); return [originX + p.x * scale, originY + p.y * scale]; },
    at: function(x, y){ return imgPxToLatLon((x - originX) / scale, (y - originY) / scale); },
    // by water from one place to another: { m: metres, n: corners } or null (tests)
    route: function(lat1, lon1, lat2, lon2){ var a = latLonToImgPx(lat1, lon1), b = latLonToImgPx(lat2, lon2), r = routeFrom(a.x, a.y, b.x, b.y); return r ? { m: Math.round(r.meters), n: r.pts.length } : null; }
  };
  function fmtDepth(m){
    if (m == null) return '–';
    if (LAKE.depth.capped && m >= LAKE.depth.max - 0.05) return LAKE.depth.max + '+';
    return m.toFixed(1).replace('.', ',');
  }
  var SHOW_DEPTH_KEY = 'ffmap_show_depth_v1';
  var showDepth = true;
  try { if (localStorage.getItem(SHOW_DEPTH_KEY) === '0') showDepth = false; } catch(e){}

  function fmtKn(kn){ return (Math.round(kn * 10) / 10).toFixed(1).replace('.', ','); }

  var speedPill = document.getElementById('speedPill');
  var speedValEl = document.getElementById('speedVal');
  function updateSpeedPill(){
    var show = !!(lastFix && lastFix.onMap);
    speedPill.classList.toggle('show', show);
    if (show) speedValEl.textContent = fmtKn(currentSpeedKn());
    speedPill.classList.toggle('noDepth', !showDepth);
    if (show && showDepth) document.getElementById('depthVal').textContent = fmtDepth(depthAtImgPx(lastFix.px, lastFix.py));
  }

  /* ---- average speed ("snittfart") for the travel-time estimate ----
     Only time actually spent on the move counts (anchored/drifting is left
     out, so a fishing stop doesn't drag it down). It's the average of the
     most recent 2 minutes of such driving -- so it quickly follows how you
     drive right now -- and it isn't used until there are 2 minutes of
     driving behind it; until then the cruise speed from Settings is used.
     When you stop, it keeps the speed of your last 2 minutes of driving.
     Stored in 10-second pieces on the phone; forgotten after 12 h without
     driving (a new day / a new boat). Demo Mode keeps its own average in
     memory, so testing never touches the real one. */
  var AVG_KEY = 'ffmap_avg_speed_v2';       // v2: 10-second pieces (v1 was per minute)
  var AVG_BUCKET_MS = 10000;
  var AVG_WINDOW_S = 120, AVG_MIN_S = 120, AVG_MAX_AGE_MS = 12 * 3600 * 1000;
  try { localStorage.removeItem('ffmap_avg_speed_v1'); } catch(e){}
  var realAvg = { b: [] };
  try { var ra = JSON.parse(localStorage.getItem(AVG_KEY) || 'null'); if (ra && ra.b) realAvg = ra; } catch(e){}
  var DEMO_AVG_KEY = 'ffmap_demo_avg_v1';
  var demoAvg = { b: [] };
  if (demoMode){
    try { var da = JSON.parse(sessionStorage.getItem(DEMO_AVG_KEY) || 'null'); if (da && da.b) demoAvg = da; } catch(e){}
  }
  function saveDemoAvg(){ try { sessionStorage.setItem(DEMO_AVG_KEY, JSON.stringify(demoAvg)); } catch(e){} }
  var avgSaveTimer = null;
  function saveAvgNow(){
    if (avgSaveTimer){ clearTimeout(avgSaveTimer); avgSaveTimer = null; }
    try { localStorage.setItem(AVG_KEY, JSON.stringify(realAvg)); } catch(e){}
  }
  function saveAvgSoon(){ if (!avgSaveTimer) avgSaveTimer = setTimeout(saveAvgNow, 10000); }
  document.addEventListener('visibilitychange', function(){ if (document.visibilityState === 'hidden') saveAvgNow(); });
  window.addEventListener('pagehide', saveAvgNow); // e.g. the reload on rotation
  function activeAvg(){ return demoMode ? demoAvg : realAvg; }
  function addUnderway(dist, dt){
    var a = activeAvg();
    var m = Math.floor(Date.now() / AVG_BUCKET_MS);
    var last = a.b[a.b.length - 1];
    if (last && last.m === m){ last.d += dist; last.dt += dt; }
    else a.b.push({ m: m, d: dist, dt: dt });
    var tot = 0;
    for (var i = a.b.length - 1; i >= 0; i--){
      tot += a.b[i].dt;
      if (tot > AVG_WINDOW_S + 20){ a.b.splice(0, i); break; }
    }
    if (a === realAvg) saveAvgSoon(); else saveDemoAvg();
  }
  function avgSpeedInfo(){
    var a = activeAvg();
    if (!a.b.length) return null;
    if (Date.now() - a.b[a.b.length - 1].m * AVG_BUCKET_MS > AVG_MAX_AGE_MS){
      a.b = [];
      if (a === realAvg) saveAvgNow();
      return null;
    }
    var d = 0, dt = 0;
    for (var i = a.b.length - 1; i >= 0 && dt < AVG_WINDOW_S; i--){
      var take = Math.min(1, (AVG_WINDOW_S - dt) / a.b[i].dt); // only as much of the oldest piece as fits in 2 min
      d += a.b[i].d * take; dt += a.b[i].dt * take;
    }
    return { kn: dt ? d / dt * KN_PER_MS : 0, seconds: dt, ready: dt >= AVG_MIN_S };
  }

  var CRUISE_KEY = 'ffmap_cruise_kn_v1';
  var cruiseKn = 2;
  try { var cs = parseFloat(localStorage.getItem(CRUISE_KEY)); if (isFinite(cs) && cs >= 0.5 && cs <= 40) cruiseKn = cs; } catch(e){}
  // the speed the measuring tool uses
  function effectiveSpeed(){
    var a = avgSpeedInfo();
    if (a && a.ready && a.kn >= 0.5) return { kn: a.kn, src: 'avg' };
    return { kn: cruiseKn, src: 'cruise' };
  }

  var cruiseInput = document.getElementById('cruiseInput');
  cruiseInput.value = fmtKn(cruiseKn);
  function commitCruise(){
    var v = parseFloat(cruiseInput.value.replace(',', '.'));
    if (!isFinite(v) || v < 0.5 || v > 40){
      cruiseInput.classList.add('invalid');
      return;
    }
    cruiseKn = Math.round(v * 10) / 10;
    cruiseInput.value = fmtKn(cruiseKn);
    cruiseInput.classList.remove('invalid');
    try { localStorage.setItem(CRUISE_KEY, String(cruiseKn)); } catch(e){}
    updateSpeedSettings();
    updateMeasurePanel();
  }
  cruiseInput.addEventListener('blur', commitCruise);
  cruiseInput.addEventListener('keydown', function(e){ if (e.key === 'Enter') cruiseInput.blur(); });
  cruiseInput.addEventListener('input', function(){ cruiseInput.classList.remove('invalid'); });
  document.getElementById('avgResetBtn').addEventListener('click', function(){
    var a = activeAvg();
    a.b = [];
    if (a === realAvg) saveAvgNow();
    updateSpeedSettings();
    updateMeasurePanel();
  });
  function updateSpeedSettings(){
    var a = avgSpeedInfo();
    var valEl = document.getElementById('avgSpeedVal');
    var subEl = document.getElementById('avgSpeedSub');
    var demoTag = demoMode ? ' (demo)' : '';
    if (!a || a.seconds < 1){
      valEl.textContent = '–';
      subEl.textContent = 'Inte kört än' + demoTag;
    } else if (!a.ready){
      valEl.textContent = fmtKn(a.kn) + ' kn';
      subEl.textContent = 'Mäter… ' + Math.round(a.seconds) + ' av 120 s' + demoTag;
    } else {
      valEl.textContent = fmtKn(a.kn) + ' kn';
      subEl.textContent = 'Senaste 2 min i rörelse' + demoTag;
    }
    var e = effectiveSpeed();
    document.getElementById('speedUsedNote').innerHTML = 'Mätverktyget räknar just nu med <b>' +
      (e.src === 'avg' ? 'snittfarten ' : 'marschfarten ') + fmtKn(e.kn) + ' kn</b>';
  }
  updateSpeedSettings();

