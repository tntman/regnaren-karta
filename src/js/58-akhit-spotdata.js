  /* ================= "Åk hit" =================
     From a spot's sheet (or a place the analysis found): the lead line is dropped there --
     it shows the depth, the distance by water, the time, and the route is drawn. */
  function startNav(name, x, y){
    setProbe({ x: x, y: y });
    // show the whole way: you, the place and the route between (between the header and the buttons);
    // not at the lake: just the place
    var pts = [{ x: x, y: y }];
    if (lastFix && lastFix.onMap){ pts.push({ x: lastFix.px, y: lastFix.py }); if (probeRoute && probeRoute.pts) pts = pts.concat(probeRoute.pts); }
    var x0 = Infinity, y0 = Infinity, x1 = -Infinity, y1 = -Infinity;
    pts.forEach(function(q){ x0 = Math.min(x0, q.x); y0 = Math.min(y0, q.y); x1 = Math.max(x1, q.x); y1 = Math.max(y1, q.y); });
    var top = 150, bot = 230, side = 50;
    var sc = Math.min((stageW - 2 * side) / Math.max(1, x1 - x0), (stageH - top - bot) / Math.max(1, y1 - y0));
    sc = Math.max(minScale, Math.min(maxScale, Math.min(sc, pts.length > 1 ? sc : Math.max(scale, fitScale * 4.5))));
    var cx = (x0 + x1) / 2, cy = (y0 + y1) / 2;
    animateTo(sc, stageW / 2 - cx * sc, top + (stageH - top - bot) / 2 - cy * sc, 600);
  }

  /* ---- what's under a spot (its sheet): depth, slope, bottom, plants + the terrain ---- */
  function renderWpData(lat, lon){
    var el = document.getElementById('wpData'), A = anBase();
    var p = latLonToImgPx(lat, lon), dm = depthAtImgPx(p.x, p.y);
    if (!A || dm == null){ el.innerHTML = dm != null ? '' : (isLakeAtImgPx(p.x, p.y) ? '<div class="wpTerrain">Okänt djup här (ingen ekolodsdata).</div>' : ''); return; }
    if (!anBottom) anLoadBottom();
    var i = anCellOfImg(p.x, p.y), W = A.W, cx = i % W, cy = Math.floor(i / W);
    var sl = A.slope[i], slTxt = sl < 3 ? 'plant' : sl < 10 ? 'sluttar' : 'brant';
    var bot = '–', botSub = anBottom ? 'ej mätt' : '…', veg = '–', vegSub = anBottom ? '' : '…';
    if (anBottom){
      var best = 0, bd = 1e9, r = Math.max(1, Math.round(15 / A.cell));     // hardness: here, or the nearest measured within 15 m
      for (var dy = -r; dy <= r; dy++) for (var dx = -r; dx <= r; dx++){
        var x = cx + dx, y = cy + dy; if (x < 0 || y < 0 || x >= W || y >= A.H) continue;
        var h = anBottom[y * W + x] & 7; if (h && dx * dx + dy * dy < bd){ bd = dx * dx + dy * dy; best = h; } }
      if (best){ bot = ['Mjuk', 'Medel', 'Hård', 'Mkt hård'][best - 1]; botSub = bd ? 'strax intill' : 'hårdhet'; }
      var rv = Math.max(1, Math.round(25 / A.cell)), nv = 0, nw = 0;           // plants: share of the water within 25 m
      for (var dy2 = -rv; dy2 <= rv; dy2++) for (var dx2 = -rv; dx2 <= rv; dx2++){
        if (dx2 * dx2 + dy2 * dy2 > rv * rv) continue;
        var x2 = cx + dx2, y2 = cy + dy2; if (x2 < 0 || y2 < 0 || x2 >= W || y2 >= A.H) continue;
        var j = y2 * W + x2; if (!A.wat[j]) continue; nw++; if (anBottom[j] & 8) nv++; }
      var f = nw ? nv / nw : 0;
      veg = f < 0.05 ? 'Inga' : f < 0.3 ? 'Lite' : f < 0.7 ? 'En del' : 'Mycket'; vegSub = Math.round(f * 100) + ' % inom 25 m';
    }
    var t = A.tpi[i], terr = t >= 0.6 ? '⛰ <b>Grynna</b> – ' + fmtDepth(t) + ' m grundare än runt om' : t <= -0.8 ? '🕳 <b>Håla</b> – ' + fmtDepth(-t) + ' m djupare än runt om' : 'Jämn botten runt om';
    el.innerHTML =
      '<div class="wpTile"><i>Djup</i><b>' + fmtDepth(dm) + ' m</b></div>' +
      '<div class="wpTile"><i>Lutning</i><b>' + Math.round(sl) + ' %</b></div>' +
      '<div class="wpTile"><i>Botten</i><b>' + bot + '</b></div>' +
      '<div class="wpTile"><i>Växter</i><b>' + veg + '</b></div>';
  }
  document.getElementById('wpGo').addEventListener('click', function(){
    var wp = waypoints.filter(function(w){ return w.id === editingId; })[0];
    if (!wp) return;
    var p = latLonToImgPx(wp.lat, wp.lon);
    editingIsNew = false; closeSheet();
    startNav(wp.name, p.x, p.y);
  });
  document.getElementById('wpLike').addEventListener('click', function(){
    var wp = waypoints.filter(function(w){ return w.id === editingId; })[0];
    if (!wp) return;
    editingIsNew = false; closeSheet();
    anLikeSpot(wp);
  });

