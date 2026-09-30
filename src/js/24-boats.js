  /* ---------------- other users' live positions ("Båtar") ---------------- */
  // Names on the map are cut to 10 characters so the labels stay small (the
  // popup you get by tapping a boat still shows the full names).
  var BOAT_LABEL_MAX = 10;
  function shortBoatName(n){
    var chars = Array.from(n || '');
    if (chars.length <= BOAT_LABEL_MAX) return n;
    return chars.slice(0, BOAT_LABEL_MAX).join('').replace(/\s+$/, '') + '…';
  }

  function renderBoats(){
    var seen = {};
    boatClustersById = {};
    if (showBoats){
      var now = Date.now();
      var fresh = Object.keys(boatPositions).map(function(uid){ return boatPositions[uid]; })
        .filter(function(b){ return now - b.updatedAt <= BOAT_REMOVE_MS; }) // hasn't checked in for a very long time -- treat as gone for good
        .filter(function(b){ return b.uid !== myUid; }) // that's you (the snapshot may predate a new login)
        .filter(function(b){
          // people sitting right next to you are in YOUR boat -- you already
          // see yourself as the big amber dot, so don't also show them as a
          // separate pip with your own boat's names on it. Only show pips
          // for boats far enough away to plausibly be someone else's.
          if (!lastOwnLatLon) return true;
          var distM = haversineKm(lastOwnLatLon.lat, lastOwnLatLon.lon, b.lat, b.lon) * 1000;
          return distM > BOAT_CLUSTER_METERS;
        });
      // Group live positions only with other live ones, and old (grey) ones
      // only with other old ones -- otherwise a boat passing a spot where
      // someone's app went quiet 40 minutes ago would get merged with that
      // leftover position into one "same boat" pip.
      var live = fresh.filter(function(b){ return now - b.updatedAt <= BOAT_GRAY_MS; });
      var old = fresh.filter(function(b){ return now - b.updatedAt > BOAT_GRAY_MS; });
      var clusters = clusterBoatPositions(live).concat(clusterBoatPositions(old));
      clusters.forEach(function(c){
        boatClustersById[c.id] = c;
        seen[c.id] = true;
        var p = latLonToImgPx(c.lat, c.lon);
        var sx = originX + p.x * scale, sy = originY + p.y * scale;
        var el = boatsLayer.querySelector('[data-cluster="' + c.id + '"]');
        if (!el){
          el = document.createElement('div');
          el.setAttribute('data-cluster', c.id);
          el.className = 'boatPip';
          el.innerHTML = '<span class="boatDot"></span><span class="boatName"></span>';
          el.addEventListener('pointerdown', function(e){ e.stopPropagation(); mapPointerDown(e, true); });
          el.addEventListener('click', function(e){
            e.stopPropagation();
            if (mapDraggedJustNow()) return;
            // look up the CURRENT cluster by id at click time, same reasoning
            // as waypoint pins: the object backing this element gets replaced
            // on every snapshot update, so a stale closure would show old data
            var currentId = el.getAttribute('data-cluster');
            var current = boatClustersById[currentId];
            if (!current) return;
            if (measureMode){ addMeasurePoint(current.lat, current.lon); return; }
            showBoatInfo(current);
          });
          boatsLayer.appendChild(el);
        }
        el.classList.toggle('boatPip--group', c.names.length > 1);
        el.classList.toggle('boatPip--stale', (now - c.updatedAt) > BOAT_GRAY_MS);
        var nameEl = el.querySelector('.boatName');
        var namesKey = c.names.join('\n');
        if (nameEl.getAttribute('data-names') !== namesKey){ // only touch the DOM when the names actually changed
          nameEl.setAttribute('data-names', namesKey);
          nameEl.innerHTML = '';
          c.names.forEach(function(n){
            var row = document.createElement('span');
            row.textContent = shortBoatName(n);
            nameEl.appendChild(row);
          });
        }
        el.style.left = sx + 'px';
        el.style.top = sy + 'px';
      });
    }
    Array.from(boatsLayer.children).forEach(function(el){
      if (!seen[el.getAttribute('data-cluster')]) el.remove();
    });
  }

  var toggleBoatsEl = document.getElementById('toggleBoats');
  toggleBoatsEl.checked = showBoats;
  toggleBoatsEl.addEventListener('change', function(){
    showBoats = toggleBoatsEl.checked;
    try { localStorage.setItem('regnaren_vis_boats_v1', showBoats ? '1' : '0'); } catch(e){}
    renderBoats();
  });

  // hide boats whose last check-in has gone stale even without a fresh
  // snapshot event (Firestore only pushes updates on actual data changes)
  setInterval(renderBoats, 30000);

  var boatInfoBackdrop = document.getElementById('boatInfoBackdrop');
  var boatInfoModal = document.getElementById('boatInfoModal');
  var boatInfoNameEl = document.getElementById('boatInfoName');
  var boatInfoNamesListEl = document.getElementById('boatInfoNamesList');
  var boatInfoMetaEl = document.getElementById('boatInfoMeta');
  var boatInfoCloseBtn = document.getElementById('boatInfoClose');
  function showBoatInfo(cluster){
    var names = cluster.names || [cluster.name || 'Okänd'];
    boatInfoNamesListEl.innerHTML = '';
    if (names.length === 1){
      boatInfoNameEl.textContent = names[0];
      boatInfoNamesListEl.style.display = 'none';
    } else {
      boatInfoNameEl.textContent = 'Samma båt';
      names.forEach(function(n){
        var row = document.createElement('div');
        row.className = 'boatInfoNameRow';
        row.textContent = n;
        boatInfoNamesListEl.appendChild(row);
      });
      boatInfoNamesListEl.style.display = 'flex';
    }
    boatInfoMetaEl.textContent = 'Uppdaterad ' + timeAgo(cluster.updatedAt);
    boatInfoBackdrop.classList.add('show');
    boatInfoModal.classList.add('show');
  }
  function hideBoatInfo(){
    boatInfoBackdrop.classList.remove('show');
    boatInfoModal.classList.remove('show');
  }
  boatInfoCloseBtn.addEventListener('click', hideBoatInfo);
  boatInfoBackdrop.addEventListener('click', hideBoatInfo);

  var allPositions = []; // every position doc for this lake, you included (admin page)
  function applyPositionsSnapshot(snap){
    var now = Date.now();
    var fresh = {};
    var raw = [];
    snap.forEach(function(doc){
      var d = doc.data();
      var docLake = d.lake || LAKE_ID;
      if (docLake !== LAKE_ID) return;
      var updatedMs = (d.updatedAt && d.updatedAt.toMillis) ? d.updatedAt.toMillis() : now;
      raw.push({ docId: doc.id, uid: d.uid || doc.id, name: d.name || '', lat: d.lat, lon: d.lon, updatedAt: updatedMs });
      if (d.uid === myUid){               // that's you -- your own big GPS dot already shows it
        if (d.msg && d.msgAt && (!ownMsg || d.msgAt >= ownMsg.at)) ownMsg = { text: d.msg, at: d.msgAt };   // (your quick message, after a reload)
        else if (!d.msg && ownMsg && d.msgAt === 0) ownMsg = null;
        return;
      }
      fresh[doc.id] = { lat: d.lat, lon: d.lon, name: d.name || '', uid: d.uid, updatedAt: updatedMs, msg: d.msg || null, msgAt: d.msgAt || 0 };
    });
    boatPositions = fresh;
    allPositions = raw;
    renderBoats();
    if (msgLayerEl) renderMessages();
    refreshAdminIfOpen();
  }

  // Only share a position that's actually at the lake -- never broadcast
  // where you are when you open the app at home, in the car, etc.
  function isNearLake(lat, lon){
    var p = latLonToImgPx(lat, lon);
    var margin = 150; // web px, ~a few hundred metres of shoreline buffer
    return p.x >= -margin && p.x <= IMG_W + margin && p.y >= -margin && p.y <= IMG_H + margin;
  }

  // How often your position is written, balanced against Firestore's daily
  // free quota (every write is a read for every other phone that's open):
  // every 20 s at most while you're moving (admin setting), but only once a
  // minute while you sit still (boats only turn grey after 15 minutes, so
  // that's plenty to keep your pip alive).
  var lastPosWriteAt = 0;
  var lastWrittenLatLon = null;
  // How often while moving is set on the admin page (10/20/30/60 s, default
  // 20 s) and shared with every phone through Firestore (config/<lake>); the
  // last known value is remembered on the phone for offline starts.
  var POS_INTERVAL_CHOICES = [10, 20, 30, 60];
  var POS_INTERVAL_DEFAULT_S = 20;
  var POS_INTERVAL_KEY = lakeKey('ffmap_pos_interval_s_v1', 'pos_interval_s_v1'); // (per lake, like config/<lake>)
  var posIntervalS = POS_INTERVAL_DEFAULT_S;
  try {
    var savedPi = parseInt(localStorage.getItem(POS_INTERVAL_KEY), 10);
    if (POS_INTERVAL_CHOICES.indexOf(savedPi) !== -1) posIntervalS = savedPi;
  } catch(e){}
  var POS_IDLE_INTERVAL_MS = 60000;
  var POS_MOVE_THRESHOLD_M = 12; // less than this counts as "still" (normal GPS jitter at anchor)
  if (rotState && rotState.pos){ lastPosWriteAt = rotState.pos.at || 0; lastWrittenLatLon = rotState.pos.ll || null; } // no extra write per rotation
  // Firestore doc ids can't contain "/" (and can't be "." / ".." / "__x__"),
  // but "Annat namn" lets people type anything -- so make the position doc
  // id safe. Ordinary names give exactly the same id as before.
  function posDocId(uid){
    var id = String(uid).replace(/\//g, '_');
    if (id === '.' || id === '..' || /^__.*__$/.test(id)) id = 'u_' + id;
    return id;
  }
  function maybeBroadcastPosition(lat, lon){
    if (!USE_FIREBASE || !posCol || !myUid) return;
    if (!isNearLake(lat, lon)) return;
    var now = Date.now();
    var since = now - lastPosWriteAt;
    var movingMs = posIntervalS * 1000;
    if (since < movingMs) return;
    var movedM = lastWrittenLatLon ? haversineKm(lastWrittenLatLon.lat, lastWrittenLatLon.lon, lat, lon) * 1000 : Infinity;
    if (movedM < POS_MOVE_THRESHOLD_M && since < Math.max(POS_IDLE_INTERVAL_MS, movingMs)) return;
    lastPosWriteAt = now;
    lastWrittenLatLon = { lat: lat, lon: lon };
    addUsage('w', 1);
    try {
      posCol.doc(posDocId(myUid)).set({
        lat: lat, lon: lon, name: userName || '', uid: myUid, lake: LAKE_ID,
        updatedAt: firebase.firestore.FieldValue.serverTimestamp()
      }, { merge: true }).catch(function(e){ console.warn('kunde inte dela position', e); });
    } catch(e){ console.warn('kunde inte dela position', e); }
  }

  // Mark your shared position as long gone (e.g. on logout), so it disappears
  // for everyone right away instead of lingering as a ghost pip for an hour.
  // (Setting an ancient timestamp rather than deleting the doc, so the
  // existing Firestore rules don't need changing.)
  function expireOwnPosition(){
    if (!USE_FIREBASE || !posCol || !myUid) return;
    if (!firebase.firestore.Timestamp) return;
    addUsage('w', 1);
    try {
      // update() rather than set(merge): never creates an empty stub doc for
      // a name that never shared a position
      posCol.doc(posDocId(myUid)).update({ updatedAt: firebase.firestore.Timestamp.fromMillis(0) })
        .catch(function(){ /* no doc for this name -- nothing to expire */ });
    } catch(e){}
  }

  // A GPS fix only arrives from watchPosition when the device's location
  // provider decides there's a new one -- on a lot of phones that gets a lot
  // less frequent (or stops entirely) once you've been sitting still for a
  // while, which is exactly what happens at anchor while fishing. So check
  // on a steady tick and re-send the last known position whenever
  // maybeBroadcastPosition decides it's due (moved, or a minute has passed).
  setInterval(function(){
    if (lastOwnLatLon && !awaitingFreshFix) maybeBroadcastPosition(lastOwnLatLon.lat, lastOwnLatLon.lon);
  }, 2000); // (a steady, cheap tick; maybeBroadcastPosition itself decides when a write is due)

  function startLongPress(sx, sy){
    cancelLongPress();
    longPressRing.style.left = sx + 'px';
    longPressRing.style.top = sy + 'px';
    // (only if the finger is still down -- a quick tap may already have ended before this frame)
    requestAnimationFrame(function(){ if (longPressTimer) longPressRing.classList.add('active'); });
    longPressTimer = setTimeout(function(){
      longPressTimer = null;
      placeWaypointAtScreen(sx, sy);
      cancelLongPress();
      if (navigator.vibrate) { try { navigator.vibrate(18); } catch(e){} }
    }, 550);
  }
  function cancelLongPress(){
    if (longPressTimer){ clearTimeout(longPressTimer); longPressTimer = null; }
    longPressRing.classList.remove('active');
  }

  // "Fiskeplats N" numbered from YOUR spots only (not everyone's), and never
  // reusing a number you already have.
  // "<Typ> N" numbered among YOUR spots of that type, never reusing a number
  // you already have (excludeId: the spot being edited doesn't count itself)
  function nextWaypointName(type, excludeId){
    type = WP_TYPES[type] ? type : 'mark';
    var label = WP_TYPES[type].label;
    var same = waypoints.filter(function(w){ return isMine(w) && w.id !== excludeId && wpType(w) === type; });
    var re = new RegExp('^' + label + ' (\\d+)$');
    var maxN = 0;
    same.forEach(function(w){
      var m = re.exec(w.name || '');
      if (m) maxN = Math.max(maxN, parseInt(m[1], 10));
    });
    return label + ' ' + (Math.max(maxN, same.length) + 1);
  }
  // a name the app made up itself (so switching type may replace it)
  function isAutoWpName(v){
    v = (v || '').trim();
    return !v || /^(Markering|Abborre|Gädda|Gös|Fara|Träffpunkt|Fiskeplats) \d+$/.test(v);
  }

  function placeWaypointAtScreen(sx, sy){
    var imgX = (sx - originX) / scale, imgY = (sy - originY) / scale;
    var ll = imgPxToLatLon(imgX, imgY);
    var name = nextWaypointName('mark'); // new spots start as a Markering
    if (USE_FIREBASE){
      // Create the doc id right here on the phone and open the sheet
      // immediately. (fsCol.add()'s promise only resolves once the SERVER
      // confirms -- with weak coverage on the lake that could take ages or
      // never happen, so the sheet wouldn't open and people would press
      // again and create duplicates.) The write itself is queued and synced
      // whenever there's coverage.
      var ref = fsCol.doc();
      addUsage('w', 1);
      ref.set({
        lat: ll.lat, lon: ll.lon, name: name, type: 'mark', uid: myUid, by: userName || '', lake: LAKE_ID,
        createdAt: firebase.firestore.FieldValue.serverTimestamp()
      }).catch(function(err){ console.warn('kunde inte spara fiskeplats', err); });
      openSheetForWp({ id:ref.id, lat:ll.lat, lon:ll.lon, name:name, type:'mark', uid:myUid, by:userName || '', lake:LAKE_ID, createdAt:Date.now() }, true);
    } else {
      var id = 'wp' + Date.now() + Math.random().toString(36).slice(2, 7);
      var wp = { id:id, lat: ll.lat, lon: ll.lon, name: name, type:'mark', uid:'local', by:userName || '', lake:LAKE_ID, createdAt: Date.now() };
      waypoints.push(wp);
      saveLocalWaypoints();
      renderWaypoints();
      openSheetForWp(wp, true);
    }
  }

  // the spot currently open in the sheet, so its distance can be kept up to
  // date as you move (see onFix)
  var editingWpInfo = null;
  function refreshSheetMeta(){
    if (!editingWpInfo) return;
    var w = editingWpInfo;
    wpMetaEl.textContent = 'Sparad av ';
    var who = document.createElement('b'); who.className = 'who'; who.textContent = w.mine ? 'dig' : (w.by || 'en lagkompis');
    wpMetaEl.appendChild(who); wpMetaEl.appendChild(document.createTextNode(' · ' + fmtSheetDate(w.createdAt)));
    renderWpData(w.lat, w.lon);            // (the depth etc. are in the tiles under)
    if (editingType === 'meet') wpMetaEl.appendChild(document.createTextNode(' · Syns för alla i 1 h'));
    if (lastOwnLatLon){
      var m = haversineKm(lastOwnLatLon.lat, lastOwnLatLon.lon, w.lat, w.lon) * 1000;
      if (wpMetaEl.textContent) wpMetaEl.appendChild(document.createTextNode(' · '));
      var distEl = document.createElement('span');
      distEl.className = 'sheetDistance';
      distEl.textContent = m < 10 ? 'Du är här' : fmtMeters(m) + ' bort';
      wpMetaEl.appendChild(distEl);
    }
    if (!w.mine && !w.admin){                              // someone else's: its type as a small pill
      var tp = document.createElement('span'), t = editingType;
      tp.className = 'miniType' + (t === 'fara' || t === 'hem' ? ' light' : '');
      tp.style.background = 'var(--t-' + t + ')'; tp.textContent = WP_TYPES[t].label;
      wpMetaEl.appendChild(tp);
    }
    if (w.admin){ var ad = document.createElement('span'); ad.className = 'adminTag'; ad.textContent = 'ADMIN'; wpMetaEl.appendChild(ad); }
  }

  var wpTypeSeg = document.getElementById('wpTypeSeg');
  var editingType = 'mark';
  function showEditingType(){
    Array.from(wpTypeSeg.children).forEach(function(b){
      var on = b.getAttribute('data-type') === editingType;
      b.classList.toggle('active', on);
      b.setAttribute('aria-checked', on ? 'true' : 'false');
    });
  }
  wpTypeSeg.addEventListener('click', function(e){
    var b = e.target.closest ? e.target.closest('button[data-type]') : null;
    if (!b || b.disabled || !editingId) return;
    editingType = b.getAttribute('data-type');
    showEditingType();
    refreshSheetMeta(); // ("Syns för alla i 1 h" for a Träffpunkt)
    // switch the made-up name along with the type ("Markering 5" -> "Gös 3"),
    // but never overwrite a name you typed yourself
    if (isAutoWpName(wpNameInput.value)) wpNameInput.value = nextWaypointName(editingType, editingId);
  });

  function openSheetForWp(wp, isNew){
    if (wpSheet._resetSize && !wpSheet.classList.contains('show')) wpSheet._resetSize();
    editingId = wp.id;
    editingIsNew = !!isNew;
    editingType = wpType(wp);
    var mine = isMine(wp);
    var canEdit = mine || adminCanEditAll();
    wpNameInput.value = wp.name;
    wpNameInput.disabled = !canEdit;
    wpDeleteBtn.hidden = !canEdit;
    wpSaveBtn.hidden = !canEdit;
    Array.from(wpTypeSeg.children).forEach(function(b){ b.disabled = !canEdit; });
    wpTypeSeg.hidden = !canEdit;                      // (someone else's: the type is a small pill on the "Sparad av" line)
    showEditingType();
    // "Åk hit" / "Liknande": for a spot that's already there (not one you're just adding)
    document.getElementById('wpGo').hidden = !!isNew;
    document.getElementById('wpLike').hidden = !!isNew || wpType(wp) === 'meet' || wpType(wp) === 'fara' || wpType(wp) === 'hem';
    if (!pinEls[wp.id]) renderWaypoints(); // draw it even if a filter (Mina / Andras / type) hides it
    editingWpInfo = { lat: wp.lat, lon: wp.lon, mine: mine, by: wp.by, createdAt: wp.createdAt, admin: !mine && canEdit };
    refreshSheetMeta();
    sheetBackdrop.classList.add('show');
    wpSheet.classList.add('show');
    if (mine) setTimeout(function(){ wpNameInput.focus(); if (isNew) wpNameInput.select(); }, 260);
    // (an admin editing someone else's spot doesn't get the keyboard popping up)
  }
  function closeSheet(){
    sheetBackdrop.classList.remove('show');
    wpSheet.classList.remove('show');
    wpNameInput.blur();
    editingId = null;
    editingIsNew = false;
    editingWpInfo = null;
    renderWaypoints(); // a spot that only showed because it was being edited is hidden again
  }
  function deleteWaypointById(id){
    if (USE_FIREBASE){ addUsage('d', 1); fsCol.doc(id).delete().catch(function(e){ console.warn(e); }); }
    else {
      waypoints = waypoints.filter(function(w){ return w.id !== id; });
      saveLocalWaypoints();
      renderWaypoints();
    }
  }
  // the one authored moment: a new spot "lands" -- the pin drops onto the map and a thin ring in its
  // colour spreads from the tip, exactly where the spot is (like the lead weight hitting the water)
  function landPin(id){
    var el = pinEls[id], wp = waypoints.filter(function(w){ return w.id === id; })[0];
    if (!el || !wp || !el.animate) return;
    var calm = window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches;
    el.animate(calm ? [{ opacity: 0 }, { opacity: 1 }] : [{ translate: '0 -30px', opacity: 0 }, { opacity: 1, offset: 0.45 }, { translate: '0 0', opacity: 1 }],
      { duration: calm ? 200 : 440, easing: 'cubic-bezier(.16,1,.3,1)' });
    if (calm) return;
    var p = latLonToImgPx(wp.lat, wp.lon), s = document.createElement('span'), col = getComputedStyle(el).backgroundColor;
    s.className = 'pinSplash';
    s.style.left = (originX + p.x * scale) + 'px'; s.style.top = (originY + p.y * scale) + 'px';
    s.style.borderColor = /rgba\(0, 0, 0, 0\)|transparent/.test(col) ? '#fff' : col;
    waypointsLayer.appendChild(s);
    s.animate([{ transform: 'scale(.2)', opacity: 1 }, { opacity: 0.9, offset: 0.45 }, { transform: 'scale(1)', opacity: 0 }],
      { duration: 650, delay: 260, easing: 'cubic-bezier(.16,1,.3,1)', fill: 'both' }).onfinish = function(){ s.remove(); };
  }
  wpSaveBtn.addEventListener('click', function(){
    if (!editingId) { closeSheet(); return; }
    if (editingIsNew){ var landId = editingId; setTimeout(function(){ landPin(landId); }, 0); }
    var v = wpNameInput.value.trim();
    var upd = { type: editingType };
    if (hiddenTypes[editingType]) setTypeHidden(editingType, false); // don't let the spot you just saved vanish
    var cur = waypoints.filter(function(w){ return w.id === editingId; })[0];
    if (cur && wpType(cur) === editingType && (!v || v === cur.name)){ closeSheet(); return; } // nothing changed
    if (v) upd.name = v;           // an emptied name keeps the old one
    // Träffpunkt: an hour from now (a new one, or a spot turned into one); only
    // one per person -- your previous one goes. Turned into something else: stays.
    var wasMeet = cur && wpType(cur) === 'meet';
    if (editingType === 'meet' && !wasMeet){
      upd.expiresAt = Date.now() + MEET_MS;
      var id0 = editingId;
      waypoints.filter(function(w){ return isMine(w) && wpType(w) === 'meet' && w.id !== id0; })
        .forEach(function(w){ deleteWaypointById(w.id); });
    }
    if (editingType !== 'meet' && wasMeet) upd.expiresAt = null;
    if (USE_FIREBASE){ addUsage('w', 1); fsCol.doc(editingId).update(upd).catch(function(e){ console.warn(e); }); }
    else {
      var wp = waypoints.filter(function(w){ return w.id === editingId; })[0];
      if (wp){ wp.type = editingType; if (v) wp.name = v; if ('expiresAt' in upd) wp.expiresAt = upd.expiresAt; saveLocalWaypoints(); renderWaypoints(); }
    }
    closeSheet();
  });
  function cancelSheet(){
    // if the sheet was opened for a waypoint that was just created (long-press),
    // cancelling should undo that creation, not leave an unnamed pin behind.
    if (editingIsNew && editingId) deleteWaypointById(editingId);
    closeSheet();
  }
  wpCancelBtn.addEventListener('click', cancelSheet);
  // Ta bort: the spot disappears at once, but is only really deleted (for everyone) after 6 s -- "Ångra"
  // brings it back. Leaving the app (or turning the phone: a reload) in between deletes it then.
  var undoToast = document.getElementById('undoToast'), undoT = null, undoPending = null;
  function flushDelete(){ if (!undoPending) return; var id = undoPending.id; undoPending = null; clearTimeout(undoT); undoToast.classList.remove('show'); deleteWaypointById(id); }
  wpDeleteBtn.addEventListener('click', function(){
    if (!editingId) return;
    flushDelete();                                           // (an earlier one still waiting: delete it now)
    var wp = waypoints.filter(function(w){ return w.id === editingId; })[0];
    undoPending = { id: editingId };
    closeSheet(); renderWaypoints();
    document.getElementById('undoTxt').innerHTML = '<b>' + escHtml((wp && wp.name) || 'Platsen') + '</b> borttagen';
    var ring = undoToast.querySelectorAll('circle')[1]; ring.classList.remove('run'); void ring.getBoundingClientRect(); ring.classList.add('run');
    undoToast.classList.add('show');
    undoT = setTimeout(flushDelete, 6000);
  });
  document.getElementById('undoBtn').addEventListener('click', function(){
    undoPending = null; clearTimeout(undoT); undoToast.classList.remove('show'); renderWaypoints(); if (typeof renderLogList === 'function' && logView.classList.contains('show')) renderLogList();
  });
  undoToast.addEventListener('pointerdown', function(e){ e.stopPropagation(); });
  window.addEventListener('pagehide', flushDelete);
  function isUndoPending(id){ return !!(undoPending && undoPending.id === id); }
  sheetBackdrop.addEventListener('click', cancelSheet);

