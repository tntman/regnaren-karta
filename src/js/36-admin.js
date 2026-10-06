  /* ---------------- Admin (bara för Filip, låst med PIN-kod) ----------------
     Note: this is a convenience lock, not real security -- identity in this
     app is just the chosen name, and the Firestore rules (not this page)
     are what actually decide who may read/write what. Only a SHA-256 hash
     of the code is stored here, never the code itself. */
  var ADMIN_PIN_HASH = '08b9a012b423837c8dfa73b63ee55c2a3f2328e1657db955e7a4ca1ceee0eaf7';
  var ADMIN_UNLOCK_KEY = 'ffmap_admin_unlock_v1';

  // isAdminName() also runs while the page is still starting (from
  // showUserName), before the constants above are set -- so it compares
  // with a literal; the other two only run on user actions.
  function isAdminName(){ return nameSlug(userName) === 'filip'; }
  function isAdminUnlocked(){
    if (!isAdminName()) return false;
    try { return localStorage.getItem(ADMIN_UNLOCK_KEY) === ADMIN_PIN_HASH; } catch(e){ return false; }
  }
  // the admin (unlocked on this device) can always change and delete everyone's spots
  function adminCanEditAll(){ return isAdminUnlocked(); }
  // (looks its elements up by id every time: it's first called while the
  // page is still starting, before the rest of this section has run)
  function updateAdminVisibility(){
    var row = document.getElementById('adminRow');
    if (row) row.hidden = !isAdminName();
    if (!isAdminName()) closeAdminView();
  }
  function closeAdminView(){
    var v = document.getElementById('adminView');
    if (v) v.classList.remove('show');
    if (adminTimer){ clearInterval(adminTimer); adminTimer = null; }
  }
  function refreshAdminIfOpen(){
    var v = document.getElementById('adminView');
    if (v && v.classList.contains('show')) renderAdmin();
  }

  var adminView = document.getElementById('adminView');
  var adminStatsEl = document.getElementById('adminStats');
  var adminUsersEl = document.getElementById('adminUsers');
  var adminUsageEl = document.getElementById('adminUsage');
  var pinBackdrop = document.getElementById('pinBackdrop');
  var pinModal = document.getElementById('pinModal');
  var pinInput = document.getElementById('pinInput');
  var pinError = document.getElementById('pinError');
  var adminTimer = null;

  function sha256Hex(text){
    if (!(window.crypto && crypto.subtle && window.TextEncoder)) return Promise.reject(new Error('no crypto'));
    return crypto.subtle.digest('SHA-256', new TextEncoder().encode(text)).then(function(buf){
      return Array.from(new Uint8Array(buf)).map(function(b){ return ('0' + b.toString(16)).slice(-2); }).join('');
    });
  }
  function showPinModal(){
    pinInput.value = '';
    pinError.hidden = true;
    pinBackdrop.classList.add('show');
    pinModal.classList.add('show');
    setTimeout(function(){ pinInput.focus(); }, 200);
  }
  function hidePinModal(){
    pinBackdrop.classList.remove('show');
    pinModal.classList.remove('show');
    pinInput.blur();
  }
  function tryPin(){
    var code = pinInput.value.trim();
    if (!code){ pinInput.focus(); return; }
    sha256Hex('ffmap-admin:' + code).then(function(h){
      if (h === ADMIN_PIN_HASH){
        try { localStorage.setItem(ADMIN_UNLOCK_KEY, h); } catch(e){}
        hidePinModal();
        openAdminView();
      } else {
        pinError.textContent = 'Fel kod, försök igen.';
        pinError.hidden = false;
        pinInput.value = '';
        pinInput.focus();
      }
    }).catch(function(){
      pinError.textContent = 'Kan inte kontrollera koden i den här webbläsaren.';
      pinError.hidden = false;
    });
  }
  document.getElementById('pinOk').addEventListener('click', tryPin);
  document.getElementById('pinCancel').addEventListener('click', hidePinModal);
  pinBackdrop.addEventListener('click', hidePinModal);
  pinInput.addEventListener('keydown', function(e){ if (e.key === 'Enter') tryPin(); });
  pinInput.addEventListener('input', function(){ pinError.hidden = true; });

  document.getElementById('adminOpenBtn').addEventListener('click', function(){
    if (isAdminUnlocked()) openAdminView(); else showPinModal();
  });
  document.getElementById('adminBackBtn').addEventListener('click', closeAdminView);
  document.getElementById('adminLock').addEventListener('click', function(){
    try { localStorage.removeItem(ADMIN_UNLOCK_KEY); } catch(e){}
    closeAdminView();
  });

  function openAdminView(){
    if (!isAdminUnlocked()) return;
    usageReports = null; usageFetchError = null;
    posIntervalSaveMsg = ''; renderPosIntervalAdmin();
    renderAdmin();
    fetchUsageTotals();
    adminView.classList.add('show');
    adminBodyScrollTop();
    if (adminTimer) clearInterval(adminTimer);
    adminTimer = setInterval(renderAdmin, 20000); // keeps "senast sedd" fresh while open
  }
  function adminBodyScrollTop(){ var b = document.getElementById('adminBody'); if (b) b.scrollTop = 0; }

  document.getElementById('adminUsageRefresh').addEventListener('click', fetchUsageTotals);

  function statTile(value, label){
    var t = document.createElement('div'); t.className = 'statTile';
    var v = document.createElement('div'); v.className = 'statValue'; v.textContent = String(value);
    var l = document.createElement('div'); l.className = 'statLabel'; l.textContent = label;
    t.appendChild(v); t.appendChild(l);
    return t;
  }

  function collectUsers(){
    var users = {};
    function get(uid, name){
      if (!uid || uid === 'local') return null;
      var u = users[uid];
      if (!u) u = users[uid] = { uid: uid, name: '', spots: 0, lastSpot: 0, pos: null };
      if (name && !u.name) u.name = name;
      return u;
    }
    waypoints.forEach(function(w){
      var u = get(w.uid, w.by);
      if (!u) return;
      u.spots++;
      u.lastSpot = Math.max(u.lastSpot, w.createdAt || 0);
    });
    allPositions.forEach(function(p){
      var u = get(p.uid, p.name);
      if (!u) return;
      if (p.name) u.name = p.name; // the position doc has the freshest spelling
      u.pos = p;
    });
    return Object.keys(users).map(function(k){
      var u = users[k];
      if (!u.name) u.name = u.uid;
      var posSeen = (u.pos && u.pos.updatedAt > 0) ? u.pos.updatedAt : 0;
      u.lastSeen = Math.max(posSeen, u.lastSpot);
      return u;
    });
  }

  function renderAdmin(){
    testRender();   // (Testläge, 37-testmode.js: only in Demo Mode)
    backupRenderStatus();
    var now = Date.now();
    var midnight = new Date(); midnight.setHours(0, 0, 0, 0);
    var users = collectUsers();
    var liveBoats = allPositions.filter(function(p){ return p.updatedAt > 0 && now - p.updatedAt <= BOAT_GRAY_MS; }).length;

    adminStatsEl.innerHTML = '';
    adminStatsEl.appendChild(statTile(waypoints.length, 'Fiskeplatser totalt'));
    adminStatsEl.appendChild(statTile(waypoints.filter(function(w){ return w.createdAt >= midnight.getTime(); }).length, 'Nya idag'));
    adminStatsEl.appendChild(statTile(waypoints.filter(function(w){ return now - w.createdAt <= 7 * 864e5; }).length, 'Nya senaste 7 d'));
    adminStatsEl.appendChild(statTile(users.length, 'Användare'));
    adminStatsEl.appendChild(statTile(liveBoats, 'Aktiva på kartan nu'));
    adminStatsEl.appendChild(statTile(allPositions.length, 'Positioner i databasen'));

    // users: active first, then most recently seen
    users.sort(function(a, b){ return (b.lastSeen || 0) - (a.lastSeen || 0); });
    adminUsersEl.innerHTML = '';
    if (!users.length){
      var empty = document.createElement('div'); empty.className = 'adminNote'; empty.textContent = 'Inga användare ännu.';
      adminUsersEl.appendChild(empty);
    }
    users.forEach(function(u){
      var age = (u.pos && u.pos.updatedAt > 0) ? now - u.pos.updatedAt : Infinity;
      var status = age <= BOAT_GRAY_MS ? 'live' : (age <= BOAT_REMOVE_MS ? 'stale' : 'none');
      var row = document.createElement('div'); row.className = 'adminUserRow';
      var info = document.createElement('div'); info.className = 'adminUserInfo';
      var nm = document.createElement('div'); nm.className = 'adminUserName';
      var dot = document.createElement('span'); dot.className = 'statusDot ' + status;
      nm.appendChild(dot);
      nm.appendChild(document.createTextNode(u.name + (u.uid === myUid ? ' (du)' : '')));
      var meta = document.createElement('div'); meta.className = 'adminUserMeta';
      var statusText = status === 'live' ? 'På kartan nu' : (status === 'stale' ? 'Grå på kartan' : 'Inte på kartan');
      meta.textContent = statusText + ' · ' + u.spots + (u.spots === 1 ? ' fiskeplats' : ' fiskeplatser') +
        (u.lastSeen ? ' · senast sedd ' + timeAgo(u.lastSeen) : '');
      info.appendChild(nm); info.appendChild(meta);
      row.appendChild(info);
      if (status !== 'none' && u.uid !== myUid && u.pos){
        var btn = document.createElement('button');
        btn.type = 'button'; btn.className = 'btnAdmin small'; btn.textContent = 'Dölj båt';
        btn.addEventListener('click', function(){
          if (confirm('Dölja ' + u.name + ' från kartan för alla?')) hidePositions([u.pos.docId]);
        });
        row.appendChild(btn);
      }
      adminUsersEl.appendChild(row);
    });

    var usage = loadUsage();
    fillUsageLines(adminUsageEl, usage);
    renderUsageTotals();
  }

  function fmtPct(n, max){
    var pct = n / max * 100;
    return (pct < 0.1 && n > 0) ? '<0,1' : pct.toFixed(1).replace('.', ',');
  }
  function fillUsageLines(el, u){
    el.innerHTML = '';
    [['Reads', u.r, 50000], ['Writes', u.w, 20000], ['Deletes', u.d, 20000]].forEach(function(x){
      var line = document.createElement('div'); line.className = 'usageLine';
      line.textContent = x[0] + ': ' + x[1].toLocaleString('sv-SE') + '  (' + fmtPct(x[1], x[2]) + ' % av kvoten)';
      el.appendChild(line);
    });
  }

  // latest fetched reports for today (one per device), keyed by device id
  var usageReports = null, usageFetchError = null, usageFetchedAt = 0;
  function fetchUsageTotals(){
    if (!USE_FIREBASE || !usageCol){ usageFetchError = 'offline'; renderUsageTotals(); return; }
    reportUsage(true); // get this device's latest numbers in first
    var day = loadUsage().day;
    usageCol.where('day', '==', day).get().then(function(snap){
      countGetReads(snap);
      var list = {};
      snap.forEach(function(doc){
        var x = doc.data();
        if ((x.lake || LAKE_ID) !== LAKE_ID) return;
        list[x.device || doc.id] = x;
      });
      usageReports = list;
      usageFetchError = null;
      usageFetchedAt = Date.now();
      renderUsageTotals();
    }).catch(function(e){
      usageFetchError = (e && e.code === 'permission-denied') ? 'denied' : 'failed';
      renderUsageTotals();
    });
  }
  function renderUsageTotals(){
    var totalEl = document.getElementById('adminUsageTotal');
    var peopleEl = document.getElementById('adminUsagePeople');
    if (!totalEl) return;
    peopleEl.innerHTML = '';
    if (usageFetchError === 'denied' || usageReportDenied){
      totalEl.innerHTML = '<div class="adminNote" style="color:var(--danger);">Totalen kräver en ny regel i Firestore (samlingen "usage"). Lägg till den i Firebase-konsolen under Firestore → Rules.</div>';
      return;
    }
    if (!usageReports){
      totalEl.innerHTML = '<div class="adminNote">' + (usageFetchError ? 'Kunde inte hämta totalen just nu.' : 'Hämtar…') + '</div>';
      return;
    }
    // this device: use the live local counters rather than the last report
    var reports = Object.assign({}, usageReports);
    var mine = loadUsage();
    reports[DEVICE_ID] = { uid: myUid, name: userName, r: mine.r, w: mine.w, d: mine.d };
    var sum = { r: 0, w: 0, d: 0 }, people = {};
    Object.keys(reports).forEach(function(k){
      var x = reports[k];
      sum.r += x.r || 0; sum.w += x.w || 0; sum.d += x.d || 0;
      var key = x.uid || k;
      var pp = people[key] || (people[key] = { name: x.name || key, r: 0, w: 0, d: 0 });
      if (x.name) pp.name = x.name;
      pp.r += x.r || 0; pp.w += x.w || 0; pp.d += x.d || 0;
    });
    fillUsageLines(totalEl, sum);
    Object.keys(people).map(function(k){ return people[k]; })
      .sort(function(a, b){ return b.r - a.r; })
      .forEach(function(pp){
        var row = document.createElement('div'); row.className = 'usagePerson';
        var n = document.createElement('span'); n.className = 'n'; n.textContent = pp.name;
        var v = document.createElement('span'); v.className = 'v';
        v.textContent = pp.r.toLocaleString('sv-SE') + ' r · ' + pp.w.toLocaleString('sv-SE') + ' w · ' + pp.d.toLocaleString('sv-SE') + ' d';
        row.appendChild(n); row.appendChild(v);
        peopleEl.appendChild(row);
      });
    var ago = document.createElement('div'); ago.className = 'adminNote';
    ago.textContent = 'Hämtat ' + timeAgo(usageFetchedAt) + ' · ' + Object.keys(reports).length + (Object.keys(reports).length === 1 ? ' enhet' : ' enheter');
    peopleEl.appendChild(ago);
  }

  // Hide boats for everyone by marking their positions as ancient (the same
  // trick as logging out -- works with the current Firestore rules).
  function hidePositions(docIds){
    if (!USE_FIREBASE || !posCol || !firebase.firestore.Timestamp || !docIds.length) return;
    docIds.forEach(function(id){
      addUsage('w', 1);
      posCol.doc(id).set({ updatedAt: firebase.firestore.Timestamp.fromMillis(0) }, { merge: true })
        .catch(function(e){ console.warn('kunde inte dölja båt', e); });
    });
  }
  document.getElementById('adminHideStale').addEventListener('click', function(){
    var now = Date.now();
    var ids = allPositions.filter(function(p){
      var age = now - p.updatedAt;
      return p.updatedAt > 0 && age > BOAT_GRAY_MS && age <= BOAT_REMOVE_MS && p.uid !== myUid;
    }).map(function(p){ return p.docId; });
    if (!ids.length){ alert('Det finns inga grå båtar just nu.'); return; }
    if (confirm('Dölja ' + ids.length + (ids.length === 1 ? ' grå båt' : ' grå båtar') + ' för alla?')) hidePositions(ids);
  });
  document.getElementById('adminHideAll').addEventListener('click', function(){
    var now = Date.now();
    var ids = allPositions.filter(function(p){
      return p.updatedAt > 0 && now - p.updatedAt <= BOAT_REMOVE_MS && p.uid !== myUid;
    }).map(function(p){ return p.docId; });
    if (!ids.length){ alert('Det finns inga båtar på kartan just nu.'); return; }
    if (confirm('Dölja alla ' + ids.length + ' båtar på kartan för alla? (Den som har appen öppen dyker upp igen inom en minut.)')) hidePositions(ids);
  });

  /* ---- export (GPX for chartplotters, CSV for Excel) ---- */
  function xmlEsc(v){ return String(v == null ? '' : v).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;'); }
  function exportStamp(){ return new Date().toLocaleDateString('sv-SE'); }
  function sortedWaypoints(){ return waypoints.slice().sort(function(a, b){ return (a.createdAt || 0) - (b.createdAt || 0); }); }
  function wpOwnerName(w){
    if (w.by) return w.by;
    var u = collectUsers().filter(function(x){ return x.uid === w.uid; })[0];
    return u ? u.name : (w.uid || '');
  }
  function buildGpx(){
    var out = ['<?xml version="1.0" encoding="UTF-8"?>',
      '<gpx version="1.1" creator="FF Map" xmlns="http://www.topografix.com/GPX/1/1">',
      '  <metadata><name>FF Map – ' + xmlEsc(LAKE_ID) + ' – fiskeplatser</name><time>' + new Date().toISOString() + '</time></metadata>'];
    sortedWaypoints().forEach(function(w){
      out.push('  <wpt lat="' + Number(w.lat).toFixed(7) + '" lon="' + Number(w.lon).toFixed(7) + '">');
      if (w.createdAt) out.push('    <time>' + new Date(w.createdAt).toISOString() + '</time>');
      out.push('    <name>' + xmlEsc(w.name || 'Fiskeplats') + '</name>');
      out.push('    <desc>' + xmlEsc(WP_TYPES[wpType(w)].label + ' · sparad av ' + wpOwnerName(w)) + '</desc>');
      out.push('    <type>' + xmlEsc(WP_TYPES[wpType(w)].label) + '</type>');
      out.push('    <sym>' + (wpType(w) === 'mark' ? 'Flag, Blue' : 'Fishing Hot Spot Facility') + '</sym>');
      out.push('  </wpt>');
    });
    out.push('</gpx>');
    return out.join('\n') + '\n';
  }
  function csvCell(v){
    v = String(v == null ? '' : v);
    return /[";\n]/.test(v) ? '"' + v.replace(/"/g, '""') + '"' : v;
  }
  function buildCsv(){
    // semicolons + decimal commas = opens straight into Swedish Excel
    var rows = [['Namn', 'Typ', 'Latitud', 'Longitud', 'Sparad av', 'Skapad']];
    sortedWaypoints().forEach(function(w){
      rows.push([w.name || 'Fiskeplats', WP_TYPES[wpType(w)].label,
        Number(w.lat).toFixed(6).replace('.', ','), Number(w.lon).toFixed(6).replace('.', ','),
        wpOwnerName(w), w.createdAt ? new Date(w.createdAt).toLocaleString('sv-SE').slice(0, 16) : '']);
    });
    return '﻿' + rows.map(function(r){ return r.map(csvCell).join(';'); }).join('\r\n') + '\r\n';
  }
  function exportFile(fileName, mime, text){
    var blob = new Blob([text], { type: mime });
    var file = null;
    try { file = new File([blob], fileName, { type: mime }); } catch(e){}
    // phones: the share sheet ("Spara i Filer", AirDrop, mail ...) is the
    // most reliable way to hand over a file; elsewhere a normal download
    if (file && navigator.canShare && navigator.share && navigator.canShare({ files: [file] })){
      navigator.share({ files: [file], title: fileName }).catch(function(){});
      return;
    }
    var a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = fileName;
    document.body.appendChild(a);
    a.click();
    setTimeout(function(){ URL.revokeObjectURL(a.href); a.remove(); }, 1500);
  }
  document.getElementById('adminExportGpx').addEventListener('click', function(){
    exportFile('ffmap-' + LAKE_ID + '-fiskeplatser-' + exportStamp() + '.gpx', 'application/gpx+xml', buildGpx());
  });
  document.getElementById('adminExportCsv').addEventListener('click', function(){
    exportFile('ffmap-' + LAKE_ID + '-fiskeplatser-' + exportStamp() + '.csv', 'text/csv', buildCsv());
  });

  /* ---- Säkerhetskopia: the whole database to a file, and back ----
     What's worth keeping: the spots (all lakes), config, the Spår and trackusers -- not the boats or the
     usage counters (they come back by themselves). A Timestamp is saved as {__ts: ms}. Two taps: "Gör en
     kopia" fetches, then "Spara filen" hands it over (the iPhone's share sheet wants a fresh tap).
     Restoring writes every doc in the file back (set): what was deleted or changed since comes back,
     what was added since is left alone. A copy only goes back into the project it came from. */
  var BACKUP_COLS = ['waypoints', 'config', 'tracks', 'trackusers'];
  var BACKUP_AT_KEY = testKey('ffmap_backup_at_v1');
  var backupMakeBtn = document.getElementById('adminBackupMake');
  var backupStatusEl = document.getElementById('adminBackupStatus');
  var backupFile = null, backupBusy = false;
  function bkOut(v){
    if (v && typeof v.toMillis === 'function') return { __ts: v.toMillis() };
    if (Array.isArray(v)) return v.map(bkOut);
    if (v && typeof v === 'object'){ var o = {}; for (var k in v) o[k] = bkOut(v[k]); return o; }
    return v;
  }
  function bkIn(v){
    if (Array.isArray(v)) return v.map(bkIn);
    if (v && typeof v === 'object'){
      var ks = Object.keys(v);
      if (ks.length === 1 && ks[0] === '__ts') return firebase.firestore.Timestamp.fromMillis(v.__ts);
      var o = {}; ks.forEach(function(k){ o[k] = bkIn(v[k]); }); return o;
    }
    return v;
  }
  function backupCounts(cols){
    var n = function(c){ return Object.keys(cols[c] || {}).length; };
    return n('waypoints') + ' fiskeplatser, ' + n('tracks') + ' spårdagar, ' + n('config') + ' inställningar';
  }
  function backupRenderStatus(){
    if (backupBusy || backupFile) return;
    var at = 0; try { at = +localStorage.getItem(BACKUP_AT_KEY) || 0; } catch(e){}
    if (!at){ backupStatusEl.textContent = 'Ingen kopia sparad från den här telefonen än.'; return; }
    var days = Math.floor((Date.now() - at) / 86400000);
    backupStatusEl.textContent = 'Senaste kopia: ' + new Date(at).toLocaleDateString('sv-SE') + (days > 0 ? ' (för ' + days + (days === 1 ? ' dag' : ' dagar') + ' sedan)' : ' (idag)');
  }
  backupMakeBtn.addEventListener('click', function(){
    if (backupFile){   // second tap: hand the file over
      exportFile(backupFile.name, 'application/json', backupFile.text);
      try { localStorage.setItem(BACKUP_AT_KEY, String(Date.now())); } catch(e){}
      backupFile = null; backupMakeBtn.textContent = 'Gör en kopia';
      backupRenderStatus(); return;
    }
    if (backupBusy) return;
    if (!USE_FIREBASE){ backupStatusEl.textContent = 'Inte ansluten till databasen – försök igen när du har täckning.'; return; }
    backupBusy = true; backupStatusEl.textContent = 'Hämtar allt från databasen…';
    var fsdb = firebase.firestore(), out = { app: 'ffmap', v: 1, project: FIREBASE_CONFIG.projectId, at: Date.now(), cols: {} };
    Promise.all(BACKUP_COLS.map(function(c){
      return fsdb.collection(c).get({ source: 'server' }).then(function(snap){
        countGetReads(snap);
        var docs = out.cols[c] = {};
        snap.forEach(function(d){ docs[d.id] = bkOut(d.data()); });
      });
    })).then(function(){
      var text = JSON.stringify(out);
      backupFile = { name: (TEST_MODE ? 'ffmap-testlage-kopia-' : 'ffmap-kopia-') + exportStamp() + '.json', text: text };
      backupBusy = false; backupMakeBtn.textContent = 'Spara filen';
      backupStatusEl.textContent = 'Klar: ' + backupCounts(out.cols) + ' (' + (text.length / 1048576).toFixed(1).replace('.', ',') + ' MB). Tryck Spara filen.';
    }).catch(function(e){
      backupBusy = false;
      backupStatusEl.textContent = 'Kunde inte hämta allt (' + ((e && e.code) || 'fel') + '). Försök igen när du har täckning.';
    });
  });
  var backupInput = document.getElementById('adminBackupFile');
  document.getElementById('adminBackupRestore').addEventListener('click', function(){
    if (backupBusy) return;
    if (!USE_FIREBASE){ backupStatusEl.textContent = 'Inte ansluten till databasen – försök igen när du har täckning.'; return; }
    backupInput.value = ''; backupInput.click();
  });
  backupInput.addEventListener('change', function(){
    var f = backupInput.files && backupInput.files[0];
    if (!f) return;
    f.text().then(function(text){
      var data = null; try { data = JSON.parse(text); } catch(e){}
      if (!data || data.app !== 'ffmap' || !data.cols){ alert('Det här är ingen säkerhetskopia från FF Map.'); return; }
      if (data.project !== FIREBASE_CONFIG.projectId){
        alert('Kopian är från en annan databas (' + data.project + ') och läggs inte in här.' + (TEST_MODE ? ' Du är i Demo Mode (testdatabasen).' : ''));
        return;
      }
      if (!confirm('Lägga tillbaka kopian från ' + new Date(data.at).toLocaleString('sv-SE').slice(0, 16) + '?\n\n' + backupCounts(data.cols) +
        '.\n\nAllt i kopian får tillbaka sina värden från kopian – även platser som tagits bort sedan dess. Det som tillkommit efter kopian rörs inte.')) return;
      var fsdb = firebase.firestore(), jobs = [], ok = 0, bad = 0;
      BACKUP_COLS.forEach(function(c){
        var docs = data.cols[c] || {};
        Object.keys(docs).forEach(function(id){
          jobs.push(fsdb.collection(c).doc(id).set(bkIn(docs[id])).then(function(){ ok++; }, function(){ bad++; }));
        });
      });
      backupBusy = true; backupStatusEl.textContent = 'Lägger tillbaka ' + jobs.length + ' saker… (utan täckning skickas de när den kommer tillbaka)';
      Promise.all(jobs).then(function(){
        backupBusy = false;
        backupStatusEl.textContent = bad ? ok + ' tillbaka, ' + bad + ' nekades av databasen.' : 'Klart: alla ' + ok + ' är tillbaka.';
      });
    });
  });

