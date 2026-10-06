  /* ---------------- Demo Mode = the test mode (TEST_MODE, 10-core.js) ----------------
     Switching it on or off reloads the page: everything shared then talks to the other database. */
  var DEMO_LAT_KEY = 'lake_' + LAKE_ID + '_demo_lat_v1'; // per-lake: a demo spot only makes sense on its own map
  var DEMO_LON_KEY = 'lake_' + LAKE_ID + '_demo_lon_v1';
  var demoMode = TEST_MODE;   // (never changes while the page runs)
  var demoLat = null, demoLon = null;
  var lastRealFix = null; // {lat, lon, acc} from the actual device GPS
  var demoBannerEl = document.getElementById('demoBanner');
  var demoCoordsRow = document.getElementById('demoCoordsRow');
  var demoLatInput = document.getElementById('demoLatInput');
  var demoLonInput = document.getElementById('demoLonInput');
  var demoRerollBtn = document.getElementById('demoRerollBtn');
  // Safety: Demo Mode switches itself off after 15 minutes, so nobody heads
  // out on the water still seeing (and sharing) a fake position. The start
  // time is stored, so a reload doesn't restart the clock -- and if the app
  // was closed for longer than that, it simply starts with Demo Mode off (10-core.js).
  var DEMO_FRESH_KEY = 'ffmap_demo_fresh_v1';   // (sessionStorage: just switched on -> show the boat, after the reload)
  var demoSince = 0;
  var demoBannerTimerEl = document.getElementById('demoBannerTimer');
  try {
    demoSince = demoMode ? Number(localStorage.getItem(DEMO_SINCE_KEY) || 0) : 0;
    var savedLat = parseFloat(localStorage.getItem(DEMO_LAT_KEY));
    var savedLon = parseFloat(localStorage.getItem(DEMO_LON_KEY));
    if (isFinite(savedLat) && isFinite(savedLon)){ demoLat = savedLat; demoLon = savedLon; }
  } catch(e){}
  demoModeToggle.checked = demoMode;
  demoBannerEl.classList.toggle('show', demoMode);

  function updateDemoTimer(){
    if (!demoMode || demoSwitching) return;
    var left = DEMO_MAX_MS - (Date.now() - demoSince);
    if (left <= 0){
      demoModeToggle.checked = false;
      setDemoMode(false);
      return;
    }
    demoBannerTimerEl.textContent = 'Stängs av om ' + Math.ceil(left / 60000) + ' min';
  }
  // checked often enough to be on time, and right away when you come back
  // to the app (timers are paused while the phone is locked)
  setInterval(updateDemoTimer, 5000);
  updateDemoTimer(); // show the countdown right away if Demo Mode was left on
  document.addEventListener('visibilitychange', function(){
    if (document.visibilityState === 'visible') updateDemoTimer();
  });

  // picks a spot well inside the map, away from the shoreline edges of the crop
  function randomDemoPoint(){
    // somewhere on the water (the depth data says where the lake is), at
    // least 1,5 m deep so it isn't right at the shore
    var marginX = IMG_W * 0.08, marginY = IMG_H * 0.08, x, y;
    for (var i = 0; i < 400; i++){
      x = marginX + Math.random() * (IMG_W - 2 * marginX);
      y = marginY + Math.random() * (IMG_H - 2 * marginY);
      var dm = depthAtImgPx(x, y);
      if (dm != null && dm >= 1.5) return imgPxToLatLon(x, y);
    }
    return imgPxToLatLon(IMG_W / 2, IMG_H / 2);
  }
  // is there water (at least ~1 m) this far ahead on this heading?
  function demoWaterAhead(lat, lon, headingDeg, meters){
    var h = headingDeg * Math.PI / 180, cosLat = Math.cos(lat * Math.PI / 180);
    var dm = depthAtLatLon(lat + meters * Math.cos(h) / 111320, lon + meters * Math.sin(h) / (111320 * cosLat));
    return dm != null && dm >= 1;
  }
  function updateDemoCoordsInputs(){
    demoLatInput.value = (demoLat != null) ? demoLat.toFixed(5) : '';
    demoLonInput.value = (demoLon != null) ? demoLon.toFixed(5) : '';
    demoLatInput.classList.remove('invalid');
    demoLonInput.classList.remove('invalid');
  }
  function setDemoCoords(ll){
    demoLat = ll.lat; demoLon = ll.lon;
    try { localStorage.setItem(DEMO_LAT_KEY, demoLat); localStorage.setItem(DEMO_LON_KEY, demoLon); } catch(e){}
    updateDemoCoordsInputs();
  }
  function rerollDemoPosition(){
    setDemoCoords(randomDemoPoint());
    demoJumped();
    if (demoMode) onFix(demoLat, demoLon, 8);
  }

  // Typing your own lat/lon works exactly like the reroll button: it moves
  // the demo position and, if Demo Mode is on, updates the GPS fix live.
  function commitManualDemoCoords(){
    demoInputDirty = false;
    var lat = parseFloat(demoLatInput.value.replace(',', '.'));
    var lon = parseFloat(demoLonInput.value.replace(',', '.'));
    var okLat = isFinite(lat) && lat >= -90 && lat <= 90;
    var okLon = isFinite(lon) && lon >= -180 && lon <= 180;
    demoLatInput.classList.toggle('invalid', !okLat);
    demoLonInput.classList.toggle('invalid', !okLon);
    if (!okLat || !okLon) return; // leave the bad field marked, don't touch the stored position yet
    setDemoCoords({ lat: lat, lon: lon });
    demoJumped();
    if (demoMode) onFix(demoLat, demoLon, 8);
  }
  demoLatInput.addEventListener('blur', commitManualDemoCoords);
  demoLonInput.addEventListener('blur', commitManualDemoCoords);
  demoLatInput.addEventListener('keydown', function(e){ if (e.key === 'Enter') demoLatInput.blur(); });
  demoLonInput.addEventListener('keydown', function(e){ if (e.key === 'Enter') demoLonInput.blur(); });
  var demoInputDirty = false; // typed but not committed yet (see saveRotationState)
  demoLatInput.addEventListener('input', function(){ demoLatInput.classList.remove('invalid'); demoInputDirty = true; });
  demoLonInput.addEventListener('input', function(){ demoLonInput.classList.remove('invalid'); demoInputDirty = true; });

  // on / off = a reload into the other database. Your boat in the one you leave goes away for the others
  // first (real -> test: your real boat; test -> real: the test boat), waiting at most 2 s for it.
  var demoSwitching = false;
  function setDemoMode(on){
    if (demoSwitching || on === TEST_MODE) return;
    demoSwitching = true;
    demoModeToggle.disabled = true;
    stopDemoMotion();
    resetSpeedTracking();           // don't mix speeds from the real and the demo position
    trkClearDemo();                 // the demo's track is only for trying the Spår out -- gone when Demo Mode starts/stops
    try {
      localStorage.setItem(DEMO_KEY, on ? '1' : '0');
      if (on){
        localStorage.setItem(DEMO_SINCE_KEY, String(Date.now()));
        setDemoCoords(randomDemoPoint());   // a fresh random spot every time Demo Mode is switched on
        setDemoMovePref(true);              // simulated motion starts right away (switch it off under Settings)
        demoAvg = { b: [] }; saveDemoAvg(); // a fresh demo average every time
        sessionStorage.setItem(DEMO_FRESH_KEY, '1');
      } else localStorage.removeItem(DEMO_SINCE_KEY);
    } catch(e){}
    // the open page (Inställningar ...) comes back, as after turning the phone (92-rotation.js) -- but nothing
    // of the old world's boat: its speeds, when it last shared its position, the demo course
    saveRotationState();
    try { var st = JSON.parse(sessionStorage.getItem(ROT_STATE_KEY)); delete st.speed; delete st.pos; delete st.usage; delete st.demoSim; sessionStorage.setItem(ROT_STATE_KEY, JSON.stringify(st)); } catch(e){}
    var go = function(){ location.reload(); };
    Promise.race([expireOwnPosition(), new Promise(function(r){ setTimeout(r, 2000); })]).then(go, go);
  }
  demoModeToggle.addEventListener('change', function(){
    setDemoMode(demoModeToggle.checked);
  });
  document.getElementById('demoBannerClose').addEventListener('click', function(e){
    e.stopPropagation();
    demoModeToggle.checked = false;
    setDemoMode(false);
  });
  demoRerollBtn.addEventListener('click', function(){
    demoRerollBtn.classList.remove('spinning');
    void demoRerollBtn.offsetWidth;
    demoRerollBtn.classList.add('spinning');
    setTimeout(function(){ demoRerollBtn.classList.remove('spinning'); }, 700);
    rerollDemoPosition();
  });

