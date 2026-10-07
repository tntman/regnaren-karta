  /* ================= Fog of war (Filter, Lager) -- off by default =================
     The map is dark except where YOU have been: a soft hole (50 m radius, fading out) around every part of
     your own saved tracks (today + the history, js/46-gps-track.js) and around where you are now. Only
     your own, only this lake. The holes are painted once into an offscreen mask (4 m per pixel, one
     sprite per 10 m cell along the track); every frame the mask is just scaled onto the dark layer.
     Not recorded in Demo Mode (no track), but the demo position gets its hole. tools/NOTES_SPAR.md */
  var FOG_KEY = 'ffmap_fog_v1', FOG_R = 50, FOG_CELL = 10;
  var fogOn = false;
  try { fogOn = localStorage.getItem(FOG_KEY) === '1'; } catch(e){}
  var fogEl = document.getElementById('fogLayer'), fogCtx = fogEl.getContext('2d'), toggleFogEl = document.getElementById('toggleFog');
  var fogM = Math.max(4, Math.sqrt(IMG_W * IMG_H * WEB_METERS_PER_PX * WEB_METERS_PER_PX / 3e6));   // metres per mask pixel (>= 4; a huge lake gets coarser)
  var fogMask = document.createElement('canvas');
  fogMask.width = Math.ceil(IMG_W * WEB_METERS_PER_PX / fogM); fogMask.height = Math.ceil(IMG_H * WEB_METERS_PER_PX / fogM);
  var fogMaskCtx = fogMask.getContext('2d'), fogCells = {}, fogDirty = true;
  var fogSprite = (function(){
    var r = FOG_R / fogM, s = Math.ceil(r * 2) + 2, c = document.createElement('canvas'); c.width = c.height = s;
    var g = c.getContext('2d'), gr = g.createRadialGradient(s / 2, s / 2, 0, s / 2, s / 2, r);
    gr.addColorStop(0, 'rgba(255,255,255,1)'); gr.addColorStop(.35, 'rgba(255,255,255,.95)'); gr.addColorStop(.7, 'rgba(255,255,255,.35)'); gr.addColorStop(1, 'rgba(255,255,255,0)');
    g.fillStyle = gr; g.fillRect(0, 0, s, s);
    return c;
  })();
  function fogHole(ctx, lat, lon){   // (a hole at one place; once per 10 m cell when it goes in the mask)
    var p = latLonToImgPx(lat, lon), mx = p.x * WEB_METERS_PER_PX / fogM, my = p.y * WEB_METERS_PER_PX / fogM;
    if (ctx === fogMaskCtx){
      var key = Math.floor(mx * fogM / FOG_CELL) + ',' + Math.floor(my * fogM / FOG_CELL);
      if (fogCells[key]) return;
      fogCells[key] = 1;
    }
    ctx.drawImage(fogSprite, mx - fogSprite.width / 2, my - fogSprite.height / 2);
  }
  function fogStep(a, b){   // a -> b, a hole about every 10 m (a = null: just b)
    if (!a){ fogHole(fogMaskCtx, b[0], b[1]); return; }
    var n = Math.max(1, Math.ceil(haversineKm(a[0], a[1], b[0], b[1]) * 1000 / FOG_CELL));
    for (var i = 1; i <= n; i++) fogHole(fogMaskCtx, a[0] + (b[0] - a[0]) * i / n, a[1] + (b[1] - a[1]) * i / n);
  }
  function fogSegs(segs){ segs.forEach(function(sg){ for (var i = 0; i < sg.length; i++) fogStep(i ? sg[i - 1] : null, sg[i]); }); }
  function fogRebuild(){
    fogDirty = true;
    if (!fogOn) return;
    fogMaskCtx.clearRect(0, 0, fogMask.width, fogMask.height); fogCells = {};
    Object.keys(trkHist).forEach(function(dk){ fogSegs(unpackSegs(trkHist[dk].p)); });
    fogSegs(track.segs);
    if (demoMode) fogSegs(demoTrack.segs);   // (Demo Mode: only while it is on)
    fogDirty = false;
    if (typeof scheduleRender === 'function') scheduleRender();
  }
  function fogAddStep(a, b){ if (fogOn && !fogDirty) fogStep(a, b); else fogDirty = true; }
  function fogDraw(){
    if (!fogOn){ fitLayer(fogEl, false); return; }
    if (fogDirty) fogRebuild();
    var dpr = fitLayer(fogEl, true, true), W = stage.clientWidth, H = stage.clientHeight;
    fogCtx.setTransform(dpr, 0, 0, dpr, 0, 0); fogCtx.globalCompositeOperation = 'source-over'; fogCtx.clearRect(0, 0, W, H);
    if (!(W >= 2 && H >= 2)) return;
    fogCtx.fillStyle = 'rgba(20,24,34,.93)'; fogCtx.fillRect(0, 0, W, H);
    fogCtx.globalCompositeOperation = 'destination-out'; fogCtx.imageSmoothingEnabled = true;
    var k = scale * fogM / WEB_METERS_PER_PX;   // mask pixel -> screen pixel
    fogCtx.drawImage(fogMask, originX, originY, fogMask.width * k, fogMask.height * k);
    if (lastOwnLatLon){   // where you are now (also in Demo Mode, where nothing is recorded)
      var p = latLonToImgPx(lastOwnLatLon.lat, lastOwnLatLon.lon), sx = originX + p.x * scale, sy = originY + p.y * scale, sw = fogSprite.width * k;
      fogCtx.drawImage(fogSprite, sx - sw / 2, sy - sw / 2, sw, sw);
    }
    fogCtx.globalCompositeOperation = 'source-over';
  }
  function fogApply(){ fogEl.classList.toggle('on', fogOn); toggleFogEl.checked = fogOn; if (fogOn){ fogDirty = true; } scheduleRender(); }
  toggleFogEl.addEventListener('change', function(){
    fogOn = toggleFogEl.checked;
    try { localStorage.setItem(FOG_KEY, fogOn ? '1' : '0'); } catch(e){}
    fogApply();
  });
  window.__ffFog = function(){ return { on: fogOn, cells: Object.keys(fogCells).length }; };   // (for the tests)
  fogEl.classList.toggle('on', fogOn); toggleFogEl.checked = fogOn;
