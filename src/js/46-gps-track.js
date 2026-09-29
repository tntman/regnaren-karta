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

  /* ---- "Spår": your route today, drawn as a line under everything ----
     Saved on this phone only ({day, segs:[[[lat,lon,t],...],...]}); a new
     track starts every morning at 06:00. A new segment starts after a jump (>250 m, e.g.
     a Demo reroll) or a long pause (>10 min), so no straight lines across
     the lake. Points closer than 8 m aren't stored (GPS jitter at anchor). */
  var TRACK_KEY = lakeKey('ffmap_track_v1', 'track_v1'), SHOW_TRACK_KEY = 'ffmap_show_track_v1';
  var TRACK_MAX_POINTS = 6000;
  var showTrack = true;
  try { if (localStorage.getItem(SHOW_TRACK_KEY) === '0') showTrack = false; } catch(e){}
  // a "track day" runs 06:00 - 06:00 (so a night session doesn't split at midnight)
  function todayStr(){ var d = new Date(Date.now() - 6 * 3600000); return d.getFullYear() + '-' + (d.getMonth() + 1) + '-' + d.getDate(); }
  var track = { day: todayStr(), segs: [] };
  try {
    var savedTrack = JSON.parse(localStorage.getItem(TRACK_KEY) || 'null');
    if (savedTrack && savedTrack.day === track.day && Array.isArray(savedTrack.segs)) track = savedTrack;
  } catch(e){}
  var trackDirty = false;
  function saveTrack(){
    if (!trackDirty) return;
    trackDirty = false;
    try { localStorage.setItem(TRACK_KEY, JSON.stringify(track)); } catch(e){}
  }
  setInterval(saveTrack, 10000);
  document.addEventListener('visibilitychange', function(){ if (document.visibilityState === 'hidden') saveTrack(); });
  window.addEventListener('pagehide', saveTrack);
  function recordTrack(lat, lon, acc){
    if (acc && acc > 40) return; // too uncertain to draw
    if (track.day !== todayStr()) track = { day: todayStr(), segs: [] };
    var now = Date.now();
    var seg = track.segs.length ? track.segs[track.segs.length - 1] : null;
    var last = seg && seg.length ? seg[seg.length - 1] : null;
    if (last){
      var d = haversineKm(last[0], last[1], lat, lon) * 1000;
      if (d < 8) return;
      if (d > 250 || now - last[2] > 10 * 60000) seg = null;
    }
    if (!seg){ seg = []; track.segs.push(seg); }
    seg.push([Math.round(lat * 1e6) / 1e6, Math.round(lon * 1e6) / 1e6, now]);
    var total = 0;
    track.segs.forEach(function(sg){ total += sg.length; });
    while (total > TRACK_MAX_POINTS && track.segs.length){ track.segs[0].shift(); total--; if (!track.segs[0].length) track.segs.shift(); }
    trackDirty = true;
    renderTrack();
  }
  var trackLayer = document.getElementById('trackLayer');
  function renderTrack(){
    trackLayer.classList.toggle('off', !showTrack);
    if (!showTrack) return;
    var d = '';
    track.segs.forEach(function(seg){
      var lx = null, ly = null, n = 0;
      for (var i = 0; i < seg.length; i++){
        var p = latLonToImgPx(seg[i][0], seg[i][1]);
        var x = originX + p.x * scale, y = originY + p.y * scale;
        if (lx !== null && i < seg.length - 1 && Math.abs(x - lx) < 1.5 && Math.abs(y - ly) < 1.5) continue; // too close to see
        d += (n ? 'L' : 'M') + x.toFixed(1) + ' ' + y.toFixed(1);
        lx = x; ly = y; n++;
      }
    });
    trackLayer.firstElementChild.setAttribute('d', d);
    trackLayer.lastElementChild.setAttribute('d', d);
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
    document.getElementById('zoomLabel').innerHTML = 'Zoom ' + currentZoom().toFixed(1).replace('.', ',') +
      '<b>lager ' + (L ? L.z : ZOOM) + '</b>';
  }

  function onFix(lat, lon, accM, speedMs, gpsHeading){
    // whatever position is actually shown as "you" -- real GPS, or the demo
    // position while Demo Mode is on -- is also what the others see for you
    // (maybeBroadcastPosition itself skips anything not at the lake)
    maybeBroadcastPosition(lat, lon);
    recordSpeed(lat, lon, accM, speedMs); // knot meter + average speed (on the phone only)
    if (isNearLake(lat, lon)) recordTrack(lat, lon, accM); // "Spår"
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

