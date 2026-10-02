  /* ================= Fångster (catches) for the heat map -- the data =================
     Every catch, wherever it comes from, becomes the same small record (a "catch"):
       { id, t (ms), comp, who, sp ('abborre' | 'gadda' | 'gos'), cm, lat, lon, px, py }
     (px/py = its place on this lake's map picture). The heat map (68-heatmap.js) only ever sees
     these -- so the SOURCE can change without touching it:
       - now:    Firestore catches/<lake> = { rows: '<json [[t, comp, who, sp, cm, lat, lon], ...]>', n },
                 (the CSV import is gone -- the catches are to come from an online database);
       - later:  point CATCH_SOURCE at that database: a new source with the same load(lakeId, cb)
                 (tools/NOTES_HEATMAP.md). */
  var CATCH_CACHE_KEY = lakeKey('ffmap_catches_v1', 'catches_v1');
  var catchData = null, catchLoading = false, catchErr = null, catchVer = 0, catchListeners = [];
  function catchesChanged(){ catchVer++; catchListeners.forEach(function(f){ try { f(); } catch(e){} }); }
  // Kartanalys: the "Från fångsterna" row, and a species chosen there, follow the catches as they arrive
  catchListeners.push(function(){ if (anSet.mode && anSet.mode.indexOf('c_') === 0) anCompute(); else if (anPanel.classList.contains('show')) anRender(); });

  // --- turning anything into catches ---
  function catchNum(v){ if (typeof v === 'number') return v; var n = parseFloat(String(v == null ? '' : v).trim().replace(',', '.')); return isFinite(n) ? n : null; }
  function catchPlain(s){ return String(s || '').toLowerCase().replace(/[åä]/g, 'a').replace(/ö/g, 'o').replace(/[^a-z0-9]/g, ''); }
  function catchSpecies(s){ var p = catchPlain(s); return p.indexOf('abbor') === 0 ? 'abborre' : p.indexOf('gad') === 0 ? 'gadda' : p.indexOf('gos') === 0 ? 'gos' : null; }
  // one catch from a record with (more or less) these names -- the CSV's columns, or a future database's
  function normCatch(o){
    var g = function(){ for (var i = 0; i < arguments.length; i++){ var v = o[arguments[i]]; if (v !== undefined && v !== null && String(v).trim() !== '') return v; } return null; };
    var t = g('t', 'timestamp', 'time', 'tid'), sp = catchSpecies(g('sp', 'species', 'art')), lat = catchNum(g('lat', 'latitude')), lon = catchNum(g('lon', 'lng', 'longitude'));
    t = typeof t === 'number' ? t : Date.parse(String(t || ''));
    if (!isFinite(t) || !sp || lat == null || lon == null || Math.abs(lat) > 90 || Math.abs(lon) > 180) return null;
    var who = String(g('who', 'name', 'namn') || '').trim(), cm = catchNum(g('cm', 'length', 'langd')) || 0, comp = String(g('comp', 'competitionId', 'competition', 'tavling') || '').trim();
    return { id: t + '|' + who + '|' + sp + '|' + cm, t: t, comp: comp, who: who, sp: sp, cm: cm, lat: lat, lon: lon, lake: String(g('lake', 'sjo') || '').trim() };
  }
  function catchPack(list){ return JSON.stringify(list.map(function(c){ return [c.t, c.comp, c.who, c.sp, c.cm, +c.lat.toFixed(6), +c.lon.toFixed(6)]; })); }
  function catchUnpack(rows){
    var a = []; try { a = JSON.parse(rows || '[]'); } catch(e){}
    return a.map(function(r){ return normCatch({ t: r[0], comp: r[1], who: r[2], sp: r[3], cm: r[4], lat: r[5], lon: r[6] }); }).filter(Boolean);
  }
  function catchOnMap(list){
    list.forEach(function(c){ var p = latLonToImgPx(c.lat, c.lon); c.px = p.x; c.py = p.y; });
    return list.sort(function(a, b){ return a.t - b.t; });
  }

  // --- the source (now: Firestore catches/<lake>) ---
  var CATCH_SOURCE = {
    name: 'firestore',
    load: function(lakeId, cb){
      if (!USE_FIREBASE || !catchDb){ cb(new Error('offline')); return; }
      catchDb.collection('catches').doc(lakeId).get().then(function(snap){
        addUsage('r', 1);
        cb(null, snap.exists ? catchUnpack(snap.data().rows) : []);
      }).catch(function(err){ cb(err); });
    }
  };
  function loadCatches(force){
    if (catchLoading || (catchData && catchData.fresh && !force)) return;
    if (!catchData){         // this phone's copy first (instant, and offline)
      try { var c0 = JSON.parse(localStorage.getItem(CATCH_CACHE_KEY) || 'null'); if (c0){ catchData = { list: catchOnMap(catchUnpack(c0.rows)), fresh: false }; catchesChanged(); } } catch(e){}
    }
    catchLoading = true;
    var tries = 0;
    (function go(){
      // (right after a start Firebase may not be signed in yet: wait a little)
      if (!USE_FIREBASE && tries++ < 20){ setTimeout(go, 700); return; }
      CATCH_SOURCE.load(LAKE_ID, function(err, list){
        catchLoading = false;
        if (err){ catchErr = err; if (!catchData) catchData = { list: [], fresh: false }; catchesChanged(); return; }
        catchErr = null;
        catchData = { list: catchOnMap(list), fresh: true };
        try { localStorage.setItem(CATCH_CACHE_KEY, JSON.stringify({ at: Date.now(), rows: catchPack(list) })); } catch(e){}
        catchesChanged();
      });
    })();
  }

  window.__ffCatches = function(){ return catchData ? catchData.list.map(function(c){ return { id: c.id, sp: c.sp, cm: c.cm, who: c.who, comp: c.comp }; }) : null; };
