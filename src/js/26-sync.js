  /* ---- swipe the sheet down to close it (same as "Avbryt") ----
     Drag from anywhere on the sheet except its text field and buttons. The
     sheet follows the finger (only downwards); let go after pulling it
     far enough -- or with a quick flick -- and it closes, otherwise it
     springs back. */
  sheetSwipe(wpSheet, function(){ cancelSheet(); });   // (drag = smaller, flick / all the way = close -- tools/UI.md)

  function applySnapshotDocs(snap){
    setTimeout(function(){ if (typeof anSet !== 'undefined' && anSet && anSet.mode === 'similar' && anRes && !anRes.M) anCompute(); }, 0);   // (the spot to compare with has arrived)
    waypoints = [];
    snap.forEach(function(doc){
      var d = doc.data();
      // All lakes currently share one Firestore collection, scoped by this
      // field. Docs saved before multi-lake support have no "lake" field —
      // treat those as belonging to Regnaren rather than dropping them.
      var docLake = d.lake || 'regnaren';
      if (docLake !== LAKE_ID) return;
      waypoints.push({
        id: doc.id, lat:d.lat, lon:d.lon, name:d.name, type:d.type || 'mark', uid:d.uid, by:d.by || '', lake:docLake,
        expiresAt: d.expiresAt || null,
        createdAt: (d.createdAt && d.createdAt.toMillis) ? d.createdAt.toMillis() : Date.now()
      });
    });
    renderWaypoints();
    refreshAdminIfOpen();
  }

  /* ---- offline indicator ----
     Three sources: the browser's own online/offline flag, whether Firestore
     is actually talking to its server (snapshot metadata.fromCache), and
     whether Firebase couldn't start at all (then spots are only saved on
     this phone). Going offline is only shown once it has lasted a few
     seconds, so a brief blip -- or the normal cache-first moment at start-
     up -- doesn't flash the badge. */
  var netBadge = document.getElementById('netBadge');
  var netText = document.getElementById('netText');
  var syncFromCache = false;
  var localOnlyMode = false;
  var offlineTimer = null, netBackT = null;
  function updateNetBadge(){
    var offline = localOnlyMode || navigator.onLine === false || (USE_FIREBASE && syncFromCache);
    if (!offline){
      if (offlineTimer){ clearTimeout(offlineTimer); offlineTimer = null; }
      // it was showing "Offline": say it's back (green) for 3 s, then go
      if (netBadge.classList.contains('show') && !netBadge.classList.contains('back')){
        netText.innerHTML = '<b>Täckning igen</b> · det du sparat skickas nu';
        netBadge.classList.add('back');
        clearTimeout(netBackT); netBackT = setTimeout(function(){ netBadge.classList.remove('show', 'back'); }, 3000);
      }
      return;
    }
    clearTimeout(netBackT); netBadge.classList.remove('back');
    netText.innerHTML = localOnlyMode
      ? '<b>Offline</b> · fiskeplatser sparas bara på telefonen'
      : '<b>Offline</b> · synkas när du får täckning';
    if (netBadge.classList.contains('show') || offlineTimer) return;
    offlineTimer = setTimeout(function(){
      offlineTimer = null;
      var stillOffline = localOnlyMode || navigator.onLine === false || (USE_FIREBASE && syncFromCache);
      if (stillOffline) netBadge.classList.add('show');
    }, 3000);
  }
  window.addEventListener('online', updateNetBadge);
  window.addEventListener('offline', updateNetBadge);

  // Has this phone already got a full copy of the spots from the server?
  var WP_SYNCED_KEY = 'lake_' + LAKE_ID + '_wp_synced_v1';
  function waypointsSyncedBefore(){
    try { return localStorage.getItem(WP_SYNCED_KEY) === '1'; } catch(e){ return false; }
  }
  function markWaypointsSynced(){
    try { localStorage.setItem(WP_SYNCED_KEY, '1'); } catch(e){}
  }

  /* ---- Firestore usage from THIS device (shown on the admin page) ----
     An estimate of what this phone has used of the daily free quota. The
     quota day follows US Pacific time (resets 09:00 Swedish time), so the
     counters do too. Listener: the first answer from the server counts the
     whole result, later answers only the documents that changed. */
  var USAGE_KEY = 'ffmap_usage_v1';
  function quotaDay(){
    try { return new Date().toLocaleDateString('sv-SE', { timeZone: 'America/Los_Angeles' }); }
    catch(e){ return new Date().toDateString(); }
  }
  function loadUsage(){
    var u = null;
    try { u = JSON.parse(localStorage.getItem(USAGE_KEY) || 'null'); } catch(e){}
    if (!u || u.day !== quotaDay()) u = { day: quotaDay(), r: 0, w: 0, d: 0 };
    return u;
  }
  function addUsage(kind, n){
    if (!n) return;
    var u = loadUsage();
    u[kind] += n;
    try { localStorage.setItem(USAGE_KEY, JSON.stringify(u)); } catch(e){}
  }
  function countListenerReads(snap, alreadyBilled){
    if (!alreadyBilled){
      addUsage('r', Math.max(1, snap.size || 0));
      return true;
    }
    if (typeof snap.docChanges === 'function'){
      var n = 0;
      try { n = snap.docChanges().length; } catch(e){}
      addUsage('r', n);
    }
    return true;
  }
  function countGetReads(snap){ addUsage('r', Math.max(1, (snap && snap.size) || 0)); }

  /* ---- report this device's counters, so the admin page can sum everyone ----
     One small doc per device per quota day, overwritten with the running
     totals: at most every 5 minutes while the app is open (only if anything
     changed), plus when the app goes to the background. ~50 extra writes a
     day for the whole group. Offline, Firestore keeps the write and sends it
     when there's coverage again. */
  var DEVICE_ID = null;
  try { DEVICE_ID = localStorage.getItem('regnaren_device_id_v1'); } catch(e){}
  if (!DEVICE_ID){
    DEVICE_ID = 'd' + Date.now().toString(36) + Math.random().toString(36).slice(2, 8);
    try { localStorage.setItem('regnaren_device_id_v1', DEVICE_ID); } catch(e){}
  }
  var USAGE_REPORT_MS = 5 * 60 * 1000;
  var lastUsageReportAt = 0, lastUsageReportKey = '';
  if (rotState && rotState.usage){ lastUsageReportAt = rotState.usage.at || 0; lastUsageReportKey = rotState.usage.key || ''; }
  var usageReportDenied = false;
  function reportUsage(force){
    if (!USE_FIREBASE || !usageCol || !myUid) return;
    var u = loadUsage();
    if (u.r + '/' + u.w + '/' + u.d === lastUsageReportKey) return; // nothing new
    if (!force && Date.now() - lastUsageReportAt < USAGE_REPORT_MS) return;
    addUsage('w', 1); // this report is itself a write
    u = loadUsage();
    lastUsageReportAt = Date.now();
    lastUsageReportKey = u.r + '/' + u.w + '/' + u.d;
    usageCol.doc(u.day + '_' + DEVICE_ID).set({
      day: u.day, device: DEVICE_ID, uid: myUid, name: userName || '', lake: LAKE_ID,
      r: u.r, w: u.w, d: u.d,
      updatedAt: firebase.firestore.FieldValue.serverTimestamp()
    }).then(function(){ usageReportDenied = false; })
      .catch(function(e){ if (e && e.code === 'permission-denied') usageReportDenied = true; });
  }
  setInterval(function(){ reportUsage(false); }, 60 * 1000);
  document.addEventListener('visibilitychange', function(){
    if (document.visibilityState === 'hidden') reportUsage(true);
  });

  var tracksCol = null, trackUsersCol = null;
  function initSharedWaypoints(cb){
    if (!FIREBASE_CONFIG.apiKey || FIREBASE_CONFIG.apiKey.indexOf('DIN_') === 0 || typeof firebase === 'undefined'){
      cb(false); return;
    }
    try {
      firebase.initializeApp(FIREBASE_CONFIG);
      var auth = firebase.auth();
      var fsdb = firebase.firestore();
      try { fsdb.enablePersistence({ synchronizeTabs:true }).catch(function(){}); } catch(e){}
      fsCol = fsdb.collection('waypoints');
      posCol = fsdb.collection('positions');
      usageCol = fsdb.collection('usage');
      tracksCol = fsdb.collection('tracks');   // (the Spår: 46-gps-track.js)
      trackUsersCol = fsdb.collection('trackusers');   // (who has tracks on which lake -- the drop-down in the Spår panel)
      var started = false;
      auth.onAuthStateChanged(function(user){
        if (!user || started) return;
        started = true;
        // Identity is the entered name (myUid is already set from it in boot()),
        // not Firebase's own anonymous auth id — that's only here to satisfy
        // Firestore's auth requirement so writes/reads are allowed.
        USE_FIREBASE = true;
        // includeMetadataChanges: also get told when the connection to the
        // server drops/returns (metadata.fromCache), for the offline badge
        var gotServerWaypoints = false;
        var wpListenerBilled = false;
        var hadLocalCopy = waypointsSyncedBefore(); // checked before the listener can set it
        fsCol.onSnapshot({ includeMetadataChanges: true }, function(snap){
          var fromCache = !!(snap.metadata && snap.metadata.fromCache);
          syncFromCache = fromCache;
          updateNetBadge();
          if (!fromCache){
            gotServerWaypoints = true;
            markWaypointsSynced();
            wpListenerBilled = countListenerReads(snap, wpListenerBilled);
          }
          applySnapshotDocs(snap);
        }, function(err){ console.warn('waypoints sync error', err); });
        // Safety net for "a new phone doesn't show my old spots": the live
        // listener above can hand back an empty first answer from the local
        // cache on a phone that has nothing saved yet. Only then (or if the
        // listener hasn't heard from the server within a few seconds) fetch
        // the spots directly from the server as well -- on every other start
        // the listener's own server answer is enough, and fetching twice
        // would just double the reads on every app start.
        var forceFetchWaypoints = function(){
          fsCol.get({ source: 'server' }).then(function(snap){
            countGetReads(snap);
            markWaypointsSynced();
            applySnapshotDocs(snap);
          }).catch(function(){});
        };
        if (!hadLocalCopy) forceFetchWaypoints();
        else setTimeout(function(){ if (!gotServerWaypoints) forceFetchWaypoints(); }, 6000);
        var posListenerBilled = false;
        posCol.onSnapshot(function(snap){
          if (!(snap.metadata && snap.metadata.fromCache)) posListenerBilled = countListenerReads(snap, posListenerBilled);
          applyPositionsSnapshot(snap);
        }, function(err){ console.warn('positions sync error', err); });
        // shared settings for everyone (just the position interval for now):
        // one small doc, 1 read at start + 1 whenever the admin changes it
        try {
          cfgDoc = fsdb.collection('config').doc(LAKE_ID);
          cfgDoc.onSnapshot(function(snap){
            if (!(snap.metadata && snap.metadata.fromCache)) addUsage('r', 1);
            sharedCfgError = null;
            applySharedConfig(snap.exists ? snap.data() : null, !!(snap.metadata && snap.metadata.fromCache));
          }, function(err){
            sharedCfgError = (err && err.code) || 'error';
            console.warn('config sync error', err);
            renderPosIntervalAdmin();
          });
        } catch(e){ console.warn('config init', e); }
        cb(true);
      });
      auth.signInAnonymously().catch(function(err){ console.warn('anonym inloggning misslyckades', err); cb(false); });
    } catch(e){ console.warn('firebase init misslyckades', e); cb(false); }
  }

  /* ---- shared settings (config/<lake>) ---- */
  var cfgDoc = null, sharedCfgError = null, posIntervalSaveMsg = '';
  function applySharedConfig(d, fromCache){
    var v = d ? parseInt(d.posIntervalS, 10) : NaN;
    // no setting saved for this lake (the server says so) -> the default, 20 s
    if (!d && !fromCache) v = POS_INTERVAL_DEFAULT_S;
    if (POS_INTERVAL_CHOICES.indexOf(v) !== -1){
      posIntervalS = v;
      try { localStorage.setItem(POS_INTERVAL_KEY, String(v)); } catch(e){} // (for offline starts)
    }
    renderPosIntervalAdmin();
  }
  function setSharedPosInterval(v){
    if (POS_INTERVAL_CHOICES.indexOf(v) === -1) return;
    posIntervalS = v; // this phone right away
    try { localStorage.setItem(POS_INTERVAL_KEY, String(v)); } catch(e){}
    if (!USE_FIREBASE || !cfgDoc){
      posIntervalSaveMsg = 'Ingen anslutning till databasen – gäller bara den här telefonen just nu.';
      renderPosIntervalAdmin(); return;
    }
    posIntervalSaveMsg = 'Sparar…';
    renderPosIntervalAdmin();
    addUsage('w', 1);
    cfgDoc.set({ posIntervalS: v, updatedBy: userName || '', updatedAt: firebase.firestore.FieldValue.serverTimestamp() }, { merge: true })
      .then(function(){ posIntervalSaveMsg = 'Sparat – gäller alla telefoner.'; renderPosIntervalAdmin(); })
      .catch(function(err){
        posIntervalSaveMsg = (err && err.code === 'permission-denied')
          ? 'Kunde inte spara: Firestore-reglerna saknar "config". Gäller bara den här telefonen tills regeln är tillagd.'
          : 'Kunde inte spara (' + ((err && err.code) || 'fel') + ').';
        renderPosIntervalAdmin();
      });
  }
  function renderPosIntervalAdmin(){
    var seg = document.getElementById('adminPosIntervalSeg');
    if (!seg) return;
    Array.from(seg.children).forEach(function(b){
      var on = parseInt(b.getAttribute('data-s'), 10) === posIntervalS;
      b.classList.toggle('active', on);
      b.setAttribute('aria-checked', on ? 'true' : 'false');
    });
    // every write is read once by every other phone that's open
    var boats = 8, perHour = boats * (3600 / posIntervalS) * (boats - 1);
    document.getElementById('adminPosIntervalEst').textContent =
      'Med ' + boats + ' båtar som kör samtidigt: ca ' + (Math.round(perHour / 1000) * 1000).toLocaleString('sv-SE') + ' reads i timmen.';
    var st = document.getElementById('adminPosIntervalStatus');
    var msg = posIntervalSaveMsg;
    if (!msg && sharedCfgError === 'permission-denied') msg = 'Firestore-reglerna saknar "config" – inställningen kan inte delas med de andra än.';
    st.textContent = msg;
    st.hidden = !msg;
  }
  document.getElementById('adminPosIntervalSeg').addEventListener('click', function(e){
    var b = e.target.closest ? e.target.closest('button[data-s]') : null;
    if (b) setSharedPosInterval(parseInt(b.getAttribute('data-s'), 10));
  });
  renderPosIntervalAdmin();

