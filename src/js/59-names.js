  /* ================= "Namn" (Filter, Lager) -- off by default =================
     The real place names around the lake from OpenStreetMap (islands, points, bays, farms, hamlets):
     a white dot and the name. Data: lakes/<id>/names.json (tools/osm_names.py), embedded in the page as
     LAKE.names = [[lat, lon, name, 'w' water | 'p' land], ...]. Names in the water come first; where two
     labels would overlap the later one is hidden (so zooming in shows more). Never takes a tap. */
  var NAMES_KEY = 'ffmap_names_v1';
  var namesOn = false;
  try { namesOn = localStorage.getItem(NAMES_KEY) === '1'; } catch(e){}
  var namesEl = document.getElementById('osmNames'), toggleNamesEl = document.getElementById('toggleNames');
  var namesList = (LAKE.names || []).slice().sort(function(a, b){ return (a[3] === 'w' ? 0 : 1) - (b[3] === 'w' ? 0 : 1); }).map(function(n){
    var p = latLonToImgPx(n[0], n[1]);
    var el = document.createElement('div');
    el.className = 'osmN' + (n[3] === 'w' ? '' : ' land');
    el.innerHTML = '<span></span>'; el.firstChild.textContent = n[2];
    namesEl.appendChild(el);
    return { x: p.x, y: p.y, w: n[2].length * 6.6 + 12, el: el };
  });
  function namesDraw(){
    if (!namesOn) return;
    var placed = [];
    namesList.forEach(function(n){
      var sx = originX + n.x * scale, sy = originY + n.y * scale;
      var show = sx > -20 && sy > -20 && sx < stageW + 20 && sy < stageH + 20;
      if (show){
        var r = { l: sx - 5, r: sx + 7 + n.w, t: sy - 9, b: sy + 9 };
        for (var i = 0; i < placed.length; i++){ var q = placed[i]; if (r.l < q.r && r.r > q.l && r.t < q.b && r.b > q.t){ show = false; break; } }
        if (show) placed.push(r);
      }
      n.el.style.display = show ? '' : 'none';
      if (show) n.el.style.transform = 'translate(' + sx.toFixed(1) + 'px,' + sy.toFixed(1) + 'px)';
    });
  }
  function namesApply(){ namesEl.classList.toggle('on', namesOn); toggleNamesEl.checked = namesOn; namesDraw(); }
  toggleNamesEl.addEventListener('change', function(){
    namesOn = toggleNamesEl.checked;
    try { localStorage.setItem(NAMES_KEY, namesOn ? '1' : '0'); } catch(e){}
    namesApply();
  });
  window.__ffNames = function(){ return { on: namesOn, total: namesList.length, shown: namesList.filter(function(n){ return n.el.style.display !== 'none'; }).length }; };   // (for the tests)
  namesApply();
