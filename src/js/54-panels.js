  /* ---- swipe a bottom panel down to close it (like a spot's sheet) -- see tools/UI.md ----
     Drag from anywhere on the panel except its fields, buttons and sliders; the panel
     follows the finger (down only); let go far enough down -- or with a quick flick --
     and it closes, otherwise it springs back. */
  function sheetSwipe(el, close){
    // Only the grip strip at the top (.grab / .sheetGrab, the bar in the middle) moves the panel:
    // drag it down = smaller (what's inside scrolls), up = bigger again (to its full size);
    // a quick flick down -- or dragging it almost all the way down -- closes it.
    // Inside the panel a finger only scrolls. (tools/UI.md)
    var d = null;
    el._resetSize = function(){ el.style.height = ''; el.style.maxHeight = ''; };
    el.addEventListener('pointerdown', function(e){
      if (!el.classList.contains('show')) return;
      if (!(e.target.closest && e.target.closest('.grab, .sheetGrab')) || e.target.closest('.gripX')) return;
      e.preventDefault();
      var h0 = el.getBoundingClientRect().height;
      // its full size: all it holds (as far as the screen allows) -- measured without changing it
      var full = Math.min(window.innerHeight * 0.88, el.scrollHeight + (el.offsetHeight - el.clientHeight));
      d = { id: e.pointerId, y0: e.clientY, h0: h0, max: Math.max(h0, full), dy: 0, pts: [[performance.now(), e.clientY]] };
      try { el.setPointerCapture(e.pointerId); } catch(err){}
      el.classList.add('dragging');
    });
    el.addEventListener('pointermove', function(e){
      if (!d || e.pointerId !== d.id) return;
      e.preventDefault();
      var now = performance.now();
      d.pts.push([now, e.clientY]); while (d.pts.length > 2 && now - d.pts[0][0] > 120) d.pts.shift();
      d.dy = e.clientY - d.y0;
      var h = Math.max(60, Math.min(d.max, d.h0 - d.dy));
      el.style.maxHeight = h + 'px'; el.style.height = h + 'px';
    });
    function end(e){
      if (!d || e.pointerId !== d.id) return;
      var dd = d; d = null; el.classList.remove('dragging');
      var now = performance.now(), a = dd.pts[0], b = dd.pts[dd.pts.length - 1];
      var v = (b[0] - a[0]) > 10 ? (b[1] - a[1]) / (b[0] - a[0]) : 0;           // px/ms over the last ~0.1 s, + = down
      var h = el.getBoundingClientRect().height;
      // (closed at its dragged size -- each panel gets its normal size back when it opens again; resetting it here made it
      // jump up at the end of the slide down, Filip 2026-10-07)
      if ((v > 1.1 && dd.dy > 40) || h < 120){ close(); return; }
      if (h >= dd.max - 2) el._resetSize();                                   // (all the way up: its normal size)
    }
    el.addEventListener('pointerup', end);
    el.addEventListener('pointercancel', end);
  }

