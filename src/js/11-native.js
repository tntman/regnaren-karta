  /* ---- the app (Capacitor, only on the branch "app") -- see tools/APP.md ----
     Does nothing on the web (NATIVE = false). Sits right after 10-core.js: the hooks below
     (lakeUrl, lakeImgError) are already used while the next files run.
     - The overview maps, thumbnails, depth/bottom data and Help are packed into the app;
       the detail tiles (tiles_vN folders) come from GitHub Pages and every tile you've looked at is
       saved on the phone (files in the app's own folder) -- so is "Ladda ner för offline".
     - Background GPS: while you're at the lake, a watcher (with Android's notification
       "FF Map delar din position") keeps the GPS going when the app is put away; its fixes
       go to handleGpsFix like the browser's, and your position is then written with
       Firestore's REST API (the SDK's connection is throttled in the background). */
  var NATIVE = !!(window.Capacitor && Capacitor.isNativePlatform && Capacitor.isNativePlatform());
  var APP_REMOTE = 'https://tntman.github.io/regnaren-karta/';   // GitHub Pages (docs/)
  var APP_FILES_KEY = 'ffmap_app_files_v1';                        // {"lakes/<id>/...": bytes} saved on the phone
  var APP_BG_KEY = 'ffmap_app_bg_share_v1';                        // "Dela position när appen är minimerad"
  var appFiles = {}, appFilesDir = null, appSaving = {};
  function appIsTile(p){ return /\/tiles_v\d+\//.test(p); }        // not packed into the app
  function appPath(url){ var i = url.indexOf('lakes/'); return i < 0 ? url : url.slice(i); }
  var appSaveIndexT = 0;
  function appSaveIndex(){
    clearTimeout(appSaveIndexT);
    appSaveIndexT = setTimeout(function(){ try { localStorage.setItem(APP_FILES_KEY, JSON.stringify(appFiles)); } catch(e){} }, 1000);
  }
  if (NATIVE){
    var AppFs = Capacitor.registerPlugin('Filesystem');
    var AppGeo = Capacitor.registerPlugin('BackgroundGeolocation');
    try { appFiles = JSON.parse(localStorage.getItem(APP_FILES_KEY) || '{}') || {}; } catch(e){}
    AppFs.getUri({ path: '', directory: 'DATA' }).then(function(r){
      appFilesDir = Capacitor.convertFileSrc(r.uri).replace(/\/?$/, '/');
    }).catch(function(e){ console.warn('appens mapp', e); });

    // a tile: saved copy first, else GitHub Pages; everything else is in the app
    lakeUrl = function(p){
      if (!appIsTile(p)) return p;
      return appFiles[p] && appFilesDir ? appFilesDir + p : APP_REMOTE + p;
    };
    // a saved copy that doesn't load (gone/broken): forget it, take the one on the net
    lakeImgError = function(el){
      if (!appFilesDir || el.src.indexOf(appFilesDir) !== 0) return false;
      var p = appPath(el.src);
      delete appFiles[p]; appSaveIndex();
      el.src = APP_REMOTE + p;
      return true;
    };
    // every tile you look at is saved (like the service worker does on the web)
    document.addEventListener('load', function(e){
      var el = e.target;
      if (el.tagName === 'IMG' && el.src.indexOf(APP_REMOTE) === 0) appSave(el.src);
    }, true);
  }
  function appWrite(p, blob){
    return new Promise(function(ok, bad){
      var fr = new FileReader();
      fr.onload = function(){ ok(fr.result.slice(fr.result.indexOf(',') + 1)); };
      fr.onerror = bad;
      fr.readAsDataURL(blob);
    }).then(function(b64){
      return AppFs.writeFile({ path: p, data: b64, directory: 'DATA', recursive: true });
    }).then(function(){ appFiles[p] = blob.size; appSaveIndex(); });
  }
  function appSave(url){
    var p = appPath(url);
    if (appFiles[p] || appSaving[p]) return;
    appSaving[p] = true;
    fetch(url).then(function(r){ if (!r.ok) throw r.status; return r.blob(); })
      .then(function(b){ return appWrite(p, b); })
      .catch(function(){}).then(function(){ delete appSaving[p]; });
  }
  // Offline (Settings): the same list and buttons, but files in the app's folder. Keyed by the
  // file's path, so a tile counts as saved whether the list gives its net or its phone address.
  var appOffStore = {
    available: function(){ return true; },
    has: function(url){ var p = appPath(url); return Promise.resolve(!appIsTile(p) || !!appFiles[p]); },
    size: function(url){
      var p = appPath(url);
      if (appFiles[p]) return Promise.resolve(appFiles[p]);
      return fetch(p).then(function(r){ return r.blob(); }).then(function(b){ return b.size; }).catch(function(){ return 0; });
    },
    put: function(url, response){ var p = appPath(url); return response.blob().then(function(b){ return appWrite(p, b); }); },
    clear: function(){                                     // (every saved tile of this lake)
      var pre = 'lakes/' + LAKE_ID + '/';
      Object.keys(appFiles).forEach(function(p){ if (p.indexOf(pre) === 0) delete appFiles[p]; });
      appSaveIndex();
      return AppFs.rmdir({ path: 'lakes/' + LAKE_ID, directory: 'DATA', recursive: true }).catch(function(){});
    }
  };

  /* ---- background GPS ---- */
  var appBgOn = true;
  try { appBgOn = localStorage.getItem(APP_BG_KEY) !== '0'; } catch(e){}
  var appPaused = false, appWatcher = null, appTok = null;  // appTok: {id, refresh, exp} for the REST write
  function appHidden(){ return appPaused || document.visibilityState === 'hidden'; }
  // the watcher runs while you're at the lake (Android: its notification shows meanwhile);
  // it has to be started while the app is open -- Android doesn't allow it from the background
  function appBgUpdate(){
    var want = appBgOn && !!myUid && !!lastRealFix && isNearLake(lastRealFix.lat, lastRealFix.lon);
    if (want && !appWatcher && !appHidden()){
      appWatcher = AppGeo.addWatcher({
        backgroundTitle: 'FF Map delar din position',
        backgroundMessage: 'Båten syns för de andra. Stängs av i Inställningar → Båten.',
        requestPermissions: false, stale: false, distanceFilter: 0   // (0: fixes at anchor too, so the boat never turns grey)
      }, appBgFix);
      appWatcher.catch(function(e){ console.warn('bakgrunds-GPS', e); appWatcher = null; });
    } else if (!want && appWatcher){
      appWatcher.then(function(id){ AppGeo.removeWatcher({ id: id }); }).catch(function(){});
      appWatcher = null;
    }
  }
  function appBgFix(loc, err){
    if (err || !loc || !appHidden()) return;               // (open app: the ordinary GPS is used)
    handleGpsFix({ coords: { latitude: loc.latitude, longitude: loc.longitude, accuracy: loc.accuracy,
                             speed: loc.speed, heading: loc.bearing }, timestamp: loc.time });
    appBgUpdate();                                         // left the lake: stop
  }
  function appGrabToken(){
    var u = window.firebase && firebase.auth && firebase.auth().currentUser;
    if (!u) return;
    u.getIdTokenResult().then(function(r){
      appTok = { id: r.token, refresh: u.refreshToken, exp: Date.parse(r.expirationTime) };
    }).catch(function(){});
  }
  // a fresh ID token without the SDK (it lasts an hour; refreshed with the refresh token)
  function appToken(){
    if (!appTok) return Promise.reject('no token');
    if (appTok.exp - Date.now() > 300000) return Promise.resolve(appTok.id);
    return Capacitor.Plugins.CapacitorHttp.post({
      url: 'https://securetoken.googleapis.com/v1/token?key=' + FIREBASE_CONFIG.apiKey,
      headers: { 'Content-Type': 'application/json' },
      data: { grant_type: 'refresh_token', refresh_token: appTok.refresh }
    }).then(function(r){
      var d = typeof r.data === 'string' ? JSON.parse(r.data) : r.data;
      if (!d || !d.id_token) throw 'token ' + r.status;
      appTok = { id: d.id_token, refresh: d.refresh_token, exp: Date.now() + d.expires_in * 1000 };
      return appTok.id;
    });
  }
  // your position doc, merged, through Firestore's REST API (native HTTP: not throttled in the background)
  function appRestWrite(data){
    var fields = {}, mask = [];
    Object.keys(data).forEach(function(k){
      var v = data[k];
      if (typeof v === 'number') fields[k] = { doubleValue: v };
      else if (typeof v === 'string') fields[k] = { stringValue: v };
      else return;                                         // (updatedAt: the server's time, below)
      mask.push(k);
    });
    var db = 'projects/' + FIREBASE_CONFIG.projectId + '/databases/(default)';
    return appToken().then(function(tok){
      return Capacitor.Plugins.CapacitorHttp.post({
        url: 'https://firestore.googleapis.com/v1/' + db + '/documents:commit',
        headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + tok },
        data: { writes: [{
          update: { name: db + '/documents/positions/' + posDocId(myUid), fields: fields },
          updateMask: { fieldPaths: mask },
          updateTransforms: [{ fieldPath: 'updatedAt', setToServerValue: 'REQUEST_TIME' }]
        }] }
      });
    }).then(function(r){ if (r.status >= 300) throw r.status; });
  }
  if (NATIVE){
    var webWriteOwnPosition = writeOwnPosition;
    writeOwnPosition = function(data){
      if (!appHidden()) return webWriteOwnPosition(data);
      appRestWrite(data).catch(function(e){ console.warn('kunde inte dela position (bakgrund)', e); webWriteOwnPosition(data); });
    };
    document.addEventListener('pause', function(){ appPaused = true; appGrabToken(); });
    document.addEventListener('resume', function(){ appPaused = false; });
    document.addEventListener('visibilitychange', function(){ if (document.visibilityState === 'hidden') appGrabToken(); });
    setInterval(function(){ if (!appHidden()) appBgUpdate(); }, 5000);

    // Settings → Båten, first row
    var appBgRow = document.createElement('label');
    appBgRow.className = 'settingsRow'; appBgRow.htmlFor = 'toggleBgShare';
    appBgRow.innerHTML = '<div class="settingsRowText"><div class="settingsRowTitle">Dela position när appen är minimerad</div>' +
      '<div class="settingsRowDesc">Vid sjön syns båten för de andra även när appen ligger i bakgrunden eller skärmen är låst. ' +
      'Telefonen visar en notis så länge positionen delas. Stäng appen helt (svep bort den) så slutar delningen.</div></div>' +
      '<span class="toggle"><input type="checkbox" id="toggleBgShare"><span class="toggleTrack"><span class="toggleThumb"></span></span></span>';
    var appBoatSec = document.querySelector('.setSec[data-sec="boat"] .setSecBody');
    appBoatSec.insertBefore(appBgRow, appBoatSec.firstChild);
    var appBgToggle = document.getElementById('toggleBgShare');
    appBgToggle.checked = appBgOn;
    appBgToggle.addEventListener('change', function(){
      appBgOn = appBgToggle.checked;
      try { localStorage.setItem(APP_BG_KEY, appBgOn ? '1' : '0'); } catch(e){}
      appBgUpdate();
    });
    // offStore is set in 18-offline.js (after this file) -- swap it once every file has run
    Promise.resolve().then(function(){ offStore = appOffStore; });
  }
