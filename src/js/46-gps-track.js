  /* ---------------- GPS ---------------- */
  var marker = document.getElementById('marker');
  var accRing = document.getElementById('accRing');
  var dot = document.getElementById('dot');
  var dotGlow = document.getElementById('dotGlow');
  var dotGlow2 = document.getElementById('dotGlow2'); // second radar ring, half a beat later
  var farAway = document.getElementById('farAway');
  var farText = document.getElementById('farText');
  function showFarAway(html){ farText.innerHTML = html; farAway.classList.add('show'); }
  function hideFarAway(){ farAway.classList.remove('show'); }
  var locateBtn = document.getElementById('locateBtn');
  var addHereBtn = document.getElementById('addHereBtn');
  addHereBtn.querySelector('.addPinHead').innerHTML = MARK_SVG; // looks like what it creates: a Markering

  var lastFix = null; // {px, py, accM, onMap}

  /* ---- "Spår": the route you drove, drawn as a line under everything (tools/NOTES_SPAR.md) ----
     Today's track: {day, segs:[[[lat,lon,t],...],...]}, saved on this phone and uploaded to Firestore
     `tracks` (one doc per person, lake and day -- kept for ever). A "track day" runs 06:00 - 06:00; when it
     ends, the day moves to the history (trkHist, per lake) -- that is what "hur långt tillbaka" shows.
     A new segment starts after a jump (>250 m, e.g. a Demo reroll) or a long pause (>10 min), so no
     straight lines across the lake. Points closer than 8 m aren't stored (GPS jitter at anchor).
     Demo Mode: a separate demoTrack, only on screen (and in sessionStorage so a rotation keeps it) -- never saved to
     the history or Firestore, and gone when Demo Mode is switched off (js/32-demo.js -> trkClearDemo). */
  var TRACK_KEY = lakeKey('ffmap_track_v1', 'track_v1'), SHOW_TRACK_KEY = 'ffmap_show_track_v1';
  var TRKHIST_KEY = lakeKey('ffmap_trackhist_v1', 'trackhist_v1'), TRKSYNC_KEY = lakeKey('ffmap_tracksync_v1', 'tracksync_v1');
  var TRKCFG_KEY = 'ffmap_track_cfg_v1';
  var TRACK_MAX_POINTS = 6000;
  var showTrack = true;
  try { if (localStorage.getItem(SHOW_TRACK_KEY) === '0') showTrack = false; } catch(e){}
  // what the Spår panel chooses (Mina / Andras, how far back, dashed, colour, stops as rings)
  var trkCfg = { mine: true, others: false, range: 'today', dash: true, color: '#FF8A1F', stops: false };
  try { var tcs = JSON.parse(localStorage.getItem(TRKCFG_KEY) || 'null'); if (tcs) for (var tck in trkCfg) if (tcs[tck] !== undefined) trkCfg[tck] = tcs[tck]; } catch(e){}
  function trkCfgSave(){ try { localStorage.setItem(TRKCFG_KEY, JSON.stringify(trkCfg)); } catch(e){} }
  function pad2(n){ return (n < 10 ? '0' : '') + n; }
  function dayStr(ms){ var d = new Date(ms - 6 * 3600000); return d.getFullYear() + '-' + pad2(d.getMonth() + 1) + '-' + pad2(d.getDate()); }
  function todayStr(){ return dayStr(Date.now()); }
  function normDay(s){ var a = String(s || '').split('-'); return a.length === 3 ? a[0] + '-' + pad2(+a[1]) + '-' + pad2(+a[2]) : String(s || ''); }   // (older saves: "2026-10-2")
  // packed track (history + Firestore): segments joined by |, points by ;, each "dLat,dLon,dSec" in base 36 (1e-6 deg)
  function packSegs(segs){
    return segs.filter(function(sg){ return sg.length; }).map(function(seg){
      var pl = 0, po = 0, pt = 0;
      return seg.map(function(p){
        var la = Math.round(p[0] * 1e6), lo = Math.round(p[1] * 1e6), t = Math.round(p[2] / 1000);
        var s = (la - pl).toString(36) + ',' + (lo - po).toString(36) + ',' + (t - pt).toString(36);
        pl = la; po = lo; pt = t; return s;
      }).join(';');
    }).join('|');
  }
  function unpackSegs(str){
    if (!str) return [];
    return String(str).split('|').filter(Boolean).map(function(sg){
      var pl = 0, po = 0, pt = 0;
      return sg.split(';').map(function(s){ var a = s.split(','); pl += parseInt(a[0], 36); po += parseInt(a[1], 36); pt += parseInt(a[2], 36); return [pl / 1e6, po / 1e6, pt * 1000]; });
    });
  }
  function simplifySegs(segs, m){   // (keeps the first and last point of every segment)
    return segs.map(function(seg){
      var out = [seg[0]];
      for (var i = 1; i < seg.length; i++){
        var l = out[out.length - 1];
        if (i === seg.length - 1 || haversineKm(l[0], l[1], seg[i][0], seg[i][1]) * 1000 >= m) out.push(seg[i]);
      }
      return out;
    }).filter(function(sg){ return sg[0]; });
  }
  // stops: points that stay within 40 m of where the stop began for >= 2 min -> [[lat, lon, minutes], ...]
  function findStops(segs){
    var pts = []; segs.forEach(function(sg){ sg.forEach(function(p){ pts.push(p); }); });
    var out = [], i = 0;
    while (i < pts.length){
      var j = i + 1, sa = pts[i][0], so = pts[i][1], n = 1;
      while (j < pts.length && haversineKm(pts[i][0], pts[i][1], pts[j][0], pts[j][1]) * 1000 <= 40){ sa += pts[j][0]; so += pts[j][1]; n++; j++; }
      var min = (pts[j - 1][2] - pts[i][2]) / 60000;
      if (n >= 2 && min >= 2){ out.push([Math.round(sa / n * 1e6) / 1e6, Math.round(so / n * 1e6) / 1e6, Math.round(min)]); i = j; } else i++;
    }
    return out;
  }
  function packStops(st){ return (st || []).map(function(s){ return s.join(','); }).join(';'); }
  function unpackStops(str){ return str ? String(str).split(';').map(function(s){ return s.split(',').map(Number); }).filter(function(a){ return a.length === 3 && !isNaN(a[0]); }) : []; }
  function segPointCount(segs){ var n = 0; segs.forEach(function(sg){ n += sg.length; }); return n; }
  // the record of one day (history / Firestore): packed simplified points + the stops
  function dayRecord(segs){ return { p: packSegs(simplifySegs(segs, 12)), s: findStops(segs), n: segPointCount(segs) }; }

  var track = { day: todayStr(), segs: [] };
  var trkHist = {};     // day -> {p, s, n, u (uploaded)} -- this person's earlier days on this lake
  try { var hs = JSON.parse(localStorage.getItem(TRKHIST_KEY) || 'null'); if (hs && typeof hs === 'object') trkHist = hs; } catch(e){}
  function saveHist(){
    for (var tries = 0; tries < 400; tries++){
      try { localStorage.setItem(TRKHIST_KEY, JSON.stringify(trkHist)); return; } catch(e){
        var ks = Object.keys(trkHist).sort(); if (ks.length <= 1) return;
        delete trkHist[ks[0]];   // phone storage full: the oldest day goes (it stays in Firestore and comes back when needed)
      }
    }
  }
  var DEMOTRACK_KEY = 'ffmap_demotrack_v1', demoTrack = { segs: [] };
  try { if (demoMode) demoTrack = JSON.parse(sessionStorage.getItem(DEMOTRACK_KEY) || 'null') || demoTrack; } catch(e){}
  function trkClearDemo(){
    demoTrack = { segs: [] }; try { sessionStorage.removeItem(DEMOTRACK_KEY); } catch(e){}
    trkPxDirty(); fogRebuild(); renderTrack();
  }
  var trkPx = {};       // cache: day key -> image-pixel version of the segments (so panning is only a multiply)
  function trkPxDirty(){ trkPx = {}; }
  function archiveTrack(tr){
    if (!tr || !tr.segs || !segPointCount(tr.segs)) return;
    trkHist[normDay(tr.day)] = dayRecord(tr.segs);
    saveHist(); trkPxDirty(); flushTrackUploads(true);
  }
  try {
    var savedTrack = JSON.parse(localStorage.getItem(TRACK_KEY) || 'null');
    if (savedTrack && Array.isArray(savedTrack.segs)){
      savedTrack.day = normDay(savedTrack.day);
      if (savedTrack.day === track.day) track = savedTrack;
      else archiveTrack(savedTrack);   // yesterday (or older) -- now history, not thrown away
    }
  } catch(e){}
  var trackDirty = false, trackUploadDirty = false, lastTrackUpAt = 0;
  function saveTrack(){
    if (!trackDirty) return;
    trackDirty = false;
    try { localStorage.setItem(TRACK_KEY, JSON.stringify(track)); } catch(e){}
  }
  setInterval(saveTrack, 10000);
  document.addEventListener('visibilitychange', function(){ if (document.visibilityState === 'hidden'){ saveTrack(); flushTrackUploads(true); } });
  window.addEventListener('pagehide', saveTrack);
  setInterval(function(){ flushTrackUploads(false); }, 60000);
  function recordTrack(lat, lon, acc){
    if (acc && acc > 40) return; // too uncertain to draw
    var demo = !!demoMode;
    if (!demo && track.day !== todayStr()){ archiveTrack(track); track = { day: todayStr(), segs: [] }; trackDirty = true; }
    var tr = demo ? demoTrack : track;   // (Demo Mode: its own little track, never saved)
    var now = Date.now();
    var seg = tr.segs.length ? tr.segs[tr.segs.length - 1] : null;
    var last = seg && seg.length ? seg[seg.length - 1] : null;
    if (last){
      var d = haversineKm(last[0], last[1], lat, lon) * 1000;
      if (d < 8) return;
      if (d > 250 || now - last[2] > 10 * 60000) seg = null;
    }
    var fresh = !seg;
    if (!seg){ seg = []; tr.segs.push(seg); }
    seg.push([Math.round(lat * 1e6) / 1e6, Math.round(lon * 1e6) / 1e6, now]);
    var total = 0;
    tr.segs.forEach(function(sg){ total += sg.length; });
    while (total > TRACK_MAX_POINTS && tr.segs.length){ tr.segs[0].shift(); total--; if (!tr.segs[0].length) tr.segs.shift(); }
    if (demo){ try { sessionStorage.setItem(DEMOTRACK_KEY, JSON.stringify(demoTrack)); } catch(e){} }
    else { trackDirty = true; trackUploadDirty = true; }
    fogAddStep(fresh ? null : last, seg[seg.length - 1]);   // (Fog of war, 48-fog.js)
    renderTrack();
  }

  /* ---- drawing: today + the chosen earlier days (Mina), other people's days (Andras), stops as rings ---- */
  var trackLayer = document.getElementById('trackLayer');
  var trkLineEl = trackLayer.querySelector('.trkLine'), trkUnderEl = trackLayer.querySelector('.trkUnder'), trkOtherEl = trackLayer.querySelector('.trkOther'), trkStopsEl = trackLayer.querySelector('.trkStops');
  var trkOthers = {};   // doc id -> {uid, name, day, p, s}  (fetched when "Andras" is on -- see fetchOthersTracks)
  function pxSegs(key, ref, n, getSegs){
    var c = trkPx[key];
    if (c && c.r === ref && c.n === n) return c.s;
    var s = getSegs().map(function(seg){
      var a = new Array(seg.length * 2);
      for (var i = 0; i < seg.length; i++){ var p = latLonToImgPx(seg[i][0], seg[i][1]); a[2 * i] = p.x; a[2 * i + 1] = p.y; }
      return a;
    });
    trkPx[key] = { r: ref, n: n, s: s };
    return s;
  }
  function trkRangeFrom(){ var r = trkCfg.range; return r === 'all' ? '' : r === 'today' ? todayStr() : dayStr(Date.now() - ((r === '7' ? 6 : 29) * 86400000)); }
  function pathOfPx(list){
    var d = '';
    list.forEach(function(seg){
      var n = seg.length / 2, lx = null, ly = null, k = 0;
      for (var i = 0; i < n; i++){
        var x = originX + seg[2 * i] * scale, y = originY + seg[2 * i + 1] * scale;
        if (lx !== null && i < n - 1 && Math.abs(x - lx) < 1.5 && Math.abs(y - ly) < 1.5) continue; // too close to see
        d += (k ? 'L' : 'M') + x.toFixed(1) + ' ' + y.toFixed(1);
        lx = x; ly = y; k++;
      }
    });
    return d;
  }
  var todayStopsCache = { n: -1, s: [] }, demoStopsCache = { n: -1, s: [] };
  function todayStops(){
    var n = segPointCount(track.segs);
    if (todayStopsCache.n !== n) todayStopsCache = { n: n, s: findStops(track.segs) };
    return todayStopsCache.s;
  }
  function demoStops(){
    var n = segPointCount(demoTrack.segs);
    if (demoStopsCache.n !== n) demoStopsCache = { n: n, s: findStops(demoTrack.segs) };
    return demoStopsCache.s;
  }
  function trkMineDays(){   // earlier days (not today) inside the chosen range, oldest first
    var from = trkRangeFrom(), td = todayStr();
    return Object.keys(trkHist).filter(function(dk){ return dk >= from && dk !== td; }).sort();
  }
  function renderTrack(){
    trackLayer.classList.toggle('off', !showTrack);
    trackLayer.classList.toggle('solid', !trkCfg.dash);
    if (!showTrack) return;
    var c = trkCfg, from = trkRangeFrom(), stops = [], mine = [];
    if (c.mine){
      trkMineDays().forEach(function(dk){
        var rec = trkHist[dk];
        mine.push.apply(mine, pxSegs('h' + dk, rec, rec.p.length, function(){ return unpackSegs(rec.p); }));
        if (c.stops) stops.push.apply(stops, rec.s || []);
      });
      if (track.day === todayStr()){
        mine.push.apply(mine, pxSegs('today', track, segPointCount(track.segs), function(){ return track.segs; }));
        if (c.stops) stops.push.apply(stops, todayStops());
      }
      if (demoMode && demoTrack.segs.length){
        mine.push.apply(mine, pxSegs('demo', demoTrack, segPointCount(demoTrack.segs), function(){ return demoTrack.segs; }));
        if (c.stops) stops.push.apply(stops, demoStops());
      }
    }
    var d = pathOfPx(mine);
    trkLineEl.setAttribute('d', d); trkUnderEl.setAttribute('d', d);
    trkLineEl.style.stroke = c.color;
    var others = [];
    if (c.others) Object.keys(trkOthers).forEach(function(id){
      var o = trkOthers[id];
      if (o.day >= from) others.push.apply(others, pxSegs('o' + id, o, o.p.length, function(){ return unpackSegs(o.p); }));
    });
    trkOtherEl.setAttribute('d', pathOfPx(others));
    if (!c.stops || !stops.length){ if (trkStopsEl.firstChild) trkStopsEl.textContent = ''; return; }
    var h = '';
    stops.forEach(function(s){
      var p = latLonToImgPx(s[0], s[1]), x = originX + p.x * scale, y = originY + p.y * scale;
      if (x < -60 || y < -60 || x > stageW + 60 || y > stageH + 60) return;
      var r = Math.min(34, 8 + Math.sqrt(s[2]) * 3.4);
      h += '<circle cx="' + x.toFixed(1) + '" cy="' + y.toFixed(1) + '" r="' + r.toFixed(1) + '"></circle><text x="' + x.toFixed(1) + '" y="' + (y - r - 4).toFixed(1) + '">' + s[2] + ' min</text>';
    });
    trkStopsEl.innerHTML = h;
  }

  /* ---- Firestore `tracks` (one doc per person, lake and day) ---- */
  function trkSafeUid(){ return String(myUid || '').replace(/[^a-z0-9åäö]+/g, '_'); }
  function trkDocId(day){ return LAKE_ID + '_' + trkSafeUid() + '_' + day; }
  function uploadTrackDay(day, rec){
    if (!USE_FIREBASE || !tracksCol || !myUid) return;
    addUsage('w', 1);
    tracksCol.doc(trkDocId(day)).set({
      lake: LAKE_ID, uid: myUid, name: userName || '', day: day, pts: rec.p, st: packStops(rec.s), n: rec.n || 0,
      lakeDay: LAKE_ID + '_' + day, ownKey: LAKE_ID + '_' + trkSafeUid() + '_' + day,
      updatedAt: firebase.firestore.FieldValue.serverTimestamp()
    }).catch(function(e){ console.warn('spår kunde inte sparas', e && e.code); });
  }
  // finished days that aren't uploaded yet (+ today's, at most every 5 min or when the app goes to the background)
  function flushTrackUploads(force){
    if (!USE_FIREBASE || !tracksCol || !myUid) return;
    var any = false;
    Object.keys(trkHist).forEach(function(dk){
      var rec = trkHist[dk];
      if (!rec.u){ rec.u = 1; any = true; uploadTrackDay(dk, rec); }   // (marked first: Firestore keeps the write even offline)
    });
    if (any) saveHist();
    if (trackUploadDirty && (force || Date.now() - lastTrackUpAt >= 5 * 60000)){
      trackUploadDirty = false; lastTrackUpAt = Date.now();
      uploadTrackDay(track.day, dayRecord(track.segs));
    }
  }
  function trkReadDocs(snap, onDoc){
    countGetReads(snap);
    snap.forEach(function(doc){ var d = doc.data() || {}; if (d.lake && d.lake !== LAKE_ID) return; onDoc(doc.id, d); });
  }
  // a new phone (or cleared storage): get this person's own days back, once
  function fetchMyTracks(){
    var done = false; try { done = localStorage.getItem(TRKSYNC_KEY) === '1'; } catch(e){}
    if (done || !tracksCol || !USE_FIREBASE || !myUid) return;
    var pre = LAKE_ID + '_' + trkSafeUid() + '_';
    tracksCol.where('ownKey', '>=', pre).where('ownKey', '<=', pre + '~').get().then(function(snap){
      trkReadDocs(snap, function(id, d){
        var dk = d.day; if (!dk) return;
        if (dk === todayStr()){ if (!segPointCount(track.segs)){ track = { day: dk, segs: unpackSegs(d.pts) }; trackDirty = true; } return; }
        if (!trkHist[dk]) trkHist[dk] = { p: d.pts || '', s: unpackStops(d.st), n: d.n || 0, u: 1 };
      });
      saveHist(); trkPxDirty(); try { localStorage.setItem(TRKSYNC_KEY, '1'); } catch(e){}
      fogRebuild();
      renderTrack(); trkRenderPanel();
    }).catch(function(e){ console.warn('mina spår kunde inte hämtas', e && e.code); });
  }
  // other people's days: only when "Andras" is switched on (reads: one per person and day, kept until the page is closed)
  var trkOthersFrom = null, trkOthersAt = 0, trkOthersBusy = false, trkOthersMsg = '';
  function fetchOthersTracks(){
    if (!trkCfg.others || !tracksCol || !USE_FIREBASE || trkOthersBusy) return;
    var from = trkRangeFrom() || '0000-00-00';
    if (trkOthersFrom !== null && from >= trkOthersFrom && Date.now() - trkOthersAt < 5 * 60000) return;   // (already have those days)
    trkOthersBusy = true; trkOthersMsg = 'Laddar…'; trkRenderPanel();
    tracksCol.where('lakeDay', '>=', LAKE_ID + '_' + from).where('lakeDay', '<=', LAKE_ID + '_9999-99-99').get().then(function(snap){
      trkReadDocs(snap, function(id, d){ if (d.uid === myUid || !d.day) return; trkOthers[id] = { uid: d.uid, name: d.name || '', day: d.day, p: d.pts || '', s: unpackStops(d.st) }; });
      trkOthersFrom = trkOthersFrom === null ? from : Math.min(trkOthersFrom, from); trkOthersAt = Date.now(); trkOthersBusy = false; trkOthersMsg = '';
      renderTrack(); trkRenderPanel();
    }).catch(function(e){
      trkOthersBusy = false; trkOthersMsg = (e && e.code === 'permission-denied') ? 'Kunde inte hämta (databasens regler saknar "tracks")' : 'Kunde inte hämta andras spår';
      trkRenderPanel();
    });
  }
  var lastOwnLatLon = null; // {lat, lon} -- whatever position is currently shown as "you" (real or demo)
  var hasCenteredOnce = false;

  // GPS problems (permission denied, no signal, unsupported) are shown in the
  // same small status pill (under the name, top left) as the "you're X km from Regnaren" message -- the two
  // never need to show at once, since that one needs a working fix.
  var lastGpsErrorCode = null; // 1 = denied, 2 = unavailable, 3 = timeout, 'unsupported'
  function gpsProblemText(){
    if (lastGpsErrorCode === 'unsupported') return 'Webbläsaren kan inte visa din position';
    if (lastGpsErrorCode === 1) return '<b>Platsåtkomst nekad</b><br><span class="farSub">Tillåt plats i telefonens inställningar</span>';
    if (lastGpsErrorCode === 2) return 'Hittar ingen GPS-position…';
    return 'Söker GPS-position…';
  }
  function showGpsProblem(){
    if (demoMode) return;                                 // demo shows its own position
    if (lastRealFix && lastGpsErrorCode !== 1) return;   // already have a fix -- a hiccup isn't worth a message
    showFarAway(gpsProblemText());
  }
  // forget the shown/shared "you" position entirely (no fix to show)
  function clearOwnFix(){
    lastFix = null;
    lastOwnLatLon = null;
    locateBtn.disabled = true;
    addHereBtn.disabled = true;
    hideFarAway();
    updateMarker();
    renderBoats();
  }

  function updateMarker(){
    if (!lastFix || !lastFix.onMap){ marker.style.display = 'none'; return; }
    marker.style.display = 'block';
    var sx = originX + lastFix.px * scale;
    var sy = originY + lastFix.py * scale;
    accRing.style.left = sx + 'px'; accRing.style.top = sy + 'px';
    dotGlow.style.left = sx + 'px'; dotGlow.style.top = sy + 'px';
    dotGlow2.style.left = sx + 'px'; dotGlow2.style.top = sy + 'px';
    dot.style.left = sx + 'px'; dot.style.top = sy + 'px';
    var accWebPx = lastFix.accM / WEB_METERS_PER_PX;
    var d = Math.max(16, Math.min(360, accWebPx * scale * 2));
    accRing.style.width = d + 'px'; accRing.style.height = d + 'px';
    compassDraw(sx, sy);   // ("Kompass" -- further down)
  }

  function niceScaleMeters(target){
    var steps = [5,10,20,50,100,200,500,1000,2000,5000,10000];
    var best = steps[0];
    for (var i=0;i<steps.length;i++){ if (steps[i] <= target) best = steps[i]; }
    return best;
  }
  function updateScaleBar(){
    var pxPerMeter = scale / WEB_METERS_PER_PX;
    var targetPx = 90;
    var meters = niceScaleMeters(targetPx / pxPerMeter);
    var barPx = meters * pxPerMeter;
    document.getElementById('scaleLine').style.width = Math.max(24, barPx) + 'px';
    document.getElementById('scaleLabel').textContent = meters >= 1000 ? (meters/1000) + ' km' : meters + ' m';
    // zoom like web maps / Genesis, and which level's picture (lines) is shown
    var L = detailLevel();
    document.getElementById('zoomLabel').innerHTML = currentZoom().toFixed(1).replace('.', ',') + ' ×' +   // "15,3 × L 14" (short, Filip)
      '<b>L ' + (L ? L.z : ZOOM) + '</b>';
  }

  function onFix(lat, lon, accM, speedMs, gpsHeading){
    // whatever position is actually shown as "you" -- real GPS, or the demo
    // position while Demo Mode is on -- is also what the others see for you
    // (maybeBroadcastPosition itself skips anything not at the lake)
    maybeBroadcastPosition(lat, lon);
    recordSpeed(lat, lon, accM, speedMs); // knot meter + average speed (on the phone only)
    if (isNearLake(lat, lon)) recordTrack(lat, lon, accM); // "Spår" (Demo Mode: a temporary track, see recordTrack)
    updateHeading(lat, lon, gpsHeading);  // the arrow in your GPS dot
    lastOwnLatLon = { lat: lat, lon: lon };
    var p = latLonToImgPx(lat, lon);
    var onMap = isNearLake(lat, lon);
    lastFix = { px:p.x, py:p.y, accM: accM || 15, onMap: onMap };
    refreshSheetMeta(); // keep "X m bort" in an open spot sheet up to date
    updateProbeText();  // ... and in the depth probe

    if (onMap){
      hideFarAway();
      locateBtn.disabled = false;
      addHereBtn.disabled = false;
    } else {
      var km = haversineKm(lat, lon, LAKE_CENTER_LAT, LAKE_CENTER_LON);
      var kmTxt = km < 10 ? km.toFixed(1).replace('.', ',') : String(Math.round(km));
      showFarAway('<b>' + kmTxt + ' km</b> från ' + LAKE.name + '<br><span class="farSub">GPS aktiveras på plats</span>');
      addHereBtn.disabled = true;
      locateBtn.disabled = true;
    }

    if (!hasCenteredOnce && onMap){
      hasCenteredOnce = true;
      centerOnFix(true);
    } else {
      updateMarker();
    }
  }

  function centerOnFix(instant){
    if (!lastFix || !lastFix.onMap) return;
    var targetScale = Math.max(scale, fitScale * 2.2);
    var tx = stageW/2 - lastFix.px * targetScale;
    var ty = stageH/2 - lastFix.py * targetScale;
    if (instant) { scale = targetScale; originX = tx; originY = ty; clampOrigin(); render(); }
    else animateTo(targetScale, tx, ty, 500);
  }

  function centerOnWaypoint(wp){
    var p = latLonToImgPx(wp.lat, wp.lon);
    var targetScale = Math.max(scale, fitScale * 4.5);
    var tx = stageW/2 - p.x * targetScale;
    var ty = stageH/2 - p.y * targetScale;
    animateTo(targetScale, tx, ty, 500);
  }

  locateBtn.addEventListener('click', function(){
    if (lastFix && lastFix.onMap){ centerOnFix(false); }
    else if (lastFix) farAway.classList.add('show');
  });

  // First pan + zoom to your position (exactly like the GPS button), then drop
  // the spot there once the map has arrived -- so it's obvious where it goes.
  var addHerePending = false;
  addHereBtn.addEventListener('click', function(){
    if (!lastFix || !lastFix.onMap || addHerePending) return;
    addHerePending = true;
    var fix = lastFix; // the position at the moment you pressed, even if a new fix arrives meanwhile
    centerOnFix(false);
    setTimeout(function(){
      addHerePending = false;
      placeWaypointAtScreen(originX + fix.px * scale, originY + fix.py * scale);
    }, reduceMotion ? 0 : 540);
  });

  function handleGpsFix(pos){
    // right after coming back to the app: ignore a position the phone had
    // cached from before it was put away -- wait for a really fresh one
    if (awaitingFreshFix && pos.timestamp && pos.timestamp < resumedAt - 2000){
      lastRealFix = { lat: pos.coords.latitude, lon: pos.coords.longitude, acc: pos.coords.accuracy, speed: pos.coords.speed, heading: pos.coords.heading };
      return;
    }
    awaitingFreshFix = false;
    lastGpsErrorCode = null;
    lastRealFix = { lat: pos.coords.latitude, lon: pos.coords.longitude, acc: pos.coords.accuracy, speed: pos.coords.speed, heading: pos.coords.heading };
    if (!demoMode) onFix(lastRealFix.lat, lastRealFix.lon, lastRealFix.acc, lastRealFix.speed, lastRealFix.heading);
  }

  /* ---- coming back to the app (from the home screen / a locked phone) ----
     While the app is in the background iOS pauses it completely. When it's
     opened again: send your FRESH position straight away (never the old one
     from before you closed it), and fetch the other boats from the server
     at once, so both sides see up-to-date positions immediately. (Fishing
     spots come in through their live listener as it reconnects.) */
  var hiddenAt = 0, awaitingFreshFix = false, resumedAt = 0;
  document.addEventListener('visibilitychange', function(){
    if (document.visibilityState === 'hidden'){ hiddenAt = Date.now(); return; }
    var away = hiddenAt ? Date.now() - hiddenAt : 0;
    hiddenAt = 0;
    if (away >= 5000) onAppResumed();
  });
  function onAppResumed(){
    if (!appStarted) return;
    resumedAt = Date.now();
    lastPosWriteAt = 0; // the first fresh position is shared at once, not after the interval
    if (demoMode && demoLat != null){
      awaitingFreshFix = false;
      onFix(demoLat, demoLon, 8);
    } else if ('geolocation' in navigator){
      awaitingFreshFix = true; // (the 2-second share tick waits for it too)
      navigator.geolocation.getCurrentPosition(handleGpsFix, function(){}, { enableHighAccuracy:true, maximumAge:0, timeout:15000 });
      // safety net: if no fresh position has come within 8 s (poor signal),
      // go on with the latest one the phone has rather than share nothing
      var myResume = resumedAt;
      setTimeout(function(){
        if (!awaitingFreshFix || resumedAt !== myResume) return;
        awaitingFreshFix = false;
        if (lastRealFix && !demoMode) onFix(lastRealFix.lat, lastRealFix.lon, lastRealFix.acc, lastRealFix.speed, lastRealFix.heading);
      }, 8000);
    }
    renderBoats(); // grey / gone status right away
    if (USE_FIREBASE && posCol){
      posCol.get({ source: 'server' }).then(function(snap){ countGetReads(snap); applyPositionsSnapshot(snap); }).catch(function(){});
    }
  }

  function startGeolocation(){
    if (!('geolocation' in navigator)){
      lastGpsErrorCode = 'unsupported';
      showGpsProblem();
      locateBtn.style.display = 'none';
      return;
    }
    showGpsProblem(); // "Söker GPS-position…" until the first fix (or an error) arrives
    navigator.geolocation.watchPosition(
      handleGpsFix,
      function(err){
        lastGpsErrorCode = err.code;
        showGpsProblem();
      },
      { enableHighAccuracy:true, maximumAge:4000, timeout:20000 }
    );
  }

