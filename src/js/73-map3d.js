  /* ================= 3D-karta: the lake's bottom and the land around it in 3D =================
     In the map-style list (hold the map button), right after the map styles: a full-screen view of its own -- the map
     itself is untouched underneath. TWO meshes of at most M3_NMAX points a side: the whole map, coarse (always there:
     you see the lake to its end, no fog), and a fine one around the point you look at with every depth cell (built
     again when the fingers have rested 0,2 s, like Under ytan's slider; the whole map's is cut out where it lies).
     On them the chosen map style's picture (aerial photo on land, Genesis' colours and lines on the water -- nothing of
     that is drawn here), lit from the north-west like the maps' relief. y = -depth in the water; on land the height
     above the lake from LAKE.land (tools/land_height.py: a small file per lake, fetched when the view opens; a lake
     without one, or no coverage the first time = flat land). Water nobody has charted -- the lake's own, or outside the
     chart; the same file says where, m3Void -- takes its depth from what is known close by and is a hole further out:
     only the water's surface lies over it (m3Make).
     Near the point you look at the picture is sharp: the zoom level's pieces (the same as the map's own, 12-map.js) put
     together on ONE canvas of M3_TEX px, shown instead of the map picture where it reaches (m3Detail).
     The fingers as in the map apps: one = move, pinch = zoom, twist = turn, two up/down = tilt (own code, further down).
     Your boat, the spots and the others' boats: the map's own pins copied on top (the same filter and icons; view only).
     Settings: ffmap_3d_v1 (Höjd ×, Vatten). Drawn only when something changed -- no loop runs. Filip 2026-11-11. */
  var M3_KEY = 'ffmap_3d_v1', M3_NMAX = 400, M3_FOV = 40;
  var M3_RFULL = Math.max(IMG_W, IMG_H) * WEB_METERS_PER_PX / 2;   // half the map's long side (m): a fine mesh this far out would be no finer than the whole map's
  var M3_TEX = 2048;   // the sharp patch's canvas (px a side): 4 x 4 pieces
  var M3_REACH = 15;   // m: water nobody has charted takes its depth from what is known this close; further out it is a hole (m3Make)
  var m3Cfg = { ex: 3, water: true, col: false, shadow: false };   // (col: Djupfärg -- the bottom coloured by depth instead of the map picture; shadow: Skuggor -- cast shadows)
  try { m3Cfg = Object.assign(m3Cfg, JSON.parse(localStorage.getItem(M3_KEY) || '{}')); } catch(e){}
  var m3View = document.getElementById('m3View'), m3Canvas = document.getElementById('m3Canvas'), m3Marks = document.getElementById('m3Marks'), m3Msg = document.getElementById('m3Msg');
  var m3 = null;   // while open: { T, r, scene, cam, far: the whole map's mesh, near: the fine one (or null), tex, c: the camera { px, py (the image px looked at), d (m away), az, tilt (0 = straight down) }, at: what the fine mesh was built for }
  function m3Save(){ try { localStorage.setItem(M3_KEY, JSON.stringify(m3Cfg)); } catch(e){} }
  var m3Land = null;   // the land's heights while the view is open: a byte per cell, LAKE.land.max x (byte / 250)^2 = m above the lake, 255 = lake, 252 = water nobody has charted (1 = asked for)
  function m3LoadLand(){
    if (!LAKE.land || m3Land) return;
    m3Land = 1;
    fetch(lakeUrl(LAKE.land.file)).then(function(r){ return r.ok ? r.text() : Promise.reject(); }).then(function(t){
      if (!m3) return;
      m3Land = unpackGrid(t.trim(), LAKE.land.w * LAKE.land.h);
      if (m3.r){ m3Drop(m3.far); m3.far = m3.at = null; m3MarksSync(); }   // (the meshes and the pins again, with the land)
    }).catch(function(){ m3Land = null; });        // (no coverage: flat land; asked again the next time it opens)
  }
  function m3Ground(x, y){ return isLakeAtImgPx(x, y) ? 0 : m3LandAt(x, y) * m3Cfg.ex; }   // the ground's (the water's) height in the picture at a map-picture px
  function m3LandAt(x, y){   // m above the lake at a map-picture px (0: in the lake, or no heights)
    var v = m3Land && m3Land.length ? gridValAt(m3Land, LAKE.land.w, LAKE.land.h, x, y) : null;
    return v === null ? 0 : v * v / 62500 * LAKE.land.max;   // (square-root steps: fine low down, by the shore -- tools/land_height.py)
  }
  // water nobody has charted (the land file's 252: the lake's own, or outside the chart -- which the depth grid calls
  // land). Drawn at the surface it stood as big hills beside the charted bottom (Filip 2026-11-12): see m3Make
  function m3Void(x, y){
    if (!m3Land || !m3Land.length) return false;
    var L = LAKE.land, xi = Math.floor(x / IMG_W * L.w), yi = Math.floor(y / IMG_H * L.h);
    return xi >= 0 && yi >= 0 && xi < L.w && yi < L.h && m3Land[yi * L.w + xi] === 252;
  }
  function m3MaxDepth(){   // the lake's deepest charted water (m): Djupfärg's darkest colour
    var g = loadDepthGrid(), m = 1; if (g) for (var i = 0; i < g.length; i++) if (g[i] < 251 && g[i] > m) m = g[i];
    return Math.max(2, m * DEPTH_STEP);
  }
  function m3Clamp(c){
    c.px = Math.max(0, Math.min(IMG_W, c.px)); c.py = Math.max(0, Math.min(IMG_H, c.py));
    c.d = Math.max(60, Math.min(M3_RFULL * 3, c.d)); c.tilt = Math.max(0.05, Math.min(1.45, c.tilt));
    return c;
  }
  function m3R(c){ return Math.min(M3_RFULL, Math.max(150, c.d * 1.6)); }   // how far out the fine mesh goes for this zoom (m)
  // a mesh of the ground and one of the water's surface over a rectangle of the map picture (px), at most M3_NMAX points
  // a side; x = east, z = south (m from the map's middle), y = -depth / the land's height (the mesh is scaled by Höjd ×)
  function m3Make(x0, y0, x1, y1, mat, wmat){
    var T = m3.T, M = WEB_METERS_PER_PX, k = Math.max(AR_CELL / M, Math.max(x1 - x0, y1 - y0) / M3_NMAX);   // image px a step: never finer than the depth cells
    var nx = Math.max(2, Math.floor((x1 - x0) / k) + 1), ny = Math.max(2, Math.floor((y1 - y0) / k) + 1);
    var pos = new Float32Array(nx * ny * 3), uv = new Float32Array(nx * ny * 2), wet = new Uint8Array(nx * ny), idx = [], widx = [], unk = [];
    for (var j = 0; j < ny; j++) for (var i = 0; i < nx; i++){
      var q = j * nx + i, x = x0 + i * k, y = y0 + j * k, d = depthAtImgPx(x, y);
      wet[q] = d !== null ? 1 : m3Void(x, y) ? 2 : isLakeAtImgPx(x, y) ? 1 : 0;   // 0 land, 1 water, 2 water nobody has charted (a depth wins: sounded since the land file was made)
      if (wet[q] === 2) unk.push(q);
      pos[q * 3] = (x - IMG_W / 2) * M; pos[q * 3 + 2] = (y - IMG_H / 2) * M;
      pos[q * 3 + 1] = d !== null ? -d : wet[q] ? -0.2 : Math.max(0.3, m3LandAt(x, y));   // (lake nobody has logged: just under the surface; land: never lower than just over it -- the water's surface never lies on the land)
      uv[q * 2] = x / IMG_W; uv[q * 2 + 1] = 1 - y / IMG_H;
    }
    // the shore: the land's points next to the water lie at the water's level -- else a steep bank rises straight from the
    // water's points, in teeth with the shallows' colour on them
    for (j = 0; j < ny; j++) for (i = 0; i < nx; i++){
      q = j * nx + i;
      if (!wet[q] && ((i && wet[q - 1]) || (i < nx - 1 && wet[q + 1]) || (j && wet[q - nx]) || (j < ny - 1 && wet[q + nx]))) pos[q * 3 + 1] = 0.3;
    }
    // Water nobody has charted: within M3_REACH m of something known it takes its depth from that -- the bottom goes on a
    // little way past the chart's edge, comes up to the shore, bridges a narrow gap in the chart -- and further out it is
    // left as a hole. (First all of it lay at the surface: big hills beside the charted bottom, Filip 2026-11-12. Then it
    // was a hole where it was 30 m wide and at the surface where it wasn't: those bits stood as pillars at the holes'
    // ragged edges, 27 m high.)
    function known(q){   // the mean of what is known around a point (the land's edge = just under the surface); null: nothing is
      var i = q % nx, j = (q - i) / nx, s = 0, n = 0;
      for (var dj = -1; dj <= 1; dj++) for (var di = -1; di <= 1; di++){
        var p = q + dj * nx + di;
        if ((di || dj) && i + di >= 0 && i + di < nx && j + dj >= 0 && j + dj < ny && wet[p] !== 2){ s += wet[p] ? pos[p * 3 + 1] : -0.2; n++; }
      }
      return n ? Math.min(-0.2, s / n) : null;
    }
    var reach = Math.max(1, Math.round(M3_REACH / (k * M))), fill = [];
    for (var r = 0; r < reach; r++){   // (a step further out each round)
      var got = [];
      unk.forEach(function(q){ var v = wet[q] === 2 ? known(q) : null; if (v !== null) got.push(q, v); });
      for (var t = 0; t < got.length; t += 2){ wet[got[t]] = 3; pos[got[t] * 3 + 1] = got[t + 1]; fill.push(got[t]); }
    }
    for (r = 0; r < reach * reach + 2; r++) fill.forEach(function(q){ pos[q * 3 + 1] = known(q); });   // ...evened out: a slope from the chart's depth up to the shore, not a step halfway
    // the ground's triangles: none with a corner that is still a hole
    function tri(p, q, r){ if (wet[p] !== 2 && wet[q] !== 2 && wet[r] !== 2) idx.push(p, q, r); }
    for (j = 0; j < ny - 1; j++) for (i = 0; i < nx - 1; i++){
      var a = j * nx + i, b = a + 1, e = a + nx; tri(a, e, b); tri(b, e, e + 1);
      if (wet[a] || wet[b] || wet[e] || wet[e + 1]) widx.push(a, e, b, b, e, e + 1);   // (the water's surface: where the lake is, a cell in over the shore -- over the holes too)
    }
    var g = new T.BufferGeometry();
    g.setAttribute('position', new T.BufferAttribute(pos, 3)); g.setAttribute('uv', new T.BufferAttribute(uv, 2)); g.setIndex(idx); g.computeVertexNormals();
    var wp = pos.slice(), wg = new T.BufferGeometry();   // the water's surface: the same points at height 0
    for (q = 1; q < wp.length; q += 3) wp[q] = 0;
    wg.setAttribute('position', new T.BufferAttribute(wp, 3)); wg.setIndex(widx);
    var o = { mesh: new T.Mesh(g, mat), water: new T.Mesh(wg, wmat), n: Math.max(nx, ny), step: k * M };
    o.mesh.castShadow = o.mesh.receiveShadow = true;   // (Skuggor: only drawn when the sun casts them)
    m3.scene.add(o.mesh, o.water);
    return o;
  }
  function m3Drop(o){ if (o){ m3.scene.remove(o.mesh, o.water); o.mesh.geometry.dispose(); o.water.geometry.dispose(); } }
  // four planes whose "outsides" together are the rectangle e = [x0, x1, z0, z1] (m), mg in from its edge: what is drawn
  // with them (the whole map's mesh) is left out there. No e: nowhere.
  function m3Hole(planes, e, mg){
    if (!e){ e = [1e9, -1e9, 1e9, -1e9]; mg = 0; }
    planes[0].constant = e[0] + mg; planes[1].constant = mg - e[1]; planes[2].constant = e[2] + mg; planes[3].constant = mg - e[3];
  }
  // the fine mesh around the point you look at -- none when it would reach as far as the whole map's (then that one is as fine)
  function m3Patch(){
    var c = m3.c, R = m3R(c), full = R >= M3_RFULL, M = WEB_METERS_PER_PX, rp = R / M, e = null;
    m3Drop(m3.near); m3.near = null;
    if (!full){
      var x0 = Math.max(0, c.px - rp), x1 = Math.min(IMG_W, c.px + rp), y0 = Math.max(0, c.py - rp), y1 = Math.min(IMG_H, c.py + rp);
      m3.near = m3Make(x0, y0, x1, y1, m3.mat, m3.wmat);
      e = [(x0 - IMG_W / 2) * M, (x1 - IMG_W / 2) * M, (y0 - IMG_H / 2) * M, (y1 - IMG_H / 2) * M];
    }
    m3Hole(m3.cutW, e, 0); m3Hole(m3.cut, e, m3.far.step);   // (the ground: a cell further in, so the two overlap rather than leave a gap)
    m3.at = { px: full ? IMG_W / 2 : c.px, py: full ? IMG_H / 2 : c.py, R: R, full: full }; m3.n = (m3.near || m3.far).n; m3.nb = (m3.nb || 0) + 1;
  }
  // the sharp patch: the sharpest zoom level whose M3_TEX px still reach 1,2 x the distance around the point you look at
  // (null: so far out that the map picture itself is as sharp)
  function m3DetLevel(c){
    var best = null;
    ((DETAIL && DETAIL.levels) || []).forEach(function(L){
      if (L.styles && L.styles.indexOf(mapStyle) === -1) return;
      if (M3_TEX / Math.pow(2, L.z - ZOOM) * S * WEB_METERS_PER_PX >= c.d * 1.2 && (!best || L.z > best.z)) best = L;
    });
    return best;
  }
  // ...its picture: first the map picture enlarged (there at once), then the level's pieces as they arrive -- a base, and
  // when it is there its lines on top (as renderDetail, 12-map.js). Moved a bit at the same level: what was already put
  // together is kept, only the new pieces are fetched.
  function m3Detail(L){
    var T = m3.T, c = m3.c, s = Math.pow(2, L.z - ZOOM) / S, t = DETAIL.tile, pad = DETAIL.pad || 0, N = M3_TEX;   // s: the level's px per map-picture px
    if (!m3.det){
      var cv = document.createElement('canvas'); cv.width = cv.height = N;
      var dt = new T.CanvasTexture(cv); dt.colorSpace = T.SRGBColorSpace; dt.anisotropy = m3.tex.anisotropy;
      m3.det = { cv: cv, ctx: cv.getContext('2d'), tex: dt, ok: {} }; m3.detT.value = dt;
    }
    var D = m3.det, g = D.ctx, X = Math.round(c.px * s - N / 2), Y = Math.round(c.py * s - N / 2), id = D.id = (D.id || 0) + 1;   // (whole level px: the pieces are drawn 1:1)
    var old = D.z === L.z ? D.ok : {}, oX = D.X, oY = D.Y, ok = {};
    g.globalCompositeOperation = 'copy';
    if (D.z === L.z) g.drawImage(D.cv, oX - X, oY - Y); else g.clearRect(0, 0, N, N);   // (the same level: what's there, moved)
    g.globalCompositeOperation = 'destination-over';   // the map picture behind it, where there is nothing yet
    var q = mapImgEl.naturalWidth / IMG_W / s, sx0 = Math.max(0, X * q), sy0 = Math.max(0, Y * q), sx1 = Math.min(mapImgEl.naturalWidth, (X + N) * q), sy1 = Math.min(mapImgEl.naturalHeight, (Y + N) * q);
    if (sx1 > sx0 && sy1 > sy0) g.drawImage(mapImgEl, sx0, sy0, sx1 - sx0, sy1 - sy0, sx0 / q - X, sy0 / q - Y, (sx1 - sx0) / q, (sy1 - sy0) / q);
    g.globalCompositeOperation = 'source-over';
    D.z = L.z; D.X = X; D.Y = Y; D.px = c.px; D.py = c.py; D.ok = ok;
    m3.detR.value.set(X / s / IMG_W, 1 - (Y + N) / s / IMG_H, IMG_W * s / N, IMG_H * s / N);   // where it lies, in the map picture's uv
    D.tex.needsUpdate = true;
    function piece(z, folder, pc, pr, k, then){   // k: its px on the canvas per px of its own (2 = a base from one level down, enlarged)
      var key = z + folder + pc + '_' + pr, x = pc * t * k - X, y = pr * t * k - Y, w = t * k;
      if (old[key] && x + X >= oX && y + Y >= oY && x + X + w <= oX + N && y + Y + w <= oY + N){ ok[key] = 1; if (then) then(); return; }   // (all of it was there already)
      var im = new Image(); im.crossOrigin = 'anonymous';   // (the app fetches pieces from the web: without this the canvas couldn't be used in 3D)
      im.onload = im.onerror = function(e){
        if (!m3 || m3.det !== D || D.id !== id) return;   // (closed, or it looks somewhere else by now)
        if (e.type === 'load'){
          g.drawImage(im, pad, pad, t, t, x, y, w, w); ok[key] = 1; D.n = (D.n || 0) + 1;
          // (to the graphics card at most ~8 times a second while the pieces arrive: every time is 16 MB)
          if (!D.up) D.up = setTimeout(function(){ D.up = 0; if (m3 && m3.det === D){ D.tex.needsUpdate = true; m3Draw(); } }, 120);
        }
        if (then) then();
      };
      im.src = detailUrl(z, folder, pc, pr);
    }
    var B = DETAIL.lines && !L.baked ? detailBaseLevel(L) : null, sh = B ? L.z - B.z : 0, lf = linesFolder(mapStyle), groups = {};
    var c0 = Math.max(0, Math.floor(X / t)), c1 = Math.min(L.cols - 1, Math.floor((X + N - 1) / t)), r0 = Math.max(0, Math.floor(Y / t)), r1 = Math.min(L.rows - 1, Math.floor((Y + N - 1) / t));
    for (var r = r0; r <= r1; r++) for (var cc = c0; cc <= c1; cc++){
      if (L.have.charAt(r * L.cols + cc) !== '1') continue;
      if (!B){ piece(L.z, mapStyle, cc, r, 1); continue; }   // (old format / a big lake's zoom 14: the lines are in the picture)
      var cb = cc >> sh, rb = r >> sh, key = cb + '_' + rb, line = piece.bind(null, L.z, lf, cc, r, 1);
      if (B.have.charAt(rb * B.cols + cb) !== '1'){ line(); continue; }
      if (!groups[key]){ groups[key] = []; piece(B.z, mapStyle, cb, rb, 1 << sh, (function(list){ return function(){ list.forEach(function(f){ f(); }); }; })(groups[key])); }
      groups[key].push(line);
    }
  }
  function m3Draw(){ if (m3 && m3.r && !m3.raf) m3.raf = requestAnimationFrame(m3Frame); }
  function m3Touch(){ m3.t = Date.now(); clearTimeout(m3.rt); m3.rt = setTimeout(m3Draw, 230); m3Draw(); }   // (the later frame: the fine mesh for the new zoom, when the fingers rest)
  function m3Frame(){
    m3.raf = 0;
    if (!loadDepthGrid()){ m3Msg.textContent = 'Laddar djupdata …'; m3.rt = setTimeout(m3Draw, 300); return; }
    var c = m3Clamp(m3.c), W = innerWidth, H = innerHeight, M = WEB_METERS_PER_PX, R = m3R(c), CX = IMG_W / 2, CY = IMG_H / 2;
    if (!m3.far) m3.far = m3Make(0, 0, IMG_W, IMG_H, m3.matFar, m3.wmatFar);   // the whole map, once (again when the land's heights have come)
    var at = m3.at;
    if (!at || (Date.now() - m3.t > 200 && (Math.abs(Math.log(R / at.R)) > 0.3 || at.full !== (R >= M3_RFULL) || (!at.full && Math.hypot(c.px - at.px, c.py - at.py) * M > at.R * 0.25)))) m3Patch();
    if (Date.now() - m3.t > 200){   // the sharp patch: for this zoom, around this point (again when you've moved 15 % of it)
      var L = m3DetLevel(c), D = m3.det;
      if (!L){ m3.detR.value.z = 0; if (D) D.z = 0; }
      else if (!D || D.z !== L.z || Math.hypot(c.px - D.px, c.py - D.py) * Math.pow(2, L.z - ZOOM) / S > M3_TEX * 0.15) m3Detail(L);
    }
    var tx = (c.px - CX) * M, tz = (c.py - CY) * M, st = Math.sin(c.tilt), cam = m3.cam;
    var ty = m3.ty != null ? m3.ty : m3Ground(c.px, c.py);   // (the point you look at is on the ground: a hill isn't turned about a point deep inside it -- or, while fingers are down, at the height they hold it)
    cam.position.set(tx + c.d * st * Math.sin(c.az), ty + c.d * Math.cos(c.tilt), tz + c.d * st * Math.cos(c.az));   // (az 0 = from the south: north up)
    cam.position.y = Math.max(cam.position.y, m3Ground(CX + cam.position.x / M, CY + cam.position.z / M) + c.d * 0.04);   // (never under the ground: the land seen from inside is nothing at all)
    cam.lookAt(tx, ty, tz);
    if (m3Cfg.shadow){   // Skuggor: the sun's shadow map over a square of 2 x the distance around the point looked at (further out: no cast shadows)
      var sun = m3.sun, sc = sun.shadow.camera, sR = Math.min(M3_RFULL * 1.5, c.d * 2);
      sun.position.set(tx - sR * 1.2, ty + sR * 0.6, tz - sR * 1.2); sun.target.position.set(tx, ty, tz); sun.target.updateMatrixWorld();   // (as the light's own direction: -1, 0.5, -1)
      sc.left = sc.bottom = -sR; sc.right = sc.top = sR; sc.near = sR * 0.2; sc.far = sR * 4; sc.updateProjectionMatrix();
    }
    cam.near = c.d / 50; cam.far = c.d + M3_RFULL * 3;   // (as far as the map's other corner)
    if (m3.w !== W || m3.h !== H){ m3.w = W; m3.h = H; m3.r.setSize(W, H, false); cam.aspect = W / H; }
    cam.updateProjectionMatrix();
    [m3.far, m3.near].forEach(function(o){ if (o){ o.mesh.scale.y = m3Cfg.ex; o.water.visible = m3Cfg.water; } });
    m3.r.render(m3.scene, cam);
    m3.marks.forEach(function(k){   // the pins: where their spot on the ground is on the screen
      var v = m3.v.set((k.p.x - CX) * M, m3Ground(k.p.x, k.p.y), (k.p.y - CY) * M).project(cam);
      var on = v.z < 1 && Math.abs(v.x) < 1.2 && Math.abs(v.y) < 1.2;
      k.el.style.display = on ? '' : 'none';
      if (on){ k.el.style.left = ((v.x + 1) / 2 * W) + 'px'; k.el.style.top = ((1 - v.y) / 2 * H + k.dy) + 'px'; }
    });
    document.getElementById('m3North').firstChild.style.transform = 'rotate(' + c.az + 'rad)';
    m3Msg.textContent = '';
  }
  // the map's own pins and boats, copied (whatever the filter shows there, with the same icons) + you; called after every full render of the map
  function m3MarksSync(){
    if (!m3 || !m3.r) return;
    m3Marks.innerHTML = ''; m3Marks.className = waypointsLayer.className; m3.marks = [];
    function add(el, lat, lon, dy){
      var p = latLonToImgPx(lat, lon); m3Marks.appendChild(el);
      m3.marks.push({ el: el, p: p, dy: dy || 0 });
    }
    waypoints.forEach(function(wp){
      var el = pinEls[wp.id];
      if (el) add(el.cloneNode(true), wp.lat, wp.lon, el.classList.contains('wpPin') ? -PIN_TIP_OFFSET * wpScale * (isMine(wp) ? 1 : OTHER_PIN_SCALE) : 0);   // (a pin: its tip on the spot)
    });
    Array.prototype.forEach.call(boatsLayer.children, function(el){ var b = boatClustersById[el.getAttribute('data-cluster')]; if (b) add(el.cloneNode(true), b.lat, b.lon); });
    if (lastOwnLatLon){ var me = document.createElement('div'); me.className = 'm3Me'; add(me, lastOwnLatLon.lat, lastOwnLatLon.lon); }
    m3Draw();
  }
  function m3Open(cam){   // cam: where it looked before a rotation reload
    if (m3) return;
    m3View.classList.add('show'); m3Ui(); m3Msg.textContent = 'Laddar 3D …';
    m3 = { loading: true };
    m3LoadLand();
    nlLib().then(function(m){
      if (!m3) return;
      var T = m[0], r;
      // (logarithmicDepthBuffer: the far end of a big lake is 30 km away and the ground by you 50 m -- the water and the bottom under it flickered without)
      try { r = new T.WebGLRenderer({ canvas: m3Canvas, antialias: true, logarithmicDepthBuffer: true }); } catch(e){ m3Msg.textContent = 'Telefonen kan inte rita 3D'; return; }
      r.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2)); r.setClearColor(0x141822, 1); r.localClippingEnabled = true; r.shadowMap.enabled = true; r.shadowMap.type = T.PCFSoftShadowMap;
      var scene = new T.Scene();
      scene.add(new T.HemisphereLight(0xffffff, 0x8a94a8, 1.0));
      var sun = new T.DirectionalLight(0xffffff, 3.0); sun.position.set(-1, 0.5, -1); scene.add(sun, sun.target);
      sun.shadow.mapSize.set(2048, 2048); sun.shadow.bias = -0.0005; sun.shadow.normalBias = 0.02; sun.castShadow = m3Cfg.shadow;   // (Skuggor: 16 MB on the graphics card while on)   // (from the north-west, as the maps' relief -- low, so the bottom's shape shows: Filip 2026-11-12)
      // the map picture, fetched again as a picture of its own (from the browser's cache) -- NOT the map's <img>: three.js
      // sizes a texture by the element's size on the page, and a big lake's picture is shown at twice its own size (it came out black)
      var pic = new Image(), tex = new T.Texture(pic); tex.colorSpace = T.SRGBColorSpace; tex.anisotropy = r.capabilities.getMaxAnisotropy();
      pic.onload = function(){ tex.needsUpdate = true; m3Draw(); };
      pic.src = mapImgEl.src;
      var detT = { value: tex }, detR = { value: new T.Vector4(0, 0, 0, 0) }, colU = { value: new T.Vector2(m3Cfg.col ? 1 : 0, m3MaxDepth()) };   // (Djupfärg: on, the lake's deepest m)   // the sharp patch's picture and where it lies (z = 0: none)
      function plane(x, z){ return new T.Plane(new T.Vector3(x, 0, z), 0); }
      function cut(){ return [plane(-1, 0), plane(1, 0), plane(0, -1), plane(0, 1)]; }   // (m3Hole)
      function ground(planes){   // the ground's look: the sharp patch's picture instead of the map picture's where it reaches (faded in at its edge)
        var mt = new T.MeshLambertMaterial({ map: tex, clippingPlanes: planes, clipIntersection: true, clipShadows: true });
        mt.onBeforeCompile = function(sh){
          sh.uniforms.uDet = detT; sh.uniforms.uDetR = detR;
          sh.uniforms.uCol = colU;
          sh.vertexShader = sh.vertexShader.replace('#include <common>', '#include <common>\nvarying float vDY;').replace('#include <begin_vertex>', '#include <begin_vertex>\nvDY = transformed.y;');
          sh.fragmentShader = sh.fragmentShader.replace('#include <common>', '#include <common>\nuniform sampler2D uDet;\nuniform vec4 uDetR;\nuniform vec2 uCol;\nvarying float vDY;')
            .replace('#include <map_fragment>', '#include <map_fragment>\nvec2 dUv = (vMapUv - uDetR.xy) * uDetR.zw; vec2 dE = min(dUv, 1.0 - dUv);\n' +
              'diffuseColor.rgb = mix(diffuseColor.rgb, texture2D(uDet, dUv).rgb, uDetR.z > 0.0 ? smoothstep(0.0, 0.05, min(dE.x, dE.y)) : 0.0);\n' +
              // Djupfärg: Under ytan's colours (72-ar.js AR_COLS), shallow yellow-green to deep dark blue, over the lake's whole depth
              'float pf = clamp(-vDY / uCol.y, 0.0, 1.0); vec3 pg = mix(vec3(0.847, 0.961, 0.627), vec3(0.345, 0.816, 0.659), smoothstep(0.0, 0.2, pf));\n' +
              'pg = mix(pg, vec3(0.165, 0.604, 0.816), smoothstep(0.2, 0.45, pf)); pg = mix(pg, vec3(0.165, 0.361, 0.753), smoothstep(0.45, 0.7, pf)); pg = mix(pg, vec3(0.157, 0.110, 0.439), smoothstep(0.7, 1.0, pf));\n' +
              'if (uCol.x > 0.5 && vDY < -0.05) diffuseColor.rgb = pow(pg, vec3(2.2));');
        };
        return mt;
      }
      function wet(planes){ return new T.MeshBasicMaterial({ color: 0x2f7fd6, transparent: true, opacity: 0.22, depthWrite: false, clippingPlanes: planes, clipIntersection: true }); }
      // where the map looked, about as much of it: tilted, north up
      var c = cam || { px: (innerWidth / 2 - originX) / scale, py: (innerHeight / 2 - originY) / scale, d: innerHeight / scale * WEB_METERS_PER_PX * 1.2, az: 0, tilt: 0.95 };
      m3 = { T: T, r: r, scene: scene, cam: new T.PerspectiveCamera(M3_FOV, 1, 1, 1e5), tex: tex, v: new T.Vector3(), marks: [], t: 0, c: m3Clamp(c),
             detT: detT, detR: detR, colU: colU, sun: sun, cut: cut(), cutW: cut(), far: null, near: null };
      m3.mat = ground(null); m3.wmat = wet(null); m3.matFar = ground(m3.cut); m3.wmatFar = wet(m3.cutW);   // (the whole map's: left out where the fine mesh lies)
      m3MarksSync(); m3Draw();
    }).catch(function(){ m3Msg.textContent = 'Kunde inte ladda 3D'; });
  }
  function m3Close(){
    if (!m3) return;
    if (m3.raf) cancelAnimationFrame(m3.raf);
    clearTimeout(m3.rt);
    // all of it back from the GPU, as Under ytan -- and the canvas down to 1 px: three's dispose() keeps the drawing buffer (~40 MB on a phone)
    if (m3.r){
      m3.scene.traverse(function(o){ if (o.geometry) o.geometry.dispose(); });
      [m3.mat, m3.wmat, m3.matFar, m3.wmatFar, m3.tex].forEach(function(o){ o.dispose(); });
      if (m3.sun.shadow.map) m3.sun.shadow.map.dispose();
      m3.r.setSize(1, 1, false); m3.r.dispose();
    }
    if (m3.det){ m3.det.tex.dispose(); m3.det.cv.width = m3.det.cv.height = 1; }   // (the sharp patch: 16 MB of canvas)
    m3 = null; m3Land = null; m3P = {}; m3Marks.innerHTML = ''; m3View.classList.remove('show');   // (m3P: a finger still down on it must not count as one the next time)
  }
  // the controls
  function m3Ui(){
    var el = document.getElementById('m3Ex'); el.value = m3Cfg.ex; rangeFill(el);
    document.getElementById('m3ExVal').textContent = '× ' + String(m3Cfg.ex).replace('.', ',');
    document.querySelector('#m3Chips [data-k=water]').classList.toggle('on', m3Cfg.water);
    document.querySelector('#m3Chips [data-k=col]').classList.toggle('on', m3Cfg.col);
    if (m3 && m3.colU) m3.colU.value.x = m3Cfg.col ? 1 : 0;
    document.querySelector('#m3Chips [data-k=shadow]').classList.toggle('on', m3Cfg.shadow);
    if (m3 && m3.sun){ m3.sun.castShadow = m3Cfg.shadow; if (!m3Cfg.shadow && m3.sun.shadow.map){ m3.sun.shadow.map.dispose(); m3.sun.shadow.map = null; } }   // (off: its 16 MB back)
    var src = document.getElementById('m3Src'); src.hidden = !LAKE.land; src.textContent = LAKE.land ? LAKE.land.credit : '';   // (whose heights: asked for by their licences)
  }
  document.getElementById('m3Ex').addEventListener('input', function(e){ m3Cfg.ex = +e.target.value; m3Save(); m3Ui(); m3Draw(); });
  document.getElementById('m3Chips').addEventListener('click', function(e){
    var b = e.target.closest('button'); if (!b || !m3 || !m3.r) return;
    if (b.id === 'm3Me'){ if (lastOwnLatLon){ var p = latLonToImgPx(lastOwnLatLon.lat, lastOwnLatLon.lon); m3.c.px = p.x; m3.c.py = p.y; m3Touch(); } return; }
    var k = b.getAttribute('data-k'); m3Cfg[k] = !m3Cfg[k]; m3Save(); m3Ui(); m3Draw();
  });
  document.getElementById('m3North').addEventListener('click', function(){ if (m3 && m3.r){ m3.c.az = 0; m3Touch(); } });
  document.getElementById('m3Close').addEventListener('click', m3Close);
  /* The fingers, as in the map apps (Filip 2026-11-11; first one finger turned and tilted and two moved): one = move
     the map; two = pinch to zoom and twist to turn, or -- side by side, both moved up or down -- tilt (up = towards the
     horizon). With a mouse: Shift / Ctrl + drag = turn and tilt. What a grip is, is decided by its first move.
     What the fingers took hold of (the bottom, a hill) stays under them: while they are down the point looked at keeps
     its height (m3.ty) -- the camera doesn't go up and down with the land it is moved over -- and lies at the height of
     what they hold. All fingers up: it is put back on the ground, along the line of sight (nothing moves in the picture). */
  // the ray from the camera through a place on the screen -- where it is at t (1 = as far in as the point looked at):
  // x, y = map-picture px from that point, up = m over it. No t: where it meets flat ground at that point's height (near
  // the horizon and above it as if the ground ended 3 x as far away: a touch there would else fling the map away)
  function m3At(x, y, t){
    var c = m3.c, q = Math.tan(M3_FOV * Math.PI / 360) / innerHeight, a = (2 * x - innerWidth) * q, b = (innerHeight - 2 * y) * q;
    var st = Math.sin(c.tilt), ct = Math.cos(c.tilt), sa = Math.sin(c.az), ca = Math.cos(c.az), w = ct - b * st;
    if (t === undefined) t = Math.min(3, ct / Math.max(1e-6, w));
    var f = st - t * (b * ct + st), k = c.d / WEB_METERS_PER_PX;
    return { x: k * (t * a * ca + f * sa), y: k * (f * ca - t * a * sa), up: c.d * (ct - t * w) };
  }
  // ...and how far in (t) that ray first goes under h(x, y), a height at a map-picture px (0: not before t = far)
  function m3Cast(x, y, h, far){
    for (var i = 0, n = 240, u, pu; i <= n; i++, pu = u){
      var p = m3At(x, y, far * i / n); u = m3.ty + p.up - h(m3.c.px + p.x, m3.c.py + p.y);
      if (u < 1e-3) return i ? far * (i - u / (u - pu)) / n : 0;   // (between the last two steps, where it went under)
    }
    return 0;
  }
  function m3Surf(x, y){ var d = depthAtImgPx(x, y); return (d !== null ? -d : isLakeAtImgPx(x, y) ? -0.2 : Math.max(0.3, m3LandAt(x, y))) * m3Cfg.ex; }   // what is drawn at a map-picture px: the bottom, or the land (as m3Make's points; water nobody has charted: about the water's level, which is what a finger takes hold of there)
  // the point looked at, moved along the line of sight to s m from the camera -- which stays where it is
  function m3Slide(s){
    var c = m3.c, k = (c.d - s) * Math.sin(c.tilt) / WEB_METERS_PER_PX;
    if (!(s >= 60 && s <= M3_RFULL * 3)) return;   // (m3Clamp would move the camera)
    m3.ty += (c.d - s) * Math.cos(c.tilt); c.px += k * Math.sin(c.az); c.py += k * Math.cos(c.az); c.d = s;
  }
  var m3P = {}, m3G = '', m3Tw = 0;   // the fingers down; what they do ('' = not decided, 'move', 'tilt', 'turn') and how far two have twisted
  function m3Grip(){   // a finger more or less: a new grip, from where they are now
    m3G = ''; m3Tw = 0;
    for (var k in m3P){ m3P[k].x0 = m3P[k].x; m3P[k].y0 = m3P[k].y; }
    if (k || !m3 || !m3.r || m3.ty == null) return;
    var c = m3.c;   // all up: the point looked at back onto the ground (no further than to the water's level)
    m3Slide(c.d * m3Cast(innerWidth / 2, innerHeight / 2, m3Ground, 1 + m3.ty / (c.d * Math.cos(c.tilt))));
    m3.ty = null; m3Touch();
  }
  function m3Up(e){ delete m3P[e.pointerId]; m3Grip(); }
  m3Canvas.addEventListener('pointerdown', function(e){ if (e.altKey || e.button === 1) e.preventDefault(); m3P[e.pointerId] = { x: e.clientX, y: e.clientY, b: e.button, alt: e.altKey }; m3Grip(); m3Canvas.setPointerCapture(e.pointerId); });
  m3Canvas.addEventListener('contextmenu', function(e){ e.preventDefault(); });   // (Alt + right = zoom: no menu)
  m3Canvas.addEventListener('pointerup', m3Up); m3Canvas.addEventListener('pointercancel', m3Up);
  m3Canvas.addEventListener('pointermove', function(e){
    var p = m3P[e.pointerId]; if (!p || !m3 || !m3.r) return;
    var c = m3.c, x = e.clientX, y = e.clientY, ids = Object.keys(m3P), o = ids.length > 1 ? m3P[ids[0] === String(e.pointerId) ? ids[1] : ids[0]] : null;
    var mx = o ? (x + o.x) / 2 : x, my = o ? (y + o.y) / 2 : y;   // the finger, or the middle of the two
    if (m3.ty == null) m3.ty = m3Ground(c.px, c.py);
    if (!m3G){   // a new grip: this move only decides what it is -- two fingers when both have moved a little (or one of them a lot)
      // a mouse as in Maya / Houdini (Filip 2026-11-12): Alt + left = turn and tilt, Alt + middle (or middle alone) = move,
      // Alt + right = zoom; Shift / Ctrl + left = turn too
      if (!o) m3G = p.alt && p.b === 2 ? 'dolly' : p.b !== 1 && (p.alt || e.shiftKey || e.ctrlKey) ? 'turn' : 'move';
      else {
        var ma = Math.hypot(x - p.x0, y - p.y0), mb = Math.hypot(o.x - o.x0, o.y - o.y0);
        if (Math.min(ma, mb) >= 4 || Math.max(ma, mb) >= 24)
        { // tilt: both up (or down) together, roughly side by side, and not pinched -- forgiving, as in the map apps (Filip 2026-11-12: it was hard to hit)
          var ya = y - p.y0, yb = o.y - o.y0, pinch = Math.abs(Math.hypot(x - o.x, y - o.y) - Math.hypot(p.x0 - o.x0, p.y0 - o.y0));
          m3G = ya * yb > 0 && Math.abs(ya + yb) > 1.2 * Math.abs(x - p.x0 + o.x - o.x0) && pinch < 0.6 * Math.abs(ya + yb) / 2 + 3 &&
                Math.abs(p.x0 - o.x0) > 0.5 * Math.abs(p.y0 - o.y0) ? 'tilt' : 'move';
        }
      }
      if (m3G === 'move'){   // the point looked at to the height of what the fingers are on
        var t = m3Cast(mx, my, m3Surf, 3);
        if (t) m3Slide(c.d - m3At(mx, my, t).up / Math.cos(c.tilt));
      }
    }
    else if (m3G === 'turn'){ c.az -= (x - p.x) * 0.006; c.tilt -= (y - p.y) * 0.005; }
    else if (m3G === 'dolly'){ c.d *= Math.exp(-(x - p.x + y - p.y) * 0.005); m3Clamp(c); }   // (right or down = nearer, as in Maya)
    else if (m3G === 'tilt') c.tilt -= (y - p.y) * 0.0025;   // (half each finger: as fast as the mouse)
    else {
      var g = m3At(o ? (p.x + o.x) / 2 : p.x, o ? (p.y + o.y) / 2 : p.y);   // what was under the finger (the middle of the two) ...
      if (o){
        var ux = p.x - o.x, uy = p.y - o.y, vx = x - o.x, vy = y - o.y, d0 = Math.hypot(ux, uy), d1 = Math.hypot(vx, vy);
        if (d0 > 10 && d1 > 10){
          c.d *= d0 / d1;
          var da = Math.atan2(ux * vy - uy * vx, ux * vx + uy * vy);   // (clockwise on the screen = the map clockwise)
          m3Tw += da; if (Math.abs(m3Tw) > 0.2) c.az += da;   // (not until they've twisted 11 degrees: a pinch alone shouldn't turn the map)
        }
      }
      m3Clamp(c);
      var h = m3At(mx, my); c.px += g.x - h.x; c.py += g.y - h.y;   // ... is under it still
    }
    p.x = x; p.y = y; m3Touch();
  });
  m3Canvas.addEventListener('wheel', function(e){ if (m3 && m3.r){ e.preventDefault(); m3.c.d *= Math.exp(e.deltaY * 0.0015); m3Touch(); } }, { passive: false });
  window.addEventListener('resize', m3Draw);
  m3Canvas.addEventListener('webglcontextlost', m3Close);   // (iOS took the 3D away, e.g. the app was put aside: close rather than show a black picture)
  window.__ffMap3d = function(o){   // (for the tests: o = camera values to set -- or o.at = [x, y]: "hit" for that place on the screen)
    var at = o && o.at;
    if (o && !o.pic && !at && m3 && m3.r){ Object.assign(m3.c, o); m3Touch(); }
    var hit = null;   // where the middle of the screen meets the ground (the fine mesh where there is one): its height (m, unscaled), place and how far from the camera
    if (m3 && m3.far){
      var rc = new m3.T.Raycaster(); rc.setFromCamera(new m3.T.Vector2(at ? at[0] / innerWidth * 2 - 1 : 0, at ? 1 - at[1] / innerHeight * 2 : 0), m3.cam);
      // (the whole map's mesh only where it is drawn: not where it is cut out for the fine one -- the fine one may have a hole there)
      var h = (m3.near && rc.intersectObject(m3.near.mesh)[0]) || rc.intersectObject(m3.far.mesh).filter(function(f){ return !m3.cut.every(function(pl){ return pl.distanceToPoint(f.point) < 0; }); })[0];
      if (h) hit = { y: h.point.y / m3Cfg.ex, d: h.distance, at: imgPxToLatLon(IMG_W / 2 + h.point.x / WEB_METERS_PER_PX, IMG_H / 2 + h.point.z / WEB_METERS_PER_PX) };
    }
    var det = m3 && m3.det && m3.det.z ? { z: m3.det.z, n: m3.det.n || 0, X: m3.det.X, Y: m3.det.Y, url: o && o.pic ? m3.det.cv.toDataURL('image/jpeg', 0.6) : '' } : null;   // (the sharp patch; pic: its picture too)
    return { land: !!(m3Land && m3Land.length), det: det, hit: hit, open: !!m3, ready: !!(m3 && m3.far && m3.at), n: m3 && m3.n, builds: m3 && m3.nb, c: m3 && m3.c, cam: m3 && m3.cam ? m3.cam.position.toArray() : null, at: m3 && m3.at, marks: m3 && m3.marks ? m3.marks.length : 0, cfg: m3Cfg };
  };
