  /* ---------- pan / zoom viewer -------------------------------------- */
  var appEl = document.getElementById('app');
  var stage = document.getElementById('stage');
  var world = document.getElementById('world');
  var img = document.getElementById('mapImg');

  var stageW = 0, stageH = 0, fitScale = 1, minScale = 1, maxScale = 1;
  var scale = 1, originX = 0, originY = 0;

  function setImgNativeSize(){
    img.style.maxWidth = 'none';
    img.style.width = IMG_W + 'px';
    img.style.height = IMG_H + 'px';
  }

  function computeBounds(){
    stageW = stage.clientWidth;
    stageH = stage.clientHeight;
    // "cover" fit: fills the screen edge-to-edge with no letterboxing on load
    // (the lake image is a long panoramic strip, so on a portrait phone the
    // natural browsing gesture is panning sideways along the shore).
    fitScale = Math.max(stageW / IMG_W, stageH / IMG_H);
    // zooming out further than fitScale reveals the whole lake at once
    minScale = Math.min(stageW / IMG_W, stageH / IMG_H) * 0.92;
    // the same max zoom on every lake (18,6 -- like web maps / Genesis); each lake uses
    // its highest level from there and enlarges it
    maxScale = Math.pow(2, MAX_ZOOM - ZOOM) / S;
  }

  function clampOrigin(){
    // Panning is intentionally unbounded -- you can pan as far past the
    // edge of the map as you like, exactly like you could on a bigger map.
    // Only the zoom level itself is clamped (minScale/maxScale, enforced in
    // zoomAtPoint and the wheel/pinch handlers below), so this is a no-op
    // kept only so every call site below (zoom, GPS re-centering, view
    // restore after a rotation reload, ...) doesn't need to change.
  }

  /* ---- depth probe ("lodlina") ----
     One tap on the map (not a double tap, not a long press, not in the
     measuring tool) drops a small lead line there showing the depth and how
     far it is from you. The next tap removes it; tap again for a new one. */
  var probe = null;         // {x, y} in map-image pixels
  var probeTimer = null;
  var probeEl = document.getElementById('probe');
  function cancelProbeTap(){ if (probeTimer){ clearTimeout(probeTimer); probeTimer = null; } }
  function scheduleProbeTap(sx, sy, hadMenu){
    cancelProbeTap();
    // wait a moment: a second tap right after means double tap = zoom
    probeTimer = setTimeout(function(){
      probeTimer = null;
      if (hadMenu || measureMode) return;
      if (typeof wpSheet !== 'undefined' && wpSheet.classList.contains('show')) return;
      if (probe){ setProbe(null); return; }        // tap again = remove
      setProbe({ x: (sx - originX) / scale, y: (sy - originY) / scale });
    }, 360);
  }
  function setProbe(pr){
    probe = pr;
    probeEl.classList.toggle('show', !!pr);
    if (!pr){ probeRoute = null; renderRoute(); }
    if (pr){
      probeEl.classList.remove('drop'); void probeEl.offsetWidth; probeEl.classList.add('drop');
      updateProbeText();
      renderProbe();
    }
  }
  // lead line: depth | distance by water | time there at your speed (+ the route drawn)
  var probeRoute = null;    // {pts, meters} or null
  function fmtEtaShort(sec){
    var min = Math.round(sec / 60);
    if (min < 1) return '<1 min';
    if (min < 60) return min + ' min';
    return Math.floor(min / 60) + ' h ' + (min % 60 < 10 ? '0' : '') + (min % 60) + ' min';
  }
  var probeCrow = false;
  function updateProbeText(){
    probeRoute = null; probeCrow = false;
    if (!probe){ renderRoute(); return; }
    var dm = depthAtImgPx(probe.x, probe.y), dEl = document.getElementById('probeDepth');
    var lake = isLakeAtImgPx(probe.x, probe.y);
    dEl.classList.toggle('unk', dm == null && lake);
    dEl.innerHTML = dm != null ? fmtDepth(dm) + ' <small>m</small>' : (lake ? 'Okänt djup' : 'Land');
    var ll = imgPxToLatLon(probe.x, probe.y);
    var have = !!(lastOwnLatLon && lastFix && lastFix.onMap);
    probeEl.classList.toggle('noDist', !have);
    var timeOk = false;
    if (have){
      var m = haversineKm(lastOwnLatLon.lat, lastOwnLatLon.lon, ll.lat, ll.lon) * 1000;
      if (m >= 10){
        var r = routeFrom(lastFix.px, lastFix.py, probe.x, probe.y);   // by water, not as the crow flies
        if (r){ probeRoute = r; m = r.meters; }
        // your speed right now when you're moving, otherwise your average / cruising speed (as the measuring tool)
        var kn = currentSpeedKn(); if (!(kn >= 1.5)) kn = effectiveSpeed().kn;
        if (r && kn > 0){ document.getElementById('probeTime').textContent = fmtEtaShort(m / (kn * 1852 / 3600)); timeOk = true; }
        if (!r && lake) probeCrow = true;                 // no way by water: a straight dotted line, "fågelvägen"
      }
      document.getElementById('probeDistTxt').textContent = m < 10 ? 'här' : fmtMeters(m) + (probeCrow ? ' fågelvägen' : '');
    }
    probeEl.classList.toggle('noTime', !timeOk);
    renderRoute();
  }
  function renderRoute(){
    var svg = document.getElementById('routeLayer');
    var line = (probe && probeRoute) ? probeRoute.pts : (probe && probeCrow && lastFix) ? [{ x: lastFix.px, y: lastFix.py }, probe] : null;
    svg.classList.toggle('crow', !!(probe && !probeRoute && probeCrow));
    var pts = line ? line.map(function(p){ return (originX + p.x * scale).toFixed(1) + ',' + (originY + p.y * scale).toFixed(1); }).join(' ') : '';
    svg.querySelector('.rtUnder').setAttribute('points', pts);
    svg.querySelector('.rtLine').setAttribute('points', pts);
  }
  function renderProbe(){
    renderRoute();
    if (!probe) return;
    probeEl.style.transform = 'translate(' + (originX + probe.x * scale).toFixed(1) + 'px,' + (originY + probe.y * scale).toFixed(1) + 'px)';
  }

  /* ---- zoom levels ("lager") ----
     Like Genesis: every zoom level has its own picture, with Genesis' depth
     lines and numbers for exactly that zoom -- more lines the closer you get.
     The map picture itself is the lowest level (zoom 14); higher levels
     (lake.json "detail".levels: which exist, for which styles, which 512 px
     pieces have water) are laid on top in pieces, only those on screen
     (fetched then, kept by the service worker afterwards). The level follows
     the zoom (rounded); past the highest level its pieces are just enlarged.
     While a new level's pieces load, the previous ones stay underneath, and
     without coverage the ordinary picture simply stays. */
  var DETAIL = LAKE.detail || null;
  var detailLayer = document.getElementById('detailLayer');
  var detailEls = {};   // 'z/style/c_r' -> img
  function currentZoom(){ return ZOOM + Math.log(scale * S) / Math.LN2; }
  function detailLevel(){           // the level shown now (null = the map picture itself)
    if (!DETAIL || !DETAIL.levels) return null;
    var want = Math.round(currentZoom()), best = null;
    DETAIL.levels.forEach(function(L){
      if (L.z <= want && L.styles.indexOf(mapStyle) !== -1 && (!best || L.z > best.z)) best = L;
    });
    return best;
  }
  function detailWanted(){ return !!detailLevel(); }
  function placeTile(el, z, c, r){
    var size = DETAIL.tile * Math.pow(2, ZOOM - z) * S * scale;   // a piece on screen (css px)
    // whole pixels + 1 px overlap: no hairline gaps between the pieces
    var x = Math.floor(originX + c * size), y = Math.floor(originY + r * size);
    el.style.width = (Math.ceil(originX + (c + 1) * size) - x + 1) + 'px';
    el.style.height = (Math.ceil(originY + (r + 1) * size) - y + 1) + 'px';
    el.style.transform = 'translate(' + x + 'px,' + y + 'px)';
    return x < stageW && y < stageH && x + size > 0 && y + size > 0;
  }
  function renderDetail(){
    var want = {}, allLoaded = true, L = detailLevel();
    if (L){
      var T = DETAIL.tile * Math.pow(2, ZOOM - L.z) * S;          // a piece in map-picture px
      var c0 = Math.max(0, Math.floor(-originX / scale / T)), c1 = Math.min(L.cols - 1, Math.floor((stageW - originX) / scale / T));
      var r0 = Math.max(0, Math.floor(-originY / scale / T)), r1 = Math.min(L.rows - 1, Math.floor((stageH - originY) / scale / T));
      for (var r = r0; r <= r1; r++) for (var c = c0; c <= c1; c++){
        if (L.have.charAt(r * L.cols + c) !== '1') continue;
        var key = L.z + '/' + mapStyle + '/' + c + '_' + r;
        want[key] = true;
        var el = detailEls[key];
        if (!el){
          el = document.createElement('img');
          el.alt = ''; el.draggable = false; el.decoding = 'async';
          el._z = L.z; el._c = c; el._r = r;
          el.onload = function(){ this.classList.add('ok'); scheduleRender(); };
          el.onerror = function(){ this.classList.add('bad'); scheduleRender(); };
          el.src = LAKE_DIR + DETAIL.file.replace('{z}', L.z).replace('{style}', mapStyle).replace('{c}', c).replace('{r}', r);
          detailLayer.appendChild(el);
          detailEls[key] = el;
        }
        el.style.zIndex = 2;
        placeTile(el, L.z, c, r);
        if (!el.classList.contains('ok') && !el.classList.contains('bad')) allLoaded = false;
      }
    }
    // pieces of another level/style: kept (underneath) until the new ones are there
    Object.keys(detailEls).forEach(function(k){
      if (want[k]) return;
      var el = detailEls[k];
      if (!allLoaded && el.classList.contains('ok') && placeTile(el, el._z, el._c, el._r)){ el.style.zIndex = 1; return; }
      el.remove(); delete detailEls[k];
    });
  }

  function render(){
    world.style.transform = 'translate(' + originX + 'px,' + originY + 'px) scale(' + scale + ')';
    renderDetail();
    if (windOn && windCanvas){ try { drawWind(); } catch(e){} }   // ("Vind och lä" -- set up further down; never stops the rest)
    if (ltOn && ltCanvas) ltDrawMap();      // ("Blixtar" -- also further down)
    if (anCanvas) anDraw();                  // (Kartanalys, further down)
    if (msgLayerEl) renderMessages();         // (quick messages, further down)
    renderTrack();
    renderProbe();
    updateMarker();
    updateScaleBar();
    renderWaypoints();
    renderBoats();
    renderMeasure();
  }

  // Touch/wheel events can fire far more often than the screen redraws
  // (120Hz+ on some phones) -- coalesce them into one redraw per frame.
  var renderQueued = false;
  function scheduleRender(){
    if (renderQueued) return;
    renderQueued = true;
    requestAnimationFrame(function(){ renderQueued = false; render(); });
  }

  function zoomAtPoint(px, py, newScale){
    newScale = Math.max(minScale, Math.min(maxScale, newScale));
    originX = px - (px - originX) * (newScale / scale);
    originY = py - (py - originY) * (newScale / scale);
    scale = newScale;
    clampOrigin();
  }

  var reduceMotion = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  // Bumped by every new animation and by touching the map, so an older
  // animation stops instead of fighting your finger (or a newer animation).
  var animToken = 0;
  function animateTo(targetScale, targetOriginX, targetOriginY, duration){
    var myToken = ++animToken;
    if (reduceMotion){ scale = targetScale; originX = targetOriginX; originY = targetOriginY; clampOrigin(); render(); return; }
    var startScale = scale, startX = originX, startY = originY;
    var t0 = performance.now();
    duration = duration || 420;
    function ease(t){ return 1 - Math.pow(1 - t, 3); }
    function step(now){
      if (myToken !== animToken) return; // cancelled
      var t = Math.min(1, (now - t0) / duration);
      var e = ease(t);
      scale = startScale + (targetScale - startScale) * e;
      originX = startX + (targetOriginX - startX) * e;
      originY = startY + (targetOriginY - startY) * e;
      clampOrigin();
      render();
      if (t < 1) requestAnimationFrame(step);
    }
    requestAnimationFrame(step);
  }

  // Where you were looking (image-space center + zoom) right before a
  // standalone-mode reload (see handleOrientationEvent below) -- restored
  // in initView() so rotating doesn't dump you back to the default view.
  var VIEW_STATE_KEY = lakeKey('regnaren_rotation_view_v1', 'rotation_view_v1');
  // Everything else that was going on right before a rotation reload (which
  // page was open, an open spot sheet with what you'd typed, speed history,
  // when your position was last shared ...) -- written by saveRotationState()
  // just before the reload, read once here, used by the parts below.
  var ROT_STATE_KEY = 'ffmap_rotation_state_v1';
  var rotState = (function(){
    var raw = null;
    try { raw = sessionStorage.getItem(ROT_STATE_KEY); sessionStorage.removeItem(ROT_STATE_KEY); } catch(e){}
    if (!raw) return null;
    try { var v = JSON.parse(raw); return (v && Date.now() - (v.t || 0) < 15000) ? v : null; } catch(e){ return null; }
  })();
  function restoreViewStateIfAny(){
    var raw = null;
    try { raw = sessionStorage.getItem(VIEW_STATE_KEY); } catch(e){}
    if (!raw) return false;
    try { sessionStorage.removeItem(VIEW_STATE_KEY); } catch(e){}
    var v;
    try { v = JSON.parse(raw); } catch(e){ return false; }
    if (!v || typeof v.scale !== 'number') return false;
    if (Date.now() - (v.t || 0) > 15000) return false; // stale -- not from the reload we just did
    scale = Math.max(minScale, Math.min(maxScale, v.scale));
    originX = stageW/2 - v.cx * scale;
    originY = stageH/2 - v.cy * scale;
    clampOrigin();
    return true;
  }

  function initView(){
    computeBounds();
    if (restoreViewStateIfAny()){
      // a restored view already reflects exactly where the user was looking
      // -- don't let the first GPS fix override it with an auto-recenter
      hasCenteredOnce = true;
      render();
      return;
    }
    scale = fitScale;
    originX = (stageW - IMG_W * scale) / 2;
    originY = (stageH - IMG_H * scale) / 2;
    clampOrigin();
    render();
  }

  function refreshLayout(){
    var cx = (stageW/2 - originX) / scale, cy = (stageH/2 - originY) / scale;
    computeBounds();
    scale = Math.max(minScale, Math.min(maxScale, scale));
    originX = stageW/2 - cx*scale;
    originY = stageH/2 - cy*scale;
    clampOrigin();
    render();
  }
  window.addEventListener('resize', function(){ refreshLayout(); checkRotationReload(); });
  if (window.visualViewport){
    // more reliable than window resize/orientationchange in some
    // WKWebView contexts (see the standalone home-screen note below)
    window.visualViewport.addEventListener('resize', function(){ refreshLayout(); checkRotationReload(); });
  }

  // True only for an iOS "Add to Home Screen" launch (no Safari chrome).
  var isStandaloneApp = !!window.navigator.standalone;
  document.documentElement.classList.toggle('iosApp', isStandaloneApp);

  // Rotating the phone can, on some mobile browsers, leave a touch/pointer
  // sequence "stuck" mid-gesture (the OS interrupts it for the rotation, so
  // pointerup/pointercancel never fires), and can leave position:fixed
  // content visually mispainted until something forces a reflow. Both show
  // up the same way: nothing responds to taps and the layout looks frozen
  // in the old orientation. Recover from both whenever the orientation
  // actually changes:
  var lastOrientationEventAt = 0;
  function handleOrientationEvent(){
    // both 'orientationchange' and screen.orientation 'change' fire for one
    // rotation -- handle it once
    var tNow = Date.now();
    if (tNow - lastOrientationEventAt < 1000) return;
    lastOrientationEventAt = tNow;
    // what was on screen right when the turn began -- before the new size moves anything (scroll
    // positions, the map's centre); used if this turn ends in a reload
    if (isStandaloneApp){
      preTurn = { t: tNow, view: { cx: (stageW / 2 - originX) / scale, cy: (stageH / 2 - originY) / scale, scale: scale, t: tNow } };
      saveRotationState();
    }

    function settle(){
      // 0) iOS can leave the page scrolled a bit after a rotation: then every tap lands beside
      //    what's drawn (the buttons seem "offset") -- put it back at the top
      try { window.scrollTo(0, 0); document.documentElement.scrollTop = 0; document.body.scrollTop = 0; } catch(e){}
      // 1) drop any pointer/gesture tracking that never got a matching
      //    pointerup (a touch interrupted by the physical rotation)
      pointers.clear();
      panStart = null; pinch = null; lastTap = null;
      cancelLongPress();
      stage.classList.remove('dragging');
      // 2) force a reflow of the fixed-position root -- works around a
      //    stale paint of position:fixed content after rotation
      appEl.style.display = 'none';
      void appEl.offsetHeight;
      appEl.style.display = '';
      // 3) recompute the map layout
      refreshLayout();
    }
    settle();
    setTimeout(settle, 150);
    setTimeout(settle, 400);
    checkRotationReload();
  }
  // iOS home-screen web apps have a long-standing WebKit bug where the screen keeps showing a
  // stale frame from before the rotation (and taps land where things WERE) -- the DOM layout is
  // already right, only what's painted is stale, so no layout fix helps. A real reload is the only
  // fix that reliably repaints. The page remembers which way round it was laid out when it loaded;
  // whenever the screen has settled the other way round, it reloads. (It used to skip any rotation
  // within 3 s of the last reload -- turning the phone back quickly then left the stale, "offset"
  // screen until you turned it again. A reload that happened in the middle of the turn now fixes
  // itself too: the page loaded the old way round, the screen settles the new way -> reload again.)
  var loadedLandscape = window.innerWidth > window.innerHeight, rotCheckT = null, preTurn = null;
  function checkRotationReload(){
    if (!isStandaloneApp) return;
    clearTimeout(rotCheckT);
    rotCheckT = setTimeout(function(){
      var land = window.innerWidth > window.innerHeight;
      if (land === loadedLandscape || !(window.innerWidth > 0 && window.innerHeight > 0)) return;
      // (a guard against reload loops: at most 4 in 20 s)
      var now = Date.now(), recent = [];
      try { recent = JSON.parse(sessionStorage.getItem('ffmap_rot_reloads') || '[]').filter(function(t){ return now - t < 20000; }); } catch(e){}
      if (recent.length >= 4) return;
      recent.push(now);
      try {
        sessionStorage.setItem('ffmap_rot_reloads', JSON.stringify(recent));
        // so initView() can put you back where you were looking instead of snapping to the
        // default view after the reload (refreshLayout keeps the centre through the turn)
        var fresh = preTurn && now - preTurn.t < 3000;
        sessionStorage.setItem(VIEW_STATE_KEY, JSON.stringify(fresh ? preTurn.view : { cx: (stageW / 2 - originX) / scale, cy: (stageH / 2 - originY) / scale, scale: scale, t: now }));
      } catch(e){}
      // open page/sheet, typed text, speed history ... (see 92-rotation.js) -- already saved when the
      // turn began (before the new size moved scroll positions); otherwise now
      if (!(preTurn && now - preTurn.t < 3000)) saveRotationState();
      window.location.reload();
    }, 450);
  }
  window.addEventListener('orientationchange', handleOrientationEvent);
  if (window.screen && window.screen.orientation){
    // the modern replacement for the (deprecated, and on some WKWebView
    // builds unreliable) window.orientationchange event above
    window.screen.orientation.addEventListener('change', handleOrientationEvent);
  }

  /* ---- pointer interaction: pan, pinch-zoom, wheel, double-tap ---- */
  var pointers = new Map();
  var panStart = null;
  var pinch = null; // {prevDist}
  var lastTap = null;

  function dist(a,b){ return Math.hypot(a.x-b.x, a.y-b.y); }
  function midpoint(a,b){ return {x:(a.x+b.x)/2, y:(a.y+b.y)/2}; }

  var gestureWasMulti = false; // this touch sequence has had 2 fingers down (a pinch)
  var tapHadMenuOpen = false;   // a tap that just closes the menu shouldn't also drop a depth probe
  stage.addEventListener('pointerdown', function(e){ mapPointerDown(e, false); });
  // a finger that starts on something on the map (a spot, a boat, a message, a label) still pans
  // the map; only a short tap without moving opens the thing (see mapDraggedJustNow)
  var lastDrag = null;
  function mapDraggedJustNow(){ return !!(lastDrag && performance.now() - lastDrag.t < 450 && lastDrag.moved >= 10); }
  function mapPointerDown(e, onItem){
    pointers.set(e.pointerId, {x:e.clientX, y:e.clientY});
    stage.classList.add('dragging');
    animToken++; // touching the map stops a running pan/zoom animation
    if (pointers.size === 1){
      gestureWasMulti = false;
      tapHadMenuOpen = typeof menuPanel !== 'undefined' && menuPanel.classList.contains('show');
      var p = pointers.values().next().value;
      panStart = {x:p.x, y:p.y, originX:originX, originY:originY, moved:0, t0:performance.now(), onItem: !!onItem};
      pinch = null;
      if (!measureMode && !onItem) startLongPress(p.x, p.y); // (in measuring mode a tap adds a point instead)
    } else if (pointers.size === 2){
      cancelLongPress();
      gestureWasMulti = true;
      var pts = Array.from(pointers.values());
      pinch = { prevDist: dist(pts[0], pts[1]) };
      panStart = null;
    }
  }

  window.addEventListener('pointermove', function(e){
    if (!pointers.has(e.pointerId)) return;
    pointers.set(e.pointerId, {x:e.clientX, y:e.clientY});

    if (pointers.size === 1 && panStart){
      var p = pointers.values().next().value;
      var dx = p.x - panStart.x, dy = p.y - panStart.y;
      panStart.moved = Math.max(panStart.moved, Math.hypot(dx,dy));
      if (panStart.moved > 10) cancelLongPress();
      originX = panStart.originX + dx;
      originY = panStart.originY + dy;
      clampOrigin();
      scheduleRender();
    } else if (pointers.size === 2 && pinch){
      var pts = Array.from(pointers.values());
      var d = dist(pts[0], pts[1]);
      var mid = midpoint(pts[0], pts[1]);
      var ratio = d / pinch.prevDist;
      zoomAtPoint(mid.x, mid.y, scale * ratio);
      pinch.prevDist = d;
      scheduleRender();
    }
  });

  function endPointer(e){
    if (!pointers.has(e.pointerId)) return;
    cancelLongPress();
    var wasSingle = pointers.size === 1 && !gestureWasMulti; // the last finger of a pinch isn't a tap
    var p = pointers.get(e.pointerId);
    pointers.delete(e.pointerId);

    if (pointers.size === 1){
      var rem = pointers.values().next().value;
      panStart = {x:rem.x, y:rem.y, originX:originX, originY:originY, moved:0, t0:performance.now()};
      pinch = null;
    } else if (pointers.size === 0){
      stage.classList.remove('dragging');
      if (panStart) lastDrag = { t: performance.now(), moved: panStart.moved };
      if (panStart && panStart.onItem){ panStart = null; pinch = null; if (typeof render === 'function') scheduleRender(); return; }   // (its own click opens it)
      if (typeof anCanvas !== 'undefined') scheduleRender();                 // (full-resolution outlines again)
      if (measureMode && wasSingle && panStart && panStart.moved < 10 && (performance.now() - panStart.t0) < 600){
        // measuring: every tap on the map is a new point (no double-tap zoom)
        addMeasurePointAtScreen(p.x, p.y);
        lastTap = null;
      } else if (wasSingle && panStart && panStart.moved < 10 && (performance.now() - panStart.t0) < 300){
        var now = performance.now();
        if (lastTap && (now - lastTap.t) < 350 && dist(lastTap, p) < 30){
          cancelProbeTap(); // it was a double tap (zoom), not a depth probe
          var mid = (scale < fitScale * 1.6) ? Math.min(maxScale, fitScale * 2.4) : fitScale;
          var tx = p.x - (p.x - originX) * (mid/scale);
          var ty = p.y - (p.y - originY) * (mid/scale);
          animateTo(mid, tx, ty, 320);
          lastTap = null;
        } else {
          lastTap = {t: now, x:p.x, y:p.y};
          scheduleProbeTap(p.x, p.y, tapHadMenuOpen);
        }
      }
      panStart = null; pinch = null;
    }
  }
  window.addEventListener('pointerup', endPointer);
  window.addEventListener('pointercancel', endPointer);

  stage.addEventListener('wheel', function(e){
    e.preventDefault();
    var factor = Math.exp(-e.deltaY * 0.0015);
    zoomAtPoint(e.clientX, e.clientY, scale * factor);
    scheduleRender();
  }, {passive:false});

