  /* ---------------- The start film (splash), tools/PLAN_SPLASH.md ----------------
     3.5 s with the logo in 3D, every time a name is chosen ("Vem är du?": a new phone, after Logga ut) and from
     Inställningar -> Avancerat -> "Spela": it fades to black over the app, then the film. three.js and the sign
     come from 35-logo3d.js (nlLib, nlMakeSign, nlTier); the clock starts when it's all built. Over 1.5 s to load,
     or it fails -> only the black fades away (0.5 s). 'flat' (no WebGL) or Reduce motion -> the flat logo fades in
     and out (2 s, nothing spins). A tap skips to the end (0.4 s). Afterwards the renderer and its canvas are gone
     -- nothing keeps running. Hjälp and the location question wait for it (afterSplash). */
  var spEl = document.getElementById('splash'), spLogo = spEl.querySelector('.spLogo'), spBloom = spEl.querySelector('.spBloom');
  var spFlatImg = spEl.querySelector('.spFlat'), spApp = document.getElementById('app'), spS = {};
  ['spBlack', 'spGlow', 'spLogo', 'spFlash', 'spVig', 'spGrain', 'spTop'].forEach(function(c){ spS[c] = spEl.querySelector('.' + c).style; });
  var spSt = { shown: false, running: false, t: 0, mode: '' }, spRaf = 0, spGl = null, spWait = [], spSafety = 0, spLoadTimer = 0, spBlur = false;
  function splashOn(){ return document.documentElement.classList.contains('splash'); }
  function afterSplash(fn){ if (splashOn()) spWait.push(fn); else fn(); }

  function spSeg(t, a, b){ return Math.max(0, Math.min(1, (t - a) / (b - a))); }
  function spInOut(x){ return x < 0.5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2; }
  // the timeline (s), the same curves as the mockup (tools/splash_mockup.html):
  // 0-1.9 one calm turn in from the dark, the light full just as it lands; 1.9-2.5 at rest, the key light's glint
  // drifts across; 2.5-3.1 it turns and flies through the camera, a warm flash at 3.0; 2.9-3.5 the black dissolves
  function splashPose(t){
    var a = spSeg(t, 0, 1.9), turn = 1 - Math.pow(1 - a, 2), lit = Math.pow(spSeg(t, 0.25, 1.9), 1.8);
    t -= 0.5;
    var o = Math.pow(spSeg(t, 2.0, 2.6), 3);
    return { scale: (0.55 + 0.45 * turn) * (1 + 9 * o * o), ry: -360 * (1 - turn) + 5 * Math.sin(t * 2.2) + 140 * o,
      rx: 10 * (1 - turn) - 25 * o, z: 0.25 * o, lit: lit, sweep: spInOut(spSeg(t, 0.8, 2.1)),
      logoA: 1 - spSeg(t, 2.4, 2.62), flash: 0.55 * Math.exp(-Math.pow((t - 2.5) / 0.1, 2)),
      blackA: 1 - spInOut(spSeg(t, 2.42, 3.0)), appBlur: 1 - spSeg(t, 2.42, 3.0) };
  }
  function spFade(d){ return function(t){ var f = spInOut(spSeg(t, 0, d)); return { lit: 0, logoA: 0, flash: 0, blackA: 1 - f, appBlur: 1 - f }; }; }
  function spFlatPose(t){   // the flat logo: in from the dark, stays, out with the black
    var out = spInOut(spSeg(t, 1.4, 2.0));
    return { lit: 0, logoA: spSeg(t, 0.15, 0.7), flash: 0, blackA: 1 - out, appBlur: 1 - out };
  }
  function spApply(p){
    spS.spLogo.opacity = p.logoA;
    spS.spGlow.opacity = (p.lit * p.logoA).toFixed(3);
    spS.spFlash.opacity = p.flash.toFixed(3);
    spS.spBlack.opacity = p.blackA;
    spS.spVig.opacity = Math.max(p.blackA, p.logoA);
    spS.spGrain.opacity = (0.09 * p.blackA).toFixed(3);
    spS.spTop.opacity = p.blackA;
    spS.spGrain.backgroundPosition = (Math.random() * 160 | 0) + 'px ' + (Math.random() * 160 | 0) + 'px';
    // the app under it: from blurred and darker to sharp (only on phones that manage it)
    spApp.style.filter = spBlur && p.appBlur ? 'blur(' + (14 * p.appBlur).toFixed(1) + 'px) brightness(' + (1 - 0.3 * p.appBlur).toFixed(2) + ')' : '';
    spApp.style.transform = spBlur && p.appBlur ? 'scale(' + (1 + 0.06 * p.appBlur).toFixed(3) + ')' : '';
  }
  function spPlay(mode, dur, pose, draw){
    var t0 = 0;
    cancelAnimationFrame(spRaf);
    spSt.mode = mode;
    function frame(now){
      if (!t0) t0 = now;
      var t = Math.min((now - t0) / 1000, dur), p = pose(t);
      spSt.t = t;
      if (draw) draw(t, p);
      spApply(p);
      if (t < dur) spRaf = requestAnimationFrame(frame); else splashDone();
    }
    spRaf = requestAnimationFrame(frame);
  }
  // the sign as on "Vem är du?", with a clear coat for the glint; lights: warm key gliding left -> right,
  // cold rim from behind, low warm fill. -> draw(t, pose)
  function spBuild(T, SVGLoader, Room, svg){
    var full = nlTier === 'full', canvas = document.createElement('canvas');
    var r = new T.WebGLRenderer({ canvas: canvas, antialias: true, alpha: true });   // (throws without WebGL)
    r.setPixelRatio(full ? Math.min(window.devicePixelRatio || 1, 2) : 1);
    r.toneMapping = T.ACESFilmicToneMapping;
    var scene = new T.Scene(), cam = new T.PerspectiveCamera(30, 1, 0.05, 50), env = null, amb = null;
    if (full){ var pm = new T.PMREMGenerator(r); env = pm.fromScene(new Room(), 0.04).texture; pm.dispose(); scene.environment = env; }
    else { amb = new T.AmbientLight(0xffffff, 0); scene.add(amb); }
    var key = new T.SpotLight(0xffd9b0, 0, 0, 0.5, 0.6, 0); scene.add(key, key.target);
    var rim = new T.DirectionalLight(0x7fb0ff, 0); rim.position.set(1.8, 1.2, -2.5); scene.add(rim);
    var rim2 = new T.DirectionalLight(0xff9a60, 0); rim2.position.set(-2, -1, -2); scene.add(rim2);
    var sign = nlMakeSign(T, SVGLoader, svg, { fine: full,
      red: new T.MeshPhysicalMaterial({ color: 0xEE2A28, metalness: 0.45, roughness: 0.3, clearcoat: 1, clearcoatRoughness: 0.08 }),
      white: new T.MeshStandardMaterial({ color: 0xffffff, metalness: 0.05, roughness: 0.45 }) });
    scene.add(sign.pivot);
    spLogo.insertBefore(canvas, spBloom);
    var bctx = full ? spBloom.getContext('2d') : null;   // the fake glow: the frame, small and blurred, on top with "screen"
    spGl = { r: r, canvas: canvas, scene: scene, env: env };
    return function(t, p){
      var w = canvas.clientWidth, h = canvas.clientHeight;
      if (!w || !h) return;
      if (canvas.width !== Math.round(w * r.getPixelRatio())){
        r.setSize(w, h, false); cam.aspect = w / h; cam.updateProjectionMatrix();
        if (bctx){ spBloom.width = Math.round(w / 4); spBloom.height = Math.round(h / 4); }
      }
      cam.position.z = 3.5 - 0.3 * spSeg(t, 0, 2.5) - p.z;
      var s = p.scale * sign.k * 0.84 * 2 * 3.2 * Math.tan(15 * Math.PI / 180) * Math.min(w / h, 1);
      sign.pivot.scale.set(s, -s, s);
      sign.pivot.rotation.set(p.rx * Math.PI / 180, p.ry * Math.PI / 180, 0);
      key.position.set(-2.4 + 4.8 * p.sweep, 2.2, 2.4);
      key.intensity = 3.2 * p.lit; rim.intensity = 7 * p.lit; rim2.intensity = 2.2 * p.lit;
      if (env) scene.environmentIntensity = 0.67 * p.lit; else amb.intensity = 0.8 * p.lit;
      r.toneMappingExposure = 0.6 + 0.35 * p.lit;
      r.render(scene, cam);
      if (bctx){ bctx.clearRect(0, 0, spBloom.width, spBloom.height); bctx.drawImage(canvas, 0, 0, spBloom.width, spBloom.height); spBloom.style.opacity = (0.18 * p.lit).toFixed(3); }
    };
  }
  function spCancelLoad(){ clearTimeout(spLoadTimer); spLoadTimer = 0; }
  // the status bar keeps its #141822 (iOS doesn't recolour it in a home-screen app, and the start picture is that
  // blue too): the film's top fades from it into the black (.tint)
  function splashStart(){
    spSt.shown = spSt.running = true; spSt.t = 0; spSt.mode = 'load';
    spEl.classList.add('tint');
    clearTimeout(spSafety); spSafety = setTimeout(splashDone, 9000);   // (whatever happens: never stuck behind the black)
    var flat = nlTier === 'flat' || nlReduce;
    spBlur = !flat && nlTier === 'full';
    spEl.classList.toggle('lite', nlTier !== 'full' || nlReduce);
    spApply({ lit: 0, logoA: 0, flash: 0, blackA: 1, appBlur: 1 });
    if (flat){ spFlatImg.src = 'ff_logo.svg'; spPlay('flat', 2, spFlatPose, null); return; }
    spLoadTimer = setTimeout(function(){ spLoadTimer = 0; spPlay('fade', 0.5, spFade(0.5), null); }, window.__ffSplashLoadMs || 1500);   // (too slow: just fade; the tests' busy browser may wait longer)
    nlLib().then(function(m){
      if (!spLoadTimer) return;   // (too late, or tapped away)
      spCancelLoad();
      var draw;
      try { draw = spBuild(m[0], m[1].SVGLoader, m[2].RoomEnvironment, m[3]); }
      catch(e){ nlSetTier('flat'); spPlay('fade', 0.5, spFade(0.5), null); return; }
      spPlay('film', 3.5, splashPose, draw);
    }).catch(function(){ if (!spLoadTimer) return; spCancelLoad(); spPlay('fade', 0.5, spFade(0.5), null); });
  }
  function splashDone(){
    cancelAnimationFrame(spRaf); spRaf = 0; clearTimeout(spSafety); spCancelLoad();
    if (spGl){
      spGl.scene.traverse(function(o){ if (o.geometry) o.geometry.dispose(); if (o.material) o.material.dispose(); });
      if (spGl.env) spGl.env.dispose();
      spGl.r.dispose(); try { spGl.r.forceContextLoss(); } catch(e){}
      spGl.canvas.remove(); spGl = null;
    }
    spBloom.width = spBloom.height = 0;
    spFlatImg.removeAttribute('src');
    spApp.style.filter = spApp.style.transform = '';
    document.documentElement.classList.remove('splash'); spEl.classList.remove('spIn');
    spSt.running = false; spSt.mode = '';
    var w = spWait; spWait = [];
    w.forEach(function(f){ f(); });
  }
  // a tap anywhere: straight to the end
  spEl.addEventListener('pointerdown', function(e){
    e.preventDefault();
    if (!spSt.running || spSt.mode === 'skip') return;
    spCancelLoad();
    spPlay('skip', 0.4, spFade(0.4), null);
  });
  // Inställningar -> Avancerat -> Startfilmen: play it again (over the map, so the settings' own 3D logo isn't running too)
  document.getElementById('splashReplayBtn').addEventListener('click', function(){
    if (splashOn()) return;
    showMapView();
    splashPlay();
  });
  // the start picture (head.html, html.boot: the logo on the dark blue, like iOS's launch image): the app fades
  // in over it once the map is there (at most 1 s), then the logo's gone for good
  (function(){
    var c = document.documentElement.classList, mi = document.getElementById('mapImg'), t;
    if (!c.contains('boot')) return;
    function go(){ clearTimeout(t); requestAnimationFrame(function(){ c.remove('boot'); c.add('booted'); setTimeout(function(){ c.remove('booted'); }, 700); }); }
    t = setTimeout(go, 1000);
    if (mi.complete && mi.naturalWidth) go(); else mi.addEventListener('load', go, { once: true });
  })();
  // a name chosen (34-name.js), "Spela": black over the app, then the film (not in the other tests: fakefb)
  function splashPlay(){
    if (splashOn() || window.__ffNoSplash) return;
    spEl.classList.add('spIn');
    document.documentElement.classList.add('splash'); splashStart();
  }
  window.__ffSplash = function(){ return { shown: spSt.shown, running: spSt.running, t: spSt.t, mode: spSt.mode, gl: !!spGl }; };
