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
  // a toggle switched on
  document.addEventListener('change', function(e){
    var t = e.target;
    if (t && t.type === 'checkbox' && t.checked && t.parentNode && t.parentNode.classList && t.parentNode.classList.contains('toggle')){
      motionIgnite(t.parentNode.querySelector('.toggleTrack'));
    }
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
  // coloured sliders: where the thumb is (--f, 0..1), so the colours past it are dimmed (css/95-design-a.css)
  function satFill(el){ var a = +el.min || 0, b = +el.max || 100; el.style.setProperty('--f', String(Math.max(0, Math.min(1, (el.value - a) / (b - a))))); }
  Array.prototype.forEach.call(document.querySelectorAll('.satSlider'), satFill);
  document.addEventListener('input', function(e){ if (e.target.classList && e.target.classList.contains('satSlider')) satFill(e.target); }, true);
  // #app must never scroll (css overflow:clip; this is for browsers without it)
  (function(){
    var app = document.getElementById('app');
    if (app) app.addEventListener('scroll', function(){ if (app.scrollTop || app.scrollLeft){ app.scrollTop = 0; app.scrollLeft = 0; } });
  })();
