  /* ---- "Blixtar" (Filter, on by default) ----
     Lightning strikes in real time from FMI (the Finnish Meteorological Institute's
     open data: it covers Sweden too, no key, CC BY 4.0, a few minutes' delay).
     Every 2 min while it's on and the app is showing: the last 30 min, ~40 km round
     the lake. Shown: a warning under the weather chip (nearest strike within 30 km,
     direction, how long ago; orange, red under 10 km), a small radar under Filter
     (you in the middle, 30 km round, north up), ⚡ on the map where it struck
     (yellow 0-5 min, orange 5-15, grey and fading to 30; new ones flash) and an
     arrow at the screen edge towards the nearest one when it's off screen.
     Distances from you when you're at the lake, otherwise from the lake's middle. */
  var SHOW_LT_KEY = 'ffmap_show_lightning_v1';
  var ltOn = true;
  try { ltOn = localStorage.getItem(SHOW_LT_KEY) !== '0'; } catch(e){ ltOn = true; }
  var LT_WIN_MIN = 30, LT_RANGE_KM = 30, LT_RED_KM = 10, LT_POLL_MS = 120000;
  var ltCanvas = document.getElementById('ltLayer'), lctx = ltCanvas.getContext('2d');
  var ltPill = document.getElementById('ltPill'), ltRadar = document.getElementById('ltRadar'), ltRadarCv = document.getElementById('ltRadarCv');
  var ltStrikes = [], ltRec = [], ltNear = null, ltFetchedAt = 0, ltFetching = false, ltFlash = { from: 0, keys: {} }, ltAnim = null;
  function ltUrl(){
    var dLat = 0.4, dLon = 0.75, now = Date.now();
    function iso(ms){ return new Date(ms).toISOString().slice(0, 19) + 'Z'; }
    return 'https://opendata.fmi.fi/wfs?service=WFS&version=2.0.0&request=getFeature&storedquery_id=fmi::observations::lightning::simple' +
      '&bbox=' + [LAKE_CENTER_LON - dLon, LAKE_CENTER_LAT - dLat, LAKE_CENTER_LON + dLon, LAKE_CENTER_LAT + dLat].map(function(v){ return v.toFixed(3); }).join(',') +
      '&parameters=peak_current&starttime=' + iso(now - (LT_WIN_MIN + 1) * 60000) + '&endtime=' + iso(now);
  }
  // FMI's XML: one element per strike, <gml:pos>lat lon</gml:pos> ... <BsWfs:Time>
  function ltParse(xml){
    var out = [], seen = {}, m, re = /<gml:pos>\s*([-\d.]+)\s+([-\d.]+)\s*<\/gml:pos>[\s\S]*?<BsWfs:Time>([^<]+)<\/BsWfs:Time>/g;
    while ((m = re.exec(xml))){
      var t = Date.parse(m[3]), k = m[1] + ',' + m[2] + ',' + m[3];
      if (!isFinite(t) || seen[k]) continue;
      seen[k] = 1; out.push({ lat: +m[1], lon: +m[2], t: t, k: k });
    }
    return out;
  }
  // strikes are fetched while they're shown on the map OR the alarm is on (the alarm never depends on the
  // "Blixtar" switch in Filter -- that only shows / hides them on the map)
  function ltWatch(){ return ltOn || !!ltAlarm.km; }
  function ltFetch(){
    if (!ltWatch() || ltFetching) return;
    if (TEST_MODE){ ltApply(testStrikes()); return; }   // (the test mode: only the admin's made-up strikes, never FMI -- 37-testmode.js)
    if (typeof fetch !== 'function') return;
    ltFetching = true;
    fetch(ltUrl()).then(function(r){ return r.ok ? r.text() : null; }).then(function(x){
      ltFetching = false;
      if (x != null) ltApply(ltParse(x));
    }).catch(function(){ ltFetching = false; });
  }
  // new strikes in: the alarm, the flash of the new ones, the map
  function ltApply(list){
    if (!ltWatch()) return;
    var had = {}, first = !ltFetchedAt, fresh = {}, n = 0;
    ltStrikes.forEach(function(s){ had[s.k] = 1; });
    ltStrikes = list; ltFetchedAt = Date.now();
    ltCheckAlarm();
    ltStrikes.forEach(function(s){ if (!had[s.k] && Date.now() - s.t < 5 * 60000){ fresh[s.k] = 1; n++; } });
    if (!first && n){ ltFlash = { from: Date.now(), keys: fresh }; if (!ltAnim) ltAnim = requestAnimationFrame(ltPulse); }
    ltRender();
  }
  function ltRef(){
    if (lastOwnLatLon && isNearLake(lastOwnLatLon.lat, lastOwnLatLon.lon)) return lastOwnLatLon;
    return { lat: LAKE_CENTER_LAT, lon: LAKE_CENTER_LON };
  }
  function ltBearing(a, b){
    var p = Math.PI / 180, y = Math.sin((b.lon - a.lon) * p) * Math.cos(b.lat * p),
        x = Math.cos(a.lat * p) * Math.sin(b.lat * p) - Math.sin(a.lat * p) * Math.cos(b.lat * p) * Math.cos((b.lon - a.lon) * p);
    return (Math.atan2(y, x) / p + 360) % 360;
  }
  function ltKm(km){ return km < 10 ? km.toFixed(1).replace('.', ',') : String(Math.round(km)); }
  function ltStyle(age){   // colour / size / opacity by age (minutes)
    if (age < 5) return { c: '255,236,80', s: 11, a: 1 };
    if (age < 15) return { c: '255,150,40', s: 9, a: 0.9 };
    return { c: '215,215,215', s: 7, a: Math.max(0.2, 0.82 - (age - 15) * 0.04) };
  }
  function ltBolt(ctx, x, y, s, rgb, a){
    var P = [[0.15, -1], [-0.45, 0.1], [-0.02, 0.1], [-0.2, 1], [0.5, -0.2], [0.05, -0.2], [0.3, -1]];
    ctx.beginPath();
    P.forEach(function(q, i){ var px = x + q[0] * s, py = y + q[1] * s; if (i) ctx.lineTo(px, py); else ctx.moveTo(px, py); });
    ctx.closePath();
    ctx.lineJoin = 'round'; ctx.lineWidth = Math.max(2, s * 0.28);
    ctx.strokeStyle = 'rgba(8,20,30,' + a + ')'; ctx.stroke();     // dark edge: shows on yellow/red map colours too
    ctx.fillStyle = 'rgba(' + rgb + ',' + a + ')'; ctx.fill();
  }
  // everything but the map symbols: the list, the warning and the radar
  function ltRender(){
    var now = Date.now(), ref = ltRef(), rec = [];
    if (ltOn) ltStrikes.forEach(function(s){
      var age = (now - s.t) / 60000;
      if (age < -2 || age > LT_WIN_MIN) return;
      rec.push({ s: s, age: Math.max(0, age), km: haversineKm(ref.lat, ref.lon, s.lat, s.lon), br: ltBearing(ref, s) });
    });
    rec.sort(function(a, b){ return b.age - a.age; });            // oldest first, newest drawn on top
    ltRec = rec;
    var inRange = rec.filter(function(r){ return r.km <= LT_RANGE_KM; });
    ltNear = null; var newest = Infinity;
    inRange.forEach(function(r){ if (!ltNear || r.km < ltNear.km) ltNear = r; newest = Math.min(newest, r.age); });
    ltPill.classList.toggle('show', !!ltNear);
    ltRadar.classList.toggle('show', !!ltNear);
    ltCanvas.classList.toggle('on', ltOn);
    if (ltNear){
      ltPill.classList.toggle('red', ltNear.km < LT_RED_KM);
      document.getElementById('ltPillMain').textContent = 'Åska ' + ltKm(ltNear.km) + ' km ' + wxCompass(ltNear.br);
      document.getElementById('ltPillSub').textContent = (newest < 1 ? 'senaste nyss' : 'senaste ' + Math.round(newest) + ' min sedan') +
        (now - ltFetchedAt > 3 * LT_POLL_MS ? ' · ej uppdaterat' : '');
      // radar
      var c = ltRadarCv.getContext('2d'), Wc = ltRadarCv.width, R = Wc / 2 - 2, cx = Wc / 2, cy = Wc / 2, k = Wc / 100;
      c.clearRect(0, 0, Wc, Wc);
      c.beginPath(); c.arc(cx, cy, R, 0, 2 * Math.PI); c.fillStyle = 'rgba(11,42,58,.88)'; c.fill();
      c.lineWidth = k; c.strokeStyle = 'rgba(255,255,255,.3)'; c.stroke();
      [10, 20].forEach(function(rk){ c.beginPath(); c.arc(cx, cy, R * rk / LT_RANGE_KM, 0, 2 * Math.PI); c.strokeStyle = 'rgba(255,255,255,.2)'; c.stroke(); });
      c.font = '700 ' + (9 * k) + 'px Calibri,"Segoe UI",sans-serif'; c.textAlign = 'center'; c.fillStyle = 'rgba(255,255,255,.65)';
      c.fillText('N', cx, cy - R + 10 * k);
      c.font = (8 * k) + 'px Calibri,"Segoe UI",sans-serif'; c.fillStyle = 'rgba(255,255,255,.45)';
      c.fillText('10', cx + R / 3 * 0.71 + 6 * k, cy + R / 3 * 0.71 + 6 * k);
      inRange.forEach(function(r){
        var st = ltStyle(r.age), a = r.br * Math.PI / 180, d = R * r.km / LT_RANGE_KM;
        c.beginPath(); c.arc(cx + Math.sin(a) * d, cy - Math.cos(a) * d, (r.age < 5 ? 2.6 : 2) * k, 0, 2 * Math.PI);
        c.fillStyle = 'rgba(' + st.c + ',' + Math.max(0.35, st.a) + ')'; c.fill();
      });
      c.beginPath(); c.arc(cx, cy, 3.5 * k, 0, 2 * Math.PI); c.fillStyle = '#E8A33D'; c.fill(); c.strokeStyle = '#fff'; c.lineWidth = k; c.stroke();
    }
    ltDrawMap();
  }
  // the strikes on the map (screen canvas, redrawn with the map) + the edge marker
  function ltDrawMap(){
    var dpr = window.devicePixelRatio || 1, W = stage.clientWidth, H = stage.clientHeight, now = Date.now();
    if (ltCanvas.width !== Math.round(W * dpr) || ltCanvas.height !== Math.round(H * dpr)){
      ltCanvas.width = Math.round(W * dpr); ltCanvas.height = Math.round(H * dpr);
    }
    lctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    lctx.clearRect(0, 0, W, H);
    var drawn = 0, edge = null;
    if (!ltOn) return { drawn: 0, edge: null };
    var fl = (now - ltFlash.from) / 2500;                           // new strikes: a ring spreading out, 2,5 s
    ltRec.forEach(function(r){
      var p = latLonToImgPx(r.s.lat, r.s.lon), x = originX + p.x * scale, y = originY + p.y * scale;
      if (x < -20 || y < -20 || x > W + 20 || y > H + 20) return;
      var st = ltStyle(r.age);
      if (fl < 1 && ltFlash.keys[r.s.k]){
        lctx.beginPath(); lctx.arc(x, y, 10 + 40 * fl, 0, 2 * Math.PI);
        lctx.strokeStyle = 'rgba(255,240,120,' + (0.9 * (1 - fl)).toFixed(3) + ')'; lctx.lineWidth = 3; lctx.stroke();
      }
      if (r.age < 2){
        [[30, 0.35], [20, 0.62]].forEach(function(q){
          lctx.beginPath(); lctx.arc(x, y, q[0], 0, 2 * Math.PI); lctx.strokeStyle = 'rgba(255,240,120,' + q[1] + ')'; lctx.lineWidth = 2; lctx.stroke();
        });
      }
      ltBolt(lctx, x, y, st.s, st.c, st.a);
      drawn++;
    });
    // the nearest strike off screen: a round marker at the edge (km + a point its way)
    var n = ltNear;
    if (n){
      var q = latLonToImgPx(n.s.lat, n.s.lon), sx = originX + q.x * scale, sy = originY + q.y * scale;
      var rr = ltRadar.getBoundingClientRect(), pr = ltPill.getBoundingClientRect();
      var top = Math.max(150, (rr.bottom || 0) + 34, (pr.bottom || 0) + 34), bot = H - 170, left = 36, right = W - 36;
      if (bot > top + 40 && (sx < 0 || sx > W || sy < top - 34 || sy > bot + 34)){
        var cx = W / 2, cy = (top + bot) / 2, dx = sx - cx, dy = sy - cy, t = Infinity;
        if (dx > 0) t = Math.min(t, (right - cx) / dx);
        if (dx < 0) t = Math.min(t, (left - cx) / dx);
        if (dy > 0) t = Math.min(t, (bot - cy) / dy);
        if (dy < 0) t = Math.min(t, (top - cy) / dy);
        if (isFinite(t)){
          var ex = cx + dx * t, ey = cy + dy * t, L = Math.hypot(dx, dy) || 1, ux = dx / L, uy = dy / L;
          var col = n.km < LT_RED_KM ? '#E63232' : '#F0961E';
          lctx.beginPath(); lctx.moveTo(ex + ux * 31, ey + uy * 31);
          lctx.lineTo(ex + ux * 18 - uy * 9, ey + uy * 18 + ux * 9); lctx.lineTo(ex + ux * 18 + uy * 9, ey + uy * 18 - ux * 9);
          lctx.closePath(); lctx.fillStyle = col; lctx.fill();
          lctx.beginPath(); lctx.arc(ex, ey, 24, 0, 2 * Math.PI); lctx.fillStyle = 'rgba(11,42,58,.93)'; lctx.fill();
          lctx.lineWidth = 3; lctx.strokeStyle = col; lctx.stroke();
          ltBolt(lctx, ex, ey - 7, 8, '255,220,70', 1);
          lctx.font = '700 10.5px Calibri,"Segoe UI",sans-serif'; lctx.textAlign = 'center'; lctx.fillStyle = '#fff';
          lctx.fillText(ltKm(n.km) + ' km', ex, ey + 14);
          edge = { x: ex, y: ey, km: n.km };
        }
      }
    }
    return { drawn: drawn, edge: edge };
  }
  function ltPulse(){
    ltAnim = null; ltDrawMap();
    if (Date.now() - ltFlash.from < 2600) ltAnim = requestAnimationFrame(ltPulse);
  }
  function ltTick(){
    if (!ltWatch() || document.visibilityState === 'hidden') return;
    if (Date.now() - ltFetchedAt >= LT_POLL_MS) ltFetch();
    ltRender();                                                     // (the ages move on)
  }
  var toggleLtEl = document.getElementById('toggleLightning');
  toggleLtEl.checked = ltOn;
  toggleLtEl.addEventListener('change', function(){
    ltOn = toggleLtEl.checked;
    try { localStorage.setItem(SHOW_LT_KEY, ltOn ? '1' : '0'); } catch(e){}
    if (!ltWatch()){ ltStrikes = []; ltFetchedAt = 0; }
    ltRender(); ltTick();
  });
  setInterval(ltTick, 15000);
  document.addEventListener('visibilitychange', ltTick);
  window.__ffLightning = function(){   // (for the tests)
    var d = ltDrawMap();
    return { on: ltOn, n: ltRec.length, inRange: ltRec.filter(function(r){ return r.km <= LT_RANGE_KM; }).length,
             nearKm: ltNear ? ltNear.km : null, pill: ltPill.classList.contains('show') ? ltPill.textContent : null,
             red: ltPill.classList.contains('red'), radar: ltRadar.classList.contains('show'), drawn: d.drawn, edge: d.edge };
  };
  window.__ffLightningFetch = function(){ ltFetchedAt = 0; ltTick(); };   // (tests / tools/help_anim.py: fetch now)

