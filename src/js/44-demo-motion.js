  /* ================= Demo: simulerad rörelse =================
     Drives the demo position around its starting point at about the cruise
     speed, a bit up and down, turning gently -- and back towards the start
     when it gets more than ~350 m away. Every second it feeds a position
     (with its speed) through exactly the same path as real GPS, so the knot
     meter, average speed, measuring tool and position sharing all get
     exercised. */
  var demoSim = null;
  var rotDemoSimUsed = false;
  var demoMoveToggle = document.getElementById('demoMoveToggle');
  // remembered so it survives a reload -- the home-screen app reloads the
  // page on every rotation (see handleOrientationEvent), which used to
  // switch the motion off
  var DEMO_MOVE_KEY = 'regnaren_demo_move_v1';
  function demoMovePref(){ try { return localStorage.getItem(DEMO_MOVE_KEY) !== '0'; } catch(e){ return true; } }
  function setDemoMovePref(on){ try { localStorage.setItem(DEMO_MOVE_KEY, on ? '1' : '0'); } catch(e){} }
  demoMoveToggle.addEventListener('change', function(){
    setDemoMovePref(demoMoveToggle.checked);
    if (demoMoveToggle.checked) startDemoMotion(); else stopDemoMotion();
  });
  function startDemoMotion(){
    if (demoSim || !demoMode || demoLat == null) return;
    demoSim = { heading: Math.random() * 360, turn: 0, t0: Date.now(), phase: Math.random() * 100,
                cLat: demoLat, cLon: demoLon, lastSave: Date.now() };
    if (rotState && rotState.demoSim && !rotDemoSimUsed){
      // after a rotation reload: same course, same circling centre as before
      rotDemoSimUsed = true;
      ['heading', 'turn', 'phase', 't0', 'cLat', 'cLon'].forEach(function(k){
        if (typeof rotState.demoSim[k] === 'number') demoSim[k] = rotState.demoSim[k];
      });
    }
    demoSim.timer = setInterval(demoSimTick, 1000);
  }
  function stopDemoMotion(){
    if (!demoSim) return;
    clearInterval(demoSim.timer);
    demoSim = null;
    if (demoLat != null) setDemoCoords({ lat: demoLat, lon: demoLon }); // stay where the boat got to
  }
  // a jump (reroll / typed coordinates): speed history would be nonsense,
  // and the simulated boat now circles the new spot
  function demoJumped(){
    resetSpeedTracking();
    if (demoSim){ demoSim.cLat = demoLat; demoSim.cLon = demoLon; }
  }
  function demoSimTick(){
    if (!demoMode){ stopDemoMotion(); return; }
    var t = (Date.now() - demoSim.t0) / 1000;
    var kn = cruiseKn * (1 + 0.16 * Math.sin(t / 23 + demoSim.phase) + 0.07 * Math.sin(t / 7.3 + demoSim.phase * 2))
             + (Math.random() - 0.5) * 0.12 * cruiseKn;
    kn = Math.max(0.2, kn);
    var ms = kn / KN_PER_MS;
    // gentle random turning ...
    demoSim.turn = (demoSim.turn + (Math.random() - 0.5) * 4) * 0.85;
    // ... and back towards the start when too far away
    var cosLat = Math.cos(demoLat * Math.PI / 180);
    var dN = (demoSim.cLat - demoLat) * 111320, dE = (demoSim.cLon - demoLon) * 111320 * cosLat;
    if (Math.sqrt(dN * dN + dE * dE) > 350){
      var toStart = Math.atan2(dE, dN) * 180 / Math.PI;
      var diff = ((toStart - demoSim.heading + 540) % 360) - 180;
      demoSim.turn += Math.max(-10, Math.min(10, diff)) * 0.5;
    }
    demoSim.heading = (demoSim.heading + demoSim.turn + 360) % 360;
    // keep off the land: if the water ends ~30 m ahead, turn to the nearest
    // heading that still has water ahead
    if (!demoWaterAhead(demoLat, demoLon, demoSim.heading, 30)){
      for (var a = 20; a <= 180; a += 20){
        var side = demoSim.turn >= 0 ? 1 : -1;
        if (demoWaterAhead(demoLat, demoLon, demoSim.heading + side * a, 30)){ demoSim.heading = (demoSim.heading + side * a + 360) % 360; break; }
        if (demoWaterAhead(demoLat, demoLon, demoSim.heading - side * a, 30)){ demoSim.heading = (demoSim.heading - side * a + 360) % 360; break; }
      }
      demoSim.turn = 0;
    }
    var h = demoSim.heading * Math.PI / 180;
    demoLat += ms * Math.cos(h) / 111320;
    demoLon += ms * Math.sin(h) / (111320 * cosLat);
    var ae = document.activeElement;
    if (ae !== demoLatInput && ae !== demoLonInput) updateDemoCoordsInputs(); // don't fight someone typing
    try { localStorage.setItem(DEMO_LAT_KEY, demoLat); localStorage.setItem(DEMO_LON_KEY, demoLon); } catch(e){}
    onFix(demoLat, demoLon, 8, ms);
  }

