  /* ================= Fångster (catches) for the heat map -- the data =================
     Every catch, wherever it comes from, becomes the same small record (a "catch"):
       { id, t (ms), comp, who, sp ('abborre' | 'gadda' | 'gos'), cm, lat, lon, px, py }
     (px/py = its place on this lake's map picture). The heat map (68-heatmap.js) only ever sees
     these -- so the SOURCE can change without touching it:
       - now:    Firestore catches/<lake> = { rows: '<json [[t, comp, who, sp, cm, lat, lon], ...]>', n },
                 filled by the admin from a CSV file (Inställningar -> Admin -> Fångster); one read.
       - later:  a live database where the competitions register catches: write a new source with
                 the same load(lakeId, cb) and point CATCH_SOURCE at it (tools/NOTES_HEATMAP.md).
     Which lake a catch belongs to: its position (inside that lake's map) -- a lake name, when there
     is one, must not say it's another lake (a lake next door inside the same map). */
  var CATCH_CACHE_KEY = lakeKey('ffmap_catches_v1', 'catches_v1');
  var catchData = null, catchLoading = false, catchErr = null, catchVer = 0, catchListeners = [];
  function catchesChanged(){ catchVer++; catchListeners.forEach(function(f){ try { f(); } catch(e){} }); }

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
  // a lake of the app whose map the place is inside (and whose name doesn't say otherwise)
  function catchLakeOf(c){
    for (var i = 0; i < LAKES.length; i++){
      var L = LAKES[i], G = L.geo, N = Math.pow(2, G.zoom) * 256;
      var x = (c.lon + 180) / 360 * N - G.originX, r = c.lat * Math.PI / 180;
      var y = (1 - Math.log(Math.tan(r) + 1 / Math.cos(r)) / Math.PI) / 2 * N - G.originY;
      if (x < 0 || y < 0 || x >= G.fullW || y >= G.fullW * G.imgH / G.imgW) continue;
      if (c.lake && catchPlain(c.lake) !== catchPlain(L.name) && catchPlain(c.lake) !== L.id) continue;
      return L.id;
    }
    return null;
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

  // --- the admin's CSV import: parse, sort into lakes, add the new ones (no duplicates) ---
  function parseCsv(text){
    var rows = [], row = [], f = '', q = false;
    text = String(text).replace(/^\ufeff/, '');
    var first = text.split(/\r?\n/)[0], delim = first.indexOf(';') > -1 && first.indexOf(',') < 0 ? ';' : ',';   // (Excel in Swedish saves with ;)
    for (var i = 0; i < text.length; i++){
      var ch = text[i];
      if (q){ if (ch === '"'){ if (text[i + 1] === '"'){ f += '"'; i++; } else q = false; } else f += ch; continue; }
      if (ch === '"') q = true;
      else if (ch === delim){ row.push(f); f = ''; }
      else if (ch === '\n' || ch === '\r'){ if (ch === '\r' && text[i + 1] === '\n') i++; row.push(f); rows.push(row); row = []; f = ''; }
      else f += ch;
    }
    if (f !== '' || row.length){ row.push(f); rows.push(row); }
    return rows;
  }
  // -> { byLake: { id: [catches] }, skipped: { noPos, otherLake, bad } }
  function catchesFromCsv(text){
    var rows = parseCsv(text), head = (rows.shift() || []).map(function(h){ return String(h).trim(); });
    var out = { byLake: {}, skipped: { noPos: 0, otherLake: 0, bad: 0 }, total: 0 };
    rows.forEach(function(r){
      if (!r.some(function(v){ return String(v).trim() !== ''; })) return;
      var o = {}; head.forEach(function(h, i){ if (h) o[h] = r[i]; });
      out.total++;
      var c = normCatch(o);
      if (!c){ if (catchNum(o.lat) == null || catchNum(o.lng != null ? o.lng : o.lon) == null) out.skipped.noPos++; else out.skipped.bad++; return; }
      var lk = catchLakeOf(c); if (!lk){ out.skipped.otherLake++; return; }
      (out.byLake[lk] = out.byLake[lk] || []).push(c);
    });
    return out;
  }
  // add them to catches/<lake> (what's there + the new ones); cb(report lines)
  function uploadCatches(parsed, cb){
    var ids = Object.keys(parsed.byLake), lines = [], left = ids.length;
    if (!ids.length){ cb(lines); return; }
    if (!USE_FIREBASE || !catchDb){ cb(['Ingen anslutning till databasen – inget sparat.']); return; }
    ids.forEach(function(id){
      var name = (LAKES.filter(function(l){ return l.id === id; })[0] || {}).name || id, doc = catchDb.collection('catches').doc(id);
      doc.get().then(function(snap){
        addUsage('r', 1);
        var have = snap.exists ? catchUnpack(snap.data().rows) : [], seen = {}, added = 0;
        have.forEach(function(c){ seen[c.id] = 1; });
        parsed.byLake[id].forEach(function(c){ if (!seen[c.id]){ seen[c.id] = 1; have.push(c); added++; } });
        have.sort(function(a, b){ return a.t - b.t; });
        if (!added){ lines.push(name + ': inga nya (' + have.length + ' sedan tidigare)'); return null; }
        addUsage('w', 1);
        return doc.set({ lake: id, n: have.length, rows: catchPack(have), updatedBy: userName || '', updatedAt: firebase.firestore.FieldValue.serverTimestamp() })
          .then(function(){ lines.push(name + ': ' + added + ' nya (' + have.length + ' totalt)'); if (id === LAKE_ID){ catchData = null; loadCatches(true); } });
      }).catch(function(err){
        lines.push(name + ': kunde inte spara' + (err && err.code === 'permission-denied' ? ' – Firestore-reglerna saknar "catches"' : ' (' + ((err && err.code) || 'fel') + ')'));
      }).then(function(){ if (--left === 0) cb(lines); });
    });
  }
  var catchFileEl = document.getElementById('adminCatchFile'), catchStatusEl = document.getElementById('adminCatchStatus');
  document.getElementById('adminCatchBtn').addEventListener('click', function(){ catchFileEl.value = ''; catchFileEl.click(); });
  catchFileEl.addEventListener('change', function(){
    var f = catchFileEl.files && catchFileEl.files[0]; if (!f) return;
    catchStatusEl.hidden = false; catchStatusEl.textContent = 'Läser ' + f.name + '…';
    var rd = new FileReader();
    rd.onload = function(){
      var p = catchesFromCsv(rd.result), n = 0; Object.keys(p.byLake).forEach(function(k){ n += p.byLake[k].length; });
      var sk = p.skipped, skip = [];
      if (sk.otherLake) skip.push(sk.otherLake + ' i sjöar som inte finns i appen');
      if (sk.noPos) skip.push(sk.noPos + ' utan position');
      if (sk.bad) skip.push(sk.bad + ' med okänd art eller tid');
      catchStatusEl.textContent = p.total + ' rader, ' + n + ' i appens sjöar. Sparar…';
      uploadCatches(p, function(lines){
        catchStatusEl.innerHTML = lines.map(escHtml).join('<br>') + (skip.length ? '<br><span style="color:var(--text-muted)">Hoppade över: ' + escHtml(skip.join(', ')) + '.</span>' : '') +
          (!lines.length ? 'Inga fångster i appens sjöar i filen.' : '');
      });
    };
    rd.onerror = function(){ catchStatusEl.textContent = 'Kunde inte läsa filen.'; };
    rd.readAsText(f, 'utf-8');
  });
  window.__ffCatches = function(){ return catchData ? catchData.list.map(function(c){ return { id: c.id, sp: c.sp, cm: c.cm, who: c.who, comp: c.comp }; }) : null; };
