  /* ================= Mätverktyg =================
     Tap points on the map (or on a fishing spot / boat to snap onto it);
     shows the distance start -> end along the points and the travel time.
     Nothing is saved or shared. */
  var measureMode = false;
  var measurePts = [];
  var measureBtn = document.getElementById('measureBtn');
  var measurePanel = document.getElementById('measurePanel');
  var measureSvg = document.getElementById('measureLayer');
  var mlUnder = measureSvg.querySelector('.mlUnder');
  var mlLine = measureSvg.querySelector('.mlLine');
  var mlPts = measureSvg.querySelector('.mlPts');
  var mlLabel = measureSvg.querySelector('.mlLabel');
  var mpMain = document.getElementById('mpMain');
  var mpSub = document.getElementById('mpSub');
  var mpUndo = document.getElementById('mpUndo');
  var mpClear = document.getElementById('mpClear');

  // kept on the phone until you close the tool with ✕ -- the home-screen app
  // reloads the page when you rotate the phone, which used to wipe it
  var MEASURE_KEY = lakeKey('ffmap_measure_v1', 'measure_v1');
  function saveMeasure(){
    try {
      if (measureMode) localStorage.setItem(MEASURE_KEY, JSON.stringify({ on: true, pts: measurePts }));
      else localStorage.removeItem(MEASURE_KEY);
    } catch(e){}
  }
  function setMeasureMode(on){
    measureMode = on;
    if (on && probe) setProbe(null); // the measuring tool takes over taps
    measurePts = [];
    cancelLongPress();
    lastTap = null;
    measureBtn.classList.toggle('active', on);
    measurePanel.classList.toggle('show', on);
    document.body.classList.toggle('measuring', on);
    renderMeasure();
    updateMeasurePanel();
    saveMeasure();
  }
  measureBtn.addEventListener('click', function(){ setMeasureMode(!measureMode); });
  document.getElementById('mpClose').addEventListener('click', function(){ setMeasureMode(false); });
  mpClear.addEventListener('click', function(){ measurePts = []; renderMeasure(); updateMeasurePanel(); saveMeasure(); });
  mpUndo.addEventListener('click', function(){ measurePts.pop(); renderMeasure(); updateMeasurePanel(); saveMeasure(); });

  function addMeasurePoint(lat, lon){
    measurePts.push({ lat: lat, lon: lon });
    if (navigator.vibrate){ try { navigator.vibrate(8); } catch(e){} }
    renderMeasure();
    updateMeasurePanel();
    saveMeasure();
  }
  function addMeasurePointAtScreen(sx, sy){
    var ll = imgPxToLatLon((sx - originX) / scale, (sy - originY) / scale);
    addMeasurePoint(ll.lat, ll.lon);
  }
  function measureDistanceM(){
    var d = 0;
    for (var i = 1; i < measurePts.length; i++){
      d += haversineKm(measurePts[i-1].lat, measurePts[i-1].lon, measurePts[i].lat, measurePts[i].lon) * 1000;
    }
    return d;
  }
  function fmtDist(m){
    if (m < 1000) return Math.round(m) + ' m';
    return (m / 1000).toFixed(m < 10000 ? 2 : 1).replace('.', ',') + ' km';
  }
  function fmtDuration(sec){
    var min = Math.round(sec / 60);
    if (min < 1) return 'under 1 min';
    if (min < 60) return 'ca ' + min + ' min';
    var h = Math.floor(min / 60), mm = min % 60;
    return 'ca ' + h + ' h ' + (mm < 10 ? '0' : '') + mm + ' min';
  }
  function updateMeasurePanel(){
    if (!measureMode) return;
    var n = measurePts.length;
    mpUndo.disabled = n === 0;
    mpClear.disabled = n === 0;
    if (n === 0){
      mpMain.textContent = 'Tryck på kartan';
      mpSub.textContent = 'Sätt ut startpunkten (eller tryck på en fiskeplats)';
      return;
    }
    if (n === 1){
      mpMain.textContent = 'Tryck ut nästa punkt';
      mpSub.textContent = 'Startpunkt satt';
      return;
    }
    var m = measureDistanceM();
    var sp = effectiveSpeed();
    mpMain.textContent = fmtDist(m) + ' · ' + fmtDuration(m / (sp.kn / KN_PER_MS));
    mpSub.textContent = n + ' punkter · vid ' + fmtKn(sp.kn) + ' kn (' + (sp.src === 'avg' ? 'din snittfart' : 'marschfart') + ')';
  }
  function renderMeasure(){
    if (!measureMode || !measurePts.length){
      mlUnder.setAttribute('points', ''); mlLine.setAttribute('points', '');
      mlPts.innerHTML = ''; mlLabel.textContent = '';
      return;
    }
    var pts = measurePts.map(function(q){
      var ip = latLonToImgPx(q.lat, q.lon);
      return [originX + ip.x * scale, originY + ip.y * scale];
    });
    var str = pts.map(function(q){ return q[0].toFixed(1) + ',' + q[1].toFixed(1); }).join(' ');
    mlUnder.setAttribute('points', str);
    mlLine.setAttribute('points', str);
    var html = '';
    pts.forEach(function(q, i){
      html += '<circle class="mlPt' + (i === 0 ? ' start' : '') + '" cx="' + q[0].toFixed(1) + '" cy="' + q[1].toFixed(1) + '" r="' + (i === 0 || i === pts.length - 1 ? 6 : 4.5) + '"></circle>';
    });
    mlPts.innerHTML = html;
    if (pts.length > 1){
      var last = pts[pts.length - 1];
      mlLabel.setAttribute('x', (last[0] + 10).toFixed(1));
      mlLabel.setAttribute('y', (last[1] - 10).toFixed(1));
      mlLabel.textContent = fmtDist(measureDistanceM());
    } else {
      mlLabel.textContent = '';
    }
  }

  // bring back a measurement that was open before the page reloaded
  try {
    var savedMeasure = JSON.parse(localStorage.getItem(MEASURE_KEY) || 'null');
    if (savedMeasure && savedMeasure.on){
      setMeasureMode(true);
      measurePts = (savedMeasure.pts || []).filter(function(q){ return q && isFinite(q.lat) && isFinite(q.lon); });
      renderMeasure();
      updateMeasurePanel();
      saveMeasure();
    }
  } catch(e){}

  // once a second: knot meter, the measuring panel (the speed it uses can
  // change while you drive) and the speed numbers under Settings
  setInterval(function(){
    updateSpeedPill();
    if (measureMode) updateMeasurePanel();
    if (settingsView.classList.contains('show')) updateSpeedSettings();
  }, 1000);

