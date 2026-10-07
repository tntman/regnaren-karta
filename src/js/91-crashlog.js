  /* ---- crash log (Inställningar → Avancerat → Senaste krasch) ----
     iOS shows a crashed page only as a reload, with no log. While the app runs, one line
     of what it was doing is written over and over to localStorage; pagehide/hidden marks
     it "closed cleanly". If the next start finds it not clean, that line was the last
     thing before the crash. Stays on the phone -- nothing is sent anywhere. */
  var CRASH_KEY = 'ffmap_crashlog_v1', CRASH_LAST_KEY = 'ffmap_crashlog_last_v1';
  var crashT0 = Date.now(), crashPeak = 0, crashZooms = 0, crashLastZ = null, crashErr = '';
  function crashLine(){
    var tiles = Object.keys(detailEls).length, L = null, z = 0, canv = 0;
    crashPeak = Math.max(crashPeak, tiles);
    try { L = detailLevel(); z = currentZoom(); } catch(e){}
    document.querySelectorAll('canvas').forEach(function(c){ canv += c.width * c.height; });
    return {
      t: Date.now(), ver: document.lastModified, lake: LAKE_ID, up: Math.round((Date.now() - crashT0) / 1000),
      zoom: Math.round(z * 10) / 10, level: L ? L.z : 14, tiles: tiles, peak: crashPeak, zooms: crashZooms,
      imgs: document.images.length, canvasMP: Math.round(canv / 1e5) / 10,
      style: mapStyle, an: anSet.mode || '', hm: hmOn, err: crashErr, clean: false
    };
  }
  function crashWrite(clean){
    try { var o = crashLine(); o.clean = !!clean; localStorage.setItem(CRASH_KEY, JSON.stringify(o)); } catch(e){}
  }
  function crashText(o){
    function hm(t){ var d = new Date(t); return d.toLocaleDateString('sv-SE') + ' ' + d.toLocaleTimeString('sv-SE'); }
    return hm(o.t) + ' · ' + o.lake + (o.ver ? ' · version ' + o.ver : '') + ' · zoom ' + o.zoom + ' (nivå ' + o.level + ') · bitar ' + o.tiles + ' (max ' + o.peak + ')' +
      ' · bilder ' + o.imgs + ' · canvas ' + o.canvasMP + ' MP · zoombyten ' + o.zooms + ' · igång ' + o.up + ' s · kartläge ' + o.style +
      (o.an ? ' · Kartanalys ' + o.an : '') + (o.hm ? ' · Heatmap' : '') + (o.err ? ' · fel: ' + o.err : '');
  }
  // the previous run: not closed cleanly = crashed
  try {
    var crashPrev = JSON.parse(localStorage.getItem(CRASH_KEY) || 'null');
    if (crashPrev && !crashPrev.clean) localStorage.setItem(CRASH_LAST_KEY, JSON.stringify(crashPrev));
  } catch(e){}
  var crashTextEl = document.getElementById('crashText'), crashCopyBtn = document.getElementById('crashCopyBtn');
  function crashShow(){
    var last = null;
    try { last = JSON.parse(localStorage.getItem(CRASH_LAST_KEY) || 'null'); } catch(e){}
    crashTextEl.textContent = last ? crashText(last) : 'Ingen krasch sparad.';
    crashCopyBtn.hidden = !last;
  }
  crashShow();
  crashCopyBtn.addEventListener('click', function(){
    var s = crashTextEl.textContent;
    try { navigator.clipboard.writeText(s).then(function(){ crashCopyBtn.textContent = 'Kopierat'; }); } catch(e){}
  });
  window.addEventListener('error', function(e){ crashErr = String(e.message || '').slice(0, 120); });
  setInterval(function(){
    var z = null;
    try { z = detailLevel(); z = z ? z.z : 14; } catch(e){}
    if (crashLastZ !== null && z !== crashLastZ) crashZooms++;
    crashLastZ = z;
    if (!document.hidden) crashWrite(false);
  }, 2000);
  // the peak between the 2-s writes (zooming fast in and out piles pieces up)
  new MutationObserver(function(){ crashPeak = Math.max(crashPeak, detailLayer.childElementCount); }).observe(detailLayer, { childList: true });
  crashWrite(false);
  window.addEventListener('pagehide', function(){ crashWrite(true); });
  document.addEventListener('visibilitychange', function(){ crashWrite(document.hidden); });
