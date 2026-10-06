  /* ================= "Namn" (Filter, Lager) -- on by default =================
     The real place names around the lake from OpenStreetMap (islands, points, bays, farms, hamlets):
     a white dot and the name. Data: lakes/<id>/names.json (tools/osm_names.py), embedded in the page as
     LAKE.names = [[lat, lon, name, 'w' water | 'p' land], ...]. Names in the water come first; where two
     labels would overlap the later one is hidden (so zooming in shows more). Never takes a tap. */
  var NAMES_KEY = 'ffmap_names_v1';
  var NAMES_CFG_KEY = 'ffmap_names_cfg_v1', NAMES_CFG_DEF = { size: 12, op: 50, dot: 1.75, kind: 'all' };   // (the look, Inställningar → Kartan → Platsnamn; the defaults = how it always was)
  var namesCfg = Object.assign({}, NAMES_CFG_DEF);
  try { Object.assign(namesCfg, JSON.parse(localStorage.getItem(NAMES_CFG_KEY) || '{}')); } catch(e){}
  var namesOn = true;   // (on unless you switched it off: '0')
  try { namesOn = localStorage.getItem(NAMES_KEY) !== '0'; } catch(e){}
  var namesEl = document.getElementById('osmNames'), toggleNamesEl = document.getElementById('toggleNames');
  var namesList = (LAKE.names || []).slice().sort(function(a, b){ return (a[3] === 'w' ? 0 : 1) - (b[3] === 'w' ? 0 : 1); }).map(function(n){
    var p = latLonToImgPx(n[0], n[1]);
    var el = document.createElement('div');
    el.className = 'osmN' + (n[3] === 'w' ? '' : ' land');
    el.innerHTML = '<span></span>'; el.firstChild.textContent = n[2];
    namesEl.appendChild(el);
    return { x: p.x, y: p.y, len: n[2].length, land: n[3] !== 'w', w: 0, el: el };
  });
  function namesDraw(){
    if (!namesOn) return;
    var cw = 0.55 * namesCfg.size;   // (about a character's width)
    var placed = [];
    namesList.forEach(function(n){
      var sx = originX + n.x * scale, sy = originY + n.y * scale;
      n.w = n.len * cw + 12;
      var show = (namesCfg.kind === 'all' || !n.land) && sx > -20 && sy > -20 && sx < stageW + 20 && sy < stageH + 20;
      if (show){
        var r = { l: sx - 5, r: sx + 7 + n.w, t: sy - 9, b: sy + 9 };
        for (var i = 0; i < placed.length; i++){ var q = placed[i]; if (r.l < q.r && r.r > q.l && r.t < q.b && r.b > q.t){ show = false; break; } }
        if (show) placed.push(r);
      }
      n.el.style.display = show ? '' : 'none';
      if (show) n.el.style.transform = 'translate(' + sx.toFixed(1) + 'px,' + sy.toFixed(1) + 'px)';
    });
  }
  var nmEl = function(id){ return document.getElementById(id); };
  function namesLook(){   // the settings -> css variables on the layer (73-names.css) + the controls
    namesEl.style.setProperty('--nSz', namesCfg.size + 'px'); namesEl.style.setProperty('--nOp', namesCfg.op / 100); namesEl.style.setProperty('--nDot', namesCfg.dot + 'px');
    nmEl('nmSize').value = namesCfg.size; nmEl('nmSizeVal').textContent = namesCfg.size + ' px';
    nmEl('nmOp').value = namesCfg.op; nmEl('nmOpVal').textContent = namesCfg.op + ' %';
    nmEl('nmDot').value = namesCfg.dot; nmEl('nmDotVal').textContent = String(namesCfg.dot).replace('.', ',') + ' px';
    Array.prototype.forEach.call(nmEl('nmKindSeg').children, function(b){ var on = b.getAttribute('data-k') === namesCfg.kind; b.classList.toggle('active', on); b.setAttribute('aria-checked', on ? 'true' : 'false'); });
    namesDraw();
  }
  function namesCfgChanged(){ try { localStorage.setItem(NAMES_CFG_KEY, JSON.stringify(namesCfg)); } catch(e){} namesLook(); }
  nmEl('nmSize').addEventListener('input', function(){ namesCfg.size = +this.value; namesCfgChanged(); });
  nmEl('nmOp').addEventListener('input', function(){ namesCfg.op = +this.value; namesCfgChanged(); });
  nmEl('nmDot').addEventListener('input', function(){ namesCfg.dot = +this.value; namesCfgChanged(); });
  nmEl('nmKindSeg').addEventListener('click', function(e){ var b = e.target.closest ? e.target.closest('button[data-k]') : null; if (!b) return; namesCfg.kind = b.getAttribute('data-k'); namesCfgChanged(); });
  nmEl('nmReset').addEventListener('click', function(){ namesCfg = Object.assign({}, NAMES_CFG_DEF); namesCfgChanged(); resetDone(this); });
  function namesApply(){ namesEl.classList.toggle('on', namesOn); toggleNamesEl.checked = namesOn; namesLook(); }
  toggleNamesEl.addEventListener('change', function(){
    namesOn = toggleNamesEl.checked;
    try { localStorage.setItem(NAMES_KEY, namesOn ? '1' : '0'); } catch(e){}
    namesApply();
  });
  window.__ffNames = function(){ return { on: namesOn, total: namesList.length, cfg: namesCfg, shown: namesList.filter(function(n){ return n.el.style.display !== 'none'; }).length }; };   // (for the tests)
  namesApply();
