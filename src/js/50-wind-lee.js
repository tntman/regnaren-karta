  /* ---- "Vind och lä" (Filter, off by default) ----
     From the weather's wind (direction + speed): for each bit of the lake, how far
     the wind has blown over open water to get there ("fetch", averaged over
     +-15 deg; the lake = Genesis + OpenStreetMap, on the route grid). Lee = where
     that's too short for waves: waves < ~5 cm by the usual fetch-limited wave
     formula, so the lee is big in light wind and shrinks in strong wind (6 m/s:
     100 m, 30-400 m; under 1,5 m/s the whole lake is calm). Lee: a lighter wash + a thin edge.
     Open water: "comets" drifting with the wind -- more, longer and faster the
     more open the water and the harder it blows. A screen canvas, redrawn with
     the map; the drifting runs ~30 frames/s only while it's on and visible. */
  var SHOW_WIND_KEY = 'ffmap_show_wind_v1';
  var windOn = false;
  try { windOn = localStorage.getItem(SHOW_WIND_KEY) === '1'; } catch(e){}
  var windCanvas = document.getElementById('windLayer'), wctx = windCanvas.getContext('2d');
  var windField = null, windParts = [], windLoop = null, windLastT = 0;
  function windNow(){
    if (!wx || !wx.data || !wx.data.current) return null;
    var c = wx.data.current; return { from: c.wind_direction_10m, ms: c.wind_speed_10m };
  }
  // how far from land (upwind) the water still counts as lee: fetch-limited wave height
  // ~ U*sqrt(F), so F = K / U^2 -- K set so that 6 m/s gives 100 m ("fishing-friendly"
  // lee, Filip's judgement; waves under ~3 cm), limited to 30-400 m
  var LEE_K = 3600;
  function leeDistM(ms){
    if (ms < 1.5) return Infinity;
    return Math.max(30, Math.min(400, LEE_K / (ms * ms)));
  }
  function computeWindField(){
    var w = windNow(); if (!w || !routeGrid()) return null;
    var key = Math.round(w.from / 5) * 5 + '/' + Math.round(w.ms * 2);
    if (windField && windField.key === key) return windField;
    var R = RT, n = R.w * R.h, fetch = new Float32Array(n), MAXM = 900, maxS = Math.ceil(MAXM / R.cellM);
    [-15, 0, 15].forEach(function(sp){
      var a = (w.from + sp) * Math.PI / 180, dx = Math.sin(a), dy = -Math.cos(a);   // towards where the wind comes from
      for (var cy = 0; cy < R.h; cy++) for (var cx = 0; cx < R.w; cx++){
        var i = cy * R.w + cx; if (!R.water[i]) continue;
        var f = MAXM;
        for (var s = 1; s <= maxS; s++){
          var x = Math.round(cx + dx * s), y = Math.round(cy + dy * s);
          if (x < 0 || y < 0 || x >= R.w || y >= R.h || !R.water[y * R.w + x]){ f = s * R.cellM; break; }
        }
        fetch[i] += f / 3;
      }
    });
    var leeD = leeDistM(w.ms);
    // A smooth fetch field at the work grid's size (the depth grid's; a big lake's coarser, workGrid): bilinear between route cells, then
    // blurred ~10 m inside the lake (no speckles / 9 m steps). The lee is then drawn per
    // screen pixel from this field (drawLeeView), so its edge stays smooth at any zoom.
    var wg = workGrid(), g = wg.g, GW = wg.W, GH = wg.H, N = GW * GH, rr = R.rf / wg.k;   // (rr: route cells in work-grid cells)
    var ff = new Float32Array(N), lk = new Float32Array(N);
    for (var y0 = 0; y0 < GH; y0++){
      var fy = (y0 + 0.5) / rr - 0.5, iy = Math.floor(fy), ty = fy - iy;
      for (var x0 = 0; x0 < GW; x0++){
        var j0 = y0 * GW + x0; if (g[j0] === 255) continue;
        lk[j0] = 1;
        var fx = (x0 + 0.5) / rr - 0.5, ix = Math.floor(fx), tx = fx - ix, sum = 0, ws = 0;
        for (var dy = 0; dy <= 1; dy++) for (var dx = 0; dx <= 1; dx++){
          var cx2 = ix + dx, cy2 = iy + dy;
          if (cx2 < 0 || cy2 < 0 || cx2 >= R.w || cy2 >= R.h || !R.water[cy2 * R.w + cx2]) continue;
          var wgt = (dx ? tx : 1 - tx) * (dy ? ty : 1 - ty); sum += fetch[cy2 * R.w + cx2] * wgt; ws += wgt;
        }
        ff[j0] = ws > 0 ? sum / ws : 0;
      }
    }
    var rad = Math.max(1, Math.round(10 / (WEB_METERS_PER_PX * IMG_W / GW)));
    function boxBlur(horiz){                      // weighted by the lake mask, so land doesn't pull it to 0
      var out = new Float32Array(N), L1 = horiz ? GW : GH, L2 = horiz ? GH : GW;
      for (var b = 0; b < L2; b++){
        var s = 0, sw = 0;
        for (var a0 = -rad; a0 < L1 + rad; a0++){
          var ai = a0 + rad; if (ai < L1){ var jj = horiz ? b * GW + ai : ai * GW + b; s += ff[jj] * lk[jj]; sw += lk[jj]; }
          var ao = a0 - rad - 1; if (ao >= 0 && ao < L1){ var jo = horiz ? b * GW + ao : ao * GW + b; s -= ff[jo] * lk[jo]; sw -= lk[jo]; }
          if (a0 >= 0 && a0 < L1){ var jc = horiz ? b * GW + a0 : a0 * GW + b; if (lk[jc]) out[jc] = sw > 0 ? s / sw : 0; }
        }
      }
      ff = out;
    }
    boxBlur(true); boxBlur(false); boxBlur(true); boxBlur(false);
    var nLee = 0, nWater = 0; for (var q = 0; q < N; q++){ if (lk[q]){ nWater++; if (ff[q] < leeD) nLee++; } }
    windField = { key: key, from: w.from, ms: w.ms, leeD: leeD, ff: ff, lk: lk, view: null, leeShare: nWater ? nLee / nWater : 0 };
    return windField;
  }
  // value of a depth-grid field at a map-picture point (bilinear)
  // how fine the per-point layers (lee, Kartanalys) are drawn: every css px when the map stands still,
  // every 2nd while it's dragged -- on a big (desktop) screen coarser, so it never counts many more
  // points than a phone does (~80 000 while dragging, ~700 000 standing still)
  function viewStep(W, H){
    var drag = stage.classList.contains('dragging');
    return Math.max(drag ? 2 : 1, Math.ceil(Math.sqrt(W * H / (drag ? 90000 : 700000))));
  }
  // a thin line drawn per point: half width `css` css px. A line thinner than the spacing of the drawn
  // points (while dragging: every 2nd px) comes out beaded -- a point lands on it or beside it. So
  // it's never thinner than one point each side, and fainter to match (the same amount of line).
  // -> [half width in points, strength]
  function edgeW(STEP, css){ var w = (css || 1.1) / STEP; return w >= 1 ? [w, 1] : [1, w]; }
  // a screen layer's canvas (lee, lightning, heat map, Kartanalys, shore, fog): the screen's size while it's on,
  // 1x1 when it's off -- a full one is 12 MB at 3x even when empty (tools/PLAN_MINNE.md). soft = drawn from
  // coarse pictures anyway: at most 2x (3x doesn't show, and is 2,25x the memory). -> the scale to draw at
  function fitLayer(c, on, soft){
    var dpr = window.devicePixelRatio || 1; if (soft) dpr = Math.min(2, dpr);
    var w = on ? Math.round(stage.clientWidth * dpr) : 1, h = on ? Math.round(stage.clientHeight * dpr) : 1;
    if (c.width !== w || c.height !== h){ c.width = w; c.height = h; }
    return dpr;
  }
  function gridAt(arr, ix, iy){     // (arr: a field on the work grid -- there once a wind field is)
    var GW = workGridC.W, GH = workGridC.H, gx = ix / IMG_W * GW - 0.5, gy = iy / IMG_H * GH - 0.5;
    var x0 = Math.floor(gx), y0 = Math.floor(gy), tx = gx - x0, ty = gy - y0;
    if (x0 < 0 || y0 < 0 || x0 >= GW - 1 || y0 >= GH - 1) return 0;
    var j = y0 * GW + x0;
    return (arr[j] * (1 - tx) + arr[j + 1] * tx) * (1 - ty) + (arr[j + GW] * (1 - tx) + arr[j + GW + 1] * tx) * ty;
  }
  // the lee for what's on screen, 1 point per css px (coarser while dragging, see viewStep; redone only when the view moves)
  function drawLeeView(F, W, H){
    var STEP = viewStep(W, H), vw = Math.ceil(W / STEP), vh = Math.ceil(H / STEP);
    var vkey = originX.toFixed(1) + ',' + originY.toFixed(1) + ',' + scale.toFixed(5) + ',' + W + 'x' + H + ',' + STEP;
    if (!F.view || F.view.key !== vkey){
      var cv = F.view ? F.view.cv : document.createElement('canvas');
      if (cv.width !== vw || cv.height !== vh){ cv.width = vw; cv.height = vh; }
      var c2 = cv.getContext('2d'), im = c2.createImageData(vw, vh), px = im.data;
      var lee = new Float32Array(vw * vh), lake = new Float32Array(vw * vh), ff = F.ff, lk = F.lk, D = F.leeD, EW = edgeW(STEP);
      for (var y = 0; y < vh; y++) for (var x = 0; x < vw; x++){
        var ix = (x * STEP + 1 - originX) / scale, iy = (y * STEP + 1 - originY) / scale, i = y * vw + x;
        var m = gridAt(lk, ix, iy); lake[i] = m;
        lee[i] = m < 0.02 ? 0 : (D - gridAt(ff, ix, iy) / m) / D;       // > 0 = lee
      }
      for (var y2 = 0; y2 < vh; y2++) for (var x2 = 0; x2 < vw; x2++){
        var i2 = y2 * vw + x2, m2 = Math.min(1, lake[i2] * 1.6), k = i2 * 4; if (m2 <= 0) continue;
        // (only water neighbours: along the shore there's no lee edge, as before)
        function nb(j){ return lake[j] > 0.3 ? lee[j] : lee[i2]; }
        var gx = (nb(x2 < vw - 1 ? i2 + 1 : i2) - nb(x2 > 0 ? i2 - 1 : i2)) / 2, gy = (nb(y2 < vh - 1 ? i2 + vw : i2) - nb(y2 > 0 ? i2 - vw : i2)) / 2;
        var d = lee[i2] / (Math.sqrt(gx * gx + gy * gy) + 1e-3);       // steps to the lee's edge
        var cov = d < -0.5 ? 0 : d > 0.5 ? 1 : d + 0.5, e = Math.max(0, 1 - Math.abs(d) / EW[0]) * EW[1];
        if (cov <= 0 && e <= 0) continue;
        // light blue, strongest at the edge and fading inwards (~22 css px)
        var a1 = (85 + 85 * Math.max(0, 1 - d * STEP / 22)) / 255 * cov * m2, a2 = 170 / 255 * e * m2, a = a2 + a1 * (1 - a2);
        if (a <= 0) continue;
        px[k] = (255 * a2 + 170 * a1 * (1 - a2)) / a; px[k + 1] = (255 * a2 + 215 * a1 * (1 - a2)) / a; px[k + 2] = 255; px[k + 3] = a * 255;
      }
      c2.putImageData(im, 0, 0);
      F.view = { key: vkey, cv: cv };
    }
    wctx.imageSmoothingEnabled = true;
    wctx.drawImage(F.view.cv, 0, 0, vw * STEP, vh * STEP);
  }
  function drawWind(){
    var W = stage.clientWidth, H = stage.clientHeight, F = windOn ? computeWindField() : null;
    var dpr = fitLayer(windCanvas, !!F, true);
    if (!F) return 0;
    wctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    wctx.clearRect(0, 0, W, H);
    if (!(W >= 2 && H >= 2)) return 0;          // (mid-rotation the map can be 0 px for a moment: nothing to draw)
    drawLeeView(F, W, H);
    if (F.ms < 1.5) return 0;
    // comets
    var force = Math.max(0.25, Math.min(1, F.ms / 8));
    var to = (F.from + 180) * Math.PI / 180, ux = Math.sin(to), uy = -Math.cos(to);
    var want = Math.round(Math.min(420, W * H / 1500) * (0.45 + 0.55 * force));
    while (windParts.length < want) windParts.push({ x: Math.random() * W, y: Math.random() * H, life: Math.random(), rate: 0.35 + Math.random() * 0.3 });
    windParts.length = want;
    var drawn = 0;
    wctx.lineCap = 'round';
    for (var i = 0; i < windParts.length; i++){
      var p = windParts[i];
      var ix = (p.x - originX) / scale, iy = (p.y - originY) / scale;
      var m = gridAt(F.lk, ix, iy); if (m < 0.6) continue;
      var e = Math.min(1, (gridAt(F.ff, ix, iy) / m - F.leeD) / 350); if (!(e > 0)) continue;
      var a = Math.sin(Math.PI * p.life) * (0.3 + 0.6 * e) * (0.5 + 0.5 * force);
      var L = (10 + 14 * e) * (0.6 + 0.4 * force);
      for (var k = 0; k < 5; k++){      // thin head, a bit thicker tail, fading backwards
        var t0 = k / 5, t1 = (k + 1) / 5;
        wctx.strokeStyle = 'rgba(255,255,255,' + (a * (1 - t0 * 0.75)).toFixed(3) + ')';
        wctx.lineWidth = 2.2 - 0.9 * t0;
        wctx.beginPath(); wctx.moveTo(p.x - ux * L * t0, p.y - uy * L * t0); wctx.lineTo(p.x - ux * L * t1, p.y - uy * L * t1); wctx.stroke();
      }
      drawn++;
    }
    return drawn;
  }
  function stepWind(now){
    windLoop = null;
    if (!windOn || document.visibilityState === 'hidden') return;
    if (now - windLastT >= 33){                                // ~30 frames/s
      var dt = windLastT ? Math.min(0.1, (now - windLastT) / 1000) : 0.033; windLastT = now;
      var F = windField, W = stage.clientWidth, H = stage.clientHeight;
      if (F){
        var to = (F.from + 180) * Math.PI / 180, v = (14 + 5 * F.ms) * dt;    // screen px per frame
        windParts.forEach(function(p){
          p.x += Math.sin(to) * v; p.y -= Math.cos(to) * v; p.life += dt * p.rate;
          if (p.life >= 1 || p.x < -30 || p.y < -30 || p.x > W + 30 || p.y > H + 30){ p.x = Math.random() * W; p.y = Math.random() * H; p.life = 0; }
        });
      }
      // (never let one bad frame stop the drifting for good -- the lee would then vanish after a
      //  rotation until the phone was turned again)
      try { drawWind(); } catch(e){ windField && (windField.view = null); }
    }
    windLoop = requestAnimationFrame(stepWind);
  }
  function applyWind(){
    windCanvas.classList.toggle('on', windOn);
    if (windOn && !windLoop){ windLastT = 0; windLoop = requestAnimationFrame(stepWind); }
    drawWind();
  }
  var toggleWindEl = document.getElementById('toggleWind');
  toggleWindEl.checked = windOn;
  toggleWindEl.addEventListener('change', function(){
    windOn = toggleWindEl.checked;
    try { localStorage.setItem(SHOW_WIND_KEY, windOn ? '1' : '0'); } catch(e){}
    applyWind();
  });
  document.addEventListener('visibilitychange', function(){ if (windOn) applyWind(); });
  window.addEventListener('pageshow', function(){ if (windOn) applyWind(); });
  window.__ffViewStep = function(W, H, drag){ var d = stage.classList.contains('dragging'); stage.classList.toggle('dragging', !!drag); var r = viewStep(W, H); stage.classList.toggle('dragging', d); return r; };
  window.__ffWind = function(){ var F = windField; return F ? { leeShare: F.leeShare, leeD: F.leeD, ms: F.ms, from: F.from, drawn: drawWind() } : null; }; // (for the tests)
  applyWind();
  document.addEventListener('visibilitychange', function(){ if (document.visibilityState === 'visible') fetchWeather(false); });

