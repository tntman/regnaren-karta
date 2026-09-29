  /* ---- Storlek på fiskeplatser (Settings) ---- */
  var WP_SIZE_KEY = 'regnaren_wp_size_v1';
  // Liten / Normal / Stor. "Normal" (the default) is what used to be
  // "Liten"; "Stor" is the original pin size.
  var WP_SIZES = [0.5, 0.7, 1];
  var wpScale = 0.7;
  try {
    var savedSize = parseFloat(localStorage.getItem(WP_SIZE_KEY));
    if (WP_SIZES.indexOf(savedSize) !== -1) wpScale = savedSize;
    else if (savedSize > 1) wpScale = 1; // old "Stor"/"Extra stor" -> the biggest size now
  } catch(e){}
  var wpSizeSeg = document.getElementById('wpSizeSeg');
  var sizePreviewPin = document.getElementById('wpSizePreviewPin');
  sizePreviewPin.classList.add('wpPin--abborre');
  sizePreviewPin.querySelector('.pinHead').innerHTML = FISH_SVG;
  function applyWpScale(){
    document.documentElement.style.setProperty('--wp-scale', String(wpScale));
    // keep the tap target at least ~34px on screen, whatever the pin size
    var hitPx = Math.max(0, (34 - 30 * wpScale) / 2) / wpScale;
    document.documentElement.style.setProperty('--wp-hit', hitPx.toFixed(1) + 'px');
    // others' spots are smaller: a ~30px tap target (a bit smaller, since they can sit close together)
    var so = wpScale * OTHER_PIN_SCALE;
    document.documentElement.style.setProperty('--wp-hit-o', (Math.max(0, (30 - 30 * so) / 2) / so).toFixed(1) + 'px');
    Array.from(wpSizeSeg.children).forEach(function(b){
      var on = parseFloat(b.getAttribute('data-size')) === wpScale;
      b.classList.toggle('active', on);
      b.setAttribute('aria-checked', on ? 'true' : 'false');
    });
  }
  applyWpScale();
  wpSizeSeg.addEventListener('click', function(e){
    var b = e.target.closest ? e.target.closest('button[data-size]') : null;
    if (!b) return;
    wpScale = parseFloat(b.getAttribute('data-size'));
    try { localStorage.setItem(WP_SIZE_KEY, String(wpScale)); } catch(e){}
    applyWpScale();
    renderWaypoints();
  });

  /* ---- Kartstil (Settings): which map picture is shown ----
     Each style is its own image file next to index.html (same satellite
     land, only the water/depth drawing differs). Only the chosen one is
     downloaded, and the service worker keeps it on the phone afterwards. */
  var MAP_STYLES = LAKE.styles; // (from lakes/<id>/lake.json)
  var DEFAULT_STYLE = MAP_STYLES[0].id;
  var MAP_STYLE_KEY = lakeKey('ffmap_map_style_v1', 'map_style_v1');
  var mapStyle = DEFAULT_STYLE;
  try { var savedStyle = localStorage.getItem(MAP_STYLE_KEY); if (MAP_STYLES.some(function(st){ return st.id === savedStyle; })) mapStyle = savedStyle; } catch(e){}
  function mapFile(id){ return LAKE_DIR + LAKE.mapFile.replace('{style}', id); }
  function thumbFile(id){ return LAKE_DIR + LAKE.thumbFile.replace('{style}', id); }
  var mapStyleList = document.getElementById('mapStyleList');
  var mapStyleMsg = document.getElementById('mapStyleMsg');
  mapStyleList.innerHTML = MAP_STYLES.map(function(st){
    return '<button type="button" class="styleOpt" role="radio" data-style="' + st.id + '"><img src="' + thumbFile(st.id) + '" alt="">' +
      '<span class="soText"><span class="soName">' + st.name + '</span><span class="soDesc" style="display:block">' + st.desc + '</span></span><span class="soCheck"></span></button>';
  }).join('');
  function markStyle(id, loadingId){
    Array.from(mapStyleList.children).forEach(function(b){
      var sid = b.getAttribute('data-style');
      b.classList.toggle('active', sid === id);
      b.classList.toggle('loading', sid === loadingId);
      b.setAttribute('aria-checked', sid === id ? 'true' : 'false');
    });
  }
  function applyLegend(id){
    var st = MAP_STYLES.filter(function(x){ return x.id === id; })[0];
    var lg = document.getElementById('legend'), bar = lg.querySelector('.bar');
    lg.classList.toggle('noBar', !st.legend);
    if (st.legend) bar.style.background = st.legend;
    // a style can have its own scale (e.g. vegetation / bottom hardness)
    var ticks = st.ticks || LAKE.legendTicks;
    document.getElementById('legendTicks').innerHTML = ticks.map(function(t){ return '<span>' + t + '</span>'; }).join('');
    lg.setAttribute('data-contour', st.note || LAKE.contourText);
  }
  var mapImgEl = document.getElementById('mapImg');
  var mapLoadingEl = document.getElementById('mapLoading');
  // Load a style's picture; only switch to it once it's actually there (so a
  // failed download -- no coverage the first time -- keeps the old map).
  function loadMapStyle(id, isStart){
    var file = mapFile(id);
    if (!isStart) markStyle(mapStyle, id);
    mapStyleMsg.hidden = true;
    var probe = new Image();
    probe.onload = function(){
      mapImgEl.src = file;
      mapStyle = id;
      try { localStorage.setItem(MAP_STYLE_KEY, id); } catch(e){}
      applyLegend(id); markStyle(id, null);
      mapLoadingEl.classList.remove('show');
      if (!isStart) scheduleRender(); // detail pieces of the new style
    };
    probe.onerror = function(){
      markStyle(mapStyle, null);
      if (isStart && id !== DEFAULT_STYLE){ loadMapStyle(DEFAULT_STYLE, true); return; } // (the default is always kept on the phone)
      mapLoadingEl.classList.remove('show');
      mapStyleMsg.textContent = 'Kunde inte ladda kartstilen – den behöver nät första gången.';
      mapStyleMsg.hidden = false;
    };
    if (isStart && !mapImgEl.getAttribute('src')) mapLoadingEl.classList.add('show');
    probe.src = file;
  }
  mapStyleList.addEventListener('click', function(e){
    var b = e.target.closest ? e.target.closest('.styleOpt') : null;
    if (!b) return;
    var id = b.getAttribute('data-style');
    if (id !== mapStyle) loadMapStyle(id, false);
  });

  /* ---- the quick map-style button (top right, left of Filter) ----
     Tap: the next of Djupfärger -> Förenklad -> Bottenhårdhet -> Vegetation
     (the name shows for a moment). Hold: a list of all the lake's styles. */
  var QUICK_STYLES = ['s1', 's2', 'c1', 'v1'].filter(function(id){ return MAP_STYLES.some(function(s){ return s.id === id; }); });
  var mapTypeBtn = document.getElementById('mapTypeBtn');
  var mapTypeToast = document.getElementById('mapTypeToast');
  var mapTypePop = document.getElementById('mapTypePop');
  var mapTypeToastTimer = null, mapTypeHold = null, mapTypeHeld = false;
  function styleName(id){ var s = MAP_STYLES.filter(function(x){ return x.id === id; })[0]; return s ? s.name : id; }
  function showMapTypeToast(id){
    mapTypeToast.textContent = styleName(id);
    mapTypeToast.classList.add('show');
    clearTimeout(mapTypeToastTimer);
    mapTypeToastTimer = setTimeout(function(){ mapTypeToast.classList.remove('show'); }, 1600);
  }
  function openMapTypePop(open){
    mapTypePop.classList.toggle('show', open);
    if (!open) return;
    mapTypeToast.classList.remove('show');
    mapTypePop.innerHTML = MAP_STYLES.map(function(st){
      return '<button type="button" class="styleOpt' + (st.id === mapStyle ? ' active' : '') + '" data-style="' + st.id + '"><img src="' + thumbFile(st.id) + '" alt="">' +
        '<span class="soText"><span class="soName">' + st.name + '</span></span><span class="soCheck"></span></button>';
    }).join('') +
      // last: the heat map of the catches -- not a map picture: it opens its own panel (68-heatmap.js)
      '<button type="button" class="styleOpt hmOpt' + (hmOn ? ' active' : '') + '" data-heat="1"><span class="hmThumb"></span>' +
      '<span class="soText"><span class="soName">Heatmap</span><span class="soDesc">' + (hmOn ? 'På · öppnar menyn' : 'Fångster · öppnar meny') + '</span></span><span class="hmArrow">›</span></button>';
  }
  mapTypeBtn.addEventListener('pointerdown', function(e){
    e.stopPropagation();
    mapTypeHeld = false;
    clearTimeout(mapTypeHold);
    mapTypeHold = setTimeout(function(){ mapTypeHeld = true; openMapTypePop(true); }, 500);
  });
  ['pointerup', 'pointerleave', 'pointercancel'].forEach(function(ev){
    mapTypeBtn.addEventListener(ev, function(){ clearTimeout(mapTypeHold); });
  });
  mapTypeBtn.addEventListener('contextmenu', function(e){ e.preventDefault(); });
  mapTypeBtn.addEventListener('click', function(e){
    e.stopPropagation();
    if (mapTypeHeld){ mapTypeHeld = false; return; }          // (that was a hold: the list is open)
    if (mapTypePop.classList.contains('show')){ openMapTypePop(false); return; }
    var i = QUICK_STYLES.indexOf(mapStyle);
    var next = QUICK_STYLES[(i + 1) % QUICK_STYLES.length];   // (not one of the four: -> Djupfärger)
    if (next && next !== mapStyle) loadMapStyle(next, false);
    showMapTypeToast(next);
  });
  mapTypePop.addEventListener('click', function(e){
    e.stopPropagation();
    var b = e.target.closest ? e.target.closest('.styleOpt') : null;
    if (!b) return;
    if (b.getAttribute('data-heat')){ openMapTypePop(false); hmShowPanel(true); return; }
    var id = b.getAttribute('data-style');
    openMapTypePop(false);
    if (id !== mapStyle) loadMapStyle(id, false);
    showMapTypeToast(id);
  });
  mapTypePop.addEventListener('pointerdown', function(e){ e.stopPropagation(); });

