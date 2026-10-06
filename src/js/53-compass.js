  /* ================= "Kompass" (Filter, Lager) -- off by default =================
     A wedge from your position (60 degrees wide, 500 m long) towards where the phone
     points: hold it at an island and see where on the map that is. Heading from the phone's
     compass (iOS webkitCompassHeading; Android 'deviceorientationabsolute'). iOS asks for
     permission, and only when it's a tap -- the switch's change event is one. Remembered
     for the session only (rotation reloads the page), not across app starts: the listener
     costs battery. The compass can be 10-20 degrees off near metal and engines. */
  var COMPASS_KEY = 'ffmap_compass_v1', COMPASS_CFG_KEY = 'ffmap_compass_cfg_v1';
  var compassCfg = { c: '#F2F2F2', len: 500, ang: 40, wedge: true, dial: true };   // Inställningar → Kartan → Kompassen: colour, length (m), angle (deg)
  try {
    var cc = JSON.parse(localStorage.getItem(COMPASS_CFG_KEY) || 'null');
    if (cc){
      if (/^#[0-9A-Fa-f]{6}$/.test(cc.c)) compassCfg.c = cc.c;
      if (cc.wedge === false && cc.dial !== false) compassCfg.wedge = false;
      else if (cc.dial === false) compassCfg.dial = false;   // aldrig båda av
      if (isFinite(cc.len)) compassCfg.len = Math.max(100, Math.min(2000, +cc.len));
      if (isFinite(cc.ang)) compassCfg.ang = Math.max(15, Math.min(120, +cc.ang));
    }
  } catch(e){}
  var compassOn = false, compassHdg = null, compassSx = 0, compassSy = 0, compassLabelT = null;
  try { compassOn = sessionStorage.getItem(COMPASS_KEY) === '1'; } catch(e){}
  var compassWedge = document.getElementById('compassWedge'), toggleCompassEl = document.getElementById('toggleCompass');
  var compassDial = document.getElementById('compassDial'), cdWedge = document.getElementById('cdWedge');
  // a pie slice pointing up from (cx,cy), radius r, angle ang
  function compassSlice(cx, cy, r, ang){
    var h = ang / 2 * Math.PI / 180, dx = r * Math.sin(h), dy = r * Math.cos(h);
    return 'M' + cx + ' ' + cy + ' L' + (cx - dx).toFixed(1) + ' ' + (cy - dy).toFixed(1) + ' A' + r + ' ' + r + ' 0 0 1 ' + (cx + dx).toFixed(1) + ' ' + (cy - dy).toFixed(1) + 'Z';
  }
  function compassStyle(){
    var c = compassCfg.c;
    compassWedge.querySelectorAll('stop').forEach(function(s){ s.setAttribute('stop-color', c); });
    var p = compassWedge.querySelector('path');
    p.setAttribute('d', compassSlice(100, 100, 100, compassCfg.ang)); p.setAttribute('stroke', c);
    var q = cdWedge.querySelector('path');
    q.setAttribute('d', compassSlice(40, 40, 20, compassCfg.ang)); q.setAttribute('fill', c);
    compassDraw();
  }
  function compassDraw(sx, sy){
    if (typeof sx === 'number'){ compassSx = sx; compassSy = sy; }
    var live = compassOn && compassHdg !== null;
    compassDial.style.display = live && compassCfg.dial ? 'block' : 'none';
    if (!live || !compassCfg.wedge){ compassWedge.style.display = 'none'; return; }
    cdWedge.setAttribute('transform', 'rotate(' + compassHdg.toFixed(1) + ' 40 40)');
    var d = Math.max(60, Math.min(2400, 2 * compassCfg.len * scale / WEB_METERS_PER_PX));
    var st = compassWedge.style;
    st.display = 'block';
    st.width = st.height = d + 'px';
    st.left = compassSx + 'px'; st.top = compassSy + 'px';
    st.transform = 'translate(-50%,-50%) rotate(' + compassHdg.toFixed(1) + 'deg)';
  }
  // the settings: colour, length, angle
  var cpColorsEl = document.getElementById('cpColors'), cpLenEl = document.getElementById('cpLen'), cpAngEl = document.getElementById('cpAng');
  var cpWedgeEl = document.getElementById('cpShowWedge'), cpDialEl = document.getElementById('cpShowDial');
  function compassCfgUi(){
    cpLenEl.value = compassCfg.len; cpAngEl.value = compassCfg.ang;
    cpWedgeEl.checked = compassCfg.wedge; cpDialEl.checked = compassCfg.dial;
    cpWedgeEl.disabled = !compassCfg.dial; cpDialEl.disabled = !compassCfg.wedge;   // den enda som är på kan inte stängas av
    document.getElementById('cpLenVal').textContent = compassCfg.len + ' m';
    document.getElementById('cpAngVal').textContent = compassCfg.ang + '°';
    Array.prototype.forEach.call(cpColorsEl.children, function(b){
      var on = b.getAttribute('data-c').toLowerCase() === compassCfg.c.toLowerCase();
      b.classList.toggle('active', on); b.setAttribute('aria-checked', on ? 'true' : 'false');
    });
  }
  function compassCfgChanged(){
    try { localStorage.setItem(COMPASS_CFG_KEY, JSON.stringify(compassCfg)); } catch(e){}
    compassCfgUi(); compassStyle();
  }
  cpColorsEl.addEventListener('click', function(e){ var b = e.target.closest('button'); if (b){ compassCfg.c = b.getAttribute('data-c'); compassCfgChanged(); } });
  cpWedgeEl.addEventListener('change', function(){ compassCfg.wedge = cpWedgeEl.checked; compassCfgChanged(); });
  cpDialEl.addEventListener('change', function(){ compassCfg.dial = cpDialEl.checked; compassCfgChanged(); });
  cpLenEl.addEventListener('input', function(){ compassCfg.len = +cpLenEl.value; compassCfgChanged(); });
  cpAngEl.addEventListener('input', function(){ compassCfg.ang = +cpAngEl.value; compassCfgChanged(); });
  compassCfgUi(); compassStyle();
  function compassOnEvent(e){
    var h = null;
    if (typeof e.webkitCompassHeading === 'number') h = e.webkitCompassHeading;                 // iOS: degrees from north
    else if (e.absolute && typeof e.alpha === 'number') h = (360 - e.alpha) % 360;              // Android
    if (h === null || !isFinite(h)) return;
    // smoothed, the short way round (north is 0 and 360)
    compassHdg = compassHdg === null ? h : (compassHdg + (((h - compassHdg) % 360 + 540) % 360 - 180) * 0.3 + 360) % 360;
    compassDraw();
  }
  function compassListen(on){
    ['deviceorientation', 'deviceorientationabsolute'].forEach(function(n){
      if (on) window.addEventListener(n, compassOnEvent); else window.removeEventListener(n, compassOnEvent);
    });
  }
  function compassSet(on){
    compassOn = on; toggleCompassEl.checked = on;
    try { sessionStorage.setItem(COMPASS_KEY, on ? '1' : '0'); } catch(e){}
    compassListen(on);
    if (!on) compassHdg = null;
    compassDraw();
  }
  function compassDenied(){
    compassSet(false);
    var lbl = document.getElementById('compassLabel');
    lbl.textContent = 'Kompass: inte tillåten';
    clearTimeout(compassLabelT);
    compassLabelT = setTimeout(function(){ lbl.textContent = 'Kompass'; }, 5000);
  }
  toggleCompassEl.checked = compassOn;
  if (compassOn) compassListen(true);   // (after a rotation reload; if iOS has forgotten the permission nothing arrives -- switch off and on again)
  toggleCompassEl.addEventListener('change', function(){
    if (!toggleCompassEl.checked){ compassSet(false); return; }
    var DOE = window.DeviceOrientationEvent;
    if (DOE && typeof DOE.requestPermission === 'function'){   // iOS 13+: must be asked right here, in the tap
      var req;
      try { req = DOE.requestPermission(); } catch(e){ compassDenied(); return; }
      req.then(function(r){ if (r === 'granted') compassSet(true); else compassDenied(); }).catch(compassDenied);
    } else if (DOE){
      compassSet(true);
    } else compassDenied();
  });
  window.__ffCompass = function(){ return { on: compassOn, hdg: compassHdg, shown: compassWedge.style.display === 'block', w: parseFloat(compassWedge.style.width) || 0, dial: compassDial.style.display === 'block', cfg: compassCfg }; };   // (for the tests)
