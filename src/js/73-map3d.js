  /* ================= 3D-karta: the lake's bottom and the land around it in 3D =================
     In the map-style list (hold the map button), right after the map styles: a full-screen view of its own -- the map
     itself is untouched underneath. ONE mesh of at most M3_NMAX points a side around the point you look at: zoomed in =
     a small area with every depth cell, zoomed out = the whole lake, coarser (built again when the fingers have rested
     0,2 s, like Under ytan's slider). On it the chosen map style's picture (aerial photo on land, Genesis' colours and
     lines on the water -- nothing of that is drawn here), lit from the north-west like the maps' relief. y = -depth in
     the water; on land the height above the lake from LAKE.land (tools/land_height.py: a small file per lake, fetched
     when the view opens; a lake without one, or no coverage the first time = flat land).
     Near the point you look at the picture is sharp: the zoom level's pieces (the same as the map's own, 12-map.js) put
     together on ONE canvas of M3_TEX px, shown instead of the map picture where it reaches (m3Detail).
     One finger = turn and tilt, two = move, pinch = zoom (three.js' OrbitControls isn't in the app's build).
     Your boat, the spots and the others' boats: the map's own pins copied on top (the same filter and icons; view only).
     Settings: ffmap_3d_v1 (Höjd ×, Vatten). Drawn only when something changed -- no loop runs. Filip 2026-11-11. */
  var M3_KEY = 'ffmap_3d_v1', M3_NMAX = 400, M3_FOV = 40;   // ponytail: one mesh, rebuilt as you zoom -- a coarse whole lake + a fine patch if the rebuild shows
  var M3_RFULL = Math.max(IMG_W, IMG_H) * WEB_METERS_PER_PX / 2;   // half the map's long side (m): from here on the mesh is the whole map
  var M3_TEX = 2048;   // the sharp patch's canvas (px a side): 4 x 4 pieces
  var m3Cfg = { ex: 3, water: true };
  try { m3Cfg = Object.assign(m3Cfg, JSON.parse(localStorage.getItem(M3_KEY) || '{}')); } catch(e){}
  var m3View = document.getElementById('m3View'), m3Canvas = document.getElementById('m3Canvas'), m3Marks = document.getElementById('m3Marks'), m3Msg = document.getElementById('m3Msg');
  var m3 = null;   // while open: { T, r, scene, cam, mesh, water, tex, c: the camera { px, py (the image px looked at), d (m away), az, tilt (0 = straight down) }, at: what the mesh was built for }
  function m3Save(){ try { localStorage.setItem(M3_KEY, JSON.stringify(m3Cfg)); } catch(e){} }
  var m3Land = null;   // the land's heights while the view is open: a byte per cell x LAKE.land.step = m above the lake, 255 = lake (1 = asked for)
  function m3LoadLand(){
    if (!LAKE.land || m3Land) return;
    m3Land = 1;
    fetch(lakeUrl(LAKE.land.file)).then(function(r){ return r.ok ? r.text() : Promise.reject(); }).then(function(t){
      if (!m3) return;
      m3Land = unpackGrid(t.trim(), LAKE.land.w * LAKE.land.h);
      if (m3.r){ m3.at = null; m3MarksSync(); }   // (the mesh and the pins again, with the land)
    }).catch(function(){ m3Land = null; });        // (no coverage: flat land; asked again the next time it opens)
  }
  function m3Ground(x, y){ return isLakeAtImgPx(x, y) ? 0 : m3LandAt(x, y) * m3Cfg.ex; }   // the ground's (the water's) height in the picture at a map-picture px
  function m3LandAt(x, y){   // m above the lake at a map-picture px (0: in the lake, or no heights)
    var v = m3Land && m3Land.length ? gridValAt(m3Land, LAKE.land.w, LAKE.land.h, x, y) : null;
    return v === null ? 0 : v * LAKE.land.step;
  }
  function m3Clamp(c){
    c.px = Math.max(0, Math.min(IMG_W, c.px)); c.py = Math.max(0, Math.min(IMG_H, c.py));
    c.d = Math.max(60, Math.min(M3_RFULL * 3, c.d)); c.tilt = Math.max(0.05, Math.min(1.45, c.tilt));
    return c;
  }
  function m3R(c){ return Math.min(M3_RFULL, Math.max(150, c.d * 1.6)); }   // how far out the mesh goes for this zoom (m)
  // the mesh: the map's rectangle within R of the point you look at; x = east, z = south (m), y = -depth (scaled by Höjd ×)
  function m3Build(){
    var T = m3.T, c = m3.c, R = m3R(c), full = R >= M3_RFULL, M = WEB_METERS_PER_PX;
    var cx = full ? IMG_W / 2 : c.px, cy = full ? IMG_H / 2 : c.py, rp = R / M;
    var x0 = Math.max(0, cx - rp), x1 = Math.min(IMG_W, cx + rp), y0 = Math.max(0, cy - rp), y1 = Math.min(IMG_H, cy + rp);
    var k = Math.max(AR_CELL / M, Math.max(x1 - x0, y1 - y0) / M3_NMAX);   // image px a step: never finer than the depth cells
    var nx = Math.max(2, Math.floor((x1 - x0) / k) + 1), ny = Math.max(2, Math.floor((y1 - y0) / k) + 1);
    var pos = new Float32Array(nx * ny * 3), uv = new Float32Array(nx * ny * 2), wet = new Uint8Array(nx * ny), idx = [], widx = [];
    for (var j = 0; j < ny; j++) for (var i = 0; i < nx; i++){
      var q = j * nx + i, x = x0 + i * k, y = y0 + j * k, d = depthAtImgPx(x, y);
      wet[q] = d !== null || isLakeAtImgPx(x, y) ? 1 : 0;
      pos[q * 3] = (x - cx) * M; pos[q * 3 + 2] = (y - cy) * M;
      pos[q * 3 + 1] = d !== null ? -d : wet[q] ? -0.2 : Math.max(0.3, m3LandAt(x, y));   // (lake nobody has logged: just under the surface; land: never lower than just over it -- the water's surface never lies on the land)
      uv[q * 2] = x / IMG_W; uv[q * 2 + 1] = 1 - y / IMG_H;
    }
    for (j = 0; j < ny - 1; j++) for (i = 0; i < nx - 1; i++){
      var a = j * nx + i, b = a + 1, e = a + nx; idx.push(a, e, b, b, e, e + 1);
      if (wet[a] || wet[b] || wet[e] || wet[e + 1]) widx.push(a, e, b, b, e, e + 1);   // (the water's surface: where the lake is, a cell in over the shore)
    }
    if (m3.mesh){ m3.scene.remove(m3.mesh, m3.water); m3.mesh.geometry.dispose(); m3.water.geometry.dispose(); }
    var g = new T.BufferGeometry();
    g.setAttribute('position', new T.BufferAttribute(pos, 3)); g.setAttribute('uv', new T.BufferAttribute(uv, 2)); g.setIndex(idx); g.computeVertexNormals();
    m3.mesh = new T.Mesh(g, m3.mat);
    var wp = pos.slice(), wg = new T.BufferGeometry();   // the water's surface: the same points at height 0
    for (q = 1; q < wp.length; q += 3) wp[q] = 0;
    wg.setAttribute('position', new T.BufferAttribute(wp, 3)); wg.setIndex(widx);
    m3.water = new T.Mesh(wg, m3.wmat);
    m3.scene.add(m3.mesh, m3.water);
    m3.at = { px: cx, py: cy, R: R, full: full }; m3.n = Math.max(nx, ny); m3.nb = (m3.nb || 0) + 1;
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
  function m3Touch(){ m3.t = Date.now(); clearTimeout(m3.rt); m3.rt = setTimeout(m3Draw, 230); m3Draw(); }   // (the later frame: the mesh for the new zoom, when the fingers rest)
  function m3Frame(){
    m3.raf = 0;
    if (!loadDepthGrid()){ m3Msg.textContent = 'Laddar djupdata …'; m3.rt = setTimeout(m3Draw, 300); return; }
    var c = m3Clamp(m3.c), at = m3.at, W = innerWidth, H = innerHeight, M = WEB_METERS_PER_PX, R = m3R(c);
    if (!at || (Date.now() - m3.t > 200 && (Math.abs(Math.log(R / at.R)) > 0.3 || (!(at.full && R >= M3_RFULL) && Math.hypot(c.px - at.px, c.py - at.py) * M > at.R * 0.25)))){ m3Build(); at = m3.at; }
    if (Date.now() - m3.t > 200){   // the sharp patch: for this zoom, around this point (again when you've moved 15 % of it)
      var L = m3DetLevel(c), D = m3.det;
      if (!L){ m3.detR.value.z = 0; if (D) D.z = 0; }
      else if (!D || D.z !== L.z || Math.hypot(c.px - D.px, c.py - D.py) * Math.pow(2, L.z - ZOOM) / S > M3_TEX * 0.15) m3Detail(L);
    }
    var tx = (c.px - at.px) * M, tz = (c.py - at.py) * M, st = Math.sin(c.tilt), cam = m3.cam, fog = m3.scene.fog;
    var ty = m3Ground(c.px, c.py);   // (the point you look at is on the ground: a hill isn't turned about a point deep inside it)
    cam.position.set(tx + c.d * st * Math.sin(c.az), ty + c.d * Math.cos(c.tilt), tz + c.d * st * Math.cos(c.az));   // (az 0 = from the south: north up)
    cam.position.y = Math.max(cam.position.y, m3Ground(at.px + cam.position.x / M, at.py + cam.position.z / M) + c.d * 0.04);   // (never under the ground: the land seen from inside is nothing at all)
    cam.lookAt(tx, ty, tz);
    cam.near = c.d / 50; cam.far = c.d + at.R * 4;
    if (m3.w !== W || m3.h !== H){ m3.w = W; m3.h = H; m3.r.setSize(W, H, false); cam.aspect = W / H; }
    cam.updateProjectionMatrix();
    fog.near = at.full ? 1e9 : c.d + at.R * 0.45; fog.far = at.full ? 2e9 : c.d + at.R * 0.95;   // (the mesh's far edge fades out; the whole map: no fog)
    m3.mesh.scale.y = m3Cfg.ex; m3.water.visible = m3Cfg.water;
    m3.r.render(m3.scene, cam);
    m3.marks.forEach(function(k){   // the pins: where their spot on the surface is on the screen
      var v = m3.v.set((k.p.x - at.px) * M, m3Ground(k.p.x, k.p.y), (k.p.y - at.py) * M), gone = v.distanceTo(cam.position) > fog.far;
      v.project(cam);
      var on = !gone && v.z < 1 && Math.abs(v.x) < 1.2 && Math.abs(v.y) < 1.2;
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
      try { r = new T.WebGLRenderer({ canvas: m3Canvas, antialias: true }); } catch(e){ m3Msg.textContent = 'Telefonen kan inte rita 3D'; return; }
      r.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2)); r.setClearColor(0x141822, 1);
      var scene = new T.Scene(); scene.fog = new T.Fog(0x141822, 1, 2);
      scene.add(new T.HemisphereLight(0xffffff, 0x8a94a8, 1.6));
      var sun = new T.DirectionalLight(0xffffff, 2.2); sun.position.set(-1, 1.3, -1); scene.add(sun);   // (from the north-west, as the maps' relief)
      var tex = new T.Texture(mapImgEl); tex.colorSpace = T.SRGBColorSpace; tex.anisotropy = r.capabilities.getMaxAnisotropy();
      if (mapImgEl.complete && mapImgEl.naturalWidth) tex.needsUpdate = true;
      else mapImgEl.addEventListener('load', function(){ tex.needsUpdate = true; m3Draw(); }, { once: true });
      // where the map looked, about as much of it: tilted, north up
      var c = cam || { px: (innerWidth / 2 - originX) / scale, py: (innerHeight / 2 - originY) / scale, d: innerHeight / scale * WEB_METERS_PER_PX * 1.2, az: 0, tilt: 0.95 };
      m3 = { T: T, r: r, scene: scene, cam: new T.PerspectiveCamera(M3_FOV, 1, 1, 1e5), tex: tex, v: new T.Vector3(), marks: [], t: 0, c: m3Clamp(c),
             detT: { value: tex }, detR: { value: new T.Vector4(0, 0, 0, 0) },   // the sharp patch's picture and where it lies (z = 0: none)
             mat: new T.MeshLambertMaterial({ map: tex }),
             wmat: new T.MeshBasicMaterial({ color: 0x2f7fd6, transparent: true, opacity: 0.22, depthWrite: false }) };
      // the sharp patch's picture instead of the map picture's where it reaches (faded in at its edge)
      m3.mat.onBeforeCompile = function(sh){
        sh.uniforms.uDet = m3.detT; sh.uniforms.uDetR = m3.detR;
        sh.fragmentShader = sh.fragmentShader.replace('#include <common>', '#include <common>\nuniform sampler2D uDet;\nuniform vec4 uDetR;')
          .replace('#include <map_fragment>', '#include <map_fragment>\nvec2 dUv = (vMapUv - uDetR.xy) * uDetR.zw; vec2 dE = min(dUv, 1.0 - dUv);\n' +
            'diffuseColor.rgb = mix(diffuseColor.rgb, texture2D(uDet, dUv).rgb, uDetR.z > 0.0 ? smoothstep(0.0, 0.05, min(dE.x, dE.y)) : 0.0);');
      };
      m3MarksSync(); m3Draw();
    }).catch(function(){ m3Msg.textContent = 'Kunde inte ladda 3D'; });
  }
  function m3Close(){
    if (!m3) return;
    if (m3.raf) cancelAnimationFrame(m3.raf);
    clearTimeout(m3.rt);
    // all of it back from the GPU, as Under ytan -- and the canvas down to 1 px: three's dispose() keeps the drawing buffer (~40 MB on a phone)
    if (m3.r){ m3.scene.traverse(function(o){ if (o.geometry) o.geometry.dispose(); if (o.material) o.material.dispose(); }); m3.tex.dispose(); m3.r.setSize(1, 1, false); m3.r.dispose(); }
    if (m3.det){ m3.det.tex.dispose(); m3.det.cv.width = m3.det.cv.height = 1; }   // (the sharp patch: 16 MB of canvas)
    m3 = null; m3Land = null; m3Marks.innerHTML = ''; m3View.classList.remove('show');
  }
  // the controls
  function m3Ui(){
    var el = document.getElementById('m3Ex'); el.value = m3Cfg.ex; rangeFill(el);
    document.getElementById('m3ExVal').textContent = '× ' + String(m3Cfg.ex).replace('.', ',');
    document.querySelector('#m3Chips [data-k=water]').classList.toggle('on', m3Cfg.water);
    var src = document.getElementById('m3Src'); src.hidden = !LAKE.land; src.textContent = LAKE.land ? LAKE.land.credit : '';   // (whose heights: asked for by their licences)
  }
  document.getElementById('m3Ex').addEventListener('input', function(e){ m3Cfg.ex = +e.target.value; m3Save(); m3Ui(); m3Draw(); });
  document.getElementById('m3Chips').addEventListener('click', function(e){
    var b = e.target.closest('button'); if (!b || !m3 || !m3.r) return;
    if (b.id === 'm3Me'){ if (lastOwnLatLon){ var p = latLonToImgPx(lastOwnLatLon.lat, lastOwnLatLon.lon); m3.c.px = p.x; m3.c.py = p.y; m3Touch(); } return; }
    m3Cfg.water = !m3Cfg.water; m3Save(); m3Ui(); m3Draw();
  });
  document.getElementById('m3North').addEventListener('click', function(){ if (m3 && m3.r){ m3.c.az = 0; m3Touch(); } });
  document.getElementById('m3Close').addEventListener('click', m3Close);
  // the fingers: one = turn (sideways) and tilt (up/down); two = move the ground with them, pinch = nearer/farther
  var m3P = {};
  function m3Up(e){ delete m3P[e.pointerId]; }
  m3Canvas.addEventListener('pointerdown', function(e){ m3P[e.pointerId] = { x: e.clientX, y: e.clientY }; m3Canvas.setPointerCapture(e.pointerId); });
  m3Canvas.addEventListener('pointerup', m3Up); m3Canvas.addEventListener('pointercancel', m3Up);
  m3Canvas.addEventListener('pointermove', function(e){
    var p = m3P[e.pointerId]; if (!p || !m3 || !m3.r) return;
    var c = m3.c, dx = e.clientX - p.x, dy = e.clientY - p.y, ids = Object.keys(m3P);
    if (ids.length === 1){ c.az -= dx * 0.006; c.tilt -= dy * 0.005; }
    else {
      var o = m3P[ids[0] === String(e.pointerId) ? ids[1] : ids[0]], d0 = Math.hypot(p.x - o.x, p.y - o.y), d1 = Math.hypot(e.clientX - o.x, e.clientY - o.y);
      if (d0 > 10 && d1 > 10) c.d *= d0 / d1;
      // (this finger moves the middle of the two by half its own move) a screen px on the ground, in image px; up/down is foreshortened by the tilt
      var m = c.d * 2 * Math.tan(M3_FOV * Math.PI / 360) / innerHeight / WEB_METERS_PER_PX / 2, f = dy * m / Math.max(0.3, Math.cos(c.tilt)), s = dx * m;
      c.px += -s * Math.cos(c.az) - f * Math.sin(c.az); c.py += s * Math.sin(c.az) - f * Math.cos(c.az);
    }
    p.x = e.clientX; p.y = e.clientY; m3Touch();
  });
  m3Canvas.addEventListener('wheel', function(e){ if (m3 && m3.r){ e.preventDefault(); m3.c.d *= Math.exp(e.deltaY * 0.0015); m3Touch(); } }, { passive: false });
  window.addEventListener('resize', m3Draw);
  m3Canvas.addEventListener('webglcontextlost', m3Close);   // (iOS took the 3D away, e.g. the app was put aside: close rather than show a black picture)
  window.__ffMap3d = function(o){   // (for the tests: o = camera values to set)
    if (o && !o.pic && m3 && m3.r){ Object.assign(m3.c, o); m3Touch(); }
    var hit = null;   // where the middle of the screen meets the mesh: its height (m, unscaled) and place
    if (m3 && m3.mesh){
      var rc = new m3.T.Raycaster(); rc.setFromCamera(new m3.T.Vector2(0, 0), m3.cam);
      var h = rc.intersectObject(m3.mesh)[0];
      if (h) hit = { y: h.point.y / m3Cfg.ex, at: imgPxToLatLon(m3.at.px + h.point.x / WEB_METERS_PER_PX, m3.at.py + h.point.z / WEB_METERS_PER_PX) };
    }
    var det = m3 && m3.det && m3.det.z ? { z: m3.det.z, n: m3.det.n || 0, X: m3.det.X, Y: m3.det.Y, url: o && o.pic ? m3.det.cv.toDataURL('image/jpeg', 0.6) : '' } : null;   // (the sharp patch; pic: its picture too)
    return { land: !!(m3Land && m3Land.length), det: det, hit: hit, open: !!m3, ready: !!(m3 && m3.mesh), n: m3 && m3.n, builds: m3 && m3.nb, c: m3 && m3.c, at: m3 && m3.at, marks: m3 && m3.marks ? m3.marks.length : 0, cfg: m3Cfg };
  };
