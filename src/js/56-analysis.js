  /* ================= Kartanalys ("Hitta ställen") =================
     One place for every "map analysis": the button bottom right opens a panel; one
     filter at a time (or a preset that combines them). What matches is lit up, the
     rest of the map is toned down. Everything is worked out on the phone from the
     lake's depth grid (+ Genesis vegetation/hardness in bottom_v<V>.txt, + the wind
     from the weather). Shown/hidden with "Kartanalys" in Filter; the choice is
     remembered per lake. The presets are common fishing rules of thumb, not data. */
  var AN_KEY = lakeKey('ffmap_analysis_v1', 'analysis_v1');
  var SHOW_AN_KEY = 'ffmap_show_analysis_v1';
  var AN_MODES = [
    ['depth', 'Djup'], ['steep', 'Branta kanter'], ['tops', 'Grynnor & hålor'], ['veg', 'Växter'],
    ['hard', 'Hård botten'], ['wind', 'Vindkant']
  ];
  var AN_PRESETS = [
    ['abborre', 'Abborre', 'grynnor och kanter på 2–6 m, gärna nära hård botten'],
    ['gadda', 'Gädda', 'växtkanten på 1–4 m och vindkanten'],
    ['gos', 'Gös', 'branta kanter på 4–10 m nära hård botten']
  ];
  var AN_HARD = ['Mjuk', 'Medelhård', 'Hård', 'Mycket hård'];      // Genesis' 4 levels
  var AN_COLORS = { depth: null, steep: [255, 70, 200], tops: [255, 190, 40], veg: [90, 235, 80], hard: [240, 70, 10],
                    wind: [255, 178, 63], similar: [255, 80, 160], abborre: [255, 210, 26], gadda: [120, 255, 120], gos: [58, 134, 255],
                    c_abborre: [255, 122, 26], c_gadda: [53, 210, 74], c_gos: [58, 134, 255] };   // (c_ = from the catches: the species' colours)
  var AN_PLAIN = { depth: 1, steep: 1, tops: 1, veg: 1, hard: 1, wind: 1, combo: 1 };   // Kartdata: no colour, just the map shown through the mask
  // the depth scale of the sliders = the legend's (0 .. the lake's max depth, same colours)
  var AN_DMAX = parseFloat(String((LAKE.legendTicks || []).slice(-1)[0] || '').replace(',', '.')) || Math.ceil(LAKE.depth.max || 20);
  var AN_SIMF = [['d', 'Djup'], ['s', 'Lutning'], ['h', 'Botten'], ['v', 'Växter'], ['t', 'Grynna/håla']];
  var AN_SIMR = [0, 25, 50, 100];                       // m round the spot (0 = right under it)
  // how far a top rises above the lowest "saddle" towards anything higher (the h-dome, by
  // morphological reconstruction): f in cm, marker = f - H grown back under f; dome = f - rec.
  // Tops: f = -depth, land counts as HIGH (shore shelves belong to the shore, not tops).
  // Holes: f = depth, land counts as LOW. Bucket queue (whole cm): fast enough on the phone.
  function anDome(f, W, H, hcm){
    var N = W * H, rec = new Int32Array(N), lo = 1e9, hi = -1e9, i, p, q, v, x;
    for (i = 0; i < N; i++){ v = rec[i] = f[i] - hcm; if (v < lo) lo = v; if (v > hi) hi = v; }
    var bk = new Array(hi - lo + 1);
    for (i = 0; i < N; i++){ v = rec[i] - lo; (bk[v] || (bk[v] = [])).push(i); }
    for (var lv = hi - lo; lv >= 0; lv--){
      var qu = bk[lv]; if (!qu) continue; bk[lv] = null;
      for (var k = 0; k < qu.length; k++){
        p = qu[k]; if (rec[p] - lo !== lv) continue;
        x = p % W;
        for (var t = 0; t < 4; t++){
          q = t === 0 ? (x > 0 ? p - 1 : -1) : t === 1 ? (x < W - 1 ? p + 1 : -1) : t === 2 ? p - W : p + W;
          if (q < 0 || q >= N) continue;
          v = rec[p] < f[q] ? rec[p] : f[q];
          if (v > rec[q]){ rec[q] = v; if (v - lo === lv) qu.push(q); else (bk[v - lo] || (bk[v - lo] = [])).push(q); }
        }
      }
    }
    var d = new Float32Array(N); for (i = 0; i < N; i++) d[i] = (f[i] - rec[i]) / 100;
    return d;
  }
  var AN_HOLE_CORE = 0.6;            // a hole is drawn by its deepest 0.6 m (else a deep basin = one huge "hole")
  function anDomes(A){
    if (A.domeTop) return A;
    var N = A.N, ft = new Int32Array(N), fh = new Int32Array(N);
    for (var i = 0; i < N; i++){
      if (A.wat[i]){ ft[i] = -Math.round(A.sm[i] * 100); fh[i] = Math.round(A.sm[i] * 100); }
      else if (A.lake[i]){ ft[i] = -50; fh[i] = 50; }            // (lake without depth data: shallow)
      else { ft[i] = 500; fh[i] = -500; }                          // land: high for tops, low for holes
    }
    A.domeTop = anDome(ft, A.W, A.H, 300); A.domeHole = anDome(fh, A.W, A.H, 300);
    return A;
  }
  // "Storlek" (Heatmap and Kartanalys' "Från fångsterna"): min-max cm on one slider with two handles. The slider's ends are the
  // smallest / biggest fish in the data shown (rounded to 5 cm); a handle at its end = no limit that way. Its own range per species:
  // set.size[key] = [lo, hi] (0 / SIZE_NONE = no limit), no entry = all.
  var SIZE_NONE = 999;
  function sizeOf(set, key){ return (set.size && set.size[key]) || [0, SIZE_NONE]; }
  function sizeOk(r, c){ return (r[0] <= 0 || c.cm >= r[0]) && (r[1] >= SIZE_NONE || c.cm <= r[1]); }
  function sizeBounds(list){
    var cm = list.map(function(c){ return c.cm; }).filter(function(v){ return v > 0; });
    if (!cm.length) return null;
    var lo = Math.floor(Math.min.apply(null, cm) / 5) * 5, hi = Math.ceil(Math.max.apply(null, cm) / 5) * 5;
    return [lo, Math.max(hi, lo + 5)];
  }
  function sizeEff(r, b){ return [r[0] <= b[0] ? 0 : Math.min(r[0], b[1]), r[1] >= b[1] ? SIZE_NONE : Math.max(r[1], b[0])]; }   // (as the slider shows it)
  function sizeOn(r, b){ var e = b ? sizeEff(r, b) : r; return e[0] > 0 || e[1] < SIZE_NONE; }
  function sizeTxt(r, b){   // always the numbers on the slider: "85–90 cm" (the ends = the smallest / biggest fish)
    var e = sizeEff(r, b);
    return (e[0] || b[0]) + '–' + (e[1] >= SIZE_NONE ? b[1] : e[1]) + ' cm';
  }
  function sizeRow(r, b, key){
    if (!b) return '';
    var e = sizeEff(r, b), v = [e[0] || b[0], e[1] >= SIZE_NONE ? b[1] : e[1]];
    var pc = function(x){ return (100 * (x - b[0]) / (b[1] - b[0])) + '%'; };
    return '<div class="anRange"><label>Storlek</label><div class="sizeDual" data-k="' + key + '" data-lo="' + b[0] + '" data-hi="' + b[1] + '" style="--a:' + pc(v[0]) + ';--b:' + pc(v[1]) + '">' +
      [0, 1].map(function(i){ return '<input type="range" data-r="cm' + i + '" min="' + b[0] + '" max="' + b[1] + '" step="5" value="' + v[i] + '" aria-label="' + (i ? 'Största längd' : 'Minsta längd') + '">'; }).join('') +
      '</div><output>' + sizeTxt(r, b) + '</output></div>';
  }
  function sizeInput(e, set){   // a handle moved: true if it was one of these (the two never pass each other)
    var t = e.target, k = t.getAttribute && t.getAttribute('data-r');
    if (k !== 'cm0' && k !== 'cm1') return false;
    var d = t.parentNode, b = [+d.getAttribute('data-lo'), +d.getAttribute('data-hi')], ins = d.querySelectorAll('input');
    var a = +ins[0].value, z = +ins[1].value;
    if (a > z){ if (k === 'cm0') a = z; else z = a; }
    ins[0].value = a; ins[1].value = z;
    var r = [a <= b[0] ? 0 : a, z >= b[1] ? SIZE_NONE : z], key = d.getAttribute('data-k');
    set.size = set.size || {};
    if (sizeOn(r)) set.size[key] = r; else delete set.size[key];
    d.style.setProperty('--a', (100 * (a - b[0]) / (b[1] - b[0])) + '%'); d.style.setProperty('--b', (100 * (z - b[0]) / (b[1] - b[0])) + '%');
    d.nextSibling.textContent = sizeTxt(r, b);
    return true;
  }
  var anSet = { simF: { d: 1, s: 1, h: 1, v: 1, t: 1 }, simR: 0, mode: null, lo: 4, hi: 6, slope: 10, topP: 0.6, holeP: 0.8, hmin: 3, dim: 0.72, ref: null,
               cF: { d: 1, s: 1, h: 1, v: 1, l: 1, t: 1 }, cCov: 7, cView: 'area', size: {},   // (c* = "Från fångsterna", 57-an-catches.js)
               combo: [], near: { tops: 0, veg: 15, hard: 15, wind: 15 } };   // Kartdata combined (mode 'combo'): the parts, "inom … m"
  var AN_DEFAULTS = JSON.stringify(anSet);   // (for "Återställ")
  anSet.cat = 'map';                            // the category shown: map / rule / data / similar
  try { var sv = JSON.parse(localStorage.getItem(AN_KEY) || 'null'); if (sv) for (var k0 in sv) anSet[k0] = sv[k0]; } catch(e){}
  delete anSet.cm0; delete anSet.cm1;   // (the first Storlek, one range for all species)
  if (!rotState) anSet.mode = null;          // a new start of the app: off (turning the phone keeps it)
  var anShow = true;
  try { anShow = localStorage.getItem(SHOW_AN_KEY) !== '0'; } catch(e){}
  var anCanvas = document.getElementById('anLayer'), anCtx = anCanvas.getContext('2d');
  var anSatCanvas = document.getElementById('anSat'), anSatCtx = anSatCanvas.getContext('2d');
  var anPanel = document.getElementById('anPanel'), anBtn = document.getElementById('anBtn'), anLabelsEl = document.getElementById('anLabels'), anPill = document.getElementById('anPill');
  var AN = null, anBottom = null, anBottomLoading = false, anRes = null, anView = null, anVer = 0;
  function anSave(){ try { localStorage.setItem(AN_KEY, JSON.stringify(anSet)); } catch(e){} }

  // weighted box blur (only water counts), radius r cells, twice ~ gaussian
  function anBlur(val, wt, W, H, r){
    var a = new Float32Array(W * H), w = new Float32Array(W * H), i;
    for (i = 0; i < W * H; i++){ a[i] = val[i] * wt[i]; w[i] = wt[i]; }
    function pass(src, horiz){
      var out = new Float32Array(W * H), L1 = horiz ? W : H, L2 = horiz ? H : W;
      for (var b = 0; b < L2; b++){
        var s = 0;
        for (var q = -r; q < L1 + r; q++){
          var qi = q + r; if (qi < L1) s += src[horiz ? b * W + qi : qi * W + b];
          var qo = q - r - 1; if (qo >= 0 && qo < L1) s -= src[horiz ? b * W + qo : qo * W + b];
          if (q >= 0 && q < L1) out[horiz ? b * W + q : q * W + b] = s;
        }
      }
      return out;
    }
    for (var t = 0; t < 2; t++){ a = pass(pass(a, true), false); w = pass(pass(w, true), false); }
    var o = new Float32Array(W * H);
    for (i = 0; i < W * H; i++) o[i] = w[i] > 1e-6 ? a[i] / w[i] : 0;
    return o;
  }
  // the lake's grids: depth, water, slope (%), "higher/lower than around" (m), distance from land (m)
  function anBase(){
    if (AN) return AN;
    var g = loadDepthGrid(); if (!g) return null;
    var W = DEPTH_W, H = DEPTH_H, N = W * H, cell = WEB_METERS_PER_PX * IMG_W / W;
    var dep = new Float32Array(N), wat = new Uint8Array(N), lake = new Uint8Array(N), i, x, y;
    for (i = 0; i < N; i++){ var v = g[i]; lake[i] = v !== 255 ? 1 : 0; if (v <= 250){ wat[i] = 1; dep[i] = v * DEPTH_STEP; } }
    var sm = anBlur(dep, wat, W, H, Math.max(1, Math.round(4 / cell)));
    var slope = new Float32Array(N);
    for (y = 1; y < H - 1; y++) for (x = 1; x < W - 1; x++){
      i = y * W + x; if (!wat[i]) continue;
      var gx = (sm[i + 1] - sm[i - 1]) / (2 * cell), gy = (sm[i + W] - sm[i - W]) / (2 * cell);
      if (!wat[i + 1] || !wat[i - 1]) gx = 0;
      if (!wat[i + W] || !wat[i - W]) gy = 0;
      slope[i] = Math.sqrt(gx * gx + gy * gy) * 100;
    }
    var big = anBlur(dep, wat, W, H, Math.max(2, Math.round(28 / cell)));
    var tpi = new Float32Array(N);
    for (i = 0; i < N; i++) if (wat[i]) tpi[i] = big[i] - sm[i];       // + shallower than around, - deeper
    // distance from land (m): two-pass chamfer
    var dist = new Float32Array(N), INF = 1e9, D1 = cell, D2 = cell * 1.414;
    for (i = 0; i < N; i++) dist[i] = lake[i] ? INF : 0;
    for (y = 0; y < H; y++) for (x = 0; x < W; x++){ i = y * W + x; if (!dist[i]) continue; var m = dist[i];
      if (x > 0) m = Math.min(m, dist[i - 1] + D1); if (y > 0){ m = Math.min(m, dist[i - W] + D1); if (x > 0) m = Math.min(m, dist[i - W - 1] + D2); if (x < W - 1) m = Math.min(m, dist[i - W + 1] + D2); } dist[i] = m; }
    for (y = H - 1; y >= 0; y--) for (x = W - 1; x >= 0; x--){ i = y * W + x; if (!dist[i]) continue; var m2 = dist[i];
      if (x < W - 1) m2 = Math.min(m2, dist[i + 1] + D1); if (y < H - 1){ m2 = Math.min(m2, dist[i + W] + D1); if (x < W - 1) m2 = Math.min(m2, dist[i + W + 1] + D2); if (x > 0) m2 = Math.min(m2, dist[i + W - 1] + D2); } dist[i] = m2; }
    AN = { W: W, H: H, N: N, cell: cell, dep: dep, wat: wat, lake: lake, sm: sm, slope: slope, tpi: tpi, shore: dist };
    return AN;
  }
  // vegetation (bit 3) + hardness 1..4 (bits 0-2) per depth cell, from Genesis (fetched when first needed)
  function anLoadBottom(){
    if (anBottom || anBottomLoading || !LAKE.bottom || typeof fetch !== 'function') return;
    anBottomLoading = true;
    fetch(lakeUrl(LAKE_DIR + LAKE.bottom.file)).then(function(r){ return r.ok ? r.text() : null; }).then(function(t){
      anBottomLoading = false; if (!t) return;
      var bin = atob(t.trim()), b = new Uint8Array(DEPTH_W * DEPTH_H), j = 0;
      for (var i = 0; i < bin.length && j < b.length; i++){
        var v = bin.charCodeAt(i);
        if (v === 250){ j += bin.charCodeAt(i + 1) | (bin.charCodeAt(i + 2) << 8); i += 2; }
        else b[j++] = v;
      }
      anBottom = b; anCompute();
      if (typeof editingWpInfo !== 'undefined' && editingWpInfo && wpSheet.classList.contains('show')) refreshSheetMeta();
    }).catch(function(){ anBottomLoading = false; });
  }
  function anNeedsBottom(m){ return (m && m.indexOf('c_') === 0) || m === 'veg' || m === 'hard' || m === 'similar' || m === 'abborre' || m === 'gadda' || m === 'gos' ||
    (m === 'combo' && (anSet.combo.indexOf('veg') >= 0 || anSet.combo.indexOf('hard') >= 0)); }
  // connected groups of cells (4-neighbours) of a mask
  function anBlobs(mask, W, H){
    var lab = new Int32Array(W * H), out = [], st = [];
    for (var s = 0; s < W * H; s++){
      if (!mask[s] || lab[s]) continue;
      var id = out.length + 1, cells = []; lab[s] = id; st.push(s);
      while (st.length){ var c = st.pop(); cells.push(c); var cx = c % W;
        if (cx > 0 && mask[c - 1] && !lab[c - 1]){ lab[c - 1] = id; st.push(c - 1); }
        if (cx < W - 1 && mask[c + 1] && !lab[c + 1]){ lab[c + 1] = id; st.push(c + 1); }
        if (c >= W && mask[c - W] && !lab[c - W]){ lab[c - W] = id; st.push(c - W); }
        if (c < W * (H - 1) && mask[c + W] && !lab[c + W]){ lab[c + W] = id; st.push(c + W); } }
      out.push(cells);
    }
    return out;
  }
  function anNear(mask, W, H, r){       // cells within r cells of the mask (square)
    var o = new Uint8Array(W * H), rows = new Uint8Array(W * H), x, y, k;
    for (y = 0; y < H; y++){ var last = -1e9;
      for (x = 0; x < W; x++){ if (mask[y * W + x]) last = x; if (x - last <= r) rows[y * W + x] = 1; }
      last = 1e9; for (x = W - 1; x >= 0; x--){ if (mask[y * W + x]) last = x; if (last - x <= r) rows[y * W + x] = 1; } }
    for (x = 0; x < W; x++){ var l2 = -1e9;
      for (y = 0; y < H; y++){ if (rows[y * W + x]) l2 = y; if (y - l2 <= r) o[y * W + x] = 1; }
      l2 = 1e9; for (y = H - 1; y >= 0; y--){ if (rows[y * W + x]) l2 = y; if (l2 - y <= r) o[y * W + x] = 1; } }
    return o;
  }
  function anVegEdge(A, lo, hi){
    var W = A.W, N = A.N, veg = new Uint8Array(N), e = new Uint8Array(N), i;
    for (i = 0; i < N; i++) veg[i] = (anBottom[i] & 8) && A.wat[i] ? 1 : 0;
    var open = new Uint8Array(N); for (i = 0; i < N; i++) open[i] = A.wat[i] && !veg[i] ? 1 : 0;
    var nearOpen = anNear(open, W, A.H, Math.max(1, Math.round(6 / A.cell)));
    for (i = 0; i < N; i++) e[i] = veg[i] && nearOpen[i] && A.dep[i] >= lo && A.dep[i] <= hi ? 1 : 0;
    return { edge: e, veg: veg };
  }
  function anHardNear(A, m){
    var hard = new Uint8Array(A.N), any = false;
    for (var i = 0; i < A.N; i++) if ((anBottom[i] & 7) >= 3 && A.wat[i]){ hard[i] = 1; any = true; }
    return any ? anNear(hard, A.W, A.H, Math.max(1, Math.round(m / A.cell))) : null;
  }
  function anWindEdge(A){
    var w = windNow(), R = routeGrid && routeGrid() ? RT : null;
    if (!w || !R) return null;
    var a = w.from * Math.PI / 180, dx = Math.sin(a), dy = -Math.cos(a), up = new Float32Array(R.w * R.h), dn = new Float32Array(R.w * R.h);
    [[dx, dy, up], [-dx, -dy, dn]].forEach(function(t){
      for (var cy = 0; cy < R.h; cy++) for (var cx = 0; cx < R.w; cx++){
        var i = cy * R.w + cx; if (!R.water[i]) continue;
        var s = 1;
        for (; s < 120; s++){ var x = Math.round(cx + t[0] * s), y = Math.round(cy + t[1] * s); if (x < 0 || y < 0 || x >= R.w || y >= R.h || !R.water[y * R.w + x]) break; }
        t[2][i] = s * R.cellM;
      }
    });
    var out = new Uint8Array(A.N);
    for (var y = 0; y < A.H; y++) for (var x = 0; x < A.W; x++){
      var i2 = y * A.W + x; if (!A.wat[i2]) continue;
      var rx = Math.min(R.w - 1, Math.floor(x / R.rf)), ry = Math.min(R.h - 1, Math.floor(y / R.rf)), ri = ry * R.w + rx;
      if (R.water[ri] && up[ri] > 300 && dn[ri] < 60) out[i2] = 1;
    }
    return { mask: out, from: w.from, ms: w.ms };
  }
  // the things "Liknande" compares, per cell -- right under (r = 0) or averaged over r m round each cell
  var anSimCache = {};
  function anSimFeatures(A, rm){
    if (anSimCache[rm] && anSimCache[rm].A === A && anSimCache[rm].b === !!anBottom) return anSimCache[rm];
    var N = A.N, veg = new Float32Array(N), hard = new Float32Array(N), hw = new Float32Array(N), sl = new Float32Array(N), i;
    for (i = 0; i < N; i++){ var bt = anBottom ? anBottom[i] : 0; veg[i] = (bt & 8) ? 1 : 0; hard[i] = bt & 7; hw[i] = (bt & 7) ? 1 : 0; sl[i] = Math.min(40, A.slope[i]); }
    var F;
    if (!rm) F = { d: A.sm, s: sl, t: A.tpi, v: veg, h: hard };
    else {
      var r = Math.max(1, Math.round(rm / A.cell)), wt = new Float32Array(N);
      for (i = 0; i < N; i++) wt[i] = A.wat[i];
      var hm = anBlur(hard, hw, A.W, A.H, r);        // (hardness: only where it's measured)
      F = { d: anBlur(A.sm, wt, A.W, A.H, r), s: anBlur(sl, wt, A.W, A.H, r), t: anBlur(A.tpi, wt, A.W, A.H, r), v: anBlur(veg, wt, A.W, A.H, r), h: hm };
    }
    F.A = A; F.b = !!anBottom; anSimCache[rm] = F;
    return F;
  }
  function anCellOfImg(x, y){ var A = AN; return Math.min(A.H - 1, Math.max(0, Math.floor(y / IMG_H * A.H))) * A.W + Math.min(A.W - 1, Math.max(0, Math.floor(x / IMG_W * A.W))); }
  function anImgOfCell(i){ var A = AN; return { x: ((i % A.W) + 0.5) / A.W * IMG_W, y: (Math.floor(i / A.W) + 0.5) / A.H * IMG_H }; }
  var anExtraRef = null;     // a place to compare with that isn't a spot (a catch from the heat map)
  function anSpots(){
    return (anExtraRef ? [anExtraRef] : []).concat(waypoints.filter(function(w){ var t = wpType(w); return t !== 'meet' && t !== 'fara' && t !== 'hem' && !isExpired(w); })
      .sort(function(a, b){ return (isMine(b) ? 1 : 0) - (isMine(a) ? 1 : 0); }));
  }
  // the chosen filter -> a mask (1 = main colour, 2 = second colour), labels and a result text
  function anCompute(){
    anRes = null; anVer++;
    var m = anSet.mode, A = anBase();
    if (m && A && anNeedsBottom(m) && !anBottom){ anLoadBottom(); if (!anBottom){ anRes = { wait: true }; anRender(); return; } }
    if (!m || !A){ anRender(); return; }
    var r = m === 'combo' ? anCombo(A) : anOne(m, A, {});
    anRes = { M: r.empty ? null : r.M, n: r.n, labels: r.labels, list: r.list, text: r.text, note: r.note, color: m === 'combo' ? null : AN_COLORS[m], ver: anVer, G: r.G || null, pts: r.pts || null };
    anRender();
  }
  // Kartdata combined: what's lit = where ALL the parts are true. The "spots" (grynnor/hålor, växter, hård
  // botten, vindkant) count within "inom … m" of them. Only Djup has a depth range (Branta kanter / Hård botten
  // are the whole lake -- add Djup to narrow them). The lit area shows the map's own colours (like Djup).
  var AN_NEAR = { tops: 1, veg: 1, hard: 1, wind: 1 };
  function anName(k){ return (AN_MODES.filter(function(x){ return x[0] === k; })[0] || [k, k])[1]; }
  function anCombo(A){
    var parts = anSet.combo, N = A.N, M = new Uint8Array(N), i, n = 0, labels = [], steps = [], zero = null;
    for (i = 0; i < N; i++) if (A.wat[i]) M[i] = 1;
    for (var p = 0; p < parts.length; p++){
      var k = parts[p], r = anOne(k, A), mk = r.M, d = anSet.near[k] || 0;
      if (r.empty || !mk) return { M: null, n: 0, labels: [], text: r.text, note: r.note, empty: true };   // (e.g. no wind yet)
      if (AN_NEAR[k] && d > 0){ var b = new Uint8Array(N); for (i = 0; i < N; i++) b[i] = mk[i] ? 1 : 0; mk = anNear(b, A.W, A.H, Math.max(1, Math.round(d / A.cell))); }
      n = 0; for (i = 0; i < N; i++){ if (M[i] && !mk[i]) M[i] = 0; if (M[i]) n++; }
      steps.push((p ? '+ ' : '') + anName(k) + (AN_NEAR[k] ? (d ? ' inom ' + d + ' m' : ' (exakt)') : '') + ': ' + anPct(n));
      if (k === 'tops') labels = r.labels;
      if (!n && !zero) zero = k;
    }
    labels = labels.filter(function(l){ return M[l.i]; });
    var text = n ? parts.map(anName).join(' + ') + ' · <b>' + anPct(n) + '</b> av sjön'
      : 'Inget kvar – <b>' + anName(zero) + '</b> tar bort det sista. ' + (AN_NEAR[zero] ? 'Prova större avstånd (inom … m).' : 'Prova att ändra dess reglage.');
    return { M: M, n: n, labels: labels, text: text, note: steps.join(' → '), empty: false };
  }
  // one filter (or a rule of thumb / the catches / Liknande) -> a mask (1 = main colour, 2 = second colour),
  // labels and a result text.
  function anOne(m, A){
    var N = A.N, M = new Uint8Array(N), i, n = 0, labels = [], list = null, text = '', note = '';
    var wat = A.wat, dep = A.dep;
    if (m === 'depth'){
      for (i = 0; i < N; i++) if (wat[i] && dep[i] >= anSet.lo && dep[i] <= anSet.hi){ M[i] = 1; n++; }
      text = '<b>' + fmtDepth(anSet.lo) + '–' + fmtDepth(anSet.hi) + ' m</b> · ' + anPct(n) + ' av sjön';   // (as the mock-up)
    } else if (m === 'steep'){
      for (i = 0; i < N; i++) if (wat[i] && A.slope[i] >= anSet.slope){ M[i] = 1; n++; }
      text = 'Lutning över <b>' + anSet.slope + ' %</b> · ' + anPct(n) + ' av sjön';
    } else if (m === 'tops'){
      anDomes(A);
      // the "caps" of the tops (and the bottoms of the holes), then only those that rise (sink)
      // at least the chosen number of metres above (below) their saddle
      var capT = new Uint8Array(N), capH = new Uint8Array(N);
      for (i = 0; i < N; i++){ if (!wat[i] || A.shore[i] < 10) continue;
        if (A.domeTop[i] >= 0.25) capT[i] = 1; else if (A.domeHole[i] >= 0.25) capH[i] = 1; }
      var tb = anBlobs(capT, A.W, A.H).map(function(c){ var best = c[0], p = 0; c.forEach(function(j){ if (A.domeTop[j] > p) p = A.domeTop[j]; if (dep[j] < dep[best]) best = j; }); return { c: c, i: best, p: p }; })
        .filter(function(b){ return b.p >= anSet.topP; }).sort(function(a, b){ return b.p - a.p; });
      var hb = anBlobs(capH, A.W, A.H).map(function(c){ var best = c[0], p = 0; c.forEach(function(j){ if (A.domeHole[j] > p) p = A.domeHole[j]; if (dep[j] > dep[best]) best = j; }); return { c: c, i: best, p: p }; })
        .filter(function(b){ return b.p >= anSet.holeP; }).sort(function(a, b){ return b.p - a.p; });
      tb.forEach(function(b, k){ b.c.forEach(function(j){ M[j] = 1; }); if (k < 14) labels.push({ i: b.i, cls: '', txt: fmtDepth(dep[b.i]) + ' m' }); });
      hb.forEach(function(b, k){ b.c.forEach(function(j){ if (A.domeHole[j] >= Math.max(0.25, b.p - AN_HOLE_CORE)) M[j] = 2; }); if (k < 8) labels.push({ i: b.i, cls: 'hole', txt: fmtDepth(dep[b.i]) + ' m' }); });
      text = '<b>' + tb.length + '</b> grynnor (reser sig minst ' + fmtDepth(anSet.topP) + ' m) · <b>' + hb.length + '</b> hålor (minst ' + fmtDepth(anSet.holeP) + ' m djupa)';
      note = '<b>Grynna</b> = ett grundare ställe ute i sjön som reser sig minst ' + fmtDepth(anSet.topP) + ' m över den lägsta "sadeln" runt den – där det sluttar ner åt alla håll. Grunda hyllor längs land räknas inte. ' +
        '<b>Håla</b> = en grop som går minst ' + fmtDepth(anSet.holeP) + ' m under kanten runt den; bara gropens djupaste del (0,6 m) visas. Siffran = djupet där grynnan är grundast / hålan djupast. Tryck på en etikett för lodet.';
    } else if (m === 'veg'){
      for (i = 0; i < N; i++) if ((anBottom[i] & 8) && wat[i]){ M[i] = 1; n++; }
      text = n ? '<b>Växter</b> (vass, näckrosor, bottenväxter) · ' + anPct(n) + ' av sjön' : 'Ingen växtlighet mätt här.';
      note = 'Där ekolodet sett växtlighet (Genesis). Kanten mot öppet vatten är ofta bäst.';
    } else if (m === 'hard'){
      var meas = 0;
      for (i = 0; i < N; i++){ var hv = anBottom[i] & 7; if (hv) meas++; if (hv >= anSet.hmin && wat[i]){ M[i] = 1; n++; } }
      text = n ? '<b>' + AN_HARD[anSet.hmin - 1] + '</b> botten eller hårdare · ' + anPct(n) + ' av sjön' : 'Ingen sådan botten mätt här.';
      note = 'Bara där ekolodet mätt hårdhet (' + anPct(meas) + ' av sjön).';
    } else if (m === 'wind'){
      var we = anWindEdge(A);
      if (!we){ text = 'Väntar på vinden (väder)…'; }
      else { for (i = 0; i < N; i++) if (we.mask[i]){ M[i] = 1; n++; }
        text = 'Vinden <b>' + wxNum(we.ms) + ' m/s från ' + wxCompass(we.from) + '</b> – där vågorna trycker in mot stranden'; note = 'Motsatsen till lä: maten driver dit.'; }
    } else if (m === 'similar'){
      var spots = anSpots(), ref = spots.filter(function(w){ return w.id === anSet.ref; })[0] || spots[0];
      if (!ref){ text = 'Spara en fiskeplats först – sedan letar appen upp liknande ställen.'; }
      else {
        anSet.ref = ref.id;
        var rp = latLonToImgPx(ref.lat, ref.lon), ri = anCellOfImg(rp.x, rp.y);
        var F = anSimFeatures(A, anSet.simR), use = AN_SIMF.filter(function(x){ return anSet.simF[x[0]]; }).map(function(x){ return x[0]; });
        var SC = { d: 1.5, s: 5, h: 0.8, v: 0.3, t: 0.8 }, r0 = {};
        use.forEach(function(k){ r0[k] = F[k][ri]; });
        var sim = new Float32Array(N), vals = [];
        for (i = 0; i < N; i++){ if (!wat[i]) continue; var d2 = 0; for (var q = 0; q < use.length; q++){ var kk = use[q], dd = (F[kk][i] - r0[kk]) / SC[kk]; d2 += dd * dd; } sim[i] = use.length ? Math.exp(-d2) : 0; vals.push(sim[i]); }
        vals.sort(function(a, b){ return b - a; });
        var th = Math.max(0.3, vals[Math.floor(vals.length * 0.04)] || 1);
        var rx = ri % A.W, ry = Math.floor(ri / A.W), away = 60 / A.cell;
        for (i = 0; i < N; i++) if (sim[i] >= th){ M[i] = 1; n++; }          // (the spot's own surroundings lit too)
        // the list: the areas ranked by their most similar place (tiny ones count a bit less),
        // not the spot itself (anything within 60 m of it)
        var blobs = anBlobs(M, A.W, A.H).filter(function(c){ return !c.some(function(j){ var xx = j % A.W - rx, yy = Math.floor(j / A.W) - ry; return xx * xx + yy * yy <= away * away; }); })
          .map(function(c){ var best = c[0]; c.forEach(function(j){ if (sim[j] > sim[best]) best = j; }); return { c: c, i: best, s: sim[best] * Math.min(1, c.length / 6) }; })
          .sort(function(a, b){ return b.s - a.s; }).slice(0, 5);
        labels.push({ i: ri, cls: 'simRef', txt: '' });
        list = blobs.map(function(b, k){
          var p = anImgOfCell(b.i), ll = imgPxToLatLon(p.x, p.y), dm = null;
          if (lastOwnLatLon && lastFix && lastFix.onMap) dm = haversineKm(lastOwnLatLon.lat, lastOwnLatLon.lon, ll.lat, ll.lon) * 1000;
          labels.push({ i: b.i, cls: 'sim', txt: String(k + 1) });
          return { n: k + 1, x: p.x, y: p.y, dep: dep[b.i], slope: A.slope[b.i], dm: dm };
        });
        text = use.length ? 'Som <b>' + escHtml(ref.name || 'platsen') + '</b>' + (anSet.simR ? ' (inom ' + anSet.simR + ' m)' : '') + ': ' +
          use.map(function(k){ return k === 'd' ? fmtDepth(r0.d) + ' m' : k === 's' ? 'lutning ' + Math.round(r0.s) + ' %' : k === 'h' ? (r0.h >= 0.5 ? AN_HARD[Math.min(3, Math.round(r0.h) - 1)] || 'mjuk' : 'botten ej mätt').toLowerCase() + ' botten'
            : k === 'v' ? 'växter ' + Math.round(r0.v * 100) + ' %' : (r0.t >= 0.6 ? 'grynna' : r0.t <= -0.8 ? 'håla' : 'jämn botten'); }).join(', ').replace('botten ej mätt botten', 'botten ej mätt')
          : 'Välj minst en sak att jämföra.';
      }
    } else if (m.indexOf('c_') === 0){                    // from the catches (data), 57-an-catches.js
      var cr = anCatchCompute(A, m.slice(2), M);
      n = cr.n; text = cr.text; note = cr.note; var cG = cr.G, cPts = cr.pts, cEmpty = cr.empty;
    } else {                                             // presets (rules of thumb)
      var hn, e2;
      if (m === 'abborre'){
        hn = anHardNear(A, 20);
        for (i = 0; i < N; i++) if (wat[i] && dep[i] >= 2 && dep[i] <= 6 && (A.slope[i] >= 8 || (A.tpi[i] >= 0.6 && A.shore[i] >= 15)) && (!hn || hn[i])){ M[i] = 1; n++; }
      } else if (m === 'gadda'){
        e2 = anVegEdge(A, 1, 4); var wd = anWindEdge(A);
        for (i = 0; i < N; i++) if (e2.edge[i] || (wd && wd.mask[i])){ M[i] = 1; n++; }
      } else if (m === 'gos'){
        hn = anHardNear(A, 15);
        for (i = 0; i < N; i++) if (wat[i] && dep[i] >= 4 && dep[i] <= 10 && A.slope[i] >= 8 && (!hn || hn[i])){ M[i] = 1; n++; }
      }
      var pr = AN_PRESETS.filter(function(x){ return x[0] === m; })[0];
      text = '<b>' + pr[1] + ':</b> ' + pr[2] + ' · ' + anPct(n) + ' av sjön';
      note = 'Tumregler från vanliga fiskeråd – inte fångstdata. Fisken läser inte kartan 🙂';
    }
    var empty = (m === 'similar' && !list) || (m === 'wind' && !n && !note) || !!cEmpty;
    return { M: M, n: n, labels: labels, list: list, text: text, note: note, empty: empty, G: cG, pts: cPts };
  }
  function anPct(n){ var w = 0, A = AN; for (var i = 0; i < A.N; i++) w += A.wat[i]; var p = 100 * n / Math.max(1, w); return (p < 1 && p > 0 ? '<1' : Math.round(p)) + ' %'; }
  function escHtml(t){ return String(t).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;'); }
  // Smooth versions of the found areas (and the lake), for drawing. The areas are yes/no per grid
  // cell: drawn straight from that, their edges came out beaded / stair-stepped -- worst zoomed out
  // and while panning, when each drawn point covers several cells and moves over them. The lee
  // never had that: it's drawn from a smooth field. So the same here: halve the grid (averaging)
  // until a cell is about one drawn point, then soften with a 1-2-1 filter. Cached per result and
  // level; the edge is then found in this smooth field exactly like the lee's.
  var anPyrBox = { p: null };          // (one cache per user: Kartanalys here, the heat map's shore line its own)
  function anField(R, A, lv, box){
    box = box || anPyrBox;
    if (!box.p || box.p.ver !== R.ver || box.p.A !== A){
      var N0 = A.W * A.H, f0 = [new Float32Array(N0), new Float32Array(N0), new Float32Array(N0), R.G ? new Float32Array(R.G) : new Float32Array(N0)];
      for (var i0 = 0; i0 < N0; i0++){ var v0 = R.M[i0]; if (v0 === 1) f0[0][i0] = 1; else if (v0 === 2) f0[1][i0] = 1; if (A.lake[i0]) f0[2][i0] = 1; }
      box.p = { ver: R.ver, A: A, raw: [{ w: A.W, h: A.H, f: f0 }], soft: [] };
    }
    var P = box.p;
    while (P.raw.length <= lv){
      var pr = P.raw[P.raw.length - 1], w2 = Math.ceil(pr.w / 2), h2 = Math.ceil(pr.h / 2), g = [];
      if (pr.w < 4 || pr.h < 4){ lv = P.raw.length - 1; break; }
      for (var c = 0; c < 4; c++){
        var src = pr.f[c], dst = new Float32Array(w2 * h2);
        for (var y = 0; y < h2; y++) for (var x = 0; x < w2; x++){
          var s = 0, n = 0;
          for (var dy = 0; dy < 2; dy++){ var yy = 2 * y + dy; if (yy >= pr.h) continue;
            for (var dx = 0; dx < 2; dx++){ var xx = 2 * x + dx; if (xx >= pr.w) continue; s += src[yy * pr.w + xx]; n++; } }
          dst[y * w2 + x] = s / n;
        }
        g.push(dst);
      }
      P.raw.push({ w: w2, h: h2, f: g });
    }
    if (!P.soft[lv]){
      var r0 = P.raw[lv], w = r0.w, h = r0.h, out = [];
      for (var c2 = 0; c2 < 4; c2++){
        var a = r0.f[c2], t = new Float32Array(w * h), o = new Float32Array(w * h);
        for (var y1 = 0; y1 < h; y1++) for (var x1 = 0; x1 < w; x1++){ var j = y1 * w + x1; t[j] = (a[x1 > 0 ? j - 1 : j] + 2 * a[j] + a[x1 < w - 1 ? j + 1 : j]) / 4; }
        for (var y2 = 0; y2 < h; y2++) for (var x2 = 0; x2 < w; x2++){ var j2 = y2 * w + x2; o[j2] = (t[y2 > 0 ? j2 - w : j2] + 2 * t[j2] + t[y2 < h - 1 ? j2 + w : j2]) / 4; }
        out.push(o);
      }
      P.soft[lv] = { w: w, h: h, f: out, lv: lv };
    }
    return P.soft[lv];
  }
  // draw: toned down outside, lit (+ a light edge) inside; per screen point like the lee
  function anDraw(){
    shoreDraw();                              // (Strandlinje on the plain map, 68-heatmap.js: off while this shows)
    var dpr = window.devicePixelRatio || 1, W = stage.clientWidth, H = stage.clientHeight;
    var on = anShow && anSet.mode && anRes && anRes.M;
    anCanvas.classList.toggle('on', !!on); anSatCanvas.classList.toggle('on', !!on);
    anLabelsEl.style.display = on ? '' : 'none';
    if (!on) return;
    [anCanvas, anSatCanvas].forEach(function(c){ if (c.width !== Math.round(W * dpr) || c.height !== Math.round(H * dpr)){ c.width = Math.round(W * dpr); c.height = Math.round(H * dpr); } });
    anCtx.setTransform(dpr, 0, 0, dpr, 0, 0); anCtx.clearRect(0, 0, W, H);
    anSatCtx.setTransform(dpr, 0, 0, dpr, 0, 0); anSatCtx.clearRect(0, 0, W, H);
    if (!(W >= 2 && H >= 2)) return;          // (mid-rotation the map can be 0 px for a moment)
    var STEP = viewStep(W, H), vw = Math.ceil(W / STEP), vh = Math.ceil(H / STEP), A = AN, R = anRes;
    var key = originX.toFixed(1) + ',' + originY.toFixed(1) + ',' + scale.toFixed(5) + ',' + W + 'x' + H + ',' + R.ver + ',' + anSet.dim + ',' + STEP;
    if (!anView || anView.key !== key){
      var cv = anView ? anView.cv : document.createElement('canvas'), sv = anView ? anView.sv : document.createElement('canvas');
      [cv, sv].forEach(function(c){ if (c.width !== vw || c.height !== vh){ c.width = vw; c.height = vh; } });
      var c2 = cv.getContext('2d'), im = c2.createImageData(vw, vh), px = im.data, col = R.color;
      var s2 = sv.getContext('2d'), sm = s2.createImageData(vw, vh), sp = sm.data;
      var dimA = Math.round(255 * anSet.dim), satA = Math.round(255 * Math.min(1, anSet.dim + 0.2));
      var N2 = vw * vh, f1 = new Float32Array(N2), f2 = new Float32Array(N2), fl = new Float32Array(N2);
      // the smooth field at the level where a cell is about one drawn point (see anField)
      var cpp = A.W / IMG_W / scale * STEP, want = Math.max(0, Math.round(Math.log(Math.max(1, cpp)) / Math.LN2));
      var Lf = anField(R, A, want), LW2 = Lf.w, LH2 = Lf.h, g1 = Lf.f[0], g2 = Lf.f[1], gl = Lf.f[2], g3 = Lf.f[3], f3 = R.G ? new Float32Array(N2) : null;
      var kx = A.W / IMG_W / (1 << Lf.lv), ky = A.H / IMG_H / (1 << Lf.lv);
      for (var y = 0; y < vh; y++) for (var x = 0; x < vw; x++){
        var ix = (x * STEP + 1 - originX) / scale, iy = (y * STEP + 1 - originY) / scale;
        var fx = ix * kx - 0.5, fy = iy * ky - 0.5, x0 = Math.floor(fx), y0 = Math.floor(fy), tx = fx - x0, ty = fy - y0;
        var a1 = 0, a2 = 0, al = 0, a3 = 0, q = y * vw + x;
        for (var dy = 0; dy <= 1; dy++) for (var dx = 0; dx <= 1; dx++){
          var cx = x0 + dx, cy = y0 + dy, wt = (dx ? tx : 1 - tx) * (dy ? ty : 1 - ty);
          if (cx < 0 || cy < 0 || cx >= LW2 || cy >= LH2) continue;
          var ci = cy * LW2 + cx;
          a1 += g1[ci] * wt; a2 += g2[ci] * wt; al += gl[ci] * wt; if (f3) a3 += g3[ci] * wt;
        }
        f1[q] = a1; f2[q] = a2; fl[q] = al; if (f3) f3[q] = a3;
      }
      // signed distance (in steps) from the 0,5 edge of a field: value / slope
      function sd(f, q, x, y){
        var gx = (f[x < vw - 1 ? q + 1 : q] - f[x > 0 ? q - 1 : q]) / 2, gy = (f[y < vh - 1 ? q + vw : q] - f[y > 0 ? q - vw : q]) / 2;
        return (f[q] - 0.5) / (Math.sqrt(gx * gx + gy * gy) + 1e-3);
      }
      function cl(v){ return v < 0 ? 0 : v > 1 ? 1 : v; }
      var EA = edgeW(STEP, 1.1), ES = edgeW(STEP, 0.9);     // (line widths: see edgeW)
      var plain = !!AN_PLAIN[anSet.mode], c1col = col, c2col = anSet.mode === 'tops' ? [60, 200, 255] : [70, 200, 60], c2a = anSet.mode !== 'tops' ? 60 : 105;
      for (var y2 = 0; y2 < vh; y2++) for (var x2 = 0; x2 < vw; x2++){
        var q2 = y2 * vw + x2, k = q2 * 4;
        var d1 = sd(f1, q2, x2, y2), d2 = sd(f2, q2, x2, y2), dl = sd(fl, q2, x2, y2);
        // (a found bit smaller than a drawn point is under 0,5 in the smooth field: shown faintly, not lost)
        var k1 = Math.max(cl(0.5 + d1), 0.8 * f1[q2]), k2 = Math.max(cl(0.5 + d2), 0.8 * f2[q2]), k0 = cl(1 - k1 - k2);
        // "over" in order: toned down, the found area(s), their white edge, the dashed shore
        var r = 0, g = 0, b = 0, a = 0;
        function over(cr, cg, cb, ca){ ca /= 255; r = cr * ca + r * (1 - ca); g = cg * ca + g * (1 - ca); b = cb * ca + b * (1 - ca); a = ca + a * (1 - ca); }
        over(6, 14, 20, dimA * k0);
        // "Skala" (from the catches): the whole lake from unlike (blue, see-through) to most alike (red)
        var ra = 0;
        if (f3 && fl[q2] > 0.05){ var rc = hmRamp(Math.max(0, Math.min(1, f3[q2] / fl[q2]))); ra = rc[3] / 255 * Math.min(1, fl[q2] * 1.6); over(rc[0], rc[1], rc[2], 255 * ra); }
        if (!plain){
          if (c1col) over(c1col[0], c1col[1], c1col[2], 105 * k1);
          over(c2col[0], c2col[1], c2col[2], c2a * k2);
        }
        var e = Math.max(cl(1 - Math.abs(d1) / EA[0]), cl(1 - Math.abs(d2) / EA[0])) * EA[1];
        if (e > 0) over(255, 255, 255, 180 * e);        // (as thin and soft as the lee's edge)
        var es = cl(1 - Math.abs(dl) / ES[0]) * ES[1];
        if (es > 0) over(255, 255, 255, 128 * es);      // the shore: a solid line, 50 %
        if (a > 0){ px[k] = r / a; px[k + 1] = g / a; px[k + 2] = b / a; px[k + 3] = a * 255; }
        sp[k] = 128; sp[k + 1] = 128; sp[k + 2] = 128; sp[k + 3] = satA * k0 * (1 - ra);
      }
      c2.putImageData(im, 0, 0); s2.putImageData(sm, 0, 0);
      anView = { key: key, cv: cv, sv: sv };
    }
    anCtx.imageSmoothingEnabled = true; anSatCtx.imageSmoothingEnabled = true;
    anCtx.drawImage(anView.cv, 0, 0, vw * STEP, vh * STEP);
    anSatCtx.drawImage(anView.sv, 0, 0, vw * STEP, vh * STEP);
    // from the catches: the catches it's worked out from, small white dots
    if (R.pts) R.pts.forEach(function(p){
      var x = originX + p.x * scale, y = originY + p.y * scale; if (x < -5 || y < -5 || x > W + 5 || y > H + 5) return;
      anCtx.beginPath(); anCtx.arc(x, y, 2.6, 0, 7); anCtx.fillStyle = '#fff'; anCtx.fill(); anCtx.lineWidth = 1; anCtx.strokeStyle = 'rgba(28,33,44,.9)'; anCtx.stroke();
    });
    // labels (tops/holes, similar places)
    Array.prototype.forEach.call(anLabelsEl.children, function(el){
      var p = anImgOfCell(+el.getAttribute('data-i'));
      el.style.left = (originX + p.x * scale) + 'px'; el.style.top = (originY + p.y * scale) + 'px';
    });
  }
  function anRender(){
    // chips + controls + result, labels; then draw
    var m = anSet.mode;
    anBtn.classList.toggle('on', !!m);
    anPill.hidden = !(m && anShow);                        // (the pill under the weather: something is shown on the map)
    document.getElementById('anClear').disabled = !m;      // (only when there's something to clear)
    anDataRow();
    var cat = anSet.cat || 'map';
    Array.prototype.forEach.call(document.querySelectorAll('#anCatSeg button'), function(b){ b.classList.toggle('on', b.getAttribute('data-cat') === cat); b.classList.toggle('has', b.getAttribute('data-cat') === anCatOf(m) && cat !== anCatOf(m)); });
    document.getElementById('anChips').hidden = cat !== 'map';
    document.getElementById('anPresets').hidden = cat !== 'rule';
    document.getElementById('anDataChips').hidden = cat !== 'data';
    document.getElementById('anReset').disabled = anIsDefault();
    Array.prototype.forEach.call(document.querySelectorAll('#anChips button[data-m], #anPresets button[data-m], #anDataChips button[data-m]'), function(b){
      var on = b.getAttribute('data-m') === m || (m === 'combo' && anSet.combo.indexOf(b.getAttribute('data-m')) >= 0);
      b.classList.toggle('on', on); if (b.parentNode.id === 'anChips') b.setAttribute('aria-pressed', on ? 'true' : 'false'); });
    document.getElementById('anChips').classList.toggle('combo', m === 'combo');   // ("+ Djup", "+ Branta kanter": they work together)
    var R = anRes, res = document.getElementById('anResult'), lst = document.getElementById('anListBox');
    lst.innerHTML = '';
    if (!m) res.innerHTML = { map: 'Välj vad du vill hitta på kartan. Det som matchar lyser, resten tonas ner.', rule: 'Tumregler från vanliga fiskeråd – inte fångstdata.',
      data: 'Var arten liknar platserna där den togs i tävlingarna.', similar: 'Välj en fiskeplats att jämföra med.' }[cat] || '';
    else if (!R) res.innerHTML = 'Djupdatan laddas…';
    else if (R.wait) res.innerHTML = 'Hämtar bottendata…';
    else {
      // (the top row: the result; its explanations are behind ⓘ; the Liknande list stays in the panel)
      res.innerHTML = R.text + (R.note ? '<span class="note">' + R.note + '</span>' : '') + (!anShow ? '<span class="pnHid"> · Dold – slå på Kartanalys i Filter</span>' : '');
      lst.innerHTML = (R.list ? '<div class="anList">' + (R.list.length ? R.list.map(function(it){
          return '<div class="li"><span class="n">' + it.n + '</span>' + fmtDepth(it.dep) + ' m · lutning ' + Math.round(it.slope) + ' %' +
            '<button type="button" data-go="' + it.n + '">' + (it.dm != null ? fmtMeters(it.dm) + ' · ' : '') + 'Åk hit ›</button></div>';
        }).join('') : '<div class="li">Inga tydliga träffar.</div>') + '</div>' : '');
    }
    anLabelsEl.innerHTML = (R && R.labels ? R.labels : []).map(function(l){
      return '<div class="anLbl ' + l.cls + '" data-i="' + l.i + '">' + escHtml(l.txt) + '</div>';
    }).join('');
    anControls();
    pnInfo(anPanel);
    anView = null; anDraw();
  }
  // a slider with one handle: label, the bar, the value
  // "Från fångsterna (data)": a button per species with its number of catches here (< 10: can't be chosen)
  function anDataRow(){
    var row = document.getElementById('anDataChips'), L = catchData ? catchData.list : [];
    if (!L.length){ row.innerHTML = '<span class="anNote" style="margin-top:2px">' + (catchData ? 'Inga fångster från tävlingarna i ' + escHtml(LAKE.name) + ' än.' : 'Hämtar fångsterna…') + '</span>'; return; }
    row.innerHTML = [['abborre', 'Abborre'], ['gadda', 'Gädda'], ['gos', 'Gös']].map(function(x){
      var n = L.filter(function(c){ return c.sp === x[0] && sizeOk(sizeOf(anSet, x[0]), c); }).length;
      return '<button type="button" data-m="c_' + x[0] + '"' + (n < AN_CMIN ? ' disabled' : '') + '>' + x[1] + ' ' + n + (n < AN_CMIN ? ' · för få' : '') + '</button>';
    }).join('');
  }
  function anRangeRow(id, label, min, max, step, val, fmt){
    return '<div class="anRange"><label for="' + id + '">' + label + '</label><input type="range" id="' + id + '" min="' + min + '" max="' + max + '" step="' + step + '" value="' + val + '"><output>' + fmt(val) + '</output></div>';
  }
  // a depth range: one bar in the depth colours (like the legend) with two handles
  function anDualRow(key){
    var ticks = (LAKE.legendTicks || ['0 m', AN_DMAX + ' m']).map(function(t){ return '<span>' + t.replace(' m', '') + '</span>'; });
    ticks[ticks.length - 1] = ticks[ticks.length - 1].replace('</span>', ' m</span>');
    return '<div class="anDual" data-k="' + key + '"><div class="anTrack" style="background:' + ((MAP_STYLES[0] && MAP_STYLES[0].legend) || '#2a86c9') + '"></div>' +
      '<div class="anSel"></div><div class="anKnob" data-h="0"></div><div class="anKnob" data-h="1"></div></div><div class="anTicks">' + ticks.join('') + '</div>';
  }
  var AN_DUAL = { depth: ['lo', 'hi'] };         // (only Djup has a depth range)
  function anDualPlace(){
    Array.prototype.forEach.call(document.querySelectorAll('#anControls .anDual'), function(d){
      var k = AN_DUAL[d.getAttribute('data-k')], a = anSet[k[0]] / AN_DMAX * 100, z = anSet[k[1]] / AN_DMAX * 100;
      d.children[1].style.left = a + '%'; d.children[1].style.width = Math.max(0, z - a) + '%';
      d.children[2].style.left = a + '%'; d.children[3].style.left = z + '%';
    });
  }
  var anCtlMode = '#';
  function anControls(){
    var m = anSet.mode, el = document.getElementById('anControls');
    var want = m + (m === 'similar' ? anSpots().length : m === 'combo' ? anSet.combo.join(',') : '');
    if (anCtlMode === want){ anDualPlace(); return; }            // (don't rebuild while dragging)
    anCtlMode = want;
    el.innerHTML = m === 'combo'
      ? anSet.combo.map(function(k){ return anCtlFor(k) +     // each part's own controls, + "inom … m" for the spots
          (AN_NEAR[k] ? anRangeRow('anNear_' + k, anName(k) + ' · inom', 0, 50, 5, anSet.near[k] || 0, function(v){ return v + ' m'; }) : ''); }).join('')
      : anCtlFor(m);
    if (m && m.indexOf('c_') === 0) anCatchDots();
    anDualPlace();
  }
  function anCtlFor(m){
    var h = '';
    if (m === 'depth') h = anDualRow('depth');
    else if (m === 'steep') h = anRangeRow('anSlope', 'Lutning', 4, 30, 1, anSet.slope, function(v){ return v + ' %'; });
    else if (m === 'tops') h = anRangeRow('anTopP', 'Grynnor', 0.3, 2.5, 0.1, anSet.topP, function(v){ return '≥ ' + fmtDepth(+v) + ' m'; }) +
      anRangeRow('anHoleP', 'Hålor', 0.3, 2.5, 0.1, anSet.holeP, function(v){ return '≥ ' + fmtDepth(+v) + ' m'; });
    else if (m && m.indexOf('c_') === 0) h = anCatchControls();
    else if (m === 'hard') h = anRangeRow('anHmin', 'Minst', 1, 4, 1, anSet.hmin, function(v){ return AN_HARD[v - 1]; });
    else if (m === 'similar'){
      var sp = anSpots();
      h = sp.length ? '<div class="anRefRow"><select id="anRefSel" aria-label="Plats att jämföra med">' + sp.map(function(w){
        return '<option value="' + escHtml(w.id) + '"' + (w.id === anSet.ref ? ' selected' : '') + '>' + escHtml(w.name || 'Plats') + (isMine(w) ? '' : ' (' + escHtml(w.by || '') + ')') + '</option>'; }).join('') + '</select>' +
        '<button type="button" id="anRefGo" title="Visa platsen på kartan">Gå till</button></div>' +
        '<div class="anLbl2">Jämför</div><div class="anFactors" id="anSimF">' + AN_SIMF.map(function(x){ return '<button type="button" data-f="' + x[0] + '" class="' + (anSet.simF[x[0]] ? 'on' : '') + '">' + x[1] + '</button>'; }).join('') + '</div>' +
        '<div class="anLbl2">Område runt platsen</div><div class="anSeg" id="anSimR">' + AN_SIMR.map(function(r){ return '<button type="button" data-r="' + r + '" class="' + (anSet.simR === r ? 'on' : '') + '">' + (r ? r + ' m' : 'Bara platsen') + '</button>'; }).join('') + '</div>' +
        '<div class="anNote"><b>Bara platsen</b> jämför det som finns precis under pinnen (en ruta på ca 5 × 5 m). <b>25–100 m</b> jämför i stället <b>snittet</b> inom den radien – både runt din plats och runt varje ställe i sjön. Då hittar du liknande <i>omgivningar</i> (t.ex. en kant med växter), inte bara en likadan punkt.<br>Listan: områdena som är mest lika, bäst först (inte slump). Platsen själv lyser men står inte i listan.</div>' : '';
    }
    return h;
  }
  var anDimSet = document.getElementById('anDimSet');
  anDimSet.value = anSet.dim; document.getElementById('anDimOut').textContent = Math.round(anSet.dim * 100) + ' %';
  anDimSet.addEventListener('input', function(){
    anSet.dim = parseFloat(anDimSet.value); document.getElementById('anDimOut').textContent = Math.round(anSet.dim * 100) + ' %';
    anSave(); anView = null; anDraw();
  });
  var anTimer = null;
  function anLater(){ anSave(); clearTimeout(anTimer); anTimer = setTimeout(anCompute, 60); }
  document.getElementById('anControls').addEventListener('input', function(e){
    if (sizeInput(e, anSet)){ anDataRow(); anLater(); return; }
    var t = e.target, v = parseFloat(t.value);
    if (t.id.indexOf('anNear_') === 0){ anSet.near[t.id.slice(7)] = v; t.nextSibling.textContent = v + ' m'; anLater(); return; }   // (combined: "inom … m")
    var map = { anSlope: 'slope', anTopP: 'topP', anHoleP: 'holeP', anHmin: 'hmin', anCCov: 'cCov' };
    if (!map[t.id]) return;
    anSet[map[t.id]] = v;
    t.nextSibling.textContent = t.id === 'anSlope' ? v + ' %' : t.id === 'anHmin' ? AN_HARD[v - 1] : t.id === 'anCCov' ? v + ' av 10' : '≥ ' + fmtDepth(v) + ' m';
    anLater();
  });
  // dragging a handle of a depth range (either handle; they can't cross)
  var anDrag = null;
  document.getElementById('anControls').addEventListener('pointerdown', function(e){
    var d = e.target.closest ? e.target.closest('.anDual') : null; if (!d) return;
    e.preventDefault(); e.stopPropagation();
    var r = d.getBoundingClientRect(), k = AN_DUAL[d.getAttribute('data-k')];
    var v = Math.max(0, Math.min(AN_DMAX, (e.clientX - r.left) / r.width * AN_DMAX));
    var h = e.target.classList.contains('anKnob') ? +e.target.getAttribute('data-h') : (Math.abs(v - anSet[k[0]]) <= Math.abs(v - anSet[k[1]]) ? 0 : 1);
    anDrag = { d: d, k: k, h: h, id: e.pointerId };
    try { d.setPointerCapture(e.pointerId); } catch(err){}
    anDragTo(e.clientX);
  });
  function anDragTo(x){
    var r = anDrag.d.getBoundingClientRect(), k = anDrag.k;
    var v = Math.round(Math.max(0, Math.min(AN_DMAX, (x - r.left) / r.width * AN_DMAX)) * 2) / 2;
    if (anDrag.h === 0) anSet[k[0]] = Math.min(v, anSet[k[1]]); else anSet[k[1]] = Math.max(v, anSet[k[0]]);
    anDualPlace(); anLater();
  }
  document.getElementById('anControls').addEventListener('pointermove', function(e){ if (anDrag && e.pointerId === anDrag.id){ e.preventDefault(); anDragTo(e.clientX); } });
  function anDragEnd(e){ if (anDrag && e.pointerId === anDrag.id) anDrag = null; }
  document.getElementById('anControls').addEventListener('pointerup', anDragEnd);
  document.getElementById('anControls').addEventListener('pointercancel', anDragEnd);
  document.getElementById('anControls').addEventListener('click', function(e){
    var cf = e.target.closest ? e.target.closest('#anCF button[data-cf]') : null, cvb = e.target.closest ? e.target.closest('#anCView button[data-cv]') : null;
    if (cf){ var ck = cf.getAttribute('data-cf'), others = AN_CF.filter(function(x){ return x[0] !== ck && anSet.cF[x[0]]; }).length;
      if (anSet.cF[ck] && !others) return;                    // (at least one stays on)
      anSet.cF[ck] = anSet.cF[ck] ? 0 : 1; cf.classList.toggle('on', !!anSet.cF[ck]); anLater(); return; }
    if (cvb){ anSet.cView = cvb.getAttribute('data-cv'); anCtlMode = '#'; anSave(); anCompute(); return; }
    if (e.target.id === 'anRefGo'){
      var wp = anSpots().filter(function(w){ return w.id === anSet.ref; })[0];
      if (wp){ showAnPanel(false); centerOnWaypoint(wp); }
      return;
    }
    var f = e.target.closest ? e.target.closest('#anSimF button') : null, r = e.target.closest ? e.target.closest('#anSimR button') : null;
    if (f){ var k = f.getAttribute('data-f'); anSet.simF[k] = anSet.simF[k] ? 0 : 1; f.classList.toggle('on', !!anSet.simF[k]); anLater(); }
    if (r){ anSet.simR = +r.getAttribute('data-r'); Array.prototype.forEach.call(r.parentNode.children, function(b){ b.classList.toggle('on', b === r); }); anLater(); }
  });
  document.getElementById('anControls').addEventListener('change', function(e){
    if (e.target.id === 'anRefSel'){ anSet.ref = e.target.value; anSave(); anCompute(); }
  });
  function anSetMode(m){ anApplyMode(anSet.mode === m ? null : m); }
  // Kartdata's buttons switch on / off: one on = that filter (as before), more = combined ('combo')
  function anMapList(){ var m = anSet.mode; return m === 'combo' ? anSet.combo.slice() : AN_MODES.some(function(x){ return x[0] === m; }) ? [m] : []; }
  function anToggleMap(k){
    var L = anMapList(), j = L.indexOf(k);
    if (j >= 0) L.splice(j, 1); else L.push(k);
    L.sort(function(a, b){ return AN_MODES.map(function(x){ return x[0]; }).indexOf(a) - AN_MODES.map(function(x){ return x[0]; }).indexOf(b); });   // (the buttons' order: the sliders don't jump around)
    anSet.combo = L.length > 1 ? L : [];
    anApplyMode(L.length > 1 ? 'combo' : L[0] || null);
  }
  function anApplyMode(m){
    anSet.mode = m; if (m !== 'combo') anSet.combo = []; if (anSet.mode) anSet.cat = anCatOf(anSet.mode); anSave(); anCtlMode = '#';
    if (anSet.mode && hmOn) hmSetOn(false);      // (not together with the heat map)
    if (anSet.mode && !anShow){ anShow = true; toggleAnEl.checked = true; try { localStorage.setItem(SHOW_AN_KEY, '1'); } catch(e){} }
    anCompute();
  }
  document.getElementById('anChips').innerHTML = AN_MODES.map(function(x){ return '<button type="button" data-m="' + x[0] + '">' + x[1] + '</button>'; }).join('');
  document.getElementById('anPresets').innerHTML = AN_PRESETS.map(function(x){ return '<button type="button" data-m="' + x[0] + '">' + x[1] + '</button>'; }).join('');
  // which category a mode is in (the row on top of the panel)
  function anCatOf(m){ return !m ? null : m === 'similar' ? 'similar' : m.indexOf('c_') === 0 ? 'data' : AN_PRESETS.some(function(x){ return x[0] === m; }) ? 'rule' : 'map'; }
  anPanel.addEventListener('click', function(e){
    var ct = e.target.closest ? e.target.closest('#anCatSeg button[data-cat]') : null;
    if (ct){
      anSet.cat = ct.getAttribute('data-cat'); anSave();
      if (anSet.cat === 'similar' && anSet.mode !== 'similar') anSetMode('similar');   // (Liknande: one thing -- straight on)
      else anRender();
      return;
    }
    var b = e.target.closest ? e.target.closest('button[data-m]') : null;
    if (b){ if (b.parentNode.id === 'anChips') anToggleMap(b.getAttribute('data-m')); else anSetMode(b.getAttribute('data-m')); return; }
    var g = e.target.closest ? e.target.closest('button[data-go]') : null;
    if (g && anRes && anRes.list){ var it = anRes.list[+g.getAttribute('data-go') - 1]; if (it){ showAnPanel(false); startNav('Liknande #' + it.n, it.x, it.y); } }
  });
  anPanel.addEventListener('pointerdown', function(e){ e.stopPropagation(); });
  sheetSwipe(anPanel, function(){ showAnPanel(false); });
  function anLikeSpot(wp){
    anSet.mode = 'similar'; anSet.cat = 'similar'; anSet.ref = wp.id; anSave(); anCtlMode = '#';
    if (!anShow){ anShow = true; toggleAnEl.checked = true; try { localStorage.setItem(SHOW_AN_KEY, '1'); } catch(e){} }
    showAnPanel(true); anCompute();
  }
  function showAnPanel(open){
    if (open && !anPanel.classList.contains('show') && anPanel._resetSize) anPanel._resetSize();
    anPanel.classList.toggle('show', open);
    if (open){ if (typeof toggleMsgPop === 'function') toggleMsgPop(false); if (hmPanel) hmShowPanel(false); loadCatches(false); anCtlMode = '#'; if (!anRes) anCompute(); else anRender(); }
  }
  anBtn.addEventListener('click', function(e){ e.stopPropagation(); showAnPanel(!anPanel.classList.contains('show')); });
  anPill.addEventListener('pointerdown', function(e){ e.stopPropagation(); });
  anPill.addEventListener('click', function(e){ e.stopPropagation(); showAnPanel(!anPanel.classList.contains('show')); });
  document.getElementById('anClose').addEventListener('click', function(){ showAnPanel(false); });
  document.getElementById('anClear').addEventListener('click', function(){ anSet.mode = null; anSet.combo = []; anSave(); anCtlMode = '#'; anCompute(); showAnPanel(false); });
  // "Återställ": every setting in the panel back to how it was from the start (what's shown stays; "Mörkare" is in Inställningar)
  // (what is shown -- mode, the combined parts -- and "Mörkare" stay)
  function anKeep(k){ return k === 'mode' || k === 'combo' || k === 'dim'; }
  function anIsDefault(){ var d = JSON.parse(AN_DEFAULTS); return Object.keys(d).every(function(k){ return anKeep(k) || JSON.stringify(anSet[k]) === JSON.stringify(d[k]); }); }
  document.getElementById('anReset').addEventListener('click', function(){
    var d = JSON.parse(AN_DEFAULTS); Object.keys(d).forEach(function(k){ if (!anKeep(k)) anSet[k] = d[k]; });
    anExtraRef = null; anSave(); anCtlMode = '#'; anCompute();
    resetDone(this);
  });
  // "↺ Återställ" (Kartanalys, Heatmap, Namn) says it's done: the arrow spins round once, then the usual grey ↺
  // (nothing left to reset)
  function resetDone(btn){
    clearTimeout(btn._rsT); btn.classList.remove('rsDone'); void btn.offsetWidth;
    btn.classList.add('rsDone'); btn.setAttribute('aria-label', 'Återställt');
    btn._rsT = setTimeout(function(){ btn.classList.remove('rsDone'); btn.setAttribute('aria-label', 'Återställ'); }, 700);
  }
  // ⓘ in the top row (Kartanalys, Heatmap): the explanations -- kept out of the panel itself -- in a box under
  // it: the notes on the result + the controls' notes. Open or not is remembered on the phone (closed at first).
  var PN_INFO_KEY = 'ffmap_panel_info_v1', pnInfoOn = false;
  try { pnInfoOn = localStorage.getItem(PN_INFO_KEY) === '1'; } catch(e){}
  function pnInfo(P){
    var box = P.querySelector('.pnInfo'), btn = P.querySelector('.pnInfoBtn'), res = P.querySelector('.pnRes'), parts = [];
    if (!box) return;
    if (pnInfoOn){
      if (res && res.scrollHeight > res.clientHeight + 2){ var c = res.cloneNode(true); Array.prototype.forEach.call(c.querySelectorAll('.note'), function(n){ n.remove(); }); parts.push(c.innerHTML); }
      Array.prototype.forEach.call(P.querySelectorAll('.pnRes .note, #anControls .anNote'), function(n){ if (n.textContent.trim()) parts.push(n.innerHTML); });
      box.innerHTML = parts.length ? parts.map(function(t){ return '<p>' + t + '</p>'; }).join('') : '<p>Ingen förklaring till det här.</p>';
    }
    box.hidden = !pnInfoOn;
    btn.classList.toggle('on', pnInfoOn); btn.setAttribute('aria-pressed', pnInfoOn ? 'true' : 'false');
  }
  function btn0(b){ Array.prototype.forEach.call(document.querySelectorAll('.pnInfoBtn'), function(x){ x.classList.remove('on'); x.setAttribute('aria-pressed', 'false'); }); }
  Array.prototype.forEach.call(document.querySelectorAll('.pnInfoBtn'), function(b){
    b.addEventListener('click', function(e){
      e.stopPropagation(); pnInfoOn = !pnInfoOn;
      try { localStorage.setItem(PN_INFO_KEY, pnInfoOn ? '1' : '0'); } catch(err){}
      var P = b.closest('#anPanel, #hmPanel'), box = P && P.querySelector('.pnInfo'), h0 = box && !box.hidden ? box.offsetHeight : 0;
      if (!box){ pnInfo(anPanel); pnInfo(hmPanel); }
      else if (pnInfoOn){ pnInfo(anPanel); pnInfo(hmPanel); motionHeight(box, 0, box.offsetHeight); }   // (it unfolds softly, 91-motion.js)
      else { btn0(b); motionHeight(box, h0, 0, function(){ pnInfo(anPanel); pnInfo(hmPanel); }); }
    });
  });
  anLabelsEl.addEventListener('pointerdown', function(e){ e.stopPropagation(); if (e.target.closest && e.target.closest('.anLbl')) mapPointerDown(e, true); });
  anLabelsEl.addEventListener('click', function(e){
    var l = e.target.closest ? e.target.closest('.anLbl') : null; if (!l) return;
    e.stopPropagation();
    if (mapDraggedJustNow()) return;
    var p = anImgOfCell(+l.getAttribute('data-i'));
    if (l.classList.contains('sim') && anRes && anRes.list){ var it = anRes.list[+l.textContent - 1]; if (it){ startNav('Liknande #' + it.n, it.x, it.y); return; } }
    showAnPanel(false); setProbe({ x: p.x, y: p.y });
  });
  var toggleAnEl = document.getElementById('toggleAnalysis');
  toggleAnEl.checked = anShow;
  toggleAnEl.addEventListener('change', function(){
    anShow = toggleAnEl.checked;
    try { localStorage.setItem(SHOW_AN_KEY, anShow ? '1' : '0'); } catch(e){}
    anRender();
  });
  // (the depth grid arrives a moment after start: work it out then)
  var anWaitGrid = setInterval(function(){ if (loadDepthGrid()){ clearInterval(anWaitGrid); if (anSet.mode) anCompute(); else anRender(); } }, 400);
  window.__ffAnalysis = function(){ var R = anRes; return { mode: anSet.mode, show: anShow, ready: !!(R && R.M), n: R ? R.n : 0, labels: R && R.labels ? R.labels.length : 0,
    list: R && R.list ? R.list.length : 0, text: R ? (R.text || '').replace(/<[^>]+>/g, '') : '' }; };

