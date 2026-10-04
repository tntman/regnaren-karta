  /* ================= Heatmap (fångster) =================
     Last in the map-style list (hold the map-style button): a bottom panel like Kartanalys, the
     map toned down the same way, and four ways to show the catches (66-catches.js):
       Värme  -- a heat map (blue -> red), radius in metres + strength
       Per art -- a heat map per species in its colour (abborre orange, gädda green, gös yellow)
       Rutor  -- hexagons of 30/60/120 m on the map with the number of catches
       Prickar -- a dot per catch (bigger fish = bigger dot), names if wanted
     Filters: species, competition. A tap on the map where there are catches opens the catch
     (who, when, depth, its place in the competition; ‹ › for the others there), with Åk hit and
     Liknande. Not together with Kartanalys (both tone the map down). Off after a restart,
     kept through a rotation. The panel closed: a "Heatmap" pill under the weather chip. */
  var HM_KEY = lakeKey('ffmap_heatmap_v1', 'heatmap_v1');
  var hmSet = { style: 'heat', sp: 'all', spOn: { abborre: 1, gadda: 1, gos: 1 }, comp: 'all', rad: 70, str: 50, hexM: 60, cnt: 1, big: 1, names: 0, h0: 0, h1: 23, who: '' };   // (who: only one person's catches -- from their profile, 67-profiles.js)
  var HM_DEFAULTS = JSON.stringify(hmSet);   // (for "Återställ")
  try { var hsv = JSON.parse(localStorage.getItem(HM_KEY) || 'null'); if (hsv) for (var hk in hsv) hmSet[hk] = hsv[hk]; } catch(e){}
  function hmSave(){ try { localStorage.setItem(HM_KEY, JSON.stringify(hmSet)); } catch(e){} }
  // hmOn = chosen (map-style list / its panel); hmShow = shown on the map (Filter → Lager → Heatmap, like Kartanalys)
  var HM_SHOW_KEY = 'ffmap_show_heatmap_v1', hmShow = true;
  try { hmShow = localStorage.getItem(HM_SHOW_KEY) !== '0'; } catch(e){}
  var hmOn = false, hmHeatCache = null, hmHexCells = null, hmCardList = null, hmCardI = 0, hmPendingCard = null;
  var hmCanvas = document.getElementById('hmLayer'), hmCtx = hmCanvas.getContext('2d');
  var hmSatCanvas = document.getElementById('hmSat'), hmSatCtx = hmSatCanvas.getContext('2d');
  var hmPanel = document.getElementById('hmPanel'), hmCard = document.getElementById('hmCard'), hmPill = document.getElementById('hmPill'), toggleHmEl = document.getElementById('toggleHeatmap'), hmBtn = document.getElementById('hmBtn');
  var HM_COL = { abborre: [255, 122, 26], gadda: [53, 210, 74], gos: [58, 134, 255] };
  var HM_SP = [['abborre', 'Abborre', 'abborren'], ['gadda', 'Gädda', 'gäddan'], ['gos', 'Gös', 'gösen']];
  var HM_MON = ['jan', 'feb', 'mar', 'apr', 'maj', 'jun', 'jul', 'aug', 'sep', 'okt', 'nov', 'dec'];
  function hmSpName(sp, i){ var s = HM_SP.filter(function(x){ return x[0] === sp; })[0]; return s ? s[i || 1] : sp; }

  // "regnaren1" -> "Regnaren 1", "vagsfjarden4" -> "Vågsfjärden 4", "malarenOpen" -> "Malaren Open"
  function hmCompName(id){
    if (!id) return 'Utan tävling';
    var m = /^(.*?)(\d+)$/.exec(id), base = m ? m[1] : id, num = m ? ' ' + m[2] : '';
    var nice = (catchPlain(base) === LAKE_ID || catchPlain(base) === catchPlain(LAKE.name)) ? LAKE.name
      : base.replace(/([a-zåäö])([A-ZÅÄÖ])/g, '$1 $2').replace(/^./, function(c){ return c.toUpperCase(); });
    return nice + num;
  }
  function hmDateRange(list){
    var t0 = Infinity, t1 = -Infinity; list.forEach(function(c){ t0 = Math.min(t0, c.t); t1 = Math.max(t1, c.t); });
    var a = new Date(t0), b = new Date(t1);
    if (a.toDateString() === b.toDateString()) return a.getDate() + ' ' + HM_MON[a.getMonth()];
    if (a.getMonth() === b.getMonth()) return a.getDate() + '–' + b.getDate() + ' ' + HM_MON[a.getMonth()];
    return a.getDate() + ' ' + HM_MON[a.getMonth()] + '–' + b.getDate() + ' ' + HM_MON[b.getMonth()];
  }
  function hmWhen(t){      // "26/9 13:00" (short: it's in a small tile); another year: "26/9 -25 13:00"
    var d = new Date(t), y = d.getFullYear() !== new Date().getFullYear() ? ' -' + String(d.getFullYear()).slice(2) : '';
    return d.getDate() + '/' + (d.getMonth() + 1) + y + ' ' + ('0' + d.getHours()).slice(-2) + ':' + ('0' + d.getMinutes()).slice(-2);
  }
  function hmAll(){ return catchData ? catchData.list : []; }
  function hmComps(){
    var by = {}; hmAll().forEach(function(c){ (by[c.comp] = by[c.comp] || []).push(c); });
    return Object.keys(by).map(function(k){ return { id: k, list: by[k] }; }).sort(function(a, b){ return b.list[0].t - a.list[0].t; });
  }
  function hmInComp(c){ return (hmSet.comp === 'all' || c.comp === hmSet.comp) && (!hmSet.who || hmSet.who.split('|').some(function(n){ return catchPlain(c.who) === catchPlain(n); })); }
  function hmHour(c){ return new Date(c.t).getHours(); }
  function hmHourOn(){ return hmSet.h0 > 0 || hmSet.h1 < 23; }
  function hmVisible(anyHour){   // (anyHour: ignore the time window -- the "När" graph shows the whole day)
    return hmAll().filter(function(c){
      if (!hmInComp(c)) return false;
      if (!anyHour && hmHourOn() && (hmHour(c) < hmSet.h0 || hmHour(c) > hmSet.h1)) return false;
      return hmSet.style === 'species' ? !!hmSet.spOn[c.sp] : (hmSet.sp === 'all' || c.sp === hmSet.sp);
    });
  }

  // ---- on / off, the panel, the pill ----
  function hmSetOn(on, openPanel, restoring){
    hmOn = !!on;
    if (hmOn){
      if (!restoring && !hmShow) hmSetShow(true);   // (turned on by hand: shown, like choosing a Kartanalys mode)
      loadCatches(false);
      if (anSet.mode){ anSet.mode = null; anSave(); anCtlMode = '#'; anCompute(); }   // (not together with Kartanalys)
      showAnPanel(false);
    } else { hmShowPanel(false); hmCloseCard(); }
    hmShowUi();
    hmHeatCache = null;
    if (openPanel) hmShowPanel(true);
    hmRenderPanel(); hmDraw();
  }
  function hmShowPanel(open){
    if (open && !hmOn){ hmSetOn(true, true); return; }
    if (open){
      if (!hmPanel.classList.contains('show') && hmPanel._resetSize) hmPanel._resetSize();
      showAnPanel(false); hmCloseCard();
      if (typeof toggleMsgPop === 'function') toggleMsgPop(false);
      hmRenderPanel();
    }
    hmPanel.classList.toggle('show', !!open);
  }
  hmPill.addEventListener('pointerdown', function(e){ e.stopPropagation(); });
  // Filter → Lager → Heatmap: only shows / hides it on the map, like Kartanalys (on / off is in its own panel)
  function hmShowUi(){
    var vis = hmOn && hmShow;
    hmCanvas.classList.toggle('on', vis); hmSatCanvas.classList.toggle('on', vis);
    hmPill.hidden = !vis;                               // (the pill: something is shown on the map)
    toggleHmEl.checked = hmShow;
    hmBtn.classList.toggle('on', vis); hmBtn.setAttribute('aria-pressed', vis ? 'true' : 'false');
  }
  function hmSetShow(show){
    hmShow = !!show; try { localStorage.setItem(HM_SHOW_KEY, hmShow ? '1' : '0'); } catch(e){}
    if (!hmShow) hmCloseCard();
    hmShowUi(); hmHeatCache = null; hmRenderPanel(); hmDraw();
  }
  toggleHmEl.addEventListener('change', function(){ hmSetShow(toggleHmEl.checked); });
  hmBtn.addEventListener('click', function(){ if (hmOn) hmSetOn(false); else hmSetOn(true, true); });   // (the quick on / off next to the map button)
  hmShowUi();
  hmPill.addEventListener('click', function(e){ e.stopPropagation(); hmShowPanel(!hmPanel.classList.contains('show')); });

  function hmRenderPanel(){
    Array.prototype.forEach.call(hmPanel.querySelectorAll('#hmStyleSeg button'), function(b){ b.classList.toggle('on', b.getAttribute('data-s') === hmSet.style); });
    document.getElementById('hmReset').disabled = JSON.stringify(hmSet) === HM_DEFAULTS;
    var st = hmSet.style, comps = hmComps();
    if (hmSet.comp !== 'all' && !comps.some(function(c){ return c.id === hmSet.comp; })) hmSet.comp = 'all';
    document.getElementById('hmLegend').innerHTML = (st === 'heat' || st === 'hex') ? '<span>Få</span><span class="bar"></span><span>Många fångster</span>' : '';
    var inComp = hmAll().filter(hmInComp), cnt = { abborre: 0, gadda: 0, gos: 0 };
    inComp.forEach(function(c){ cnt[c.sp]++; });
    var dot = function(sp){ return '<span class="hmSpDot" style="background:rgb(' + HM_COL[sp] + ')"></span>'; };
    // (each row: its name first, then the choices -- one line, sideways if they don't fit)
    document.getElementById('hmSp').innerHTML = '<span class="rowLbl">' + (st === 'species' ? 'Arter' : 'Art') + '</span>' + (st === 'species'
      ? HM_SP.map(function(x){ return '<button type="button" data-spt="' + x[0] + '" class="' + (hmSet.spOn[x[0]] ? 'on' : '') + '">' + dot(x[0]) + x[1] + ' ' + cnt[x[0]] + '</button>'; }).join('')
      : [['all', 'Alla']].concat(HM_SP).map(function(x){ return '<button type="button" data-sp="' + x[0] + '" class="' + (hmSet.sp === x[0] ? 'on' : '') + '">' + x[1] + '</button>'; }).join(''));
    document.getElementById('hmComp').innerHTML = '<span class="rowLbl">Tävling</span><button type="button" data-comp="all" class="' + (hmSet.comp === 'all' ? 'on' : '') + '">Alla</button>' +
      comps.map(function(c){ return '<button type="button" data-comp="' + escHtml(c.id) + '" class="' + (hmSet.comp === c.id ? 'on' : '') + '">' + escHtml(hmCompName(c.id)) + ' · ' + hmDateRange(c.list) + '</button>'; }).join('');
    var rng = function(k, l, min, max, stp){ return '<div class="anRange"><label>' + l + '</label><input type="range" data-r="' + k + '" min="' + min + '" max="' + max + '" step="' + stp + '" value="' + hmSet[k] + '"><output id="hmOut_' + k + '">' + hmOutTxt(k) + '</output></div>'; };
    var tog = function(k, l){ return '<button type="button" data-t="' + k + '" class="' + (hmSet[k] ? 'on' : '') + '">' + (hmSet[k] ? '✓ ' : '') + l + '</button>'; };
    document.getElementById('hmCtl').innerHTML =
      st === 'heat' ? rng('rad', 'Radie', 20, 200, 10) + rng('str', 'Styrka', 0, 100, 5)
      : st === 'species' ? rng('rad', 'Radie', 20, 200, 10)
      : st === 'hex' ? '<div class="pnRow2"><div class="anSeg" aria-label="Rutans storlek">' + [30, 60, 120].map(function(m){ return '<button type="button" data-hx="' + m + '" class="' + (hmSet.hexM === m ? 'on' : '') + '">' + m + ' m</button>'; }).join('') + '</div><div class="anChips">' + tog('cnt', 'Visa antal') + '</div></div>'
      : '<div class="anChips">' + tog('big', 'Större prick = större fisk') + tog('names', 'Visa namn') + '</div>';
    hmRenderTime();
    var res = document.getElementById('hmResult'), all = hmAll();
    if (!catchData) res.innerHTML = 'Hämtar fångster…';
    else if (!all.length) res.innerHTML = catchErr ? 'Kunde inte hämta fångsterna (ingen anslutning?).' : 'Inga fångster i ' + escHtml(LAKE.name) + ' än.';
    else {
      var v = hmVisible(), c2 = { abborre: 0, gadda: 0, gos: 0 }; v.forEach(function(c){ c2[c.sp]++; });
      res.innerHTML = (hmSet.who ? '<button type="button" class="hmWho" data-who="">Bara ' + escHtml(hmSet.who.split('|').join(', ')) + ' ✕</button> ' : '') + '<b>' + v.length + ' fångster</b> i ' + escHtml(LAKE.name) + (catchLiveComp() ? ' · <b class="hmLive">Live</b>' : '') + (hmHourOn() ? ' · kl ' + hmHourTxt() : '') + ' · ' + HM_SP.map(function(x){ return c2[x[0]] + ' ' + x[1].toLowerCase(); }).join(', ') +
        '<span class="note">' + (st === 'dots' ? 'Tryck på en prick för allt om fångsten.' : st === 'hex' ? 'Tryck på en ruta för fångsterna i den.' : 'Tryck på kartan där det är färg för fångsterna där.') + '</span>' +
        (!hmShow ? '<span class="pnHid"> · Dold – slå på Heatmap i Filter</span>' : '');
    }
    pnInfo(hmPanel);
  }
  // "När": a bar per hour of the day (catches passing species + competition); press / drag = a time window that filters the map
  function hmHourTxt(){ return ('0' + hmSet.h0).slice(-2) + '–' + ('0' + (hmSet.h1 + 1)).slice(-2); }
  function hmRenderTime(){
    var el = document.getElementById('hmTime'), L = hmAll().length ? hmVisible(true) : [], n = [];
    if (!L.length){ el.innerHTML = ''; return; }
    var lo = 24, hi = -1, h, i; for (h = 0; h < 24; h++) n[h] = 0;
    L.forEach(function(c){ n[hmHour(c)]++; });
    for (h = 0; h < 24; h++) if (n[h]){ lo = Math.min(lo, h); hi = Math.max(hi, h); }
    var mx = Math.max.apply(null, n), best = 0, bs = -1;                     // (best 3 hours in a row)
    for (h = 0; h <= 21; h++){ var s = n[h] + n[h + 1] + n[h + 2]; if (s > bs){ bs = s; best = h; } }
    var bars = '', hrs = '';
    for (h = lo; h <= hi; h++){
      var v = n[h] / mx, rgba = hmRamp(0.25 + 0.75 * v);   // (never the see-through dark end)
      bars += '<i data-h="' + h + '" class="' + (h >= hmSet.h0 && h <= hmSet.h1 ? 'on' : '') + '" style="height:' + Math.max(4, Math.round(v * 100)) + '%;background:rgb(' + Math.round(rgba[0]) + ',' + Math.round(rgba[1]) + ',' + Math.round(rgba[2]) + ')"><b>' + n[h] + '</b></i>';
      hrs += '<span>' + ('0' + h).slice(-2) + '</span>';
    }
    el.setAttribute('data-lo', lo); el.setAttribute('data-hi', hi);
    el.innerHTML = '<div class="hmTimeHead"><span class="rowLbl">När</span><span class="hmTimeBest">Bäst kl ' + ('0' + best).slice(-2) + '–' + ('0' + (best + 3)).slice(-2) + ' · ' + Math.round(100 * bs / L.length) + ' %</span></div>' +
      '<div class="hmBars">' + bars + '</div><div class="hmAx">' + hrs + '</div>';
  }
  (function(){
    var el = document.getElementById('hmTime'), a = -1, moved = false, prev = null;
    function hourAt(e){
      var b = el.querySelector('.hmBars'); if (!b) return -1;
      var r = b.getBoundingClientRect(), lo = +el.getAttribute('data-lo'), hi = +el.getAttribute('data-hi');
      return lo + Math.max(0, Math.min(hi - lo, Math.floor((e.clientX - r.left) / r.width * (hi - lo + 1))));
    }
    function apply(h){ hmSet.h0 = Math.min(a, h); hmSet.h1 = Math.max(a, h); hmSave(); hmHeatCache = null; hmRenderPanel(); hmDraw(); }
    el.addEventListener('pointerdown', function(e){
      e.stopPropagation(); if (!el.querySelector('.hmBars')) return;
      a = hourAt(e); moved = false; prev = [hmSet.h0, hmSet.h1];
      try { el.setPointerCapture(e.pointerId); } catch(x){}
      apply(a);
    });
    el.addEventListener('pointermove', function(e){
      if (a < 0) return; var h = hourAt(e); if (h === (hmSet.h0 === a ? hmSet.h1 : hmSet.h0)) return;
      moved = true; apply(h);
    });
    function up(){
      if (a < 0) return;
      if (!moved && prev[0] === a && prev[1] === a){ hmSet.h0 = 0; hmSet.h1 = 23; hmSave(); hmHeatCache = null; hmRenderPanel(); hmDraw(); }   // (the same hour again = all)
      a = -1;
    }
    el.addEventListener('pointerup', up); el.addEventListener('pointercancel', up);
  })();
  function hmOutTxt(k){ return k === 'rad' ? hmSet.rad + ' m' : hmSet.str < 34 ? 'Svag' : hmSet.str < 67 ? 'Mellan' : 'Stark'; }
  hmPanel.addEventListener('pointerdown', function(e){ e.stopPropagation(); });
  hmPanel.addEventListener('click', function(e){
    var t = e.target.closest ? e.target.closest('button') : null; if (!t) return;
    var a;
    if ((a = t.getAttribute('data-s'))) hmSet.style = a;
    else if ((a = t.getAttribute('data-sp'))) hmSet.sp = a;
    else if ((a = t.getAttribute('data-spt'))) hmSet.spOn[a] = hmSet.spOn[a] ? 0 : 1;
    else if ((a = t.getAttribute('data-comp'))) hmSet.comp = a;
    else if ((a = t.getAttribute('data-hx'))) hmSet.hexM = +a;
    else if (t.hasAttribute('data-who')) hmSet.who = '';
    else if ((a = t.getAttribute('data-t'))) hmSet[a] = hmSet[a] ? 0 : 1;
    else return;
    hmSave(); hmHeatCache = null; hmRenderPanel(); hmDraw();
  });
  hmPanel.addEventListener('input', function(e){
    var k = e.target.getAttribute && e.target.getAttribute('data-r'); if (!k) return;
    hmSet[k] = +e.target.value; hmSave();
    var o = document.getElementById('hmOut_' + k); if (o) o.textContent = hmOutTxt(k);
    document.getElementById('hmReset').disabled = JSON.stringify(hmSet) === HM_DEFAULTS;   // (↺ at once, while dragging)
    hmHeatCache = null; hmDraw();
  });
  document.getElementById('hmClose').addEventListener('click', function(){ hmShowPanel(false); });
  document.getElementById('hmOff').addEventListener('click', function(){ hmSetOn(false); });
  document.getElementById('hmReset').addEventListener('click', function(){ hmSet = JSON.parse(HM_DEFAULTS); hmSave(); hmHeatCache = null; hmRenderPanel(); hmDraw(); resetDone(this); });
  sheetSwipe(hmPanel, function(){ hmShowPanel(false); });

  // ---- drawing (a screen canvas like Kartanalys: the map toned down, the catches on top) ----
  function hmRamp(v){   // "glöd": transparent dark violet -> magenta -> orange -> amber -> warm white
    var S = [[0, [60, 10, 90, 0]], [0.12, [90, 20, 130, 120]], [0.35, [190, 40, 140, 185]], [0.6, [245, 110, 60, 215]], [0.85, [255, 190, 70, 235]], [1, [255, 245, 200, 245]]];
    for (var k = 1; k < S.length; k++) if (v <= S[k][0]){
      var t = (v - S[k - 1][0]) / (S[k][0] - S[k - 1][0]), A = S[k - 1][1], B = S[k][1];
      return [A[0] + (B[0] - A[0]) * t, A[1] + (B[1] - A[1]) * t, A[2] + (B[2] - A[2]) * t, A[3] + (B[3] - A[3]) * t];
    }
    return S[S.length - 1][1];
  }
  // a heat layer (every STEP css px, see viewStep): soft spots of `rad` metres, coloured by pal(0..1)
  function hmHeatLayer(pts, W, H, STEP, mpp, pal){
    var vw = Math.ceil(W / STEP), vh = Math.ceil(H / STEP), cv = document.createElement('canvas'); cv.width = vw; cv.height = vh;
    var o = cv.getContext('2d'), R = Math.max(6, hmSet.rad / mpp) / STEP, a = 0.12 + 0.43 * hmSet.str / 100;
    pts.forEach(function(s){
      var x = s.x / STEP, y = s.y / STEP; if (x < -R || y < -R || x > vw + R || y > vh + R) return;
      var g = o.createRadialGradient(x, y, 0, x, y, R); g.addColorStop(0, 'rgba(0,0,0,' + a + ')'); g.addColorStop(1, 'rgba(0,0,0,0)');
      o.fillStyle = g; o.fillRect(x - R, y - R, 2 * R, 2 * R);
    });
    var im = o.getImageData(0, 0, vw, vh), d = im.data;
    for (var i = 0; i < d.length; i += 4){
      var v = d[i + 3] / 255; if (v < 0.02){ d[i + 3] = 0; continue; }
      var c = pal(v); d[i] = c[0]; d[i + 1] = c[1]; d[i + 2] = c[2]; d[i + 3] = c[3];
    }
    o.putImageData(im, 0, 0);
    return cv;
  }
  function hmHexOf(xm, ym, R){           // map metres -> the hexagon (axial q, r) it's in
    var q = (Math.sqrt(3) / 3 * xm - ym / 3) / R, r = (2 / 3 * ym) / R, s = -q - r;
    var rq = Math.round(q), rr = Math.round(r), rs = Math.round(s), dq = Math.abs(rq - q), dr = Math.abs(rr - r), ds = Math.abs(rs - s);
    if (dq > dr && dq > ds) rq = -rr - rs; else if (dr > ds) rr = -rq - rs;
    return { q: rq, r: rr };
  }
  function hmDraw(){
    var dpr = window.devicePixelRatio || 1, W = stage.clientWidth, H = stage.clientHeight;
    [hmCanvas, hmSatCanvas].forEach(function(c){ if (c.width !== Math.round(W * dpr) || c.height !== Math.round(H * dpr)){ c.width = Math.round(W * dpr); c.height = Math.round(H * dpr); } });
    hmCtx.setTransform(dpr, 0, 0, dpr, 0, 0); hmCtx.clearRect(0, 0, W, H);
    hmSatCtx.setTransform(dpr, 0, 0, dpr, 0, 0); hmSatCtx.clearRect(0, 0, W, H);
    hmHexCells = null;
    if (!hmOn || !hmShow || !(W >= 2 && H >= 2)) return;
    // the map toned down and greyed like in Kartanalys (Inställningar "Mörkare")
    hmSatCtx.fillStyle = 'rgba(128,128,128,' + Math.min(1, anSet.dim + 0.2) + ')'; hmSatCtx.fillRect(0, 0, W, H);
    hmCtx.fillStyle = 'rgba(6,14,20,' + anSet.dim + ')'; hmCtx.fillRect(0, 0, W, H);
    var L = hmVisible(), st = hmSet.style;
    if (st !== 'heat' && st !== 'species' || !L.length) hmDrawShore(W, H);
    if (!L.length) return;
    var mpp = WEB_METERS_PER_PX / scale;
    var P = L.map(function(c){ return { c: c, x: originX + c.px * scale, y: originY + c.py * scale }; });
    if (st === 'heat' || st === 'species'){
      var STEP = viewStep(W, H), key = [originX.toFixed(1), originY.toFixed(1), scale.toFixed(5), W, H, STEP, catchVer, JSON.stringify(hmSet)].join('|');
      if (!hmHeatCache || hmHeatCache.key !== key){
        var cv;
        if (st === 'heat') cv = hmHeatLayer(P, W, H, STEP, mpp, hmRamp);
        else {
          cv = document.createElement('canvas'); cv.width = Math.ceil(W / STEP); cv.height = Math.ceil(H / STEP);
          var o = cv.getContext('2d'); o.globalCompositeOperation = 'lighter';
          HM_SP.forEach(function(x){
            var col = HM_COL[x[0]], S2 = P.filter(function(p){ return p.c.sp === x[0]; }); if (!S2.length) return;
            o.drawImage(hmHeatLayer(S2, W, H, STEP, mpp, function(v){ var k = Math.min(1, v * 1.6); return [col[0], col[1], col[2], 60 + 180 * k]; }), 0, 0);
          });
        }
        hmHeatCache = { key: key, cv: cv, STEP: STEP };
      }
      hmCtx.imageSmoothingEnabled = true;
      hmCtx.drawImage(hmHeatCache.cv, 0, 0, hmHeatCache.cv.width * hmHeatCache.STEP, hmHeatCache.cv.height * hmHeatCache.STEP);
      hmDrawShore(W, H);
    } else if (st === 'hex'){
      var R = hmSet.hexM / Math.sqrt(3), mI = WEB_METERS_PER_PX, cells = {}, mx = 0;
      L.forEach(function(c){ var h = hmHexOf(c.px * mI, c.py * mI, R), k = h.q + ',' + h.r; (cells[k] = cells[k] || { q: h.q, r: h.r, list: [] }).list.push(c); });
      for (var k in cells) mx = Math.max(mx, cells[k].list.length);
      var Rpx = R / mI * scale;
      hmCtx.textAlign = 'center'; hmCtx.textBaseline = 'middle'; hmCtx.font = '700 ' + Math.max(8, Math.min(13, Rpx * 0.75)) + 'px Calibri,"Segoe UI",sans-serif';
      for (var k2 in cells){
        var h2 = cells[k2], cx = originX + R * Math.sqrt(3) * (h2.q + h2.r / 2) / mI * scale, cy = originY + R * 1.5 * h2.r / mI * scale;
        h2.x = cx; h2.y = cy;
        if (cx < -Rpx || cy < -Rpx || cx > W + Rpx || cy > H + Rpx) continue;
        var col = hmRamp(0.2 + 0.8 * Math.sqrt(h2.list.length / mx));
        hmCtx.beginPath();
        for (var a = 0; a < 6; a++){ var an = Math.PI / 180 * (60 * a - 30); hmCtx.lineTo(cx + Math.max(1, Rpx - 1) * Math.cos(an), cy + Math.max(1, Rpx - 1) * Math.sin(an)); }
        hmCtx.closePath();
        hmCtx.fillStyle = 'rgba(' + (col[0] | 0) + ',' + (col[1] | 0) + ',' + (col[2] | 0) + ',0.75)'; hmCtx.fill();
        hmCtx.lineWidth = 1; hmCtx.strokeStyle = 'rgba(255,255,255,0.55)'; hmCtx.stroke();
        if (hmSet.cnt && Rpx >= 8){ hmCtx.fillStyle = col[0] * 0.3 + col[1] * 0.59 + col[2] * 0.11 < 140 ? '#fff' : '#0B2A3A'; hmCtx.fillText(String(h2.list.length), cx, cy + 0.5); }
      }
      hmHexCells = { R: R, cells: cells, rpx: Rpx };
    } else {
      P.slice().sort(function(a, b){ return b.c.cm - a.c.cm; }).forEach(function(p){
        if (p.x < -20 || p.y < -20 || p.x > W + 20 || p.y > H + 20) return;
        var col = HM_COL[p.c.sp], r = hmDotR(p.c);
        hmCtx.beginPath(); hmCtx.arc(p.x, p.y, r, 0, 7); hmCtx.fillStyle = 'rgba(' + col + ',0.9)'; hmCtx.fill();
        hmCtx.lineWidth = 1.3; hmCtx.strokeStyle = 'rgba(11,42,58,0.9)'; hmCtx.stroke();
        if (hmSet.names && p.c.who){
          hmCtx.font = '600 11px Calibri,"Segoe UI",sans-serif'; hmCtx.textAlign = 'left'; hmCtx.textBaseline = 'middle';
          hmCtx.lineWidth = 3; hmCtx.strokeStyle = 'rgba(6,14,20,0.85)'; hmCtx.strokeText(p.c.who, p.x + r + 3, p.y);
          hmCtx.fillStyle = '#fff'; hmCtx.fillText(p.c.who, p.x + r + 3, p.y);
        }
      });
    }
    // the catch that's open: a white ring
    var sel = hmCardList && hmCard.classList.contains('show') ? hmCardList[hmCardI] : null;
    if (sel){
      var sx = originX + sel.px * scale, sy = originY + sel.py * scale;
      hmCtx.beginPath(); hmCtx.arc(sx, sy, (st === 'dots' ? hmDotR(sel) : 6) + 6, 0, 7);
      hmCtx.lineWidth = 3; hmCtx.strokeStyle = '#fff'; hmCtx.stroke();
    }
  }
  // the lake's edge: a thin white line at 50 %, drawn exactly like Kartanalys' (the lake field smoothed
  // to about one drawn point, the line where it crosses 0,5 -- see anField / edgeW)
  var hmShoreBox = { p: null }, hmShoreCache = null, HM_NOMASK = null;
  function hmShoreLayer(W, H){
    var A = anBase(); if (!A) return null;
    var STEP = viewStep(W, H), key = [originX.toFixed(1), originY.toFixed(1), scale.toFixed(5), W, H, STEP].join('|');
    if (hmShoreCache && hmShoreCache.key === key) return hmShoreCache;
    if (!HM_NOMASK || HM_NOMASK.length !== A.N) HM_NOMASK = new Uint8Array(A.N);
    var vw = Math.ceil(W / STEP), vh = Math.ceil(H / STEP), fp = A.W / IMG_W / scale * STEP;
    var Lf = anField({ ver: 'shore', M: HM_NOMASK, G: null }, A, Math.max(0, Math.round(Math.log(Math.max(1, fp)) / Math.LN2)), hmShoreBox);
    var g = Lf.f[2], LW2 = Lf.w, LH2 = Lf.h, kx = A.W / IMG_W / (1 << Lf.lv), ky = A.H / IMG_H / (1 << Lf.lv), fl = new Float32Array(vw * vh);
    for (var y = 0; y < vh; y++) for (var x = 0; x < vw; x++){
      var fx = (x * STEP + 1 - originX) / scale * kx - 0.5, fy = (y * STEP + 1 - originY) / scale * ky - 0.5, x0 = Math.floor(fx), y0 = Math.floor(fy), tx = fx - x0, ty = fy - y0, a = 0;
      for (var dy = 0; dy <= 1; dy++) for (var dx = 0; dx <= 1; dx++){
        var cx = x0 + dx, cy = y0 + dy; if (cx < 0 || cy < 0 || cx >= LW2 || cy >= LH2) continue;
        a += g[cy * LW2 + cx] * (dx ? tx : 1 - tx) * (dy ? ty : 1 - ty);
      }
      fl[y * vw + x] = a;
    }
    var cv = document.createElement('canvas'); cv.width = vw; cv.height = vh;
    var o = cv.getContext('2d'), im = o.createImageData(vw, vh), d = im.data, ES = edgeW(STEP, 0.9);
    for (var y2 = 0; y2 < vh; y2++) for (var x2 = 0; x2 < vw; x2++){
      var q = y2 * vw + x2;
      var gx = (fl[x2 < vw - 1 ? q + 1 : q] - fl[x2 > 0 ? q - 1 : q]) / 2, gy = (fl[y2 < vh - 1 ? q + vw : q] - fl[y2 > 0 ? q - vw : q]) / 2;
      var es = Math.max(0, Math.min(1, 1 - Math.abs((fl[q] - 0.5) / (Math.sqrt(gx * gx + gy * gy) + 1e-3)) / ES[0])) * ES[1];
      if (es > 0){ var k = q * 4; d[k] = d[k + 1] = d[k + 2] = 255; d[k + 3] = 128 * es; }
    }
    o.putImageData(im, 0, 0);
    return (hmShoreCache = { key: key, cv: cv, STEP: STEP });
  }
  function hmDrawShore(W, H){
    var sh = hmShoreLayer(W, H); if (!sh) return;
    hmCtx.imageSmoothingEnabled = true; hmCtx.drawImage(sh.cv, 0, 0, sh.cv.width * sh.STEP, sh.cv.height * sh.STEP);
  }
  function hmDotR(c){ return hmSet.big ? Math.max(3.5, Math.min(11, 3 + c.cm / 14)) : 5.5; }

  // ---- a tap on the map: the catches there (from scheduleProbeTap) ----
  function hmTapAt(sx, sy){
    if (!hmOn || !hmShow || !catchData) return false;
    var list = [], L = hmVisible();
    if (hmSet.style === 'hex' && hmHexCells){
      var mI = WEB_METERS_PER_PX, h = hmHexOf((sx - originX) / scale * mI, (sy - originY) / scale * mI, hmHexCells.R), cell = hmHexCells.cells[h.q + ',' + h.r];
      if (cell) list = cell.list.slice().sort(function(a, b){ return b.cm - a.cm; });
    } else {
      var best = null, bd = Infinity;
      L.forEach(function(c){ var d = Math.hypot(originX + c.px * scale - sx, originY + c.py * scale - sy); if (d < bd){ bd = d; best = c; } });
      var lim = hmSet.style === 'dots' ? hmDotR(best || { cm: 0 }) + 12 : 30;
      if (best && bd <= lim){
        // it and the others within 50 m of it, nearest the finger first
        list = L.filter(function(c){ return hmMetres(c, best) <= 50; }).sort(function(a, b){
          return Math.hypot(originX + a.px * scale - sx, originY + a.py * scale - sy) - Math.hypot(originX + b.px * scale - sx, originY + b.py * scale - sy); });
      }
    }
    if (!list.length){
      if (hmCard.classList.contains('show')){ hmCloseCard(); return true; }   // (a tap beside: just closes the catch)
      return false;
    }
    hmOpenCard(list, 0);
    return true;
  }
  function hmMetres(a, b){ return Math.hypot(a.px - b.px, a.py - b.py) * WEB_METERS_PER_PX; }

  // ---- the catch panel ----
  function hmOpenCard(list, i){
    hmCardList = list; hmCardI = i || 0;
    hmPanel.classList.remove('show');
    if (!hmCard.classList.contains('show') && hmCard._resetSize) hmCard._resetSize();
    hmFillCard(); hmCard.classList.add('show'); hmDraw();
  }
  function hmCloseCard(){ var was = hmCard.classList.contains('show'); hmCard.classList.remove('show'); hmCardList = null; if (was) hmDraw(); }
  function hmOrdinal(n){ return n + ((n % 10 === 1 || n % 10 === 2) && n % 100 !== 11 && n % 100 !== 12 ? ':a' : ':e'); }
  function hmFillCard(){
    var c = hmCardList[hmCardI]; if (!c) return;
    var same = hmAll().filter(function(x){ return x.comp === c.comp && x.sp === c.sp; }).sort(function(a, b){ return b.cm - a.cm; });
    var rank = 1; same.forEach(function(x){ if (x.cm > c.cm) rank++; });
    var near = hmAll().filter(function(x){ return x !== c && x.comp === c.comp && hmMetres(x, c) <= 50; }).length;
    var dep = depthAtLatLon(c.lat, c.lon);
    document.getElementById('hmCardKick').textContent = 'FÅNGST · ' + hmCompName(c.comp).toUpperCase();
    document.getElementById('hmCardTitle').innerHTML = '<span class="hmSpDot" style="width:13px;height:13px;background:rgb(' + HM_COL[c.sp] + ')"></span>' + hmSpName(c.sp) + (c.cm ? ' ' + String(c.cm).replace('.', ',') + ' cm' : '');
    document.getElementById('hmCardData').innerHTML = [['Vem', c.who || '–'], ['När', hmWhen(c.t)], ['Djup', dep != null ? fmtDepth(dep) + ' m' : '–'], ['Plats', rank + ' av ' + same.length]]
      .map(function(t, k){ var pf = !k && c.who; return '<div class="wpTile' + (pf ? ' pfLink" data-who="' + escHtml(pf) : '') + '"><i>' + t[0] + '</i><b>' + escHtml(t[1]) + '</b></div>'; }).join('');
    catchImg(document.getElementById('hmCardImg'), c.img);
    document.getElementById('hmCardNote').textContent = (rank === 1 ? 'Största ' : hmOrdinal(rank) + ' största ') + hmSpName(c.sp, 2) + ' i tävlingen' +
      ' · ' + (near ? near + ' fångster till inom 50 m' : 'inga andra fångster inom 50 m');
    document.getElementById('hmCardNav').hidden = hmCardList.length < 2;
    document.getElementById('hmCardPos').textContent = (hmCardI + 1) + ' av ' + hmCardList.length + ' här';
  }
  hmCard.addEventListener('pointerdown', function(e){ e.stopPropagation(); });
  document.getElementById('hmCardData').addEventListener('click', function(e){ var t = e.target.closest && e.target.closest('.pfLink'); if (t) openProfile(t.getAttribute('data-who')); });
  sheetSwipe(hmCard, hmCloseCard);
  document.getElementById('hmCardClose').addEventListener('click', hmCloseCard);
  document.getElementById('hmCardPrev').addEventListener('click', function(){ if (!hmCardList) return; hmCardI = (hmCardI - 1 + hmCardList.length) % hmCardList.length; hmFillCard(); hmDraw(); });
  document.getElementById('hmCardNext').addEventListener('click', function(){ if (!hmCardList) return; hmCardI = (hmCardI + 1) % hmCardList.length; hmFillCard(); hmDraw(); });
  document.getElementById('hmCardGo').addEventListener('click', function(){
    var c = hmCardList && hmCardList[hmCardI]; if (!c) return;
    hmCloseCard(); startNav(hmSpName(c.sp) + ' ' + c.cm + ' cm', c.px, c.py);
  });
  document.getElementById('hmCardLike').addEventListener('click', function(){
    var c = hmCardList && hmCardList[hmCardI]; if (!c) return;
    // Liknande (Kartanalys) with the catch as the place to compare with -- the heat map goes off
    anExtraRef = { id: 'catch:' + c.id, name: 'Fångst: ' + hmSpName(c.sp) + ' ' + c.cm + ' cm', by: c.who, lat: c.lat, lon: c.lon, type: 'mark' };
    hmSetOn(false); anLikeSpot(anExtraRef);
  });

  catchListeners.push(function(){
    hmHeatCache = null; hmRenderPanel(); hmDraw();
    if (hmPendingCard && catchData && catchData.list.length){       // (a catch that was open before a rotation)
      var ids = hmPendingCard.ids, L = hmAll().filter(function(c){ return ids.indexOf(c.id) >= 0; });
      L.sort(function(a, b){ return ids.indexOf(a.id) - ids.indexOf(b.id); });
      if (L.length) hmOpenCard(L, Math.min(hmPendingCard.i || 0, L.length - 1));
      hmPendingCard = null;
    }
  });
  window.__ffHeat = function(){
    return { on: hmOn, show: hmShow, style: hmSet.style, hexR: hmHexCells ? hmHexCells.rpx : null, panel: hmPanel.classList.contains('show'), pill: !hmPill.hidden, n: catchData ? hmVisible().length : null,
      hex: hmHexCells ? Object.keys(hmHexCells.cells).map(function(k){ var h = hmHexCells.cells[k]; return { n: h.list.length, x: h.x, y: h.y }; }) : null,
      card: hmCard.classList.contains('show') && hmCardList ? { i: hmCardI, n: hmCardList.length, id: hmCardList[hmCardI].id } : null };
  };
  window.__ffHeatScreen = function(id){ var c = hmAll().filter(function(x){ return x.id === id; })[0]; return c ? [originX + c.px * scale, originY + c.py * scale] : null; };
