  /* ---------------- sjöar (lakes) ---------------- */
  // The list comes from lakes/*/lake.json (LAKES, top of the script).
  // Choosing another lake remembers it and reloads the page with that lake.
  function switchLake(id){
    try { localStorage.setItem(LAKE_KEY, id); } catch(e){}
    var url = location.pathname + location.search.replace(/([?&])lake=[^&]*&?/, '$1').replace(/[?&]$/, '');
    location.replace(url);
  }
  var lakeListEl = document.getElementById('lakeList');
  var lakePinSvg = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 21s-7-6.7-7-11.5A7 7 0 0 1 19 9.5C19 14.3 12 21 12 21z"></path><circle cx="12" cy="9.5" r="2.4"></circle></svg>';
  var lakeCheckSvg = '<svg class="menuItemCheck" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6 9 17l-5-5"></path></svg>';
  function renderLakeList(){
    lakeListEl.innerHTML = LAKES.map(function(lake){
      var isCurrent = lake.id === LAKE_ID;
      return '<button class="menuItem' + (isCurrent ? ' menuItem--active' : '') + '" data-lake-id="' + lake.id + '">' +
        lakePinSvg + lake.name + (isCurrent ? lakeCheckSvg : '') +
        '</button>';
    }).join('');
  }
  renderLakeList();
  lakeListEl.addEventListener('click', function(e){
    var btn = e.target.closest ? e.target.closest('.menuItem') : null;
    if (!btn) return;
    var id = btn.getAttribute('data-lake-id');
    var lake = LAKES.filter(function(l){ return l.id === id; })[0];
    if (!lake) return;
    if (lake.id === LAKE_ID){ toggleMenu(false); return; }
    switchLake(lake.id);
  });

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

  function renderLogList(){
    var sorted = waypoints.filter(function(w){ return !isExpired(w) && !isUndoPending(w.id); }).sort(function(a,b){ return (b.createdAt||0) - (a.createdAt||0); });
    if (!sorted.length){
      logList.innerHTML = '<div id="logEmpty">Inga fiskeplatser sparade än.<br>Håll ner fingret på kartan för att lägga till en.</div>';
      return;
    }
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

