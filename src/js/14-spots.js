  /* ---------------- waypoints (fish pins) ----------------------------
     Two modes:
     - Shared (Firebase Firestore + silent anonymous sign-in): everyone
       who opens the page sees the same pins live, in real time, with no
       login screen ever shown. Fill in FIREBASE_CONFIG below to turn
       this on.
     - Local fallback (localStorage): if Firebase isn't configured, pins
       are saved only on this device, exactly as before. --------------- */
  var WP_KEY = 'lake_' + LAKE_ID + '_waypoints_v1';
  var WP_KEY_LEGACY = 'regnaren_waypoints_v1'; // pre-multi-lake key, migrated once below
  var waypointsLayer = document.getElementById('waypoints');
  var longPressRing = document.getElementById('longPressRing');
  var sheetBackdrop = document.getElementById('sheetBackdrop');
  var wpSheet = document.getElementById('wpSheet');
  var wpNameInput = document.getElementById('wpName');
  var wpMetaEl = document.getElementById('wpMeta');
  var wpSaveBtn = document.getElementById('wpSave');
  var wpCancelBtn = document.getElementById('wpCancel');
  var wpDeleteBtn = document.getElementById('wpDelete');

  var waypoints = [];
  var editingId = null;
  var editingIsNew = false;
  var longPressTimer = null;
  var USE_FIREBASE = false;
  var myUid = null;
  var fsCol = null;
  var catchDb = null;       // (Firestore, for the heat map's catches -- set in 26-sync.js)
  var PIN_SIZE = 30;
  var PIN_TIP_OFFSET = PIN_SIZE * Math.SQRT1_2; // distance from box-center to the rotated pin's tip

  var showMine = true, showOthers = true;
  try {
    var vm = localStorage.getItem('regnaren_vis_mine_v1');
    var vo = localStorage.getItem('regnaren_vis_others_v1');
    if (vm !== null) showMine = vm === '1';
    if (vo !== null) showOthers = vo === '1';
  } catch(e){}

  var showBoats = true;          // (the boats' names are always shown -- no "Namn" switch)
  try {
    var sb = localStorage.getItem('regnaren_vis_boats_v1');
    if (sb !== null) showBoats = sb === '1';
  } catch(e){}
  var boatsLayer = document.getElementById('boatsLayer');
  var boatPositions = {}; // uid -> {lat, lon, name, uid, updatedAt}
  var boatClustersById = {}; // last-rendered clusters, keyed for click lookups (see renderBoats)
  var posCol = null; // Firestore 'positions' collection ref (see initSharedWaypoints)
  var usageCol = null; // Firestore 'usage' collection: each device's daily read/write counts (admin page)
  var BOAT_GRAY_MS = 15 * 60 * 1000; // a boat that hasn't updated in this long turns grey -- still shown at its last known spot, just marked as not live anymore
  var BOAT_REMOVE_MS = 60 * 60 * 1000; // a boat that hasn't updated in THIS long is finally removed entirely
  var BOAT_CLUSTER_METERS = 30; // positions this close are treated as "the same boat"

  // People sitting in the same boat show up as one pip instead of a pile of
  // overlapping dots. Simple greedy clustering: each not-yet-placed person
  // founds a cluster and pulls in anyone else still within the margin --
  // fine for a handful of boats at a small lake, no need for anything fancier.
  function clusterBoatPositions(list){
    var used = {};
    var clusters = [];
    list.forEach(function(b, i){
      if (used[b.uid]) return;
      used[b.uid] = true;
      var members = [b];
      list.forEach(function(other, j){
        if (i === j || used[other.uid]) return;
        var distM = haversineKm(b.lat, b.lon, other.lat, other.lon) * 1000;
        if (distM <= BOAT_CLUSTER_METERS){
          used[other.uid] = true;
          members.push(other);
        }
      });
      var latSum = 0, lonSum = 0, maxUpdated = 0;
      members.forEach(function(m){
        latSum += m.lat; lonSum += m.lon;
        if (m.updatedAt > maxUpdated) maxUpdated = m.updatedAt;
      });
      clusters.push({
        id: members.map(function(m){ return m.uid; }).sort().join('+'),
        lat: latSum / members.length,
        lon: lonSum / members.length,
        names: members.map(function(m){ return m.name || 'Okänd'; }),
        updatedAt: maxUpdated
      });
    });
    return clusters;
  }

  // Fill these in from your Firebase project's config (Project settings ->
  // General -> "Your apps" -> SDK setup and configuration). Safe to leave
  // public in this file: Firebase apps are secured by the Firestore rules
  // set in the console, not by hiding this config.
  var FIREBASE_CONFIG = {
    apiKey: "AIzaSyDkpWsfQFxpkkNOmDJmJr7jGyBO3S7GZH4",
    authDomain: "regnaren-b8b6a.firebaseapp.com",
    projectId: "regnaren-b8b6a",
    storageBucket: "regnaren-b8b6a.firebasestorage.app",
    messagingSenderId: "565375427934",
    appId: "1:565375427934:web:d958caf9f2ac3d3e965bcf"
  };

  var FISH_SVG = '<svg viewBox="0 0 384 384" fill="currentColor"><path d="M 200.40625 82.164062 L 191.828125 82.164062 L 178.441406 84.570312 L 167.804688 88.34375 L 157.164062 94.175781 L 151.328125 98.640625 L 143.429688 106.539062 L 139.65625 111.335938 L 135.195312 118.207031 L 130.734375 127.46875 L 130.050781 130.558594 L 142.402344 129.53125 L 157.507812 129.53125 L 173.976562 130.90625 L 188.390625 133.648438 L 188.738281 119.234375 L 190.800781 107.566406 L 194.574219 95.550781 Z M 200.40625 82.164062 "/><path d="M 96.75 142.574219 L 101.210938 149.78125 L 107.390625 162.824219 L 111.855469 178.265625 L 113.917969 192.691406 L 113.917969 209.503906 L 111.511719 225.292969 L 109.792969 231.816406 L 106.019531 242.453125 L 101.210938 252.066406 L 96.75 258.585938 L 117 263.046875 L 139.65625 265.453125 L 167.113281 265.109375 L 177.757812 264.082031 L 194.226562 261.328125 L 216.539062 255.496094 L 238.507812 247.261719 L 261.503906 235.933594 L 293.085938 217.402344 L 313.671875 233.191406 L 334.957031 247.605469 L 349.371094 256.183594 L 359.324219 261.328125 L 361.386719 262.019531 L 363.441406 261.675781 L 363.441406 260.300781 L 339.421875 203.324219 L 339.074219 201.609375 L 348.683594 183.421875 L 356.578125 166.941406 L 367.558594 140.859375 L 367.558594 139.140625 L 363.789062 139.828125 L 358.980469 142.230469 L 338.046875 154.925781 L 313.335938 172.09375 L 295.140625 186.164062 L 263.21875 167.289062 L 239.199219 155.273438 L 218.601562 147.039062 L 203.152344 142.230469 L 191.828125 139.484375 L 178.441406 137.085938 L 166.769531 135.710938 L 145.492188 135.023438 L 132.796875 135.710938 L 121.125 137.085938 L 108.082031 139.484375 Z M 96.75 142.574219 "/><path d="M 87.832031 145.320312 L 77.871094 149.4375 L 65.863281 155.273438 L 53.851562 162.140625 L 45.609375 167.632812 L 33.253906 177.238281 L 22.613281 187.539062 L 16.441406 195.089844 L 15.75 198.179688 L 17.8125 202.980469 L 20.558594 207.441406 L 28.449219 217.738281 L 37.027344 226.664062 L 45.609375 233.871094 L 54.878906 240.398438 L 64.828125 246.234375 L 82.335938 254.121094 L 88.171875 256.183594 L 90.234375 256.183594 L 93.667969 252.75 L 97.09375 246.914062 L 101.558594 236.960938 L 104.300781 228.382812 L 107.390625 211.90625 L 107.738281 194.746094 L 105.328125 177.929688 L 103.621094 171.40625 L 99.839844 161.109375 L 95.378906 152.183594 L 91.605469 146.347656 L 89.886719 145.320312 Z M 87.832031 145.320312 "/><path d="M 186.683594 301.492188 L 180.15625 287.414062 L 173.640625 269.574219 L 161.96875 270.601562 L 135.539062 270.253906 L 137.59375 274.371094 L 143.429688 281.925781 L 150.984375 289.132812 L 158.878906 294.628906 L 166.769531 298.402344 L 175.011719 300.800781 L 182.21875 301.835938 Z M 186.683594 301.492188 "/></svg>';

  /* Kinds of spot. Spots saved before types existed have no type -> Markering. */
  var WP_TYPES = {
    mark:    { label: 'Markering' },
    abborre: { label: 'Abborre' },
    gadda:   { label: 'Gädda' },
    gos:     { label: 'Gös' },
    fara:    { label: 'Fara' },          // a shoal, a rock ... something to steer clear of
    meet:    { label: 'Träffpunkt' },    // a beacon for everyone (lunch on an island ...), gone after an hour
    hem:     { label: 'Hem' }            // home / the jetty
  };
  var MEET_MS = 60 * 60 * 1000;
  function isExpired(wp){ return wpType(wp) === 'meet' && wp.expiresAt && Date.now() > wp.expiresAt; }
  function wpType(wp){ return (wp && WP_TYPES[wp.type]) ? wp.type : 'mark'; }
  // Filter (fold-out under the toggles): hidden spot types, and others' opacity.
  var TYPE_FILTER_KEY = 'ffmap_type_filter_v1';  // JSON list of HIDDEN types -- default: all shown
  var OTHERS_OP_KEY = 'ffmap_others_opacity_v1'; // '1' (default) or '0.5'
  var hiddenTypes = {};
  try { (JSON.parse(localStorage.getItem(TYPE_FILTER_KEY)) || []).forEach(function(t){ if (WP_TYPES[t]) hiddenTypes[t] = true; }); } catch(e){}
  var othersOpacity = 1;
  try { if (localStorage.getItem(OTHERS_OP_KEY) === '0.5') othersOpacity = 0.5; } catch(e){}
  var MARK_SVG = '<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="6" fill="currentColor"></circle></svg>'; // plain position dot
  var FARA_SVG = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round"><path d="M7.5 7.5l9 9M16.5 7.5l-9 9"></path></svg>'; // an X (lists, type picker)
  // on the map: a red stop sign (octagon) with a white edge and a white X
  var FARA_SIGN = '<svg viewBox="0 0 24 24"><path d="M8 1.6h8l6.4 6.4v8L16 22.4H8L1.6 16V8z" fill="#E5322D" stroke="#fff" stroke-width="2.2" stroke-linejoin="round"></path>' +
    '<path d="M8.2 8.2l7.6 7.6M15.8 8.2l-7.6 7.6" stroke="#fff" stroke-width="3" stroke-linecap="round"></path></svg>';
  var MEET_SVG = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linejoin="round" stroke-linecap="round"><path d="M6 21V4"></path><path d="M6 4h11l-2.5 4L17 12H6"></path></svg>'; // flag
  var HOME_SVG = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linejoin="round" stroke-linecap="round"><path d="M4 11.5 12 5l8 6.5"></path><path d="M6.5 10v8.5h11V10"></path><path d="M10.5 18.5v-4.5h3v4.5"></path></svg>'; // a house
  function wpIconSvg(type){ return type === 'mark' ? MARK_SVG : type === 'fara' ? FARA_SVG : type === 'meet' ? MEET_SVG : type === 'hem' ? HOME_SVG : FISH_SVG; }

  function loadLocalWaypoints(){
    try {
      var raw = localStorage.getItem(WP_KEY);
      if (raw === null && LAKE_ID === 'regnaren'){
        // one-time migration from the old, pre-multi-lake key name
        var legacy = localStorage.getItem(WP_KEY_LEGACY);
        if (legacy !== null){
          localStorage.setItem(WP_KEY, legacy);
          raw = legacy;
        }
      }
      waypoints = raw ? JSON.parse(raw) : [];
    } catch(e){ waypoints = []; }
  }
  function saveLocalWaypoints(){
    try { localStorage.setItem(WP_KEY, JSON.stringify(waypoints)); } catch(e){}
  }
  function isMine(wp){ return wp.uid === 'local' || wp.uid === myUid; }
  function timeAgo(ms){
    var s = Math.max(1, Math.round((Date.now() - ms) / 1000));
    if (s < 60) return 'nyss';
    var m = Math.round(s / 60); if (m < 60) return m + ' min sedan';
    var h = Math.round(m / 60); if (h < 24) return h + ' h sedan';
    return Math.round(h / 24) + ' d sedan';
  }
  function fmtMeters(m){
    if (m < 1000) return (m < 100 ? Math.round(m) : Math.round(m / 10) * 10) + ' m';
    return (m / 1000).toFixed(1).replace('.', ',') + ' km';
  }

  var pinEls = {}; // waypoint id -> its element (no DOM lookups per pin on every frame)
  var OTHER_PIN_SCALE = 0.7; // others' spots, relative to yours (must match .wpPin--other in the CSS)
  function renderWaypoints(){
    var seen = {};
    if (pendingSheetRestore) tryRestoreSheet();
    waypoints.forEach(function(wp){
      var mine = isMine(wp);
      var editing = wp.id === editingId; // the spot you're editing always shows, whatever the filters say
      if (isExpired(wp) && !editing) return;   // a Träffpunkt whose hour is up
      if (isUndoPending(wp.id)) return;        // (just taken away -- "Ångra" can still bring it back)
      if (!editing && wpType(wp) !== 'fara'){   // a Fara always shows, whatever the filters say
        if (mine && !showMine) return;
        if (!mine && !showOthers) return;
        if (hiddenTypes[wpType(wp)]) return;
      }
      seen[wp.id] = true;
      var p = latLonToImgPx(wp.lat, wp.lon);
      var sx = originX + p.x * scale, sy = originY + p.y * scale;
      var el = pinEls[wp.id];
      if (!el){
        el = document.createElement('div');
        el.setAttribute('data-id', wp.id);
        el.addEventListener('pointerdown', function(e){ e.stopPropagation(); mapPointerDown(e, true); });
        el.addEventListener('click', function(e){
          e.stopPropagation();
          if (mapDraggedJustNow()) return;       // (the finger panned the map -- not a tap on the spot)
          // look up the CURRENT waypoint by id at click time rather than closing over
          // the object from render time -- that object gets replaced on every re-render
          // (a Firestore sync, a refresh, a reload), so a stale closure would keep
          // reopening the sheet with whatever name/data the pin had when first drawn.
          var currentId = el.getAttribute('data-id');
          var current = waypoints.filter(function(w){ return w.id === currentId; })[0];
          if (!current) return;
          if (measureMode){ addMeasurePoint(current.lat, current.lon); return; } // snap a point onto the spot
          openSheetForWp(current, false);
        });
        waypointsLayer.appendChild(el);
        pinEls[wp.id] = el;
      }
      var type = wpType(wp);
      if (el.getAttribute('data-type') !== type){ // (re)draw the icon only when the type changes
        el.setAttribute('data-type', type);
        el.innerHTML = type === 'meet'
          ? '<span class="bcRing"></span><span class="bcRing"></span><span class="bcRing"></span><div class="bcCore">' + MEET_SVG + '</div><div class="bcTag"></div>'
          : type === 'fara' ? FARA_SIGN
          : '<div class="pinHead">' + wpIconSvg(type) + '</div>';
      }
      if (type === 'fara'){
        // the same stop sign for everyone's, centred on the spot
        if (el.className !== 'wpFara') el.className = 'wpFara';
        el.style.left = sx + 'px';
        el.style.top = sy + 'px';
        return;
      }
      if (type === 'meet'){
        // a beacon, centred on the spot, the same for everyone: "Lunch · Calle · 42 min kvar"
        if (el.className !== 'wpBeacon') el.className = 'wpBeacon';
        var left = wp.expiresAt ? Math.max(1, Math.ceil((wp.expiresAt - Date.now()) / 60000)) : 60;
        var tag = (wp.name || 'Träffpunkt') + ' · ' + (mine ? 'du' : (wp.by || 'lagkompis')) + ' · ' + left + ' min kvar';
        var tagEl = el.querySelector('.bcTag');
        if (tagEl.textContent !== tag) tagEl.textContent = tag;
        el.style.left = sx + 'px';
        el.style.top = sy + 'px';
        return;
      }
      var cls = 'wpPin wpPin--' + type + (mine ? '' : ' wpPin--other');
      if (el.className !== cls) el.className = cls;
      el.style.left = sx + 'px';
      el.style.top = (sy - PIN_TIP_OFFSET * wpScale * (mine ? 1 : OTHER_PIN_SCALE)) + 'px'; // the tip on the spot (others' are smaller)
    });
    Object.keys(pinEls).forEach(function(id){
      if (!seen[id]){ pinEls[id].remove(); delete pinEls[id]; }
    });
    if (typeof logView !== 'undefined' && logView.classList.contains('show')) renderLogList();
  }
  // Träffpunkt: when the hour is up it disappears for everyone (hidden right
  // away); your own is then also removed from the database. The minutes left
  // on the beacons are refreshed every half minute.
  var removedExpired = {};
  function pruneExpiredMeets(){
    waypoints.forEach(function(wp){
      if (isExpired(wp) && isMine(wp) && !removedExpired[wp.id] && wp.id !== editingId){
        removedExpired[wp.id] = true;
        deleteWaypointById(wp.id);
      }
    });
  }
  setInterval(function(){ pruneExpiredMeets(); renderWaypoints(); }, 30000);

