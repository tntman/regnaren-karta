  /* ================= PB (personbästa) under a competition =================
     Every phone checks the live catches of the competition going on (catchLive.all, all waters): a counted catch longer
     than that person's longest earlier fish of the species -- in all of Fiskfiskarna's competitions (the profile's TOP,
     if the copy was fetched before the catch), the history and earlier in this competition -- is a PB. Someone's very
     first fish of a species is not. Only PBs from the last hour, each once (ffmap_pb_v1).
     - Yours: a card "Grattis till ditt PB!" with "Skicka snabbmess med PB-fisken" (the bubble gets a rainbow edge, 64-messages.js);
       confetti until the card is closed.
     - Someone else's: a note at the top (like Hotzone's) + confetti for an hour; ✕ = the confetti fades over 30 s.
     Survives a reload/rotation (the state is in localStorage). Filip 2026-10-09. */
  var PB_KEY = 'ffmap_pb_v1', PB_WIN = 3600e3, PB_FADE = 30;
  var pbState = { seen: {}, on: null };   // on: { c, prev, mine, until, closed }
  try { pbState = Object.assign(pbState, JSON.parse(localStorage.getItem(PB_KEY) || '{}')); } catch(e){}
  var pbCard = document.getElementById('pbCard'), pbBackdrop = document.getElementById('pbBackdrop'), pbNote = document.getElementById('pbNote');
  var pbCanvas = document.getElementById('pbConf'), pbRun = null;
  function pbSave(){ try { localStorage.setItem(PB_KEY, JSON.stringify(pbState)); } catch(e){} }
  function pbCm(v){ return String(v).replace('.', ','); }

  // the longest of this person's species before the catch, or 0 (none)
  function pbPrev(c, all){
    var who = catchPlain(c.who), best = 0, P = profStore(), p = P && profKey(P, c.who);
    // (the profile's TOP: a copy fetched after the catch may already hold it -- equal then = this fish, not an earlier one)
    if (p && p.top && p.top[c.sp] && (!catchHist || catchHist.at < c.t || p.top[c.sp] !== c.cm)) best = p.top[c.sp];
    all.forEach(function(x){ if (x.t < c.t && x.sp === c.sp && !x.no && catchPlain(x.who) === who && x.cm > best) best = x.cm; });
    return best;
  }
  function pbCheck(){
    var now = Date.now(), live = catchLive && catchLiveComp() ? catchLive.all : [];
    var all = live.concat(catchData ? catchData.comp : []), fresh = null;
    live.forEach(function(c){
      if (c.no || !c.who || pbState.seen[c.id] || now - c.t > PB_WIN) return;
      pbState.seen[c.id] = c.t;
      var prev = pbPrev(c, all);
      if (prev && c.cm > prev && (!fresh || c.t > fresh.c.t)) fresh = { c: { id: c.id, t: c.t, who: c.who, sp: c.sp, cm: c.cm, img: c.img || null }, prev: prev };
    });
    Object.keys(pbState.seen).forEach(function(k){ if (now - pbState.seen[k] > 2 * PB_WIN) delete pbState.seen[k]; });
    if (fresh){ fresh.until = fresh.c.t + PB_WIN; pbState.on = fresh; }
    pbSave(); pbShow();
  }
  function pbShow(){
    var o = pbState.on;
    if (!o || o.closed || Date.now() > o.until){ pbHide(); return; }
    o.mine = !!userName && catchPlain(o.c.who) === catchPlain(userName);   // (asked each time: the name may come after the catches)
    var fish = hmSpName(o.c.sp) + ' ' + pbCm(o.c.cm) + ' cm';
    pbCard.style.setProperty('--sp', MSG_SP_COL[o.c.sp]);
    if (o.mine){
      document.getElementById('pbFish').textContent = fish;
      document.getElementById('pbWas').textContent = 'Ditt förra bästa: ' + pbCm(o.prev) + ' cm';
      pbBackdrop.classList.add('show'); pbCard.classList.add('show'); pbNote.classList.remove('show');
    } else {
      document.getElementById('pbNoteTitle').textContent = o.c.who + ' fick PB!';
      document.getElementById('pbNoteSub').textContent = fish + ' · förra bästa ' + pbCm(o.prev) + ' cm';
      pbBackdrop.classList.remove('show'); pbCard.classList.remove('show'); pbNote.classList.add('show');
    }
    pbConfetti(o.mine ? 0 : o.until);
  }
  function pbHide(){ pbBackdrop.classList.remove('show'); pbCard.classList.remove('show'); pbNote.classList.remove('show'); }
  function pbClose(){   // yours: the confetti stops at once; someone else's: it fades over 30 s
    var o = pbState.on; if (!o) return;
    o.closed = true; pbSave(); pbHide();
    if (pbRun) pbRun.fade = o.mine ? 0.01 : PB_FADE;
  }
  pbBackdrop.addEventListener('click', pbClose);
  document.getElementById('pbClose').addEventListener('click', pbClose);
  document.getElementById('pbSend').addEventListener('click', function(){
    var o = pbState.on; pbClose();
    if (o) sendMsg(Array.from('PB! ' + hmSpName(o.c.sp) + ' ' + pbCm(o.c.cm) + ' 🎉').slice(0, MSG_OWN_MAX).join(''), { sp: o.c.sp, img: o.c.img, pb: true });
  });
  document.getElementById('pbNoteClose').addEventListener('click', pbClose);

  // the confetti over the whole screen (canvas, never takes a tap); until = stop then (0 = until closed)
  var PB_COLS = ['#F09A60', '#FFD23F', '#34C759', '#3A86FF', '#FF4D6D', '#ffffff'];
  function pbConfetti(until){
    if (pbRun){ if (!pbRun.fade) pbRun.until = until; return; }
    if (window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches) return;
    var cx = pbCanvas.getContext('2d'), R = { until: until, fade: 0, alpha: 1, ps: [] }, W = 0, H = 0;
    function add(y){ R.ps.push({ x: Math.random() * W, y: y, w: 8 + Math.random() * 10, h: 5 + Math.random() * 7, c: PB_COLS[Math.random() * PB_COLS.length | 0],
      vy: 1.6 + Math.random() * 2.2, vx: -0.6 + Math.random() * 1.2, r: Math.random() * 6, vr: -0.1 + Math.random() * 0.2, sw: Math.random() * 6 }); }
    function size(){ W = pbCanvas.width = innerWidth * 2; H = pbCanvas.height = innerHeight * 2; }
    size(); for (var i = 0; i < 70; i++) add(Math.random() * H);
    pbCanvas.hidden = false; pbRun = R;
    // ponytail: one canvas redrawn every frame for up to an hour -- fine for ~90 pieces; pause when hidden if battery matters
    (function tick(){
      if (pbRun !== R) return;
      if (W !== innerWidth * 2) size();
      if (!R.fade && R.until && Date.now() > R.until) R.fade = PB_FADE;
      if (R.fade){ R.alpha -= 1 / (R.fade * 60); if (R.alpha <= 0){ pbRun = null; cx.clearRect(0, 0, W, H); pbCanvas.hidden = true; return; } }
      else if (R.ps.length < 90) add(-20);
      cx.clearRect(0, 0, W, H); cx.globalAlpha = Math.max(0, R.alpha);
      R.ps.forEach(function(q){
        q.y += q.vy; q.sw += 0.05; q.x += q.vx + Math.sin(q.sw) * 0.8; q.r += q.vr;
        cx.save(); cx.translate(q.x, q.y); cx.rotate(q.r); cx.scale(1, Math.abs(Math.cos(q.sw * 1.3))); cx.fillStyle = q.c; cx.fillRect(-q.w / 2, -q.h / 2, q.w, q.h); cx.restore();
      });
      R.ps = R.ps.filter(function(q){ return q.y < H + 30; });
      requestAnimationFrame(tick);
    })();
  }
  catchListeners.push(pbCheck);
  pbShow();   // (after a reload: a PB that is still going on)
  window.__ffPb = function(){ return { card: pbCard.classList.contains('show'), note: pbNote.classList.contains('show') ? document.getElementById('pbNoteTitle').textContent + ' | ' + document.getElementById('pbNoteSub').textContent : null, confetti: !!pbRun, fade: pbRun ? pbRun.fade : null, on: pbState.on }; };   // (for the tests)
