  /* ================= Under ytan (AR): the lake's bottom in 3D through the camera =================
     Last in the map-style list (hold the map button): a full-screen view, nothing else of the app,: the camera's picture (or dark, camera off) with the
     bottom around you drawn on top in 3D (three.js, loaded like the logo's: nlLib, 35-logo3d.js). Where you are = GPS
     (no fix: the map's centre); where the phone looks = deviceorientation (iOS: webkitCompassHeading for north, asked
     in the tap like the compass, 53-compass.js; Demo Mode: the demo boat -- "Båten hit" in a new spot's sheet puts it there). The water's surface is not measured: depths count from it and the eye is
     "Ögonhöjd" above it (1 m, sitting in a boat). A drag sideways turns the bottom (the compass can be 10-20 degrees off),
     remembered. Settings (ffmap_ar_v1): camera, Avstånd 100-1000 m, Djup × 1-5, Ögonhöjd 0,5-3 m. Filip 2026-10-12. */
  var AR_KEY = 'ffmap_ar_v1';
  // as fine as the depth data (one point per cell: Regnaren ~5 m, Sjösjön ~2 m), at most AR_NMAX points a side
  var AR_CELL = IMG_W / DEPTH_W * WEB_METERS_PER_PX, AR_NMAX = 400;   // ponytail: 400² = 160k points -- the whole radius at once; nearer-finer rings if a phone can't keep up
  var AR_FOV = 62;   // ponytail: one vertical field of view for every phone's camera (portrait); per-model if it's visibly off
  var arCfg = { cam: true, r: 300, ex: 3, eye: 1, north: 0, grid: true, surf: true, dots: false, waves: false, shore: true, sticks: true, lod: true };   // (from grid: the switches in the controls -- all on trial, Filip 2026-10-12)
  try { arCfg = Object.assign(arCfg, JSON.parse(localStorage.getItem(AR_KEY) || '{}')); } catch(e){}
  var arView = document.getElementById('arView'), arVideo = document.getElementById('arVideo'), arMsg = document.getElementById('arMsg');
  var ar = null;   // { T, r, scene, cam, mesh, lines, at:{px,py,r}, raf } while open
  var arOri = null, arCorr = null, arStream = null;
  function arSave(){ try { localStorage.setItem(AR_KEY, JSON.stringify(arCfg)); } catch(e){} }

  // depth colour: light green in the shallows -> blue -> deep violet (prövat 2026-10-12: rött -> mörkblått -- the old ones were better)
  var AR_COLS = [[0, 0xd8f5a0], [0.2, 0x58d0a8], [0.45, 0x2a9ad0], [0.7, 0x2a5cc0], [1, 0x281c70]];
  function arColor(T, d, max){
    var f = Math.min(1, d / max), i = 1; while (i < AR_COLS.length - 1 && AR_COLS[i][0] < f) i++;
    var a = AR_COLS[i - 1], b = AR_COLS[i];
    return new T.Color(a[1]).lerp(new T.Color(b[1]), (f - a[0]) / (b[0] - a[0]));
  }
  function arWhere(){   // the image px the bottom is built around
    if (lastFix && lastFix.onMap) return { px: lastFix.px, py: lastFix.py, gps: true };
    return { px: (innerWidth / 2 - originX) / scale, py: (innerHeight / 2 - originY) / scale, gps: false };
  }
  // the bottom: N x N points over 2r x 2r around you; x = east, z = south, y = -depth (the mesh is scaled by Djup ×)
  function arBuild(){
    var T = ar.T, w = arWhere(), R = arCfg.r, AR_N = Math.max(64, Math.min(AR_NMAX, Math.round(2 * R / AR_CELL))), n = AR_N + 1, k = 2 * R / AR_N / WEB_METERS_PER_PX;
    var h = 2 * R / AR_N, gl = Math.max(1, Math.round(10 / h)), gn = Math.max(1, Math.round(5 / h)), gs = Math.max(1, Math.round(20 / h));   // the bottom's grid every ~10 m (~5 m near you), the surface's ~20 m
    function near(i, j, m){ return Math.hypot((i - AR_N / 2) * h, (j - AR_N / 2) * h) < m; }
    var pos = new Float32Array(n * n * 3), col = new Float32Array(n * n * 3), ok = new Uint8Array(n * n), max = LAKE.depth.max || 20;
    for (var j = 0; j < n; j++) for (var i = 0; i < n; i++){
      var q = j * n + i, d = depthAtImgPx(w.px + (i - AR_N / 2) * k, w.py + (j - AR_N / 2) * k);
      pos[q * 3] = (i - AR_N / 2) * 2 * R / AR_N; pos[q * 3 + 2] = (j - AR_N / 2) * 2 * R / AR_N;
      if (d !== null){ ok[q] = 1; pos[q * 3 + 1] = -d; var c = arColor(T, d, max); col[q * 3] = c.r; col[q * 3 + 1] = c.g; col[q * 3 + 2] = c.b; }
    }
    var idx = [], ln = [];
    for (j = 0; j < AR_N; j++) for (i = 0; i < AR_N; i++){
      var a = j * n + i, b = a + 1, c2 = a + n, d2 = c2 + 1;
      if (ok[a] && ok[b] && ok[c2]) idx.push(a, c2, b);
      if (ok[b] && ok[c2] && ok[d2]) idx.push(b, c2, d2);
      var fine = near(i, j, 80);   // the grid: finer near you (where the depth shows best)
      if ((i % gl === 0 || (fine && i % gn === 0)) && ok[a] && ok[c2]) ln.push(a, c2);
      if ((j % gl === 0 || (fine && j % gn === 0)) && ok[a] && ok[b]) ln.push(a, b);
    }
    // depth cues that work at Djup × 1 too: a grid on the surface (two layers that move apart as you turn) and
    // depth sticks from the surface down to the bottom near you (long = deep)
    var sg = [], st = [], s10 = Math.max(1, Math.round(10 / h)), s25 = Math.max(1, Math.round(25 / h));
    for (j = 0; j < AR_N; j += gn) for (i = 0; i < AR_N; i += gn){   // the surface: every ~20 m, ~5 m within 40 m
      var q0 = j * n + i, x0 = pos[q0 * 3], z0 = pos[q0 * 3 + 2], f = near(i, j, 40);
      if (!ok[q0]) continue;
      if ((j % gs === 0 || f) && i + gn <= AR_N && ok[q0 + gn]) sg.push(x0, 0, z0, x0 + gn * h, 0, z0);
      if ((i % gs === 0 || f) && j + gn <= AR_N && ok[q0 + gn * n]) sg.push(x0, 0, z0, x0, 0, z0 + gn * h);
    }
    for (j = 0; j <= AR_N; j++) for (i = 0; i <= AR_N; i++){   // the sticks: every ~10 m within 60 m, every ~25 m out to 150 m
      var q1 = j * n + i;
      if (!ok[q1] || !((i % s10 === 0 && j % s10 === 0 && near(i, j, 60)) || (i % s25 === 0 && j % s25 === 0 && near(i, j, Math.min(R, 150))))) continue;
      st.push(pos[q1 * 3], 0, pos[q1 * 3 + 2], pos[q1 * 3], pos[q1 * 3 + 1], pos[q1 * 3 + 2]);
    }
    if (ar.grp){ ar.scene.remove(ar.grp); ar.grp.children.forEach(function(o){ o.geometry.dispose(); }); }
    var g = new T.BufferGeometry();
    g.setAttribute('position', new T.BufferAttribute(pos, 3)); g.setAttribute('color', new T.BufferAttribute(col, 3));
    g.setIndex(idx); g.computeVertexNormals();
    ar.mesh = new T.Mesh(g, ar.mat);
    var lg = new T.BufferGeometry(); lg.setAttribute('position', g.getAttribute('position')); lg.setIndex(ln);
    ar.lines = new T.LineSegments(lg, ar.lmat);
    function segs(a, m){ var bg = new T.BufferGeometry(); bg.setAttribute('position', new T.Float32BufferAttribute(a, 3)); return new T.LineSegments(bg, m); }
    ar.surf = segs(sg, ar.smat); ar.sticks = segs(st, ar.stmat);
    // the waterline: where the lake meets the land, at the surface (marching squares on the water/land mask) -- it should
    // sit on the real shore in the camera's picture
    var wl = [], M = [[], [[3, 0]], [[0, 1]], [[3, 1]], [[1, 2]], [[3, 0], [1, 2]], [[0, 2]], [[3, 2]], [[2, 3]], [[2, 0]], [[0, 1], [2, 3]], [[2, 1]], [[1, 3]], [[1, 0]], [[0, 3]], []];
    for (j = 0; j < AR_N; j++) for (i = 0; i < AR_N; i++){
      var qa = j * n + i, cs = ok[qa] | ok[qa + 1] << 1 | ok[qa + n + 1] << 2 | ok[qa + n] << 3;
      if (!cs || cs === 15) continue;
      var xa = pos[qa * 3], za = pos[qa * 3 + 2], E = [[xa + h / 2, za], [xa + h, za + h / 2], [xa + h / 2, za + h], [xa, za + h / 2]];   // the cell's edges' middles: top, right, bottom, left
      M[cs].forEach(function(sgm){ wl.push(E[sgm[0]][0], 0, E[sgm[0]][1], E[sgm[1]][0], 0, E[sgm[1]][1]); });
    }
    ar.wline = segs(wl, ar.wmat);
    var dg = new T.BufferGeometry(); dg.setAttribute('position', new T.Float32BufferAttribute(sg, 3));
    ar.dots = new T.Points(dg, ar.dmat);   // (Prickar: the surface grid's corners)
    ar.grp = new T.Group(); ar.grp.add(ar.mesh, ar.lines, ar.surf, ar.sticks, ar.dots, ar.wline);   // (the group is scaled by Djup ×: the surface at 0 stays)
    ar.scene.add(ar.grp);
    ar.scene.fog = new T.Fog(0x0b1830, R * 0.25, R * 1.1);   // (far = darker: the depth reads in 3D)
    ar.at = { px: w.px, py: w.py, r: R, ex: -1 }; ar.n = AR_N;
    arMsg.textContent = w.gps ? '' : 'Ingen GPS – visar från kartans mitt';
    if (!idx.length) arMsg.textContent = 'Ingen djupdata här';
  }
  function arOnEvent(e){
    if (typeof e.alpha !== 'number' || typeof e.beta !== 'number') return;
    var a = e.alpha;
    if (typeof e.webkitCompassHeading === 'number' && isFinite(e.webkitCompassHeading)){   // iOS: alpha starts anywhere -> turn it to north
      var c = ((360 - e.webkitCompassHeading - a) % 360 + 360) % 360;
      arCorr = arCorr === null ? c : (arCorr + (((c - arCorr) % 360 + 540) % 360 - 180) * 0.05 + 360) % 360;
      a += arCorr;
    }
    arOri = { alpha: a, beta: e.beta, gamma: e.gamma || 0 };
  }
  function arListen(on){
    ['deviceorientation', 'deviceorientationabsolute'].forEach(function(n){
      if (on) window.addEventListener(n, arOnEvent); else window.removeEventListener(n, arOnEvent);
    });
  }
  // the camera's turn from alpha/beta/gamma (as three.js' old DeviceOrientationControls)
  function arQuat(T, o, out){
    var D = Math.PI / 180, sa = (screen.orientation && screen.orientation.angle) || window.orientation || 0;
    out.setFromEuler(new T.Euler(o.beta * D, (o.alpha + arCfg.north) * D, -o.gamma * D, 'YXZ'));
    out.multiply(new T.Quaternion(-Math.SQRT1_2, 0, 0, Math.SQRT1_2));   // the camera looks out of the phone's back
    out.multiply(new T.Quaternion().setFromAxisAngle(new T.Vector3(0, 0, 1), -sa * D));
    return out;
  }
  function arFrame(){
    if (!ar) return;
    ar.raf = requestAnimationFrame(arFrame);
    var T = ar.T, w = arWhere();
    if (!ar.mesh && loadDepthGrid()) arBuild();
    if (!ar.mesh) { arMsg.textContent = 'Laddar djupdata …'; return; }
    if (Math.hypot(w.px - ar.at.px, w.py - ar.at.py) * WEB_METERS_PER_PX > arCfg.r * 0.2 || ar.at.r !== arCfg.r) arBuild();
    // you moved a bit within the mesh: shift it under you instead of rebuilding
    ar.grp.position.set((ar.at.px - w.px) * WEB_METERS_PER_PX, 0, (ar.at.py - w.py) * WEB_METERS_PER_PX);
    ar.grp.scale.y = arCfg.ex;
    // the lead straight under you, with the depth at its end
    var du = depthAtImgPx(w.px, w.py);
    ar.lines.visible = arCfg.grid; ar.sticks.visible = arCfg.sticks;
    ar.surf.visible = arCfg.surf; ar.dots.visible = arCfg.dots; ar.wline.visible = arCfg.shore; ar.surfU.uMode.value = arCfg.waves ? 2 : 0; ar.surfU.uT.value = performance.now() / 1000;
    if (!arCfg.lod) du = null;
    ar.plumb.visible = ar.sinker.visible = du !== null;
    if (du !== null){ ar.plumb.scale.y = Math.max(0.01, du * arCfg.ex); ar.sinker.position.y = -du * arCfg.ex; }
    ar.cam.position.y = arCfg.eye;
    var tq = arQuat(T, arOri || { alpha: 0, beta: 80, gamma: 0 }, ar.tq);
    ar.cam.quaternion.slerp(tq, ar.first ? 1 : 0.3); ar.first = false;
    var W = innerWidth, H = innerHeight;
    if (ar.w !== W || ar.h !== H){ ar.w = W; ar.h = H; ar.r.setSize(W, H, false); ar.cam.aspect = W / H; ar.cam.fov = W > H ? AR_FOV * H / W * 1.3 : AR_FOV; ar.cam.updateProjectionMatrix(); }
    ar.r.render(ar.scene, ar.cam);
    var pl = document.getElementById('arPlumb'), v = du !== null ? new T.Vector3(0, -du * arCfg.ex, 0).project(ar.cam) : null;
    if (v && v.z < 1 && Math.abs(v.x) < 1 && Math.abs(v.y) < 1){
      pl.hidden = false; pl.textContent = fmtDepth(du) + ' m under dig';
      pl.style.left = ((v.x + 1) / 2 * W) + 'px'; pl.style.top = ((1 - v.y) / 2 * H) + 'px';
    } else pl.hidden = true;
    // the depth straight ahead: where the middle of the screen meets the bottom
    var now = Date.now(); if (now - (ar.rayAt || 0) < 250) return; ar.rayAt = now;   // (4 times a second: the mesh is big)
    ar.ray.setFromCamera(ar.mid, ar.cam);
    var hit = ar.ray.intersectObject(ar.mesh)[0];
    document.getElementById('arDepth').textContent = hit ? fmtDepth(-hit.point.y / arCfg.ex) + ' m' + (hit.distance > 1 ? ' · ' + Math.round(Math.hypot(hit.point.x, hit.point.z)) + ' m bort' : '') : '';
  }
  function arCamera(on){
    if (arStream){ arStream.getTracks().forEach(function(t){ t.stop(); }); arStream = null; }
    arVideo.srcObject = null; arView.classList.toggle('cam', false);
    if (!on || !navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) return;
    navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment' }, audio: false }).then(function(s){
      if (!ar){ s.getTracks().forEach(function(t){ t.stop(); }); return; }
      arStream = s; arVideo.srcObject = s; arVideo.play().catch(function(){}); arView.classList.add('cam');
    }).catch(function(){ arMsg.textContent = 'Kameran är inte tillåten – visar utan kamera'; });
  }
  function arOpen(){
    if (ar) return;
    arView.classList.add('show'); arUi();
    var DOE = window.DeviceOrientationEvent;
    if (DOE && typeof DOE.requestPermission === 'function'){   // iOS: asked right here, in the tap
      // (not in a tap -- after a rotation reload -- it may throw: listen anyway, as the compass; if iOS forgot, nothing arrives)
      try { DOE.requestPermission().then(function(r){ if (r === 'granted') arListen(true); else arMsg.textContent = 'Rörelse och riktning är inte tillåtet'; }).catch(function(){ arListen(true); }); } catch(e){ arListen(true); }
    } else arListen(true);
    ar = { loading: true };
    arCamera(arCfg.cam);
    nlLib().then(function(m){
      if (!ar) return;
      var T = m[0], c = document.getElementById('arCanvas'), r;
      try { r = new T.WebGLRenderer({ canvas: c, antialias: true, alpha: true }); } catch(e){ arMsg.textContent = 'Telefonen kan inte rita 3D'; return; }
      r.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2)); r.setClearColor(0, 0);
      var scene = new T.Scene(), cam = new T.PerspectiveCamera(AR_FOV, 1, 0.3, 3000);
      scene.add(new T.HemisphereLight(0xdfefff, 0x101828, 0.9));
      var sun = new T.DirectionalLight(0xffffff, 2.4); sun.position.set(-0.8, 0.6, -0.4); scene.add(sun);
      // the surface itself: faint flat; Vågor = moving ripples near you (mode 1, clear near / hazy far, tried and left out)
      var surfU = { uMode: { value: 0 }, uT: { value: 0 } };
      var surf = new T.Mesh(new T.CircleGeometry(3000, 64), new T.ShaderMaterial({ uniforms: surfU, transparent: true, side: T.DoubleSide, depthWrite: false,
        vertexShader: 'varying vec3 vP; void main(){ vec4 w = modelMatrix * vec4(position, 1.0); vP = w.xyz; gl_Position = projectionMatrix * viewMatrix * w; }',
        fragmentShader: 'varying vec3 vP; uniform float uMode, uT; void main(){ float d = length(vP.xz); vec3 c = vec3(0.23, 0.53, 1.0); float a = 0.07;' +
          ' if (uMode > 0.5 && uMode < 1.5){ a = mix(0.02, 0.55, smoothstep(8.0, 350.0, d)); c = mix(vec3(0.75, 0.88, 1.0), c, smoothstep(0.0, 120.0, d)); }' +
          ' if (uMode > 1.5){ float w = sin(vP.x * 0.9 + uT * 1.3) * sin(vP.z * 0.7 - uT) + sin((vP.x + vP.z) * 0.35 + uT * 0.8) + 0.5 * sin(vP.x * 2.1 - vP.z * 1.7 + uT * 2.0);' +
          ' a = 0.08 + smoothstep(0.6, 1.6, w) * 0.55 * (1.0 - smoothstep(30.0, 200.0, d)); c = vec3(0.82, 0.93, 1.0); }' +
          ' gl_FragColor = vec4(c, a); }' }));
      surf.rotation.x = -Math.PI / 2; scene.add(surf);
      ar = { T: T, r: r, surfU: surfU, scene: scene, cam: cam, first: true, tq: new T.Quaternion(), ray: new T.Raycaster(), mid: new T.Vector2(0, 0),
             mat: new T.MeshLambertMaterial({ vertexColors: true, transparent: true, opacity: 0.82, side: T.DoubleSide }),
             lmat: new T.LineBasicMaterial({ color: 0xffffff, transparent: true, opacity: 0.3, fog: true }),
             smat: new T.LineBasicMaterial({ color: 0xcfe8ff, transparent: true, opacity: 0.4, fog: true }),
             dmat: new T.PointsMaterial({ color: 0xdff0ff, size: 3, sizeAttenuation: false, transparent: true, opacity: 0.8, fog: true }),
             wmat: new T.LineBasicMaterial({ color: 0xffffff, transparent: true, opacity: 0.9 }),
             stmat: new T.LineBasicMaterial({ color: 0xcfe8ff, transparent: true, opacity: 0.32, fog: true }) };
      var pg = new T.BufferGeometry(); pg.setAttribute('position', new T.Float32BufferAttribute([0, 0, 0, 0, -1, 0], 3));
      ar.plumb = new T.Line(pg, new T.LineBasicMaterial({ color: 0xF09A60 }));
      ar.sinker = new T.Mesh(new T.SphereGeometry(0.12, 12, 8), new T.MeshBasicMaterial({ color: 0xF09A60 }));
      scene.add(ar.plumb, ar.sinker);
      arFrame();
    }).catch(function(){ arMsg.textContent = 'Kunde inte ladda 3D'; });
  }
  function arClose(){
    if (!ar) return;
    if (ar.raf) cancelAnimationFrame(ar.raf);
    if (ar.r){ if (ar.grp) ar.grp.children.forEach(function(o){ o.geometry.dispose(); }); ar.r.dispose(); }
    ar = null; arListen(false); arCamera(false); arCorr = null;
    arView.classList.remove('show');
  }
  // the controls
  var AR_SL = { arR: ['r', function(v){ return v + ' m'; }], arEx: ['ex', function(v){ return '× ' + v; }], arEye: ['eye', function(v){ return String(v).replace('.', ',') + ' m'; }] };
  function arUi(){
    Object.keys(AR_SL).forEach(function(id){ var el = document.getElementById(id); el.value = arCfg[AR_SL[id][0]]; rangeFill(el); document.getElementById(id + 'Val').textContent = AR_SL[id][1](arCfg[AR_SL[id][0]]); });
    document.getElementById('arCam').classList.toggle('on', arCfg.cam);
    Array.prototype.forEach.call(document.querySelectorAll('#arChips [data-k]'), function(b){ b.classList.toggle('on', !!arCfg[b.getAttribute('data-k')]); });
    var nb = document.getElementById('arNorth'), nv = Math.round(((arCfg.north + 540) % 360) - 180);
    nb.hidden = !nv; nb.textContent = 'Vriden ' + nv + '° ✕';
  }
  Object.keys(AR_SL).forEach(function(id){
    document.getElementById(id).addEventListener('input', function(e){ arCfg[AR_SL[id][0]] = +e.target.value; arSave(); arUi(); });
  });
  document.getElementById('arCam').addEventListener('click', function(){ arCfg.cam = !arCfg.cam; arSave(); arUi(); arCamera(arCfg.cam); });
  document.getElementById('arChips').addEventListener('click', function(e){
    var b = e.target.closest('[data-k]'); if (!b) return;
    var k = b.getAttribute('data-k'); arCfg[k] = !arCfg[k]; arSave(); arUi();
  });
  document.getElementById('arNorth').addEventListener('click', function(){ arCfg.north = 0; arSave(); arUi(); });
  document.getElementById('arClose').addEventListener('click', arClose);
  // the controls' grip: drag down (or a flick) = minimised to the grip; drag up / a tap = back (arCfg.min, remembered)
  var arCtl = document.getElementById('arCtl'), arGrab = arCtl.querySelector('.arGrab'), arG = null;
  function arMin(on){ arCfg.min = on; arSave(); arCtl.classList.toggle('min', on); }
  arCtl.classList.toggle('min', !!arCfg.min);
  arGrab.addEventListener('pointerdown', function(e){ arG = { y: e.clientY, t: Date.now(), dy: 0 }; arGrab.setPointerCapture(e.pointerId); arCtl.classList.add('drag'); });
  arGrab.addEventListener('pointermove', function(e){
    if (!arG) return; arG.dy = e.clientY - arG.y;
    arCtl.style.transform = 'translateY(' + (arCfg.min ? Math.min(0, arG.dy) * 0.4 : Math.max(0, arG.dy)) + 'px)';
  });
  function arGrabEnd(){
    if (!arG) return; var g = arG; arG = null; arCtl.classList.remove('drag'); arCtl.style.transform = '';
    var flick = Date.now() - g.t < 300;
    if (Math.abs(g.dy) < 6) arMin(!arCfg.min);                          // a tap
    else if (!arCfg.min && (g.dy > 50 || (flick && g.dy > 20))) arMin(true);
    else if (arCfg.min && (g.dy < -30 || (flick && g.dy < -10))) arMin(false);
  }
  arGrab.addEventListener('pointerup', arGrabEnd); arGrab.addEventListener('pointercancel', arGrabEnd);
  // a drag sideways on the picture turns the bottom (when it doesn't sit over the real shore)
  var arDrag = null, arCv = document.getElementById('arCanvas');
  arCv.addEventListener('pointerdown', function(e){ arDrag = { x: e.clientX, n: arCfg.north }; arCv.setPointerCapture(e.pointerId); });
  arCv.addEventListener('pointermove', function(e){ if (arDrag){ arCfg.north = (arDrag.n + (e.clientX - arDrag.x) / innerWidth * 60 + 360) % 360; arUi(); } });
  arCv.addEventListener('pointerup', function(){ if (arDrag){ arDrag = null; arSave(); } });
  document.addEventListener('visibilitychange', function(){ if (ar && ar.r) arCamera(!document.hidden && arCfg.cam); });
  window.__ffAr = function(o){ if (o) arOri = o; var w = arWhere(); return { open: !!ar, at: imgPxToLatLon(w.px, w.py), gps: w.gps, ready: !!(ar && ar.mesh), depth: document.getElementById('arDepth').textContent, msg: arMsg.textContent, cfg: arCfg, n: ar && ar.n, cam: arView.classList.contains('cam') }; };   // (for the tests)
