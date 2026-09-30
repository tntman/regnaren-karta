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
      if (km <= ltAlarm.km && (!hit || km < hit.km)) hit = { km: km, br: ltBearing(ref, s), age: (now - s.t) / 60000 };
    });
    if (!hit) return;
    document.getElementById('ltAlarmMain').textContent = '⚡ Blixt ' + ltKm(hit.km) + ' km bort!';
    document.getElementById('ltAlarmSub').textContent = wxCompass(hit.br) + ' · ' + (hit.age < 1 ? 'nyss' : 'för ' + Math.round(hit.age) + ' min sedan') + ' – sök skydd';
    document.getElementById('ltAlarm').classList.add('show');
    window.__ltAlarms = (window.__ltAlarms || 0) + 1;
    if (ltAlarm.sound) ltBeep();
    if (ltAlarm.vib && navigator.vibrate) try { navigator.vibrate([400, 200, 400, 200, 400]); } catch(e){}
  }
  document.getElementById('ltAlarmOk').addEventListener('click', function(){ document.getElementById('ltAlarm').classList.remove('show'); });

