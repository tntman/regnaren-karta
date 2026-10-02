  /* ---- Kartans färg (Settings): how saturated the map image is ----
     A CSS filter on the map image only (markers, boats and buttons keep
     their colours). The depth-scale bar gets the same filter so its colours
     still match the map. Remembered on this phone. */
  var MAP_SAT_KEY = 'ffmap_map_saturation_v1';
  var mapSat = 80; // percent -- default: a bit calmer than the raw map
  try { var savedSat = parseInt(localStorage.getItem(MAP_SAT_KEY), 10); if (savedSat >= 0 && savedSat <= 100) mapSat = savedSat; } catch(e){}
  var mapSatSlider = document.getElementById('mapSatSlider');
  var mapSatVal = document.getElementById('mapSatVal');
  function applyMapSaturation(){
    var f = mapSat >= 100 ? '' : 'saturate(' + (mapSat / 100) + ')';
    document.getElementById('mapImg').style.filter = f;
    document.getElementById('detailLayer').style.filter = f;
    var bar = document.querySelector('#legend .bar');
    if (bar) bar.style.filter = f;
    mapSatSlider.value = String(mapSat);
    mapSatVal.textContent = mapSat + ' %';
  }
  mapSatSlider.addEventListener('input', function(){
    mapSat = Math.max(0, Math.min(100, parseInt(mapSatSlider.value, 10) || 0));
    applyMapSaturation();
    try { localStorage.setItem(MAP_SAT_KEY, String(mapSat)); } catch(e){}
  });
  applyMapSaturation();

  /* ---- Pulserande ring vid din position (Settings, default on) ---- */
  var GPS_PULSE_KEY = 'ffmap_gps_pulse_v1';
  var gpsPulseOn = true;
  try { if (localStorage.getItem(GPS_PULSE_KEY) === '0') gpsPulseOn = false; } catch(e){}
  var gpsPulseToggle = document.getElementById('gpsPulseToggle');
  function applyGpsPulse(){
    gpsPulseToggle.checked = gpsPulseOn;
    document.getElementById('marker').classList.toggle('noPulse', !gpsPulseOn);
  }
  gpsPulseToggle.addEventListener('change', function(){
    gpsPulseOn = gpsPulseToggle.checked;
    try { localStorage.setItem(GPS_PULSE_KEY, gpsPulseOn ? '1' : '0'); } catch(e){}
    applyGpsPulse();
  });
  applyGpsPulse();

  var toggleDepthEl = document.getElementById('toggleDepth');
  var toggleTrackEl = document.getElementById('toggleTrack');
  // (their checkboxes are set in boot() -- showDepth / showTrack are read further down)
  toggleDepthEl.addEventListener('change', function(){
    showDepth = toggleDepthEl.checked;
    try { localStorage.setItem(SHOW_DEPTH_KEY, showDepth ? '1' : '0'); } catch(e){}
    updateSpeedPill();
  });
  toggleTrackEl.addEventListener('change', function(){
    showTrack = toggleTrackEl.checked;
    try { localStorage.setItem(SHOW_TRACK_KEY, showTrack ? '1' : '0'); } catch(e){}
    renderTrack();
  });
  var TRACK_OP_KEY = 'ffmap_track_opacity_v1';
  var trackOp = 60;
  try { var sto = parseInt(localStorage.getItem(TRACK_OP_KEY), 10); if (sto >= 10 && sto <= 100) trackOp = sto; } catch(e){}
  var trackOpSlider = document.getElementById('trackOpSlider');
  function applyTrackOpacity(){
    document.getElementById('trackLayer').style.opacity = String(trackOp / 100);
    trackOpSlider.value = String(trackOp);
    document.getElementById('trackOpVal').textContent = trackOp + ' %';
  }
  trackOpSlider.addEventListener('input', function(){
    trackOp = Math.max(10, Math.min(100, parseInt(trackOpSlider.value, 10) || 60));
    try { localStorage.setItem(TRACK_OP_KEY, String(trackOp)); } catch(e){}
    applyTrackOpacity();
  });
  applyTrackOpacity();
  document.getElementById('trackClearBtn').addEventListener('click', function(){
    if (!confirm('Börja om spåret härifrån? Spåret hittills suddas.')) return;
    if (demoMode){ trkClearDemo(); return; }
    track = { day: todayStr(), segs: [] };
    // the new track starts right where you are now, and keeps recording as you go
    if (lastOwnLatLon && lastFix && lastFix.onMap) track.segs.push([[Math.round(lastOwnLatLon.lat * 1e6) / 1e6, Math.round(lastOwnLatLon.lon * 1e6) / 1e6, Date.now()]]);
    trackDirty = true; saveTrack(); renderTrack();
    var btn = document.getElementById('trackClearBtn');
    btn.textContent = 'Klart ✓'; setTimeout(function(){ btn.textContent = 'Börja om'; }, 1800);
  });

  var toggleMineEl = document.getElementById('toggleMine');
  var toggleOthersEl = document.getElementById('toggleOthers');
  toggleMineEl.checked = showMine;
  toggleOthersEl.checked = showOthers;
  toggleMineEl.addEventListener('change', function(){
    showMine = toggleMineEl.checked;
    try { localStorage.setItem('regnaren_vis_mine_v1', showMine ? '1' : '0'); } catch(e){}
    renderWaypoints();
  });
  toggleOthersEl.addEventListener('change', function(){
    showOthers = toggleOthersEl.checked;
    try { localStorage.setItem('regnaren_vis_others_v1', showOthers ? '1' : '0'); } catch(e){}
    renderWaypoints();
  });

