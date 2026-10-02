  /* ---------------- init ---------------- */
  var appStarted = false; // true once geolocation + Firebase have been started for this page load
  function continueBootAfterName(){
    appStarted = true;
    if (demoMode){
      if (demoLat == null || demoLon == null) setDemoCoords(randomDemoPoint());
      else updateDemoCoordsInputs();
      demoCoordsRow.style.display = 'flex';
      document.getElementById('demoMoveRow').style.display = 'flex';
      onFix(demoLat, demoLon, 8);
      if (demoMovePref()){
        startDemoMotion();
        document.getElementById('demoMoveToggle').checked = !!demoSim;
      }
    }
    startGeolocation();
    initSharedWaypoints(function(ok){
      if (!ok && USE_FIREBASE) return; // a late sign-in error after the shared mode already started -- ignore
      localOnlyMode = !ok;
      updateNetBadge();
      if (!ok){ loadLocalWaypoints(); renderWaypoints(); }
      else { uploadLocalOnlySpots(); fetchMyTracks(); flushTrackUploads(false); fetchOthersTracks(); }
    });
  }
  // Spots saved only on this phone because the shared database wasn't
  // available (no coverage when the app started, or a long-press in the very
  // first second) -- upload them now that it is, instead of leaving them
  // hidden on the phone for ever. (Only recent ones.)
  function uploadLocalOnlySpots(){
    if (!USE_FIREBASE || !fsCol || !myUid) return;
    var list;
    try { list = JSON.parse(localStorage.getItem(WP_KEY) || '[]'); } catch(e){ return; }
    if (!Array.isArray(list) || !list.length) return;
    var now = Date.now(), keep = [], n = 0;
    list.forEach(function(w){
      var pending = w && w.uid === 'local' && (!w.lake || w.lake === LAKE_ID) &&
        now - (w.createdAt || 0) < 7 * 24 * 3600 * 1000 && isFinite(w.lat) && isFinite(w.lon) && w.id;
      if (!pending){ keep.push(w); return; }
      n++;
      addUsage('w', 1);
      try {
        fsCol.doc(String(w.id)).set({
          lat: w.lat, lon: w.lon, name: w.name || WP_TYPES[wpType(w)].label, type: wpType(w),
          uid: myUid, by: userName || '', lake: LAKE_ID,
          createdAt: firebase.firestore.FieldValue.serverTimestamp()
        }).catch(function(err){ console.warn('kunde inte ladda upp fiskeplats', err); });
      } catch(e){ keep.push(w); }
    });
    if (n){ try { localStorage.setItem(WP_KEY, JSON.stringify(keep)); } catch(e){} }
  }

