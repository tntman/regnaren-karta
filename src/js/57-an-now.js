  /* ================= Kartanalys "Fiska nu" -- where the group caught the most fish at this time =================
     The competitions' catches in THIS lake (66-catches.js), each weighed by how close it is to now: the day of the
     year (any year) and the time of day -- a catch a week ago at the same hour weighs a lot, one in July at dawn next
     to nothing. Few catches near now: the window widens step by step (and says so). Catches within 60 m are one
     place; the 5 places with the biggest share of the weighed catches, at least 150 m apart. % = that share -- not a
     real chance (nobody logs the hours without a bite), ⓘ says so. "När": a few hours ahead (anSet.nowH). Filip 2026-10-07. */
  var AN_NOW_SP = [['all', 'Alla'], ['abborre', 'Abborre'], ['gadda', 'Gädda'], ['gos', 'Gös']];
  var AN_NOW_MIN = 20, AN_NOW_R = 60, AN_NOW_APART = 150;
  // [days, hours]: how far from now a catch still weighs (gauss sigma); the first step with enough weighed catches is used
  var AN_NOW_WIN = [[14, 2], [21, 2], [30, 3], [45, 3], [60, 4], [90, 6], [183, 12]];
  function anNowList(sp){ return (catchData ? catchData.list : []).filter(function(c){ return (sp === 'all' || c.sp === sp) && c.px != null; }); }
  function anNowWhen(){ return new Date(Date.now() + (anSet.nowH || 0) * 3600e3); }
  function anDoy(d){ return Math.floor((Date.UTC(d.getFullYear(), d.getMonth(), d.getDate()) - Date.UTC(d.getFullYear(), 0, 0)) / 864e5); }
  function anNowCompute(A, sp, M){
    var out = { n: 0, text: '', note: '', pts: null, list: null, labels: [], sv: null, empty: true };
    if (!catchData){ loadCatches(false); out.text = 'Hämtar fångsterna…'; return out; }
    var cs = anNowList(sp).filter(function(c){ c._i = anCellOfImg(c.px, c.py); return A.wat[c._i]; });
    var spName = sp === 'all' ? 'fångster' : (AN_CSP[sp] || [0, sp])[1];
    if (cs.length < AN_NOW_MIN){
      out.text = 'För få ' + spName + ' i ' + escHtml(LAKE.name) + ' för tips (' + cs.length + ' av minst ' + AN_NOW_MIN + ').';
      out.note = 'Fiska nu behöver minst ' + AN_NOW_MIN + ' fångster från tävlingarna i sjön' + (sp === 'all' ? '' : ' av arten') + '. Prova <b>Alla</b>.';
      return out;
    }
    var T = anNowWhen(), td = anDoy(T), th = T.getHours() + T.getMinutes() / 60, win = null, sum = 0;
    cs.forEach(function(c){ var d = new Date(c.t), dd = Math.abs(anDoy(d) - td), dh = Math.abs(d.getHours() + d.getMinutes() / 60 - th);
      c._dd = Math.min(dd, 365 - dd); c._dh = Math.min(dh, 24 - dh); });
    for (var s = 0; s < AN_NOW_WIN.length; s++){
      win = AN_NOW_WIN[s]; sum = 0;
      cs.forEach(function(c){ c._w = Math.exp(-0.5 * (c._dd * c._dd / (win[0] * win[0]) + c._dh * c._dh / (win[1] * win[1]))); sum += c._w; });
      if (sum >= 8) break;
    }
    var near = cs.filter(function(c){ return c._w >= 0.25; });
    out.pts = near.map(function(c){ return { x: c.px, y: c.py }; });
    // the places: the catch with the most weight within 60 m round it, its catches go; again -- at least 150 m from the others
    var left = cs.slice(), spots = [];
    function m(a, b){ var dx = (a.px - b.px) * WEB_METERS_PER_PX, dy = (a.py - b.py) * WEB_METERS_PER_PX; return Math.sqrt(dx * dx + dy * dy); }
    while (spots.length < 5 && left.length){
      var best = null, bw = 0;
      left.forEach(function(c){
        if (spots.some(function(p){ return m(c, p) < AN_NOW_APART; })) return;
        var w = 0; left.forEach(function(o){ if (m(c, o) <= AN_NOW_R) w += o._w; });
        if (w > bw){ bw = w; best = c; }
      });
      if (!best || bw < 0.01) break;
      var mine = left.filter(function(o){ return m(best, o) <= AN_NOW_R; }), sx = 0, sy = 0;
      mine.forEach(function(o){ sx += o.px * o._w; sy += o.py * o._w; });
      var p = { px: sx / bw, py: sy / bw, w: bw, cs: mine };
      if (!A.wat[anCellOfImg(p.px, p.py)]){ p.px = best.px; p.py = best.py; }     // (the middle of a bay's catches can be land)
      spots.push(p);
      left = left.filter(function(o){ return mine.indexOf(o) < 0; });
    }
    // lit: 60 m round each place (Skala: the biggest share strongest, fading out to the edge)
    var R = AN_NOW_R / A.cell, W = A.W, sv = anSet.scale ? new Float32Array(A.N) : null, top = spots.length ? spots[0].w : 1;
    spots.forEach(function(p, k){
      var ci = anCellOfImg(p.px, p.py), cx = ci % W, cy = Math.floor(ci / W);
      for (var y = Math.max(0, Math.floor(cy - R)); y <= Math.min(A.H - 1, Math.ceil(cy + R)); y++) for (var x = Math.max(0, Math.floor(cx - R)); x <= Math.min(W - 1, Math.ceil(cx + R)); x++){
        var i = y * W + x, d = Math.sqrt((x - cx) * (x - cx) + (y - cy) * (y - cy)); if (d > R || !A.wat[i]) continue;
        if (!M[i]) out.n++; M[i] = 1;
        if (sv) sv[i] = Math.max(sv[i], p.w / top * (1 - 0.5 * d / R));
      }
      out.labels.push({ i: ci, cls: 'sim now', txt: String(k + 1) });
    });
    out.sv = sv;
    out.list = spots.map(function(p, k){
      var ll = imgPxToLatLon(p.px, p.py), dm = null, cnt = {};
      if (lastOwnLatLon && lastFix && lastFix.onMap) dm = haversineKm(lastOwnLatLon.lat, lastOwnLatLon.lon, ll.lat, ll.lon) * 1000;
      p.cs.forEach(function(c){ cnt[c.sp] = (cnt[c.sp] || 0) + 1; });
      var sps = ['gos', 'abborre', 'gadda'].filter(function(x){ return cnt[x]; }).sort(function(a, b){ return cnt[b] - cnt[a]; }).map(function(x){ return [x, AN_CSP[x][0] + ' ' + cnt[x]]; });
      return { n: k + 1, x: p.px, y: p.py, dep: A.sm[anCellOfImg(p.px, p.py)], dm: dm, pct: Math.max(1, Math.round(100 * p.w / sum)), sps: sps, nav: 'Fiska nu #' + (k + 1) };
    });
    var hh = function(h){ return 'kl ' + h; };
    var months = {}; near.forEach(function(c){ months[new Date(c.t).getMonth()] = 1; });
    var mo = Object.keys(months).map(Number).sort(function(a, b){ return a - b; }).map(function(x){ return HM_MON[x]; });
    var hrs = near.map(function(c){ return new Date(c.t).getHours(); }), h0 = Math.min.apply(null, hrs), h1 = Math.max.apply(null, hrs);
    var wide = win[0] > 30;
    out.text = '<b>Bäst ' + (anSet.nowH ? hh(T.getHours()) : 'nu') + '</b> · ' + (sp === 'all' ? 'alla arter' : AN_CSP[sp][0].toLowerCase()) + ', ' + near.length + ' fångster nära i tid' + (wide ? ' (få – bredare)' : '');
    out.note = '<p><b>Fiska nu</b> visar var gruppen har fått mest fisk vid <b>den här tiden</b> – samma tid på året (vilket år som helst) och på dygnet. ' +
      'Fångster nära i tid räknas mycket, fångster långt ifrån nästan inget. Fångster inom ' + AN_NOW_R + ' m räknas som en plats.</p>' +
      '<p><b>%</b> = hur stor del av de fångsterna som togs på platsen. Det är inte en garanti att få fisk – bara var det nappat mest förut. ' +
      'Där ingen har fiskat finns inga fångster, och fisken kan ha flyttat.</p>' +
      '<ul class="pnList"><li><b>Underlag:</b> ' + near.length + ' fångster' + (mo.length ? ' (' + mo.join(', ') + (hrs.length ? ', ' + hh(h0) + '–' + (h1 + 1) : '') + ')' : '') + ' av ' + cs.length + ' i sjön.' +
      (wide ? ' Det fanns få fångster nära i tid, så den räknar med upp till ' + win[0] + ' dagar och ' + win[1] + ' timmar bort.' : '') + '</li>' +
      '<li><b>När:</b> dra för att se tipsen för senare i dag.</li><li><b>Åk hit</b> visar vägen dit. Tryck på en rad för att se platsen på kartan.</li></ul>';
    out.empty = !spots.length;
    return out;
  }
  function anNowLbl(v){ return +v ? 'kl ' + new Date(Date.now() + v * 3600e3).getHours() : 'Nu'; }
  function anNowControls(){ return anRangeRow('anNowH', 'När', 0, 12, 1, anSet.nowH || 0, anNowLbl); }
  // the species buttons (Alla first), each with its number of catches here
  function anNowRow(){
    var row = document.getElementById('anNowChips');
    row.innerHTML = AN_NOW_SP.map(function(x){ var n = anNowList(x[0]).length;
      return '<button type="button" data-m="n_' + x[0] + '"' + (n ? '' : ' disabled') + '>' + x[1] + (catchData ? ' ' + n : '') + '</button>'; }).join('');
  }
