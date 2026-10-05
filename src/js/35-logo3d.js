  /* ---------------- The logo as a 3D sign (three.js, assets/three-r170*.js) ----------------
     On "Vem är du?" (#nameLogo), in Hjälp's (#helpLogo) and Inställningar's (#settingsLogo) headers.
     A thick red sign with a red back: it sways a little by itself, a drag spins it (the harder,
     the faster), it slows down and always stops the right way round. Older phones step down by
     themselves (measured over the first frames, remembered in ffmap_logo3d_v1, for all three):
       'full' = sharp, reflections (RoomEnvironment) -> 'lite' = pixel ratio 1, plain lights ->
       'flat' = no WebGL: the picture turned with CSS, a red back (also: no WebGL, load failed).
     Each one runs only while its view has the class 'show' (watched, no hooks needed). */
  var NL_KEY = 'ffmap_logo3d_v1';
  var nlTier = 'full';
  try { nlTier = localStorage.getItem(NL_KEY) || 'full'; } catch(e){}
  if ((navigator.hardwareConcurrency || 4) <= 2) nlTier = 'flat';
  var nlReduce = !!(window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches);
  var nlLibP = null;   // three.js + the logo's SVG, loaded once for all of them

  function nlSetTier(t){
    nlTier = t;
    try { localStorage.setItem(NL_KEY, t); } catch(e){}
  }
  function nlLib(){
    return nlLibP || (nlLibP = Promise.all([import('./three-r170.min.js'), import('./three-r170-svg.js'), import('./three-r170-room.js'),
      fetch('ff_logo.svg').then(function(r){ return r.text(); })]));
  }
  // the sign: a thick red extrusion with the white parts on its front face, centred; scale k = 1 unit wide
  // (o.red / o.white: the materials, o.fine: rounder bevels and curves). Also the start film (35-splash.js)
  function nlMakeSign(T, SVGLoader, svg, o){
    var D = 50, B = 9;   // the sign's thickness and bevel, in the SVG's units (the logo is ~1488 wide)
    var inner = new T.Group();
    new SVGLoader().parse(svg).paths.forEach(function(p){
      var isWhite = /^(white|#fff(fff)?)$/i.test(String(p.userData.style.fill).trim());
      SVGLoader.createShapes(p).forEach(function(s){
        var m = isWhite ? new T.Mesh(new T.ShapeGeometry(s, 8), o.white)
                        : new T.Mesh(new T.ExtrudeGeometry(s, { depth: D, bevelEnabled: true, bevelThickness: B, bevelSize: B,
                                                                bevelSegments: o.fine ? 4 : 1, curveSegments: o.fine ? 10 : 5 }), o.red);
        if (isWhite) m.position.z = D + B + 1;   // on the front face
        inner.add(m);
      });
    });
    var box = new T.Box3().setFromObject(inner), c = box.getCenter(new T.Vector3()), sz = box.getSize(new T.Vector3());
    inner.position.set(-c.x, -c.y, -c.z);
    var pivot = new T.Group(), k = 1 / sz.x;
    pivot.scale.set(k, -k, k);   // (the SVG's y points down)
    pivot.add(inner);
    return { pivot: pivot, k: k };
  }

  function makeLogo3d(el, view){
    var spin = el.querySelector('.nlSpin');
    var nl = { ry: 0, vy: 0, spring: false, drag: null, raf: 0, last: 0, prev: 0, t: 0, gl: null, loading: false, meas: [], slow: false };

    function flat(){
      if (nl.gl){ try { nl.gl.r.dispose(); } catch(e){} nl.gl.canvas.remove(); nl.gl = null; }
      el.classList.remove('gl');
      el.classList.add('flat');
    }
    function load(){
      if (nl.gl && nl.gl.tier !== nlTier) flat();   // another logo stepped down meanwhile
      if (nlTier === 'flat'){ flat(); return; }
      el.classList.remove('flat');
      if (nl.gl || nl.loading) return;
      nl.loading = true;
      nlLib().then(function(m){
        nl.loading = false;
        if (!nl.gl && nlTier !== 'flat') build(m[0], m[1].SVGLoader, m[2].RoomEnvironment, m[3]);
      }).catch(function(){ nl.loading = false; nlSetTier('flat'); flat(); });
    }

    function build(T, SVGLoader, Room, svg){
      var canvas = document.createElement('canvas');
      canvas.className = 'logo3dCanvas';
      var r;
      try { r = new T.WebGLRenderer({ canvas: canvas, antialias: true, alpha: true, powerPreference: 'low-power' }); }
      catch(e){ nlSetTier('flat'); flat(); return; }
      var full = nlTier === 'full';
      r.setPixelRatio(full ? Math.min(window.devicePixelRatio || 1, 2) : 1);
      var scene = new T.Scene();
      var cam = new T.PerspectiveCamera(30, 1.44, 0.1, 20);
      cam.position.z = 1.75;
      if (full){
        var pm = new T.PMREMGenerator(r);
        scene.environment = pm.fromScene(new Room(), 0.04).texture;
        pm.dispose();
        scene.environmentIntensity = 0.55;
        var key = new T.DirectionalLight(0xffffff, 0.9); key.position.set(-1, 1.5, 2); scene.add(key);
      } else {
        scene.add(new T.AmbientLight(0xffffff, 1.1));
        var l1 = new T.DirectionalLight(0xffffff, 2); l1.position.set(-1, 1.5, 2); scene.add(l1);
        var l2 = new T.DirectionalLight(0xffffff, 1.4); l2.position.set(1, -0.5, -2); scene.add(l2);
      }
      var pivot = nlMakeSign(T, SVGLoader, svg, { fine: full,
        red: new T.MeshStandardMaterial({ color: 0xEE2A28, metalness: 0.4, roughness: 0.28 }),
        white: new T.MeshStandardMaterial({ color: 0xffffff, metalness: 0.05, roughness: 0.5 }) }).pivot;
      scene.add(pivot);
      el.appendChild(canvas);
      nl.gl = { r: r, scene: scene, cam: cam, pivot: pivot, canvas: canvas, w: 0, h: 0, tier: nlTier };
      nl.meas = [];
      el.classList.add('gl');
    }

    // the spin: friction, then a spring to the whole turn it would stop nearest -> 0
    function step(dt){
      if (nl.drag) return;
      if (!nl.spring){
        nl.vy *= Math.pow(0.985, dt * 60);
        nl.ry += nl.vy * dt;
        if (Math.abs(nl.vy) < 120){ nl.spring = true; nl.target = Math.round((nl.ry + nl.vy * 1.1) / 360) * 360; }
      } else if (nl.ry !== 0 || nl.vy !== 0){
        nl.vy += (-40 * (nl.ry - nl.target) - 12.6 * nl.vy) * dt;
        nl.ry += nl.vy * dt;
        if (Math.abs(nl.ry - nl.target) < 0.3 && Math.abs(nl.vy) < 3){ nl.ry = 0; nl.vy = 0; }
      }
    }
    function frame(now){
      nl.raf = requestAnimationFrame(frame);
      var dt = nl.last ? Math.min((now - nl.last) / 1000, 0.05) : 0.016;
      nl.last = now;
      nl.t += dt;
      step(dt);
      var sw = nlReduce ? 0 : 14 * Math.sin(nl.t * 2 * Math.PI / 5), sx = nlReduce ? 0 : 4 * Math.sin(nl.t * 2 * Math.PI / 7);
      var g = nl.gl;
      if (g){
        var w = g.canvas.clientWidth, h = g.canvas.clientHeight;
        if (w && (w !== g.w || h !== g.h)){ g.w = w; g.h = h; g.r.setSize(w, h, false); g.cam.aspect = w / h; g.cam.updateProjectionMatrix(); }
        g.pivot.rotation.y = (sw + nl.ry) * Math.PI / 180;
        g.pivot.rotation.x = sx * Math.PI / 180;
        g.r.render(g.scene, g.cam);
        // too slow -> one step down (frames 15-75 after it appeared)
        if (nl.meas.length < 75 && nl.meas.push(nl.slow ? 0.05 : (now - (nl.prev || now)) / 1000) === 75){
          var avg = nl.meas.slice(15).reduce(function(a, b){ return a + b; }, 0) / 60;
          if (avg > (nlTier === 'full' ? 1 / 40 : 1 / 30)){
            nlSetTier(nlTier === 'full' ? 'lite' : 'flat');
            load();
          }
        }
      } else {
        spin.style.transform = 'rotateX(' + sx.toFixed(2) + 'deg) rotateY(' + (sw + nl.ry).toFixed(2) + 'deg)';
        spin.style.setProperty('--ry', ((sw + nl.ry) % 360).toFixed(1));
      }
      nl.prev = now;
    }
    function start(){
      load();
      if (!nl.raf){ nl.last = 0; nl.prev = 0; nl.raf = requestAnimationFrame(frame); }
    }
    function stop(){
      cancelAnimationFrame(nl.raf); nl.raf = 0;
      nl.ry = nl.vy = 0; nl.drag = null;
    }

    // drag = spin; the speed of the last ~80 ms carries on
    el.addEventListener('pointerdown', function(e){
      nl.drag = { x: e.clientX, hist: [{ ry: nl.ry, t: performance.now() }] };
      nl.spring = false; nl.vy = 0;
      try { el.setPointerCapture(e.pointerId); } catch(err){}
    });
    el.addEventListener('pointermove', function(e){
      if (!nl.drag) return;
      nl.ry += (e.clientX - nl.drag.x) * 0.5;
      nl.drag.x = e.clientX;
      var now = performance.now();
      nl.drag.hist.push({ ry: nl.ry, t: now });
      while (nl.drag.hist.length > 2 && now - nl.drag.hist[0].t > 80) nl.drag.hist.shift();
    });
    function up(){
      if (!nl.drag) return;
      var h = nl.drag.hist, a = h[0], now = performance.now();
      nl.vy = now - a.t > 5 ? Math.max(-2000, Math.min(2000, (nl.ry - a.ry) / ((now - a.t) / 1000))) : 0;
      if (now - h[h.length - 1].t > 100) nl.vy = 0;   // held still before letting go
      nl.drag = null;
    }
    el.addEventListener('pointerup', up);
    el.addEventListener('pointercancel', up);

    // runs only while its view is shown
    function sync(){ if (view.classList.contains('show')) start(); else stop(); }
    new MutationObserver(sync).observe(view, { attributes: true, attributeFilter: ['class'] });
    sync();
    return function(o){   // (for the tests; {slow:true} = pretend the frames are slow)
      if (o && o.slow){ nl.slow = true; nl.meas = []; }
      return { tier: nlTier, gl: !!nl.gl, ry: nl.ry, vy: nl.vy, moving: !!nl.drag || nl.ry !== 0 || nl.vy !== 0, running: !!nl.raf };
    };
  }
  window.__ffNameLogo = makeLogo3d(document.getElementById('nameLogo'), nameModal);
  window.__ffHelpLogo = makeLogo3d(document.getElementById('helpLogo'), document.getElementById('helpView'));
  window.__ffSettingsLogo = makeLogo3d(document.getElementById('settingsLogo'), document.getElementById('settingsView'));
