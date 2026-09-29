  /* ================= Håll skärmen tänd (Wake Lock) -- Filter, off by default ================= */
  var WAKE_KEY = 'ffmap_wakelock_v1';
  var wakeOn = false, wakeLock = null;
  try { wakeOn = localStorage.getItem(WAKE_KEY) === '1'; } catch(e){}
  function applyWake(){
    if (wakeOn && document.visibilityState === 'visible' && navigator.wakeLock && !wakeLock){
      navigator.wakeLock.request('screen').then(function(l){
        wakeLock = l; if (l.addEventListener) l.addEventListener('release', function(){ wakeLock = null; });
        if (!wakeOn){ l.release(); wakeLock = null; }
      }).catch(function(){});
    }
    if (!wakeOn && wakeLock){ try { wakeLock.release(); } catch(e){} wakeLock = null; }
  }
  var toggleWakeEl = document.getElementById('toggleWake');
  toggleWakeEl.checked = wakeOn;
  if (!('wakeLock' in navigator)) toggleWakeEl.closest('label').title = 'Stöds inte av den här webbläsaren (iPhone: iOS 18.4 eller senare)';
  toggleWakeEl.addEventListener('change', function(){
    wakeOn = toggleWakeEl.checked;
    try { localStorage.setItem(WAKE_KEY, wakeOn ? '1' : '0'); } catch(e){}
    applyWake();
  });
  document.addEventListener('visibilitychange', applyWake);
  applyWake();
  var wakeBadge = document.getElementById('wakeBadge'), wakeNote = document.getElementById('wakeNote'), wakeNoteT = null;
  function wakeUi(){ wakeBadge.hidden = !wakeOn; }
  wakeBadge.addEventListener('click', function(e){
    e.stopPropagation();
    wakeOn = false; toggleWakeEl.checked = false;
    try { localStorage.setItem(WAKE_KEY, '0'); } catch(err){}
    applyWake(); wakeUi();
    wakeNote.classList.remove('fade'); wakeNote.classList.add('show');
    clearTimeout(wakeNoteT);
    wakeNoteT = setTimeout(function(){ wakeNote.classList.add('fade'); wakeNoteT = setTimeout(function(){ wakeNote.classList.remove('show', 'fade'); }, 900); }, 20000);
  });
  document.getElementById('wakeNoteClose').addEventListener('click', function(){ clearTimeout(wakeNoteT); wakeNote.classList.remove('show', 'fade'); });
  toggleWakeEl.addEventListener('change', wakeUi);
  wakeUi();
  window.__ffWake = function(){ return { on: wakeOn, held: !!wakeLock }; };

