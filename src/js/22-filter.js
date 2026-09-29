  /* ---- Filter: fold-out under the toggles ---- */
  var visMoreBtn = document.getElementById('visMoreBtn');
  var visMoreEl = document.getElementById('visMore');
  var visTypesEl = document.getElementById('visTypes');
  var othersOpSeg = document.getElementById('othersOpacitySeg');
  var VIS_MORE_OPEN_KEY = 'ffmap_vis_more_open_v1'; // session only: survives the rotation reload
  function setVisMoreOpen(open){
    visMoreEl.hidden = !open;
    visMoreBtn.setAttribute('aria-expanded', open ? 'true' : 'false');
    document.getElementById('visPanel').classList.toggle('moreOpen', open);
    document.getElementById('visMoreBtn').classList.toggle('open', open);
    try { sessionStorage.setItem(VIS_MORE_OPEN_KEY, open ? '1' : '0'); } catch(e){}
  }
  visMoreBtn.addEventListener('click', function(){ setVisMoreOpen(visMoreEl.hidden); });
  try { if (sessionStorage.getItem(VIS_MORE_OPEN_KEY) === '1') setVisMoreOpen(true); } catch(e){}

  delete hiddenTypes.fara;   // (Fara can't be hidden -- no switch for it; an old saved choice is dropped)
  visTypesEl.innerHTML = Object.keys(WP_TYPES).filter(function(t){ return t !== 'fara'; }).map(function(t){
    return '<label class="visRow">' +
      '<span class="visSwatch ws-' + t + '">' + wpIconSvg(t) + '</span>' +
      '<span class="visLabel">' + WP_TYPES[t].label + '</span>' +
      '<span class="toggle"><input type="checkbox" data-type="' + t + '"' + (hiddenTypes[t] ? '' : ' checked') + '>' +
      '<span class="toggleTrack"><span class="toggleThumb"></span></span></span>' +
    '</label>';
  }).join('');
  // the little orange dot on the closed "Filter" button: something is hidden from the map
  function showFilterDot(){ visMoreBtn.classList.toggle('filtered', !showMine || !showOthers || !showBoats || Object.keys(hiddenTypes).length > 0); }
  document.getElementById('visPanel').addEventListener('change', function(){ showFilterDot(); });
  function setTypeHidden(t, hide){
    if (hide) hiddenTypes[t] = true; else delete hiddenTypes[t];
    var cb = visTypesEl.querySelector('input[data-type="' + t + '"]');
    if (cb) cb.checked = !hide;
    try { localStorage.setItem(TYPE_FILTER_KEY, JSON.stringify(Object.keys(hiddenTypes))); } catch(e){}
    showFilterDot();
    renderWaypoints();
  }
  visTypesEl.addEventListener('change', function(e){
    var t = e.target.getAttribute && e.target.getAttribute('data-type');
    if (t) setTypeHidden(t, !e.target.checked);
  });
  showFilterDot();

  function applyOthersOpacity(){
    waypointsLayer.classList.toggle('othersDim', othersOpacity < 1);
    Array.from(othersOpSeg.children).forEach(function(b){
      var on = parseFloat(b.getAttribute('data-op')) === othersOpacity;
      b.classList.toggle('active', on);
      b.setAttribute('aria-checked', on ? 'true' : 'false');
    });
  }
  othersOpSeg.addEventListener('click', function(e){
    var b = e.target.closest ? e.target.closest('button[data-op]') : null;
    if (!b) return;
    othersOpacity = parseFloat(b.getAttribute('data-op'));
    try { localStorage.setItem(OTHERS_OP_KEY, String(othersOpacity)); } catch(e){}
    applyOthersOpacity();
  });
  applyOthersOpacity();

