  /* ================= Kartanalys "Från fångsterna (data)" -- per species =================
     Not rules of thumb: the competitions' catches (66-catches.js) of one species in THIS lake.
     For every catch: what the place is like (within 25 m) -- depth, slope, bottom, plants,
     distance to land, grynna/håla. Compared with the whole lake: in which kinds of place was the
     species caught more often than the lake is like that (per value and step; "lift", smoothed)?
     Every bit of the lake gets a score (the lifts of the values that are switched on, multiplied).
     Lit ("Tänt"): from the most alike down until "cCov" of 10 catches are inside -- so the DATA
     decides how much is lit: a clear pattern = a small area. "Skala": the whole lake coloured from
     unlike to most alike. Too few catches (< 10 on the depth map): can't be chosen. */
  var AN_CF = [['d', 'Djup'], ['s', 'Lutning'], ['h', 'Botten'], ['v', 'Växter'], ['l', 'Från land'], ['t', 'Grynna/håla']];
  var AN_CMIN = 10, anCatchStrength = {};
  var AN_CSP = { abborre: ['Abborre', 'abborrar'], gadda: ['Gädda', 'gäddor'], gos: ['Gös', 'gösar'] };
  // per value: the step each bit of the lake is in (-1 = not known there); cached per lake (+ bottom data)
  function anCatchBins(A){
    if (A.cBins && A.cBinsB === !!anBottom) return A.cBins;
    var F = anSimFeatures(A, 25), N = A.N, hasB = !!anBottom;
    var defs = {
      d: { b: [0, 1, 2, 3, 4, 5, 6, 8, 10, 14, 20, 30, 1e9], v: F.d, u: ' m' },
      s: { b: [0, 2, 4, 7, 10, 15, 25, 1e9], v: F.s, u: ' % lutning' },
      h: { b: [0.5, 1.5, 2.5, 3.5, 5], v: F.h, lab: ['mjuk botten', 'medelhård botten', 'hård botten', 'mycket hård botten'], miss: function(x){ return !hasB || !(x > 0); } },
      v: { b: [0, 0.1, 0.35, 0.7, 1.01], v: F.v, lab: ['inga växter', 'lite växter', 'en del växter', 'mycket växter'], miss: function(){ return !hasB; } },
      l: { b: [0, 25, 50, 100, 200, 400, 1e9], v: A.shore, u: ' m från land' },
      t: { b: [-1e9, -0.6, -0.2, 0.2, 0.6, 1e9], v: F.t, lab: ['hålor', 'svackor', 'jämn botten', 'kullar', 'grynnor'] }
    };
    var out = { defs: defs, bins: {}, lake: {}, tot: {} };
    Object.keys(defs).forEach(function(k){
      var D = defs[k], nb = D.b.length - 1, bins = new Int8Array(N), cnt = new Float64Array(nb), tot = 0;
      for (var i = 0; i < N; i++){
        bins[i] = -1; if (!A.wat[i]) continue;
        var x = D.v[i]; if (D.miss && D.miss(x)) continue;
        var j = 0; while (j < nb - 1 && x >= D.b[j + 1]) j++;
        bins[i] = j; cnt[j]++; tot++;
      }
      out.bins[k] = bins; out.lake[k] = cnt; out.tot[k] = tot;
    });
    A.cBins = out; A.cBinsB = hasB;
    return out;
  }
  // -> fills M (lit = 1) or returns G (0..1 per cell, "Skala"); text, note; pts = the catches (map px)
  function anCatchCompute(A, sp, M){
    var out = { n: 0, text: '', note: '', G: null, pts: null, empty: true }, nm = AN_CSP[sp] || [sp, sp];
    if (!catchData){ loadCatches(false); out.text = 'Hämtar fångsterna…'; return out; }
    var cs = catchData.list.filter(function(c){ return c.sp === sp && sizeOk(sizeOf(anSet, sp), c); }), cells = [];
    cs.forEach(function(c){ var i = anCellOfImg(c.px, c.py); if (A.wat[i]) cells.push(i); });
    out.pts = cs.map(function(c){ return { x: c.px, y: c.py }; });
    if (cells.length < AN_CMIN){
      out.text = 'För få fångster av ' + nm[0].toLowerCase() + ' här: ' + cells.length + (cs.length > cells.length ? ' på djupkartan (av ' + cs.length + ')' : '') + ' – minst ' + AN_CMIN + ' behövs.';
      return out;
    }
    var B = anCatchBins(A), N = A.N, wat = A.wat, L = {};
    AN_CF.forEach(function(x){
      var k = x[0], lake = B.lake[k], nb = lake.length, ca = new Float64Array(nb), nc = 0, bins = B.bins[k];
      cells.forEach(function(i){ var j = bins[i]; if (j >= 0){ ca[j]++; nc++; } });
      var logl = new Float32Array(nb), lift = [];
      for (var j = 0; j < nb; j++){ var l = lake[j] ? ((ca[j] + 1) / (nc + nb)) / ((lake[j] + 1) / (B.tot[k] + nb)) : 1; lift.push(l); logl[j] = Math.log(l); }
      L[k] = { ca: ca, nc: nc, lift: lift, logl: logl, ok: nc >= 5 };
    });
    var on = AN_CF.map(function(x){ return x[0]; }).filter(function(k){ return anSet.cF[k] && L[k].ok; });
    if (!on.length){ out.text = 'Slå på minst en sak att jämföra (' + AN_CF.filter(function(x){ return L[x[0]].ok; }).map(function(x){ return x[1].toLowerCase(); }).join(', ') + ').'; return out; }
    function scoreWith(keys){
      var S = new Float32Array(N);
      for (var i = 0; i < N; i++){ if (!wat[i]) continue; var s = 0;
        for (var q = 0; q < keys.length; q++){ var j = B.bins[keys[q]][i]; if (j >= 0) s += L[keys[q]].logl[j]; }
        S[i] = s; }
      return S;
    }
    // lit from the most alike down until cCov of 10 catches are inside
    function litShare(S){
      var cv = cells.map(function(i){ return S[i]; }).sort(function(a, b){ return b - a; });
      var thr = cv[Math.max(0, Math.ceil(cv.length * anSet.cCov / 10) - 1)], n = 0, w = 0;
      for (var i = 0; i < N; i++) if (wat[i]){ w++; if (S[i] >= thr) n++; }
      return { thr: thr, n: n, share: n / Math.max(1, w) };
    }
    var S = scoreWith(on), lit = litShare(S);
    // how much each value on its own points the species out (the dots on its button): lit share
    // alone against "no information" (cCov/10 of the lake for cCov/10 of the catches)
    anCatchStrength = {};
    AN_CF.forEach(function(x){
      var k = x[0]; if (!L[k].ok){ anCatchStrength[k] = 0; return; }
      var r = (anSet.cCov / 10) / Math.max(0.005, litShare(scoreWith([k])).share);
      anCatchStrength[k] = r < 1.5 ? 1 : r < 2.5 ? 2 : 3;
    });
    anCatchDots();
    if (anSet.cView === 'grad'){
      var sv = new Float32Array(N), w = 0;
      for (var i = 0; i < N; i++) if (wat[i]) sv[w++] = S[i];
      sv = sv.subarray(0, w); sv.sort();
      var lo = sv[Math.floor(w * 0.3)], hi = sv[Math.floor(w * 0.99)], G = new Float32Array(N);
      for (var i2 = 0; i2 < N; i2++) if (wat[i2]) G[i2] = Math.max(0, Math.min(1, (S[i2] - lo) / Math.max(1e-6, hi - lo)));
      out.G = G;
    } else {
      for (var i3 = 0; i3 < N; i3++) if (wat[i3] && S[i3] >= lit.thr) M[i3] = 1;
    }
    out.n = lit.n;
    // what stands out: the steps it was clearly more often caught in (of the values switched on)
    var parts = [];
    on.forEach(function(k){
      var D = B.defs[k], Lk = L[k], best = [];
      Lk.lift.forEach(function(l, j){ if (l >= 1.6 && Lk.ca[j] / Lk.nc >= 0.12) best.push(j); });
      if (!best.length) return;
      if (D.lab) parts.push(best.map(function(j){ return D.lab[j]; }).join('/'));
      else { var a = D.b[best[0]], b = D.b[best[best.length - 1] + 1];
        parts.push((b > 1e8 ? 'över ' + String(a).replace('.', ',') : String(a).replace('.', ',') + '–' + String(b).replace('.', ',')) + D.u); }
    });
    var pct = Math.round(lit.share * 100), word = lit.share < 0.12 ? 'Tydligt mönster' : lit.share < 0.25 ? 'Måttligt mönster' : 'Svagt mönster';
    out.text = '<b>' + nm[0] + '</b> togs oftast: ' + (parts.length ? parts.join(', ') : 'inget som sticker ut tydligt') + '. ' +
      (anSet.cView === 'grad' ? 'Färgen går från olikt till <b>mest likt fångstplatserna</b>.'
        : 'Tänt: <b>' + (pct < 1 ? '<1' : pct) + ' %</b> av sjön – där togs ' + anSet.cCov + ' av 10 ' + nm[1] + '. <b>' + word + '</b>.');
    var months = {}; cs.forEach(function(c){ months[HM_MON[new Date(c.t).getMonth()]] = 1; });
    out.note = cells.length + ' fångster från tävlingarna (' + Object.keys(months).join(', ') + ')' + (cs.length > cells.length ? '; ' + (cs.length - cells.length) + ' utanför djupkartan räknas inte' : '') +
      '. Visar var man fick fisk – inte var all fisk finns.' + (cells.length < 20 ? ' <b>Osäkert:</b> få fångster.' : '');
    out.empty = false;
    return out;
  }
  // the dots on each value's button: how much it alone points the species out here
  function anCatchDots(){
    Array.prototype.forEach.call(document.querySelectorAll('#anCF button[data-cf]'), function(b){
      var s = anCatchStrength[b.getAttribute('data-cf')], d = b.querySelector('.anDots');
      if (d) d.textContent = s ? '●●●'.slice(0, s) + '○○○'.slice(0, 3 - s) : '–';
      b.disabled = s === 0;
    });
  }
  function anCatchControls(){
    return '<div class="anSeg" id="anCView">' + [['area', 'Tänt'], ['grad', 'Skala']].map(function(x){ return '<button type="button" data-cv="' + x[0] + '" class="' + (anSet.cView === x[0] ? 'on' : '') + '">' + x[1] + '</button>'; }).join('') + '</div>' +
      (catchData ? sizeRow(sizeOf(anSet, anSet.mode.slice(2)), sizeBounds(catchData.list.filter(function(c){ return c.sp === anSet.mode.slice(2); })), anSet.mode.slice(2)) : '') +
      '<div class="anLbl2">Vad som jämförs</div>' +
      '<div class="anNote"><b>Vad som jämförs:</b> slå av det du inte vill jämföra. ●●● = hur mycket värdet ensamt pekar ut arten här.</div>' +
      '<div class="anFactors" id="anCF">' + AN_CF.map(function(x){ return '<button type="button" data-cf="' + x[0] + '" class="' + (anSet.cF[x[0]] ? 'on' : '') + '">' + x[1] + ' <span class="anDots"></span></button>'; }).join('') + '</div>' +
      (anSet.cView === 'grad' ? '' : anRangeRow('anCCov', 'Typiskt', 5, 9, 1, anSet.cCov, function(v){ return v + ' av 10'; }) +
      '<div class="anNote">Hur många av fångsterna det tända ska rymma. <b>Lägre</b> = bara de allra mest typiska ställena – udda fångster räknas bort, mindre yta. <b>Högre</b> = fler fångster får plats, större yta.</div>');
  }
