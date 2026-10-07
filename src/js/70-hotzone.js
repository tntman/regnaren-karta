  /* ================= "Hotzone" (Filter, Lager) -- on by default =================
     While a competition is going on on this lake: where it bites right now. A spot is hot when 4 fish have been
     caught within 200 m in the last hour (whoever caught them); it lives as long as it keeps biting (a catch within
     the hour). Every hot spot gets a red dashed ring that breathes, with 🔥 and the count of the last hour. A new hot
     spot gives a note at the top (species, the nearest place name, how far) -- at most one note per 45 min; a spot
     that turns hot during the pause only gets its ring. Data: the live catches in the lake (catchLive.list,
     66-catches.js), fetched every 2 min while this is on. Thresholds tried on the real catches: tools/NOTES_HOTZONE.md. */
  var HZ_KEY = 'ffmap_hotzone_v1', HZ_NOTE_KEY = lakeKey('ffmap_hotzone_note_v1', 'hotzone_note_v1');
  var HZ_R = 200, HZ_N = 4, HZ_WIN = 3600e3, HZ_PAUSE = 45 * 60e3, HZ_SHOW = 10e3;
  var HZ_PL = { abborre: 'abborrar', gadda: 'gäddor', gos: 'gösar' };
  var hzOn = true;   // (on unless you switched it off: '0')
  try { hzOn = localStorage.getItem(HZ_KEY) !== '0'; } catch(e){}
  var hzEl = document.getElementById('hzLayer'), hzNote = document.getElementById('hzNote'), toggleHzEl = document.getElementById('toggleHotzone');
  var hzZones = [], hzNoteZone = null, hzNoteTimer = null, hzTick = null;
  // which spots have had their say: { at: the last note, ids: { zoneId: last seen } } -- kept over a reload/rotation
  var hzSaid = { at: 0, ids: {} };
  try { hzSaid = Object.assign(hzSaid, JSON.parse(localStorage.getItem(HZ_NOTE_KEY) || '{}')); } catch(e){}
  function hzM(a, b){ return haversineKm(a.lat, a.lon, b.lat, b.lon) * 1000; }

  // the hot spots now: catches in time order; one that makes 4 within 200 m in the hour starts a spot (centred on it),
  // later ones within 200 m of a living spot keep it alive. (ponytail: O(n²) over a day's catches -- a few hundred at most)
  function hzCompute(now){
    var L = (catchLive && catchLiveComp() ? catchLive.list : []).filter(function(c){ return c.lat != null; }).slice().sort(function(a, b){ return a.t - b.t; });
    var zones = [];
    L.forEach(function(c, i){
      var z = zones.filter(function(z){ return c.t - z.last <= HZ_WIN && hzM(z, c) <= HZ_R; })[0];
      if (z){ z.last = c.t; return; }
      var near = L.slice(0, i + 1).filter(function(x){ return c.t - x.t <= HZ_WIN && hzM(x, c) <= HZ_R; });
      if (near.length >= HZ_N) zones.push({ id: c.id, lat: c.lat, lon: c.lon, start: c.t, last: c.t });
    });
    return zones.filter(function(z){ return now - z.last <= HZ_WIN; }).map(function(z){
      z.fish = L.filter(function(x){ return now - x.t <= HZ_WIN && x.t <= now && hzM(x, z) <= HZ_R; });
      z.n = z.fish.length;
      return z;
    });
  }
  function hzUpdate(){
    clearTimeout(hzTick); hzTick = null;
    var now = Date.now();
    hzZones = hzOn ? hzCompute(now) : [];
    if (hzZones.length) hzTick = setTimeout(hzUpdate, 60e3);   // (a spot dies an hour after its last fish, new data or not)
    // new spots, newest first: the first gets the note if the pause is over; the rest only their rings
    hzZones.filter(function(z){ return !hzSaid.ids[z.id]; }).sort(function(a, b){ return b.start - a.start; }).forEach(function(z){
      if (now - hzSaid.at >= HZ_PAUSE){ hzSaid.at = now; hzShowNote(z); }
      hzSaid.ids[z.id] = now;
    });
    var alive = {}; hzZones.forEach(function(z){ alive[z.id] = 1; hzSaid.ids[z.id] = now; });
    // (spots not seen for 2 h: forgotten -- not at once, the live catches come a moment after a start)
    Object.keys(hzSaid.ids).forEach(function(k){ if (now - hzSaid.ids[k] > 2 * HZ_WIN) delete hzSaid.ids[k]; });
    try { localStorage.setItem(HZ_NOTE_KEY, JSON.stringify(hzSaid)); } catch(e){}
    if (hzNoteZone && !alive[hzNoteZone.id]) hzHideNote();
    hzEl.innerHTML = hzZones.map(function(z){ return '<div class="hzZ" data-id="' + escHtml(z.id) + '"><div class="hzRing"></div><div class="hzTag">\u{1F525} ' + z.n + '</div></div>'; }).join('');
    hzDraw();
  }
  function hzDraw(){
    Array.prototype.forEach.call(hzEl.children, function(el, i){
      var z = hzZones[i]; if (!z) return;
      var c = latLonToImgPx(z.lat, z.lon), e = latLonToImgPx(z.lat + HZ_R / 111320, z.lon), r = Math.abs(c.y - e.y) * scale;
      el.style.transform = 'translate(' + (originX + c.x * scale - r).toFixed(1) + 'px,' + (originY + c.y * scale - r).toFixed(1) + 'px)';
      el.style.width = el.style.height = (2 * r).toFixed(1) + 'px';
    });
  }

  // the note: "Hotzone: 4 abborrar senaste timmen" / "vid Storön · 800 m bort"
  function hzText(z){
    var by = {}; z.fish.forEach(function(c){ by[c.sp] = (by[c.sp] || 0) + 1; });
    var sp = Object.keys(by), what = sp.length === 1 ? HZ_PL[sp[0]] : 'fiskar';
    var name = null, best = 1500;   // (the nearest place name within 1.5 km)
    (LAKE.names || []).forEach(function(n){ var d = hzM(z, { lat: n[0], lon: n[1] }); if (d < best){ best = d; name = n[2]; } });
    var far = lastOwnLatLon ? hzM(z, lastOwnLatLon) : null;
    var where = [name ? 'vid ' + name : '', far == null ? '' : far < 1000 ? Math.round(far / 50) * 50 + ' m bort' : (far / 1000).toFixed(1).replace('.', ',') + ' km bort'].filter(Boolean).join(' · ');
    return { title: 'Hotzone: ' + z.n + ' ' + what + ' senaste timmen', sub: (where ? where + ' · ' : '') + 'tryck för att åka dit' };
  }
  function hzShowNote(z){
    var t = hzText(z);
    document.getElementById('hzNoteTitle').textContent = t.title;
    document.getElementById('hzNoteSub').textContent = t.sub;
    hzNoteZone = z; hzNote.classList.add('show');
    clearTimeout(hzNoteTimer); hzNoteTimer = setTimeout(hzHideNote, HZ_SHOW);
  }
  function hzHideNote(){ clearTimeout(hzNoteTimer); hzNote.classList.remove('show'); hzNoteZone = null; }
  document.getElementById('hzNoteGo').addEventListener('click', function(){ var z = hzNoteZone; hzHideNote(); if (z) centerOnWaypoint(z); });
  document.getElementById('hzNoteClose').addEventListener('click', hzHideNote);

  catchListeners.push(hzUpdate);
  toggleHzEl.checked = hzOn;
  toggleHzEl.addEventListener('change', function(){
    hzOn = toggleHzEl.checked;
    try { localStorage.setItem(HZ_KEY, hzOn ? '1' : '0'); } catch(e){}
    if (!hzOn) hzHideNote();
    hzUpdate(); catchLiveTick();
  });
  window.__ffHotzone = function(){ hzUpdate(); return { on: hzOn, zones: hzZones.map(function(z){ return { n: z.n, lat: z.lat, lon: z.lon }; }),
    note: hzNote.classList.contains('show') ? document.getElementById('hzNoteTitle').textContent + ' | ' + document.getElementById('hzNoteSub').textContent : null }; };   // (for the tests)
