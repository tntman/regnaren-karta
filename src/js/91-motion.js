  // ================= Design A: the glow that flares once when something is switched on =================
  // (DESIGN.md; the flare itself is css/95-design-a.css, .ign). Only on a tap or a switch -- never when a
  // view opens with things already on.
  function motionIgnite(el){
    if (!el) return;
    el.classList.remove('ign');
    void el.offsetWidth;            // restart the animation if it's already running
    el.classList.add('ign');
  }
  document.addEventListener('animationend', function(e){
    var el = e.target && e.target.closest ? e.target.closest('.ign') : null;
    if (el && e.animationName && e.animationName.indexOf('ign') === 0) el.classList.remove('ign');
  }, true);
  // a map button / ⏻ that is on after the tap (the app's own handlers run first), and Sikte on every tap
  document.addEventListener('click', function(e){
    var b = e.target && e.target.closest ? e.target.closest('#locateBtn, #anBtn, #measureBtn, #hmBtn, #msgBtn, .hdBtn') : null;
    if (!b) return;
    setTimeout(function(){
      var on = b.id === 'locateBtn' || b.classList.contains('on') || b.classList.contains('active') || b.classList.contains('open');
      if (on && !b.disabled) motionIgnite(b);
    }, 0);
  }, true);
  // sections (Inställningar) and the ⓘ boxes unfold softly: the height glides open -- and closed again
  function motionHeight(el, from, to, done){
    if (!el.animate || (window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches)){ if (done) done(); return; }
    el.style.overflow = 'hidden';
    var a = el.animate([{ height: from + 'px' }, { height: to + 'px' }], { duration: 380, easing: 'cubic-bezier(.16,1,.3,1)' });
    a.onfinish = a.oncancel = function(){ el.style.overflow = ''; if (done) done(); };
  }
  document.addEventListener('click', function(e){
    var sm = e.target && e.target.closest ? e.target.closest('details.setSec > summary') : null;
    if (!sm) return;
    var d = sm.parentNode;
    e.preventDefault();                                     // (we open / close it ourselves, after the glide)
    if (d._closing) return;
    var h0 = d.offsetHeight;
    if (!d.open){ d.open = true; motionHeight(d, h0, d.offsetHeight); return; }
    d.open = false; var h1 = d.offsetHeight; d.open = true;  // (the closed height, measured without a paint)
    d._closing = true;
    motionHeight(d, h0, h1, function(){ d.open = false; d._closing = false; });
  }, true);
  // tabs (.anSeg / .helpSeg): the chosen tab's background glides from the old tab to the new one
  document.addEventListener('click', function(e){
    var b = e.target && e.target.closest ? e.target.closest('.anSeg button, .helpSeg button') : null;
    if (!b) return;
    var seg = b.parentNode, old = seg.querySelector('button.on');
    if (!old || old === b) return;
    var r0 = old.getBoundingClientRect();
    setTimeout(function(){                                   // (after the app's own handler has moved .on)
      var now = seg.isConnected ? seg.querySelector('button.on') : null;   // (a re-drawn row: no glide)
      if (!now || now === old) return;
      var r1 = now.getBoundingClientRect();
      now.style.setProperty('--sl', (r0.left - r1.left) + 'px'); now.style.setProperty('--sr', (r1.right - r0.right) + 'px');
      now.classList.remove('segGlide'); void now.offsetWidth; now.classList.add('segGlide');
    }, 0);
  }, true);
  // coloured sliders: where the thumb is (--f, 0..1), so the colours past it are dimmed (css/95-design-a.css)
  function satFill(el){ var a = +el.min || 0, b = +el.max || 100; el.style.setProperty('--f', String(Math.max(0, Math.min(1, (el.value - a) / (b - a))))); }
  Array.prototype.forEach.call(document.querySelectorAll('.satSlider'), satFill);
  document.addEventListener('input', function(e){ if (e.target.classList && e.target.classList.contains('satSlider')) satFill(e.target); }, true);
  // #app must never scroll (css overflow:clip; this is for browsers without it)
  (function(){
    var app = document.getElementById('app');
    if (app) app.addEventListener('scroll', function(){ if (app.scrollTop || app.scrollLeft){ app.scrollTop = 0; app.scrollLeft = 0; } });
  })();
