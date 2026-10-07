  /* ================= Fångster (catches) for the heat map -- the data =================
     Every catch, wherever it comes from, becomes the same small record (a "catch"):
       { id, t (ms), comp, who, sp ('abborre' | 'gadda' | 'gos'), cm, lat, lon, px, py }
     (px/py = its place on this lake's map picture). The heat map (68-heatmap.js) only ever sees
     these. The source: Fiskfiskarnas API (Jonathan, no sign-in to read; tools/NOTES_HEATMAP.md):
       - history: dashboard.php -> .heatmap (every competition catch with GPS) + .competitions (status);
         fetched at start / when the heat map is turned on, only when catchHistDue() says so;
       - live:    tavling.php?action=bootstrap -> .catches of a competition going on on this lake:
         when the app opens, then every 5 min (30 s while the heat map is on), only while visible.
     This phone's copy (localStorage) = the lake's catches + its competitions -> offline, between competitions.
     Which lake a catch belongs to: its position (inside that lake's map) -- a lake name, when there
     is one, must not say it's another lake (a lake next door inside the same map). */
  var CATCH_API = 'https://fiskfiskarna.se/api/';
  var CATCH_REAL_KEY = lakeKey('ffmap_catches_v1', 'catches_v1'), CATCH_CACHE_KEY = testKey(CATCH_REAL_KEY), CATCH_NET_KEY = 'ffmap_catchnet_v1';
  var CATCH_HOUR = 3600e3, CATCH_DAY = 864e5, CATCH_LIVE_SLOW = 300e3, CATCH_LIVE_HZ = 120e3, CATCH_LIVE_FAST = 30e3;
  var catchData = null, catchLoading = false, catchErr = null, catchVer = 0, catchListeners = [];
  var catchHist = null, catchLive = null, catchLiveTimer = null;   // (catchHist: { at, list, comps, total })
  function catchesChanged(){ catchVer++; catchListeners.forEach(function(f){ try { f(); } catch(e){} }); }
  // Kartanalys: the "Från fångsterna" row, and a species chosen there, follow the catches as they arrive
  catchListeners.push(function(){ if (anSet.mode && (anSet.mode.indexOf('c_') === 0 || anSet.mode.indexOf('n_') === 0)) anCompute(); else if (anPanel.classList.contains('show')) anRender(); });

  // --- turning anything into catches ---
  function catchNum(v){ if (typeof v === 'number') return v; var n = parseFloat(String(v == null ? '' : v).trim().replace(',', '.')); return isFinite(n) ? n : null; }
  function catchPlain(s){ return String(s || '').toLowerCase().replace(/[åä]/g, 'a').replace(/ö/g, 'o').replace(/[^a-z0-9]/g, ''); }
  function catchSpecies(s){ var p = catchPlain(s); return p.indexOf('abbor') === 0 ? 'abborre' : p.indexOf('gad') === 0 ? 'gadda' : p.indexOf('gos') === 0 ? 'gos' : null; }
  // one catch from a record with (more or less) these names -- the CSV's columns, or a future database's
  // (anyPlace: a catch without a usable position is kept too, lat/lon null -- the competition's own list)
  function normCatch(o, anyPlace){
    var g = function(){ for (var i = 0; i < arguments.length; i++){ var v = o[arguments[i]]; if (v !== undefined && v !== null && String(v).trim() !== '') return v; } return null; };
    var t = g('t', 'timestamp', 'time', 'tid'), sp = catchSpecies(g('sp', 'species', 'art')), lat = catchNum(g('lat', 'latitude')), lon = catchNum(g('lon', 'lng', 'longitude'));
    t = typeof t === 'number' ? t : Date.parse(String(t || ''));
    if (lat == null || lon == null || Math.abs(lat) > 90 || Math.abs(lon) > 180){ if (anyPlace !== true) return null; lat = lon = null; }   // (=== true: .map(normCatch) passes the index)
    if (!isFinite(t) || !sp) return null;
    var who = String(g('who', 'name', 'namn') || '').trim(), cm = catchNum(g('cm', 'length', 'langd')) || 0, comp = String(g('comp', 'competitionId', 'competition', 'tavling') || '').trim();
    var c = { id: t + '|' + who + '|' + sp + '|' + cm, t: t, comp: comp, who: who, sp: sp, cm: cm, lat: lat, lon: lon, lake: String(g('lake', 'sjo') || '').trim() };
    if (o.approved === false) c.no = 1;   // (live: not counted, e.g. a perch under 25 cm)
    var img = String(o.imageUrl || '');  // (live: the photo -- Cloudinary, asked for 600 px wide instead of 2000)
    if (/^https:\/\//.test(img) || (TEST_MODE && img === TEST_IMG)) c.img = img.replace(/(res\.cloudinary\.com\/[^/]+\/image\/upload\/)w_\d+,/, '$1w_600,');
    return c;
  }
  // the same water? ("Sibbo" = Sibbofjärden, id or name)
  function catchSameWater(name, L){ var p = catchPlain(name), n = catchPlain(L.name); return !!p && (p === L.id || n.indexOf(p) === 0 || p.indexOf(n) === 0); }
  // a lake of the app whose map the place is inside (and whose name doesn't say otherwise)
  function catchLakeOf(c){
    for (var i = 0; i < LAKES.length; i++){
      var L = LAKES[i], G = L.geo, N = Math.pow(2, G.zoom) * 256;
      var x = (c.lon + 180) / 360 * N - G.originX, r = c.lat * Math.PI / 180;
      var y = (1 - Math.log(Math.tan(r) + 1 / Math.cos(r)) / Math.PI) / 2 * N - G.originY;
      if (x < 0 || y < 0 || x >= G.fullW || y >= G.fullW * G.imgH / G.imgW) continue;
      if (c.lake && !catchSameWater(c.lake, L)) continue;
      return L.id;
    }
    return null;
  }
  function catchPack(list){ return JSON.stringify(list.map(function(c){ return [c.t, c.comp, c.who, c.sp, c.cm, c.lat == null ? null : +c.lat.toFixed(6), c.lon == null ? null : +c.lon.toFixed(6), c.lake || '']; })); }
  function catchUnpack(rows, anyPlace){
    var a = []; try { a = JSON.parse(rows || '[]'); } catch(e){}
    return a.map(function(r){ return normCatch({ t: r[0], comp: r[1], who: r[2], sp: r[3], cm: r[4], lat: r[5], lon: r[6], lake: r[7] }, anyPlace === true); }).filter(Boolean);
  }
  function catchOnMap(list){
    list.forEach(function(c){ var p = latLonToImgPx(c.lat, c.lon); c.px = p.x; c.py = p.y; });
    return list.sort(function(a, b){ return a.t - b.t; });
  }

  // --- Fiskfiskarnas API: a GET, counted per day on this phone (Inställningar -> Fångstdata) ---
  function catchNet(){
    var d = new Date(), day = d.getFullYear() + '-' + (d.getMonth() + 1) + '-' + d.getDate(), s = null;
    try { s = JSON.parse(localStorage.getItem(CATCH_NET_KEY) || 'null'); } catch(e){}
    return s && s.day === day ? s : { day: day, h: 0, hb: 0, l: 0, lb: 0 };
  }
  function catchErrOf(e){ return { at: Date.now(), msg: e instanceof TypeError ? 'ingen anslutning' : String((e && e.message) || 'fel') }; }
  function catchGet(path, kind, cb, real){   // (real: the real API also in Demo Mode -- only the profiles, 67-profiles.js)
    if (TEST_MODE && !real){ setTimeout(function(){ cb(null, testApi(path)); }, 0); return; }   // (the test mode: the made-up competition, 37-testmode.js -- never the real API)
    var res;
    (window.fetch ? fetch(CATCH_API + path, { cache: 'no-store' }) : Promise.reject(new Error('fetch saknas'))).then(function(r){
      return r.text().then(function(t){
        var s = catchNet(); s[kind]++; s[kind + 'b'] += (+r.headers.get('content-length')) || t.length;   // (what came over the net: gzip)
        try { localStorage.setItem(CATCH_NET_KEY, JSON.stringify(s)); } catch(e){}
        if (!r.ok) throw new Error('HTTP ' + r.status);
        res = JSON.parse(t);
      });
    }).then(function(){ cb(null, res); }, function(e){ cb(e || new Error('fel')); });
  }

  // --- the history (dashboard.php): only when it can have changed ---
  function catchLakeComps(status){ return catchHist ? catchHist.comps.filter(function(c){ return c.status === status; }) : []; }
  function catchTodayIso(){ var d = new Date(); return d.getFullYear() + '-' + pad2(d.getMonth() + 1) + '-' + pad2(d.getDate()); }
  // a competition going on, or one that should have started (its date has come) -> look every hour
  function catchCompSoon(){
    var d = catchTodayIso();
    return catchLakeComps('active').length > 0 || catchLakeComps('planned').some(function(c){ return /^\d{4}-\d\d-\d\d$/.test(c.date) && c.date <= d; });
  }
  // fetch the history again? -> why (in words), or null = the copy will do
  function catchHistDue(){
    if (!catchHist) return 'ingen kopia i telefonen';
    var age = Date.now() - catchHist.at;
    if (catchCompSoon() && age > CATCH_HOUR) return catchLakeComps('active').length ? 'en tävling pågick' : 'en tävling skulle ha börjat';
    if (age > CATCH_DAY) return 'kopian är äldre än ett dygn';
    return null;
  }
  function catchHistNextAt(){ return catchHist ? catchHist.at + (catchCompSoon() ? CATCH_HOUR : CATCH_DAY) : 0; }
  function catchReadCopy(){
    if (catchHist) return;
    try { var c = JSON.parse(localStorage.getItem(CATCH_CACHE_KEY) || 'null');
      if (c && c.v === 4) catchHist = { at: c.at, total: c.total, comps: c.comps || [], prof: c.prof || {}, list: catchUnpack(c.rows), away: catchUnpack(c.away, true) }; } catch(e){}   // (v3: no "away" -> fetched again)
    if (catchHist) catchMerge();
  }
  // the history + the live catches (the same catch once) -> catchData:
  //   list = caught in this lake (heat map, Kartanalys); comp = that + the lake's competitions in other waters (the profile)
  function catchMerge(){
    var once = function(lists){ var seen = {}, out = []; lists.forEach(function(l){ l.forEach(function(c){ if (!seen[c.id]){ seen[c.id] = 1; out.push(c); } }); }); return out; };
    var H = catchHist || { list: [], away: [] }, L = catchLive || { list: [], all: [] };
    var list = catchOnMap(once([H.list, L.list]));
    catchData = { list: list, comp: once([list, H.away, L.all]).sort(function(a, b){ return a.t - b.t; }) };
    catchesChanged();
  }
  function loadHistory(){
    if (catchLoading) return;
    catchLoading = true; catchesChanged();
    catchGet('dashboard.php', 'h', function(err, d){
      catchLoading = false;
      if (!err && !(d && Array.isArray(d.heatmap))) err = new Error('oväntat svar');
      if (err){ catchErr = catchErrOf(err); if (!catchData) catchData = { list: [], comp: [] }; catchesChanged(); return; }
      catchErr = null;
      var comps = (d.competitions || []).filter(function(c){ return catchSameWater(c.water || c.location, LAKE); })
          .map(function(c){ return { id: String(c.competition_id), name: c.competition_name || '', date: c.date || '', status: c.status || '' }; });
      var ids = {}; comps.forEach(function(c){ ids[c.id] = 1; });
      var all = d.heatmap.map(function(x){ return normCatch(x, true); }).filter(Boolean);
      var here = function(c){ return c.lat != null && catchLakeOf(c) === LAKE_ID; };
      catchHist = { at: Date.now(), total: d.heatmap.length, prof: profPack(d), comps: comps,   // (profPack: 67-profiles.js)
        list: all.filter(here),
        away: all.filter(function(c){ return ids[c.comp] && !here(c); }) };   // (the lake's competitions, caught in another water: the profile)
      try { localStorage.setItem(CATCH_CACHE_KEY, JSON.stringify({ v: 4, at: catchHist.at, total: catchHist.total, comps: catchHist.comps, prof: catchHist.prof, rows: catchPack(catchHist.list), away: catchPack(catchHist.away) })); } catch(e){}
      catchMerge();
      catchLiveTick();
    });
  }
  // the heat map / Kartanalys want the catches (force: "Hämta nu")
  function loadCatches(force){
    catchReadCopy();
    if (force || catchHistDue()) loadHistory();
    catchLiveTick();
  }

  // --- live (tavling.php bootstrap): a competition going on on this lake, while the app is in view ---
  function catchLiveComp(){ return catchLakeComps('active')[0] || null; }
  function catchLiveFast(){ return !!(hmOn || (anSet.mode && anSet.mode.indexOf('c_') === 0)); }
  // (opening: the app just started / came back -> fetch now if the last is > 60 s old)
  function catchLiveTick(opening){
    clearTimeout(catchLiveTimer); catchLiveTimer = null;
    var c = catchLiveComp();
    if (!c){ if (catchLive){ catchLive = null; catchMerge(); } return; }
    if (document.visibilityState === 'hidden' || (catchLive && catchLive.loading)) return;
    var last = catchLive && catchLive.comp === c.id ? catchLive.at : 0, rate = catchLiveFast() ? CATCH_LIVE_FAST : hzOn ? CATCH_LIVE_HZ : CATCH_LIVE_SLOW;   // (hzOn: Hotzone, 70-hotzone.js)
    var wait = opening && Date.now() - last > 60e3 ? 0 : last + rate - Date.now();
    if (wait > 0){ catchLiveTimer = setTimeout(catchLiveTick, wait); return; }
    if (!catchLive || catchLive.comp !== c.id) catchLive = { comp: c.id, name: c.name, at: 0, list: [], all: [] };
    var L = catchLive; L.loading = true;
    catchGet('tavling.php?action=bootstrap&competitionId=' + encodeURIComponent(c.id), 'l', function(err, d){
      L.loading = false; L.at = Date.now();
      if (!err && !(d && d.ok && Array.isArray(d.catches))) err = new Error((d && d.error) || 'oväntat svar');
      if (err) L.err = catchErrOf(err);
      else {   // (an annulled catch = the catch + a "VOID" row pointing at it: both go)
        var voided = {}; d.catches.forEach(function(x){ if (x.voidRef) voided[x.voidRef] = 1; });
        L.err = null;
        // all: the whole competition, whichever water (Ledare, Senaste fisk); list: only those caught in this lake (the heat map)
        L.all = d.catches.filter(function(x){ return x.displayValue !== 'VOID' && !voided[x.timestamp]; })
          .map(function(x){ return normCatch(x, true); }).filter(Boolean);
        L.list = L.all.filter(function(x){ return x.lat != null && catchLakeOf(x) === LAKE_ID; });
      }
      if (catchLive === L) catchMerge();
      catchLiveTick();
    });
  }
  document.addEventListener('visibilitychange', function(){
    if (document.visibilityState !== 'visible'){ clearTimeout(catchLiveTimer); catchLiveTimer = null; return; }
    if (catchHistDue()) loadHistory();
    catchLiveTick(true);
  });
  // at start (a moment after the map): the copy, the history if it's due, live if a competition is on
  setTimeout(function(){ catchReadCopy(); if (catchHistDue()) loadHistory(); catchLiveTick(true); }, 1200);

  // --- Inställningar -> Fångstdata: what this phone has fetched ---
  function catchClock(t){ var d = new Date(t); return (new Date().toDateString() === d.toDateString() ? '' : d.getDate() + '/' + (d.getMonth() + 1) + ' ') + pad2(d.getHours()) + ':' + pad2(d.getMinutes()); }
  function catchAgo(t){ var m = Math.round((Date.now() - t) / 60000); return m < 1 ? 'nyss' : m < 60 ? 'för ' + m + ' min sedan' : m < 1440 ? 'för ' + Math.round(m / 60) + ' h sedan' : 'för ' + Math.round(m / 1440) + ' d sedan'; }
  function catchKb(b){ return b >= 1e6 ? (b / 1e6).toFixed(1).replace('.', ',') + ' MB' : Math.max(b ? 1 : 0, Math.round(b / 1e3)) + ' kB'; }
  function catchSum(){   // (the line under the closed title)
    var c = catchLiveComp();
    return [catchData ? catchData.list.length + ' fångster' : 'inte hämtade', c ? 'Live: ' + (c.name || c.id) : catchHist && 'hämtade ' + catchClock(catchHist.at)];
  }
  function catchRenderSettings(){
    var el = document.getElementById('ctInfo'); if (!el) return;
    var h = catchHist, c = catchLiveComp(), L = catchLive, s = catchNet(), due = catchHistDue(), copy = 0;
    var row = function(k, v){ return '<div class="ctRow"><span>' + k + '</span><b>' + v + '</b></div>'; };
    try { copy = (localStorage.getItem(CATCH_CACHE_KEY) || '').length; } catch(e){}
    var comps = h ? h.comps.filter(function(x){ return x.status === 'active' || x.status === 'planned'; }) : [];
    var done = h ? h.comps.filter(function(x){ return x.status === 'done'; }).sort(function(a, b){ return a.date < b.date ? 1 : -1; })[0] : null;
    var err = catchErr || (L && L.err);
    el.innerHTML = '<div class="ctHead">Historik</div>' +
      row('Senast hämtad', catchLoading ? 'hämtar…' : h ? catchClock(h.at) + ' (' + catchAgo(h.at) + ')' : 'aldrig') +
      row('Fångster', h ? h.list.length + ' i ' + escHtml(LAKE.name) + ' · ' + h.total + ' totalt' : '–') +
      row('Kopian', h ? catchKb(copy) + ' i telefonen' : '–') +
      row('Nästa hämtning', due ? 'nu – ' + due : 'vid start efter ' + catchClock(catchHistNextAt()) + (catchCompSoon() ? ' (tävling)' : ' (ett dygn)')) +
      '<div class="ctHead">Tävlingar i ' + escHtml(LAKE.name) + '</div>' +
      comps.map(function(x){ return row((x.status === 'active' ? '● ' : '○ ') + escHtml(x.name || x.id), x.status === 'active' ? 'pågår' : 'planerad ' + escHtml(x.date)); }).join('') +
      (done ? row('Senaste', escHtml(done.name || done.id) + ' · ' + escHtml(done.date)) : '') +
      (!comps.length && !done ? '<div class="ctRow"><span>Inga ännu</span></div>' : '') +
      '<div class="ctHead">Live</div>' +
      (c ? row('Status', 'på – ' + escHtml(c.name || c.id) + ' pågår') +
           row('Takt', catchLiveFast() ? 'var 30:e s (heatmapen är på)' : hzOn ? 'var 2:a min (Hotzone är på)' : 'var 5:e min') +
           row('Senast hämtad', L && L.at ? catchClock(L.at) + ':' + pad2(new Date(L.at).getSeconds()) + ' · ' + L.list.length + ' fångster' : 'hämtar…')
         : row('Status', 'av – ingen tävling pågår')) +
      '<div class="ctHead">Idag</div>' +
      row('Anrop', 'historik ' + s.h + ' · live ' + s.l) + row('Data', '≈ ' + catchKb(s.hb + s.lb)) +
      (err ? row('Senaste fel', escHtml(err.msg) + ' ' + catchClock(err.at)) : '');
  }
  catchListeners.push(function(){ setSums(); });
  document.getElementById('ctFetch').addEventListener('click', function(){ if (catchLive) catchLive.at = 0; loadCatches(true); });

  window.__ffCatches = function(){ return catchData ? catchData.list.map(function(c){ return { id: c.id, sp: c.sp, cm: c.cm, who: c.who, comp: c.comp }; }) : null; };

  /* --- Tävlingsnotisen (was the lock until 2026-10-07, tools/PLAN_TAVLINGSLAS.md): spots can always be added, changed
     and removed. Outside a competition on this lake (more than a week before / after one) the first change of the day shows
     a note instead: no competition now (the next one, if it has a date), Demo Mode to just try, and that private fishing and
     open competitions are welcome. "Fortsätt" does what you were doing; at most once a day per lake and phone. Never in
     Demo Mode, for an unlocked admin, or when the app doesn't know (no copy, the API not answering). Filip 2026-10-07. */
  var LOCK_DAYS = 7, LOCK_NOTE_KEY = lakeKey('ffmap_compnote_v1', 'compnote_v1'), lockThen = null, lockGo = false;
  function lockDays(c){ return /^\d{4}-\d\d-\d\d$/.test(c.date) ? Math.round((Date.parse(c.date) - Date.parse(catchTodayIso())) / CATCH_DAY) : null; }
  function compNear(){
    if (TEST_MODE || isAdminUnlocked() || window.__ffNoLock) return true;   // (__ffNoLock: only the test browser, fakefb.py)
    catchReadCopy();
    if (!catchHist || catchErr) return true;
    return catchHist.comps.some(function(c){ var d = lockDays(c); return c.status === 'active' || (d !== null && Math.abs(d) <= LOCK_DAYS); });
  }
  // true = the note is shown and `then` waits for "Fortsätt" (the caller stops); false = go on
  function compNote(then){
    if (lockGo || compNear()) return false;
    try { if (Date.now() - (+localStorage.getItem(LOCK_NOTE_KEY) || 0) < CATCH_DAY) return false; localStorage.setItem(LOCK_NOTE_KEY, String(Date.now())); } catch(e){}
    lockThen = then; showLockCard(); return true;
  }
  var lockBackdrop = document.getElementById('lockBackdrop'), lockCard = document.getElementById('lockCard');
  var LOCK_WD = ['söndag', 'måndag', 'tisdag', 'onsdag', 'torsdag', 'fredag', 'lördag'];
  var LOCK_MON = ['januari', 'februari', 'mars', 'april', 'maj', 'juni', 'juli', 'augusti', 'september', 'oktober', 'november', 'december'];
  function showLockCard(){
    // ponytail: a copy over an hour old is asked again now; the answer counts from the next try
    if (catchHist && !catchLoading && Date.now() - catchHist.at > CATCH_HOUR) loadHistory();
    var cs = catchHist ? catchHist.comps.filter(function(c){ return c.status === 'planned' || c.status === 'active' || lockDays(c) > 0; }) : [];
    var next = cs.filter(function(c){ return lockDays(c) > 0; }).sort(function(a, b){ return a.date < b.date ? -1 : 1; })[0] || cs[0], at = next && lockDays(next) !== null ? new Date(next.date + 'T12:00:00Z') : null;
    document.getElementById('lockTitle').textContent = 'Ingen tävling pågår i ' + LAKE.name;
    document.getElementById('lockWhen').innerHTML = next ? 'Nästa tävling i ' + escHtml(LAKE.name) + ': <b>' + escHtml(next.name || 'tävling') + '</b>' +
      (at ? ', ' + LOCK_WD[at.getUTCDay()] + ' ' + at.getUTCDate() + ' ' + LOCK_MON[at.getUTCMonth()] + '.' : ' (datum inte bestämt).') : 'Ingen tävling i ' + escHtml(LAKE.name) + ' är planerad just nu.';
    lockBackdrop.classList.add('show'); lockCard.classList.add('show');
  }
  function hideLockCard(){ lockBackdrop.classList.remove('show'); lockCard.classList.remove('show'); lockThen = null; }
  lockBackdrop.addEventListener('click', hideLockCard);
  document.getElementById('lockClose').addEventListener('click', function(){ var t = lockThen; hideLockCard(); if (t){ lockGo = true; try { t(); } finally { lockGo = false; } } });   // "Fortsätt" (lockGo: what it does doesn't ask again)
  document.getElementById('lockDemo').addEventListener('click', function(){   // (like Hjälp's Demo Mode link, 30-help.js)
    hideLockCard(); if (wpSheet.classList.contains('show')) closeSheet();
    showSettingsView(); openSettingsSec('adv');
    setTimeout(function(){ document.getElementById('demoModeToggle').scrollIntoView({ block: 'center' }); }, 50);
  });
  window.__ffLock = function(){ return { near: compNear(), shown: lockCard.classList.contains('show'), when: document.getElementById('lockWhen').textContent }; };
