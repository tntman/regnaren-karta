  /* ---- rotation: keep everything as it was ----
     The home-screen app reloads the whole page when the phone is rotated
     (see handleOrientationEvent). Settings, filters, Demo Mode, the
     measurement etc. are stored as you change them; this saves the rest --
     what was on screen and what was half-done -- right before the reload,
     and puts it back afterwards. */
  var pendingSheetRestore = null, pendingLogScroll = null;
  function saveRotationState(){
    // a half-typed number field: its blur/commit never fires on a reload
    try {
      if (document.activeElement === cruiseInput) commitCruise();
      if (demoInputDirty) commitManualDemoCoords();
    } catch(e){}
    var st = { t: Date.now() };
    try {
      st.view = adminView.classList.contains('show') ? 'admin'
              : settingsView.classList.contains('show') ? 'settings'
              : logView.classList.contains('show') ? 'log' : 'map';
      st.scroll = {
        log: logList.scrollTop,
        settings: document.getElementById('settingsBody').scrollTop,
        admin: document.getElementById('adminBody').scrollTop
      };
      st.menu = menuPanel.classList.contains('show');
      st.logQ = logQ;   // (the Logg search, 28-menu.js)
      st.an = anPanel.classList.contains('show');
      if (hmOn) st.hm = { panel: hmPanel.classList.contains('show'), card: hmCardList && hmCard.classList.contains('show') ? { ids: hmCardList.map(function(c){ return c.id; }), i: hmCardI } : null };
      if (helpView.classList.contains('show')) st.help = helpLastPlace || helpPlace();
      st.trk = trkPanel.classList.contains('show');
      if (pfCard.classList.contains('show')) st.pf = pfName;
      st.wx = wxCard.classList.contains('show');
      st.probe = probe;
      if (editingId && wpSheet.classList.contains('show')){
        st.sheet = { id: editingId, isNew: editingIsNew, name: wpNameInput.value, type: editingType };
      }
      if (nameModal.classList.contains('show')){
        st.nameModal = { sel: selectedRosterName, other: otherNameMode, text: nameInput.value, scroll: nameListEl.scrollTop };
      }
      st.speed = { f: speedFixes, s: speedSamples };
      st.pos = { at: lastPosWriteAt, ll: lastWrittenLatLon };
      st.usage = { at: lastUsageReportAt, key: lastUsageReportKey };
      if (demoSim) st.demoSim = { heading: demoSim.heading, turn: demoSim.turn, phase: demoSim.phase, t0: demoSim.t0, cLat: demoSim.cLat, cLon: demoSim.cLon };
    } catch(e){}
    try { sessionStorage.setItem(ROT_STATE_KEY, JSON.stringify(st)); } catch(e){}
  }
  function restoreRotationUi(){
    if (!rotState) return;
    var r = rotState;
    try {
      if (r.nameModal && nameModal.classList.contains('show')){
        var chip = r.nameModal.other ? nameListEl.querySelector('[data-other]')
                 : (r.nameModal.sel ? nameListEl.querySelector('.nameChip[data-name="' + String(r.nameModal.sel).replace(/"/g, '') + '"]') : null);
        if (chip) chip.click();
        if (r.nameModal.other) nameInput.value = r.nameModal.text || '';
        updNameBtn();
        nameListEl.scrollTop = r.nameModal.scroll || 0;
        return; // nothing else is open before you've picked a name
      }
      var sc = r.scroll || {};
      if (r.logQ){ logQ = logSearch.value = r.logQ; }
      if (r.view === 'log'){
        showLogView();
        pendingLogScroll = sc.log || null;
        if (pendingLogScroll) renderLogList();
      } else if (r.view === 'settings' || r.view === 'admin'){
        showSettingsView();
        document.getElementById('settingsBody').scrollTop = sc.settings || 0;
        if (r.view === 'admin' && isAdminUnlocked()){
          openAdminView();
          document.getElementById('adminBody').scrollTop = sc.admin || 0;
        }
      }
      if (r.help){ showHelpView(r.help.first); helpGoTo(r.help); setTimeout(function(){ helpGoTo(r.help); }, 500); }
      if (r.menu) toggleMenu(true);
      if (r.wx) setWxOpen(true);
      if (r.probe && typeof r.probe.x === 'number'){ setProbe(r.probe); probeEl.classList.remove('drop'); }
      if (r.an) showAnPanel(true);
      if (r.trk) trkShowPanel(true);
      if (r.pf) openProfile(r.pf);
      if (r.hm){ if (r.hm.card) hmPendingCard = r.hm.card; hmSetOn(true, r.hm.panel, true); }   // (the card first: the copy may be there at once)
      if (r.sheet && r.sheet.id){
        pendingSheetRestore = { s: r.sheet, until: Date.now() + 10000 };
        tryRestoreSheet();
      }
    } catch(e){ console.warn('kunde inte återställa efter rotation', e); }
  }
  // the spot has to be back in the list (from the phone's cache or the
  // server) before its sheet can reopen -- checked on every render
  function tryRestoreSheet(){
    var pr = pendingSheetRestore;
    if (!pr) return;
    if (Date.now() > pr.until){ pendingSheetRestore = null; return; }
    var wp = waypoints.filter(function(w){ return w.id === pr.s.id; })[0];
    if (!wp) return;
    pendingSheetRestore = null;
    setTimeout(function(){
      if (wpSheet.classList.contains('show')) return; // something else was opened meanwhile
      openSheetForWp(wp, !!pr.s.isNew);
      if (typeof pr.s.name === 'string') wpNameInput.value = pr.s.name;
      if (pr.s.type && WP_TYPES[pr.s.type] && !wpNameInput.disabled){ editingType = pr.s.type; showEditingType(); }
    }, 0);
  }

  function boot(){
    toggleDepthEl.checked = showDepth;
    toggleTrackEl.checked = showTrack;
    setImgNativeSize();
    initView();
    if (userName){
      myUid = nameSlug(userName);
      continueBootAfterName();
    } else {
      showNameModal();
    }
    restoreRotationUi();
    fetchWeather(false);
  }
  boot(); // (the map picture loads in the background -- its size is fixed, see IMG_W/IMG_H)

  // Offline start: a small service worker (sw.js, uploaded next to
  // index.html) keeps a copy of the app so it opens even without coverage.
  // If sw.js isn't there, this quietly does nothing.
  if ('serviceWorker' in navigator && (location.protocol === 'https:' || location.hostname === 'localhost')){
    var registerSw = function(){
      navigator.serviceWorker.register('sw.js').catch(function(){});
      // keep this lake's start files on the phone (default map + chosen style + depth)
      navigator.serviceWorker.ready.then(function(reg){
        var urls = [mapFile(DEFAULT_STYLE), mapFile(mapStyle), LAKE_DIR + LAKE.depth.file, 'ff_logo.svg', 'three-r170.min.js', 'three-r170-svg.js', 'three-r170-room.js'];   // (the logo and its 3D: the name picker after Logga ut, offline too)
        if (reg.active) reg.active.postMessage({ type: 'precache', urls: urls });
      }).catch(function(){});
    };
    if (document.readyState === 'complete') registerSw(); else window.addEventListener('load', registerSw);
  }
})();
