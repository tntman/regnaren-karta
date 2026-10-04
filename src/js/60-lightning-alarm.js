  /* ================= Åskvarning (lightning alarm) =================
     Settings: Av / 5 / 10 / 20 km (default 10), sound, vibration. A new strike (under
     5 min old) closer than that -> a big red warning, a beep and a buzz (vibration: not
     on iPhone -- Safari has no vibration). Each strike warns once. */
  var LT_ALARM_KEY = 'ffmap_lt_alarm_v1';
  var ltAlarm = { km: 10, sound: true, vib: true };
  try { var la = JSON.parse(localStorage.getItem(LT_ALARM_KEY) || 'null'); if (la) ltAlarm = la; } catch(e){}
  var ltAlarmed = {}, ltAudio = null;
  function ltAlarmSave(){ try { localStorage.setItem(LT_ALARM_KEY, JSON.stringify(ltAlarm)); } catch(e){} ltAlarmUi(); ltTick(); }
  function ltAlarmUi(){
    Array.prototype.forEach.call(document.querySelectorAll('#ltAlarmSeg button'), function(b){ var on = +b.getAttribute('data-km') === ltAlarm.km; b.classList.toggle('active', on); b.setAttribute('aria-checked', on ? 'true' : 'false'); });
    document.getElementById('ltAlarmSound').checked = !!ltAlarm.sound; document.getElementById('ltAlarmVib').checked = !!ltAlarm.vib;
    // the warning switched off: a red pill under the weather (tap = Inställningar at the warning)
    document.getElementById('ltOffPill').hidden = !!ltAlarm.km;
  }
  document.getElementById('ltOffPill').addEventListener('pointerdown', function(e){ e.stopPropagation(); });
  document.getElementById('ltOffPill').addEventListener('click', function(e){
    e.stopPropagation(); showSettingsView(); openSettingsSec('warn');
    var row = document.getElementById('ltAlarmRow'), body = document.getElementById('settingsBody');
    setTimeout(function(){ body.scrollTop += row.getBoundingClientRect().top - body.getBoundingClientRect().top - 12; }, 50);
  });
  document.getElementById('ltAlarmSeg').addEventListener('click', function(e){ var b = e.target.closest ? e.target.closest('button[data-km]') : null; if (b){ ltAlarm.km = +b.getAttribute('data-km'); ltAlarmSave(); } });
  document.getElementById('ltAlarmSound').addEventListener('change', function(e){ ltAlarm.sound = e.target.checked; ltAlarmSave(); });
  document.getElementById('ltAlarmVib').addEventListener('change', function(e){ ltAlarm.vib = e.target.checked; ltAlarmSave(); });
  ltAlarmUi();
  // sound needs a first touch before the page may play it (iPhone): get it ready then
  document.addEventListener('pointerdown', function(){
    if (ltAudio || !(window.AudioContext || window.webkitAudioContext)) return;
    try { ltAudio = new (window.AudioContext || window.webkitAudioContext)(); ltAudio.resume && ltAudio.resume(); } catch(e){}
  }, true);
  function ltBeep(){
    if (!ltAudio) return;
    try {
      var t0 = ltAudio.currentTime;
      [0, 0.28, 0.56].forEach(function(dt){
        var o = ltAudio.createOscillator(), g = ltAudio.createGain();
        o.type = 'square'; o.frequency.value = 880; o.connect(g); g.connect(ltAudio.destination);
        g.gain.setValueAtTime(0.0001, t0 + dt); g.gain.exponentialRampToValueAtTime(0.25, t0 + dt + 0.02); g.gain.exponentialRampToValueAtTime(0.0001, t0 + dt + 0.2);
        o.start(t0 + dt); o.stop(t0 + dt + 0.22);
      });
    } catch(e){}
  }
  function ltCheckAlarm(){
    if (!ltAlarm.km) return;                   // (NOT tied to the map layer: see ltWatch)
    var now = Date.now(), ref = ltRef(), hit = null;
    ltStrikes.forEach(function(s){
      if (ltAlarmed[s.k]) return;
      ltAlarmed[s.k] = 1;
      if (now - s.t > 5 * 60000) return;
      var km = haversineKm(ref.lat, ref.lon, s.lat, s.lon);
      if (km <= ltAlarm.km && (!hit || km < hit.km)) hit = { km: km, br: ltBearing(ref, s), age: (now - s.t) / 60000, t: s.t };
    });
    if (!hit){ ltCheckClear(); return; }
    ltClearSet(Math.max(ltClearGet(), hit.t));
    ltShowNote(false, '⚡ Blixt ' + ltKm(hit.km) + ' km bort!', wxCompass(hit.br) + ' · ' + (hit.age < 1 ? 'nyss' : 'för ' + Math.round(hit.age) + ' min sedan') + ' – sök skydd');
    window.__ltAlarms = (window.__ltAlarms || 0) + 1;
    if (ltAlarm.sound) ltBeep();
    if (ltAlarm.vib && navigator.vibrate) try { navigator.vibrate([400, 200, 400, 200, 400]); } catch(e){}
  }
  function ltShowNote(clear, main, sub){
    var a = document.getElementById('ltAlarm');
    a.classList.toggle('clear', clear);
    document.getElementById('ltAlarmMain').textContent = main;
    document.getElementById('ltAlarmSub').textContent = sub;
    document.getElementById('ltAlarmOk').textContent = clear ? 'OK' : 'OK, jag har sett';
    a.classList.add('show');
  }
  // "Åskan har dragit förbi": after a warning, when no strike has come within the distance for a whole
  // FMI window (30 min, fresh data), a calm green note -- once. The newest strike near you is remembered
  // over a reload (turning the phone); after 3 h it's just forgotten (no "all clear" the next day).
  var LT_CLEAR_KEY = testKey('ffmap_lt_clear_v1');
  function ltClearGet(){ try { return +localStorage.getItem(LT_CLEAR_KEY) || 0; } catch(e){ return 0; } }
  function ltClearSet(t){ try { if (t) localStorage.setItem(LT_CLEAR_KEY, String(t)); else localStorage.removeItem(LT_CLEAR_KEY); } catch(e){} }
  function ltCheckClear(){
    var last = ltClearGet(); if (!last) return;
    var now = Date.now(), ref = ltRef(), near = 0;
    ltStrikes.forEach(function(s){ if (haversineKm(ref.lat, ref.lon, s.lat, s.lon) <= ltAlarm.km) near = Math.max(near, s.t); });
    if (near > last){ ltClearSet(near); return; }
    if (now - last > 3 * 3600000){ ltClearSet(0); return; }
    if (near || now - last < LT_WIN_MIN * 60000) return;
    ltClearSet(0);
    ltShowNote(true, '✓ Åskan har dragit förbi', 'Ingen blixt inom ' + ltAlarm.km + ' km på ' + LT_WIN_MIN + ' min');
  }
  document.getElementById('ltAlarmOk').addEventListener('click', function(){ document.getElementById('ltAlarm').classList.remove('show'); });

