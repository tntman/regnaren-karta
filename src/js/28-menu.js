  /* ---------------- sjöar (lakes) ---------------- */
  // The list comes from lakes/*/lake.json (LAKES, top of the script).
  // Choosing another lake remembers it and reloads the page with that lake.
  function switchLake(id){
    try { localStorage.setItem(LAKE_KEY, id); } catch(e){}
    var url = location.pathname + location.search.replace(/([?&])lake=[^&]*&?/, '$1').replace(/[?&]$/, '');
    location.replace(url);
  }
  /* ---- Sjö och Tävling: the menu's two top rows (Filip 2026-11-05), each opening its own list (#menuSub) ----
     Sjö: "Automatiskt" (on from the start, LAKE_AUTO_KEY) = the GPS changes the lake straight away when you're at
     another lake (lakeAutoCheck -- a real GPS fix, 46-gps-track.js), then a note says so (#lakeNote) with a way back.
     Choosing a lake yourself turns it off. Tävling: see catchLiveComp (66-catches.js) -- automatically the one going on
     on this lake, else Mälaren Open on Mälaren / Fiskfiskarna Open elsewhere; or one going on that you choose. */
  var lakeListEl = document.getElementById('lakeList'), menuSubEl = document.getElementById('menuSub');
  var lakePinSvg = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 21s-7-6.7-7-11.5A7 7 0 0 1 19 9.5C19 14.3 12 21 12 21z"></path><circle cx="12" cy="9.5" r="2.4"></circle></svg>';
  var lakeCheckSvg = '<svg class="menuItemCheck" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6 9 17l-5-5"></path></svg>';
  var cupSvg = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M8 21h8M12 17v4M7 4h10v5a5 5 0 0 1-10 0V4z"></path><path d="M7 6H4a3 3 0 0 0 3 4M17 6h3a3 3 0 0 1-3 4"></path></svg>';
  var gpsSvg = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="12" r="7"></circle><circle cx="12" cy="12" r="2.5"></circle><path d="M12 2v3M12 19v3M2 12h3M19 12h3"></path></svg>';
  var backSvg = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M15 18l-6-6 6-6"></path></svg>';
  var AUTO_TAG = '<span class="mnAuto">● auto</span>';
  var LAKE_AUTO_KEY = 'ffmap_lake_auto_v1', LAKE_SWITCH_KEY = 'ffmap_lake_switched_v1';
  function lakeAutoOn(){ try { return localStorage.getItem(LAKE_AUTO_KEY) !== '0'; } catch(e){ return true; } }
  function setLakeAuto(on){ try { localStorage.setItem(LAKE_AUTO_KEY, on ? '1' : '0'); } catch(e){} }
  // is the place inside this lake's map? (the map covers the lake and a bit of land around it)
  function lakeMapHas(L, lat, lon){
    var G = L.geo, N = Math.pow(2, G.zoom) * 256;
    var x = (lon + 180) / 360 * N - G.originX, r = lat * Math.PI / 180;
    var y = (1 - Math.log(Math.tan(r) + 1 / Math.cos(r)) / Math.PI) / 2 * N - G.originY;
    return x >= 0 && y >= 0 && x < G.fullW && y < G.fullW * G.imgH / G.imgW;
  }
  // a real GPS fix: at another lake (and not at this one) -> that lake, at once
  function lakeAutoCheck(lat, lon){
    if (!lakeAutoOn() || window.__ffNoLakeAuto || isNearLake(lat, lon)) return;   // (__ffNoLakeAuto: the test browser, fakefb.py)
    var L = LAKES.filter(function(l){ return l.id !== LAKE_ID && lakeMapHas(l, lat, lon); })[0];
    if (!L) return;
    try { sessionStorage.setItem(LAKE_SWITCH_KEY, JSON.stringify({ from: LAKE_ID, to: L.id, t: Date.now() })); } catch(e){}
    switchLake(L.id);
  }
  function myLatLon(){ return typeof lastRealFix !== 'undefined' && lastRealFix && !demoMode ? lastRealFix : lastOwnLatLon; }
  function lakeKmTxt(L){
    var m = myLatLon(); if (!m) return '';
    if (L.id === LAKE_ID ? isNearLake(m.lat, m.lon) : lakeMapHas(L, m.lat, m.lon)) return 'här';
    var km = haversineKm(m.lat, m.lon, L.center[0], L.center[1]);
    return (km < 10 ? km.toFixed(1).replace('.', ',') : Math.round(km)) + ' km';
  }
  // "du är med" / "du är inte anmäld": the competition's participants (live), when known
  function compMeTxt(c){
    var L = catchLive && catchLive.comp === c.id ? catchLive : null;
    if (!L || !L.parts || !L.parts.length) return '';
    return L.parts.indexOf(catchPlain(userName)) >= 0 ? 'du är med' : 'du är inte anmäld';
  }
  function compWhenTxt(c){ return c.open ? 'Hela året' + (c.water ? ' · ' + c.water : ' · alla vatten') : 'Pågår' + (c.water ? ' · ' + c.water : ''); }
  function renderLakeList(){
    var near = lakeKmTxt(LAKE) === 'här', c = catchLiveComp(), me = c ? compMeTxt(c) : '';
    lakeListEl.innerHTML =
      '<button class="menuItem mnPick" data-sub="lake">' + lakePinSvg + '<span class="mnT"><span class="mnK">Sjö' + (lakeAutoOn() ? AUTO_TAG : '') + '</span><b>' + escHtml(LAKE.name) + '</b>' +
        '<small>' + (near ? 'Du är här' : myLatLon() ? lakeKmTxt(LAKE) + ' bort' : 'Ingen GPS-position') + (lakeAutoOn() ? ' – väljs av GPS:en' : ' – vald av dig') + '</small></span><span class="mnChev">›</span></button>' +
      '<button class="menuItem mnPick" data-sub="comp">' + cupSvg + '<span class="mnT"><span class="mnK">Tävling' + (c && !compChosen() ? AUTO_TAG : '') + '</span><b>' + (c ? escHtml(c.name || c.id) : 'Ingen just nu') + '</b>' +
        '<small>' + (c ? escHtml(compWhenTxt(c)) + (me ? ' · ' + me : '') : catchHist ? 'Ingen tävling pågår' : 'Inte hämtat än') + '</small></span><span class="mnChev">›</span></button>';
  }
  function menuSubRow(cls, icon, title, sub, right, attrs){
    return '<button type="button" class="menuItem mnRow' + cls + '"' + (attrs || '') + '>' + icon + '<span class="mnT"><b>' + title + '</b>' + (sub ? '<small>' + sub + '</small>' : '') + '</span>' + (right || '') + '</button>';
  }
  function fmtDay(iso){ var p = iso.split('-'); return (+p[2]) + ' ' + MONTHS_SV[+p[1] - 1]; }
  function renderMenuSub(which){
    var h = '<button type="button" class="mnHead" data-back="1">' + backSvg + (which === 'lake' ? 'Välj sjö' : 'Välj tävling') + '</button>';
    if (which === 'lake'){
      var auto = lakeAutoOn(), m = myLatLon(), lakes = LAKES.slice();
      if (m) lakes.sort(function(a, b){ return haversineKm(m.lat, m.lon, a.center[0], a.center[1]) - haversineKm(m.lat, m.lon, b.center[0], b.center[1]); });
      h += menuSubRow(' mnBig', gpsSvg, 'Automatiskt', 'Byter sjö automatiskt med GPS', '<span class="mnSw' + (auto ? ' on' : '') + '"></span>', ' data-auto="lake"') +
        '<div class="mnSec">' + (m ? 'Sjöar · närmast först' : 'Sjöar') + '</div>' +
        lakes.map(function(L){ var cur = L.id === LAKE_ID, km = lakeKmTxt(L);
          return menuSubRow(cur ? ' menuItem--active' : '', lakePinSvg, escHtml(L.name), km === 'här' ? 'du är här' : '', (km && km !== 'här' ? '<span class="mnRight">' + km + '</span>' : '') + (cur ? lakeCheckSvg : ''), ' data-lake-id="' + L.id + '"'); }).join('');
    } else {
      var chosen = compChosen(), cur = catchLiveComp(), on = catchActiveComps(), comps = (catchHist && catchHist.all) || [];
      var day = function(c){ return /^\d{4}-\d\d-\d\d$/.test(c.date) ? fmtDay(c.date) : 'datum inte bestämt'; };
      h += menuSubRow(' mnBig', gpsSvg, 'Automatiskt', 'Den som pågår på sjön du är vid, annars Open', '<span class="mnSw' + (chosen ? '' : ' on') + '"></span>', ' data-auto="comp"') +
        '<div class="mnSec">Pågår</div>' +
        (on.length ? on.map(function(c){ var me = cur && cur.id === c.id, t = compMeTxt(c);
          return menuSubRow(me ? ' menuItem--active' : '', cupSvg, escHtml(c.name || c.id) + (me && !chosen ? AUTO_TAG : ''), escHtml(compWhenTxt(c)) + (t ? ' · ' + t : ''), me ? lakeCheckSvg : '', ' data-comp="' + escHtml(c.id) + '"'); }).join('')
          : '<div class="mnNote">' + (catchHist ? 'Ingen tävling pågår just nu.' : 'Tävlingarna är inte hämtade än.') + '</div>');
      var planned = comps.filter(function(c){ return c.status === 'planned'; });
      var done = comps.filter(function(c){ return c.status === 'done'; }).sort(function(a, b){ return a.date < b.date ? 1 : -1; }).slice(0, 3);
      if (planned.length) h += '<div class="mnSec">Kommande</div>' + planned.map(function(c){ return menuSubRow(' mnInfo', cupSvg, escHtml(c.name || c.id), escHtml(c.water) + ' · ' + day(c), '', ' disabled'); }).join('');
      if (done.length) h += '<div class="mnSec">Avslutade</div>' + done.map(function(c){ return menuSubRow(' mnInfo mnDim', cupSvg, escHtml(c.name || c.id), day(c) + ' · ' + escHtml(c.water), '', ' disabled'); }).join('');
    }
    menuSubEl.innerHTML = h;
    menuSubEl.setAttribute('data-which', which);
    menuPanel.classList.add('sub');
  }
  function closeMenuSub(){ menuPanel.classList.remove('sub'); menuSubEl.removeAttribute('data-which'); renderLakeList(); }
  lakeListEl.addEventListener('click', function(e){
    e.stopPropagation();   // (the rows are drawn again -- the click mustn't count as one outside the menu)
    var btn = e.target.closest ? e.target.closest('[data-sub]') : null;
    if (btn) renderMenuSub(btn.getAttribute('data-sub'));
  });
  menuSubEl.addEventListener('click', function(e){
    e.stopPropagation();
    var t = e.target.closest ? e.target.closest('button') : null;
    if (!t) return;
    if (t.hasAttribute('data-back')){ closeMenuSub(); return; }
    var a = t.getAttribute('data-auto');
    if (a === 'lake'){
      setLakeAuto(!lakeAutoOn()); renderMenuSub('lake');
      var m = myLatLon(); if (lakeAutoOn() && m && !demoMode) lakeAutoCheck(m.lat, m.lon);
      return;
    }
    if (a === 'comp'){ var cur = catchLiveComp(); compChoose(compChosen() ? null : cur && cur.id); renderMenuSub('comp'); return; }
    var lid = t.getAttribute('data-lake-id');
    if (lid){
      setLakeAuto(false);
      if (lid === LAKE_ID){ renderMenuSub('lake'); return; }
      switchLake(lid); return;
    }
    var cid = t.getAttribute('data-comp');
    if (cid){ compChoose(cid); renderMenuSub('comp'); }
  });
  // after the GPS changed the lake: say so, with a way back (that turns Automatiskt off)
  function lakeSwitchNote(){
    var v = null;
    try { v = JSON.parse(sessionStorage.getItem(LAKE_SWITCH_KEY) || 'null'); sessionStorage.removeItem(LAKE_SWITCH_KEY); } catch(e){}
    if (!v || v.to !== LAKE_ID || Date.now() - v.t > 30000) return;
    var from = LAKES.filter(function(l){ return l.id === v.from; })[0], note = document.getElementById('lakeNote'), back = document.getElementById('lakeNoteBack');
    document.getElementById('lakeNoteTitle').textContent = 'Du är vid ' + LAKE.name;
    document.getElementById('lakeNoteSub').textContent = 'Kartan har bytt sjö automatiskt.';
    back.hidden = !from; if (from) back.textContent = 'Tillbaka till ' + from.name;
    back.onclick = function(){ setLakeAuto(false); switchLake(from.id); };
    document.getElementById('lakeNoteClose').onclick = function(){ note.classList.remove('show'); };
    note.classList.add('show');
    setTimeout(function(){ note.classList.remove('show'); }, 12000);
  }
  lakeSwitchNote();

  /* ---------------- menu (Karta / Logg / Inställningar) ---------------- */
  var menuBtn = document.getElementById('menuBtn');
  var menuPanel = document.getElementById('menuPanel');
  var menuItemMap = document.getElementById('menuItemMap');
  var menuItemLog = document.getElementById('menuItemLog');
  var menuItemSettings = document.getElementById('menuItemSettings');
  var logView = document.getElementById('logView');
  var logList = document.getElementById('logList');
  var logBackBtn = document.getElementById('logBackBtn');
  var settingsView = document.getElementById('settingsView');
  var settingsBackBtn = document.getElementById('settingsBackBtn');
  var demoModeToggle = document.getElementById('demoModeToggle');

  function toggleMenu(open){
    if (open){ menuPanel.classList.remove('sub'); renderLakeList(); }   // (Sjö / Tävling: as they are now)
    menuPanel.classList.toggle('show', open);
  }
  menuBtn.addEventListener('click', function(e){
    e.stopPropagation();
    toggleMenu(!menuPanel.classList.contains('show'));
  });
  document.addEventListener('click', function(e){
    if (menuPanel.classList.contains('show') && !menuPanel.contains(e.target) && e.target !== menuBtn){
      toggleMenu(false);
    }
  });

  // "24 sep. 14:02" (with the year when it isn't this year)
  function fmtSheetDate(ms){
    var d = new Date(ms || Date.now()), now = new Date();
    var opt = { day:'numeric', month:'short' };
    if (d.getFullYear() !== now.getFullYear()) opt.year = 'numeric';
    return d.toLocaleDateString('sv-SE', opt) + ' ' + d.toLocaleTimeString('sv-SE', { hour:'2-digit', minute:'2-digit' });
  }
  function fmtLogDate(ms){
    var d = new Date(ms);
    var dd = d.toLocaleDateString('sv-SE', { day:'numeric', month:'short' });
    var tt = d.toLocaleTimeString('sv-SE', { hour:'2-digit', minute:'2-digit' });
    return dd + ' · ' + tt;
  }

  /* ---- the filter on top (only the list -- the map keeps Filter's choices): search (name or who), Alla/Mina/Andras,
     the types as Filter's dots (filled = shown). Who + types are kept (ffmap_log_filter_v1); the search only over a rotation. */
  var LOG_FILTER_KEY = 'ffmap_log_filter_v1', logF = { who: 'all', hidden: [] }, logQ = '';
  try { Object.assign(logF, JSON.parse(localStorage.getItem(LOG_FILTER_KEY) || '{}')); } catch(e){}
  var logSearch = document.getElementById('logSearch'), logWhoSeg = document.getElementById('logWhoSeg'), logTypesEl = document.getElementById('logTypes'), logCountEl = document.getElementById('logCount');
  var LOG_SHORT = { mark: 'Mark', abborre: 'Abb', gadda: 'Gädda', gos: 'Gös', meet: 'Träff', hem: 'Hem', fara: 'Fara' };
  logTypesEl.innerHTML = Object.keys(WP_TYPES).map(function(t){
    return '<label class="visDot" title="' + WP_TYPES[t].label + '"><input type="checkbox" data-type="' + t + '"' + (logF.hidden.indexOf(t) < 0 ? ' checked' : '') + ' aria-label="' + WP_TYPES[t].label + '">' +
      '<span class="visSwatch ws-' + t + '">' + wpIconSvg(t) + '</span><span class="visDotL">' + (LOG_SHORT[t] || WP_TYPES[t].label) + '</span></label>';
  }).join('');
  function logSeg(){ Array.prototype.forEach.call(logWhoSeg.children, function(b){ var on = b.getAttribute('data-who') === logF.who; b.classList.toggle('active', on); b.setAttribute('aria-checked', on); }); }
  function logSave(){ try { localStorage.setItem(LOG_FILTER_KEY, JSON.stringify(logF)); } catch(e){} }
  logSeg();
  logWhoSeg.addEventListener('click', function(e){ var b = e.target.closest('button'); if (!b) return; logF.who = b.getAttribute('data-who'); logSeg(); logSave(); renderLogList(); });
  logTypesEl.addEventListener('change', function(e){
    var t = e.target.getAttribute('data-type'); if (!t) return;
    logF.hidden = logF.hidden.filter(function(x){ return x !== t; }).concat(e.target.checked ? [] : [t]); logSave(); renderLogList();
  });
  logSearch.addEventListener('input', function(){ logQ = logSearch.value; renderLogList(); });
  logSearch.addEventListener('keydown', function(e){ if (e.key === 'Enter') logSearch.blur(); });
  function logPlain(s){ return String(s || '').toLowerCase().replace(/[åä]/g, 'a').replace(/ö/g, 'o'); }
  function logShows(wp){
    var mine = isMine(wp), q = logPlain(logQ).trim();
    if (logF.who === 'mine' ? !mine : logF.who === 'others' ? mine : false) return false;
    if (logF.hidden.indexOf(wpType(wp)) >= 0) return false;
    return !q || logPlain(wp.name || 'Fiskeplats').indexOf(q) >= 0 || logPlain(mine ? 'du ' + userName : wp.by).indexOf(q) >= 0;
  }

  function renderLogList(){
    var all = waypoints.filter(function(w){ return !isExpired(w) && !isUndoPending(w.id); }).sort(function(a,b){ return (b.createdAt||0) - (a.createdAt||0); });
    var sorted = all.filter(logShows);
    logCountEl.hidden = sorted.length === all.length;
    logCountEl.textContent = 'Visar ' + sorted.length + ' av ' + all.length;
    if (!all.length){
      logList.innerHTML = '<div id="logEmpty">Inga fiskeplatser sparade än.<br>Håll ner fingret på kartan för att lägga till en.</div>';
      return;
    }
    if (!sorted.length){ logList.innerHTML = '<div id="logEmpty">Inga platser med det här filtret.</div>'; return; }
    var html = sorted.map(function(wp){
      var mine = isMine(wp);
      var whoRaw = mine ? 'Du' : (wp.by || 'Lagkompis');
      var who = whoRaw.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
      var name = (wp.name || 'Fiskeplats').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
      return '' +
        '<div class="logItem" data-id="' + wp.id + '">' +
          '<span class="visSwatch ws-' + wpType(wp) + (mine ? '' : ' visSwatch--other') + '">' + wpIconSvg(wpType(wp)) + '</span>' +
          '<div class="logInfo">' +
            '<div class="logTitle">' + name + '</div>' +
            '<div class="logMeta">' + who + ' · ' + fmtLogDate(wp.createdAt) + ' · ' + timeAgo(wp.createdAt) + '</div>' +
          '</div>' +
          '<svg class="logChevron" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 18l6-6-6-6"></path></svg>' +
        '</div>';
    }).join('');
    logList.innerHTML = html;
    if (pendingLogScroll != null && logList.scrollHeight - logList.clientHeight >= pendingLogScroll){
      logList.scrollTop = pendingLogScroll; pendingLogScroll = null;
    }
  }

  logList.addEventListener('click', function(e){
    var row = e.target.closest ? e.target.closest('.logItem') : null;
    if (!row) return;
    var id = row.getAttribute('data-id');
    var wp = waypoints.filter(function(w){ return w.id === id; })[0];
    if (!wp) return;
    showMapView();
    centerOnWaypoint(wp);
  });

  function showLogView(){
    renderLogList();
    logView.classList.add('show');
    settingsView.classList.remove('show');
    menuItemMap.classList.remove('menuItem--active');
    menuItemSettings.classList.remove('menuItem--active');
    menuItemLog.classList.add('menuItem--active');
    toggleMenu(false);
  }
  /* ---- Inställningar in sections (Kartan, Båten, Varningar ...): closed = one line of what's chosen.
     Which ones are open is remembered on the phone. ---- */
  var SET_OPEN_KEY = 'ffmap_settings_open_v1';
  var setSecs = Array.from(document.querySelectorAll('#settingsBody .setSec'));
  (function(){
    var open = []; try { open = JSON.parse(localStorage.getItem(SET_OPEN_KEY) || '[]'); } catch(e){}
    setSecs.forEach(function(s){ s.open = open.indexOf(s.getAttribute('data-sec')) >= 0; });
  })();
  setSecs.forEach(function(s){
    s.addEventListener('toggle', function(){
      try { localStorage.setItem(SET_OPEN_KEY, JSON.stringify(setSecs.filter(function(x){ return x.open; }).map(function(x){ return x.getAttribute('data-sec'); }))); } catch(e){}
    });
  });
  function openSettingsSec(id){ setSecs.forEach(function(s){ if (s.getAttribute('data-sec') === id) s.open = true; }); }
  // the line under each closed title, read from the controls themselves
  function setSums(){
    var el = function(id){ return document.getElementById(id); };
    var act = function(id){ var b = document.querySelector('#' + id + ' .active'); return b ? b.textContent.trim() : ''; };
    var on = function(id){ return el(id).checked; };
    var put = function(id, parts){ var t = parts.filter(Boolean).join(' · '); el('setSum-' + id).textContent = t.charAt(0).toUpperCase() + t.slice(1); };
    var st = document.querySelector('#mapStyleList .styleOpt.active .soName');
    put('map', [act('wpSizeSeg') + ' storlek', st && st.textContent, 'färg ' + el('mapSatVal').textContent, 'andras ' + act('othersOpacitySeg'), 'kompass ' + el('cpLenVal').textContent + ' ' + el('cpAngVal').textContent, !on('toggleShore') && 'ingen strandlinje']);
    put('boat', [on('toggleDepth') && 'djupet', on('gpsPulseToggle') && 'ring', on('toggleWake') && 'skärmen tänd',
      (el('cruiseInput').value || '–') + ' kn marschfart']);
    var km = act('ltAlarmSeg');
    put('warn', km === 'Av' || !km ? ['Åskvarning av'] : ['Åskvarning ' + km, on('ltAlarmSound') && 'ljud', on('ltAlarmVib') && 'vibration']);
    put('an', ['Tona ner ' + el('anDimOut').textContent]);
    put('catch', catchSum()); catchRenderSettings();   // (66-catches.js)
    var ob = el('offBtn').textContent, os = el('offStatus').textContent;
    put('off', [ob === 'Ta bort' ? 'Nedladdad' : ob === 'Pausa' ? 'Laddar ner …' : ob === 'Fortsätt' ? 'Pausad' : /kartversion/.test(os) ? 'Ny kartversion – ladda ner igen' : 'Inte nedladdad',
      ob === 'Ladda ner' && !/kartversion/.test(os) && os.split(' · ')[1]]);
    put('adv', ['Demo Mode ' + (on('demoModeToggle') ? 'på' : 'av'), !el('adminRow').hidden && 'Admin']);
  }
  ['change', 'input', 'click'].forEach(function(t){ document.getElementById('settingsBody').addEventListener(t, function(){ setTimeout(setSums, 0); }); });
  function showSettingsView(){
    updateSpeedSettings(); // fresh speed numbers the moment it opens
    setSums();
    document.getElementById('settingsNameSub').textContent = (isAdminUnlocked() ? 'Admin · ' : '') + LAKE.name;
    settingsView.classList.add('show');
    logView.classList.remove('show');
    menuItemMap.classList.remove('menuItem--active');
    menuItemLog.classList.remove('menuItem--active');
    menuItemSettings.classList.add('menuItem--active');
    toggleMenu(false);
  }
  function showMapView(){
    closeAdminView();
    logView.classList.remove('show');
    settingsView.classList.remove('show');
    menuItemLog.classList.remove('menuItem--active');
    menuItemSettings.classList.remove('menuItem--active');
    menuItemMap.classList.add('menuItem--active');
    toggleMenu(false);
  }
  menuItemMap.addEventListener('click', showMapView);
  menuItemLog.addEventListener('click', showLogView);
  menuItemSettings.addEventListener('click', showSettingsView);
  logBackBtn.addEventListener('click', showMapView);
  settingsBackBtn.addEventListener('click', showMapView);

