  /* ---- "Ladda ner sjön för offline" (Settings) ----
     Everything for the four styles in the quick button (all zoom levels) + the
     depth data, into a cache of its own per lake and map version
     ("ffmap-offline-<lake>-<version>"). The service worker looks in every cache,
     and keeps these when it clears its own. Stop = pause; pressing again goes on
     where it stopped (what's already saved is skipped). A new map version makes
     an old download out of date. */
  var OFF_VER = (LAKE.mapFile.match(/map_(v\d+)_/) || [0, 'v1'])[1];
  var OFF_CACHE = 'ffmap-offline-' + LAKE_ID + '-' + OFF_VER;
  var OFF_KEY = lakeKey('ffmap_offline_v1', 'offline_v1');     // {ver, files, bytes, done}
  var offBtn = document.getElementById('offBtn'), offBar = document.getElementById('offBar'),
      offFill = document.getElementById('offBarFill'), offStatus = document.getElementById('offStatus');
  var offRunning = false, offStop = false;
  document.getElementById('offTitle').textContent = 'Ladda ner ' + LAKE.name + ' för offline';
  // Where the downloaded files are kept. Here: the browser's Cache API. A hook for the app
  // (src/js/11-native.js on the branch "app" swaps it for files on the phone) -- don't remove it.
  var offStore = {
    _c: null,
    _open: function(){ return this._c || (this._c = caches.open(OFF_CACHE)); },
    available: function(){ return !!window.caches; },
    has: function(url){ return this._open().then(function(c){ return c.match(url); }).then(function(r){ return !!r; }); },
    size: function(url){ return this._open().then(function(c){ return c.match(url); }).then(function(r){ return r ? r.blob().then(function(b){ return b.size; }) : 0; }); },
    put: function(url, response){ return this._open().then(function(c){ return c.put(url, response); }); },
    clear: function(){                                   // (every download of this lake, every map version)
      this._c = null;
      if (!window.caches) return Promise.resolve();
      return caches.keys().then(function(keys){
        return Promise.all(keys.filter(function(k){ return k.indexOf('ffmap-offline-' + LAKE_ID + '-') === 0; }).map(function(k){ return caches.delete(k); }));
      });
    }
  };
  function offlineFiles(){
    var list = [lakeUrl(LAKE_DIR + LAKE.depth.file)];
    if (LAKE.bottom) list.push(lakeUrl(LAKE_DIR + LAKE.bottom.file));     // (Kartanalys: vegetation + hardness)
    QUICK_STYLES.forEach(function(sid){
      list.push(mapFile(sid), thumbFile(sid));
      ((DETAIL && DETAIL.levels) || []).forEach(function(L){
        if (L.styles.indexOf(sid) === -1) return;
        for (var r = 0; r < L.rows; r++) for (var c = 0; c < L.cols; c++){
          if (L.have.charAt(r * L.cols + c) === '1')
            list.push(lakeUrl(LAKE_DIR + DETAIL.file.replace('{z}', L.z).replace('{style}', sid).replace('{c}', c).replace('{r}', r)));
        }
      });
    });
    return list;
  }
  function offSaved(){ try { return JSON.parse(localStorage.getItem(OFF_KEY) || 'null'); } catch(e){ return null; } }
  function fmtMB(b){ return (b / 1048576).toFixed(b < 10485760 ? 1 : 0).replace('.', ',') + ' MB'; }
  function offShow(){
    var s = offSaved(), n = offlineFiles().length;
    offStatus.classList.remove('ok'); offBtn.classList.remove('ghost');
    if (offRunning) return;
    offBar.hidden = true;
    if (s && s.done && s.ver === OFF_VER){
      offStatus.textContent = 'Klar · ' + fmtMB(s.bytes) + ' sparat på telefonen · fungerar utan täckning';
      offStatus.classList.add('ok'); offBtn.textContent = 'Ta bort'; offBtn.classList.add('ghost');
    } else if (s && s.ver !== OFF_VER){
      offStatus.textContent = 'Ny kartversion finns – ladda ner igen'; offBtn.textContent = 'Ladda ner';
    } else if (s && s.files){
      offStatus.textContent = 'Pausad · ' + Math.round(100 * s.files / n) + ' % · tryck för att fortsätta'; offBtn.textContent = 'Fortsätt';
    } else {
      offStatus.textContent = n + ' kartbitar · ca ' + fmtMB(n * 60000); offBtn.textContent = 'Ladda ner';
    }
  }
  function offRemove(){
    return offStore.clear().then(function(){ try { localStorage.removeItem(OFF_KEY); } catch(e){} });
  }
  function offDownload(){
    if (!offStore.available()){ offStatus.textContent = 'Den här webbläsaren kan inte spara kartan offline.'; return; }
    if (navigator.storage && navigator.storage.persist) navigator.storage.persist().catch(function(){});
    var s = offSaved();
    var start = (s && s.ver !== OFF_VER) ? offRemove() : Promise.resolve();
    offRunning = true; offStop = false;
    offBtn.textContent = 'Pausa'; offBtn.classList.add('ghost'); offBar.hidden = false;
    var list = offlineFiles(), i = 0, done = 0, bytes = 0, failed = 0;
    start.then(function(){
      function step(){
        offFill.style.transform = 'scaleX(' + (done / list.length).toFixed(3) + ')';
        offStatus.textContent = 'Laddar ner… ' + done + ' av ' + list.length + ' · ' + fmtMB(bytes);
        try { localStorage.setItem(OFF_KEY, JSON.stringify({ ver: OFF_VER, files: done, bytes: bytes, done: false })); } catch(e){}
      }
      function one(){
        if (offStop || i >= list.length) return Promise.resolve();
        var url = new URL(list[i++], location.href).href;
        return offStore.has(url).then(function(hit){
          if (hit) return offStore.size(url).then(function(n){ bytes += n; });
          return fetch(url).then(function(r){
            if (!r.ok) throw new Error(r.status);
            return r.clone().blob().then(function(b){ bytes += b.size; return offStore.put(url, r); });
          });
        }).catch(function(){ failed++; }).then(function(){ done++; if (done % 10 === 0 || done === list.length) step(); return one(); });
      }
      var workers = []; for (var k = 0; k < 6; k++) workers.push(one());   // 6 at a time
      return Promise.all(workers).then(function(){
        offRunning = false;
        if (offStop){ step(); offShow(); return; }
        if (failed){
          try { localStorage.setItem(OFF_KEY, JSON.stringify({ ver: OFF_VER, files: done - failed, bytes: bytes, done: false })); } catch(e){}
          offShow(); offStatus.textContent = failed + ' bitar kunde inte hämtas (täckning?) – tryck Fortsätt'; return;
        }
        try { localStorage.setItem(OFF_KEY, JSON.stringify({ ver: OFF_VER, files: done, bytes: bytes, done: true })); } catch(e){}
        offMarkRunning(false); offShow();
      });
    }).catch(function(){ offRunning = false; offShow(); offStatus.textContent = 'Kunde inte spara (fullt minne?)'; });
  }
  // (turning the phone reloads the page: a download that was running goes on by itself)
  var OFF_RUN_KEY = 'ffmap_offline_running_v1';
  function offMarkRunning(on){ try { on ? sessionStorage.setItem(OFF_RUN_KEY, LAKE_ID) : sessionStorage.removeItem(OFF_RUN_KEY); } catch(e){} }
  offBtn.addEventListener('click', function(){
    if (offRunning){ offStop = true; offMarkRunning(false); return; }     // pause
    var s = offSaved();
    if (s && s.done && s.ver === OFF_VER){ offRemove().then(offShow); return; }
    offMarkRunning(true); offDownload();
  });
  offShow();
  (function(){
    var r = null; try { r = sessionStorage.getItem(OFF_RUN_KEY); } catch(e){}
    var s = offSaved();
    if (r === LAKE_ID && !(s && s.done && s.ver === OFF_VER)) offDownload(); else offMarkRunning(false);
  })();
  document.addEventListener('click', function(e){
    if (mapTypePop.classList.contains('show') && !mapTypePop.contains(e.target) && e.target !== mapTypeBtn) openMapTypePop(false);
  });
  markStyle(mapStyle, null);
  applyLegend(mapStyle);
  loadMapStyle(mapStyle, true);

