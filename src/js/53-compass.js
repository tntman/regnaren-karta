  /* ================= "Kompass" (Filter, Lager) -- off by default =================
     A wedge from your position (60 degrees wide, 500 m long) towards where the phone
     points: hold it at an island and see where on the map that is. Heading from the phone's
     compass (iOS webkitCompassHeading; Android 'deviceorientationabsolute'). iOS asks for
     permission, and only when it's a tap -- the switch's change event is one. Remembered
     for the session only (rotation reloads the page), not across app starts: the listener
     costs battery. The compass can be 10-20 degrees off near metal and engines. */
  var COMPASS_KEY = 'ffmap_compass_v1', COMPASS_M = 500;
  var compassOn = false, compassHdg = null, compassSx = 0, compassSy = 0, compassLabelT = null;
  try { compassOn = sessionStorage.getItem(COMPASS_KEY) === '1'; } catch(e){}
  var compassWedge = document.getElementById('compassWedge'), toggleCompassEl = document.getElementById('toggleCompass');
  function compassDraw(sx, sy){
    if (typeof sx === 'number'){ compassSx = sx; compassSy = sy; }
    if (!compassOn || compassHdg === null){ compassWedge.style.display = 'none'; return; }
    var d = Math.max(60, Math.min(2400, 2 * COMPASS_M * scale / WEB_METERS_PER_PX));
    var st = compassWedge.style;
    st.display = 'block';
    st.width = st.height = d + 'px';
    st.left = compassSx + 'px'; st.top = compassSy + 'px';
    st.transform = 'translate(-50%,-50%) rotate(' + compassHdg.toFixed(1) + 'deg)';
  }
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
  window.__ffCompass = function(){ return { on: compassOn, hdg: compassHdg, shown: compassWedge.style.display === 'block', w: parseFloat(compassWedge.style.width) || 0 }; };   // (for the tests)
