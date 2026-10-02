  /* ================= Spår-menyn (bottenruta) =================
     Opens from the Spår icon in Filter (the icon has a small amber dot: it can be tapped) or from
     Inställningar -> Spår -> Öppna. What it chooses lives in trkCfg (46-gps-track.js, 'ffmap_track_cfg_v1'):
     Mina + one other person from a drop-down (only that person's days are fetched, the moment they are
     picked), how far back, dashed or solid, colour, visibility (the old slider, js/20-map-look.js), stops as rings
     with a minimum time. tools/NOTES_SPAR.md */
  var trkPanel = document.getElementById('trkPanel');
  var trkSwatch = document.querySelector('.visSwatch--track');
  var trkWhoSel = document.getElementById('trkWhoSel');
  function trkFillWho(){   // the member list without yourself (myUid is only known once you've picked your name)
    trkWhoSel.innerHTML = '<option value="">Ingen</option>' + NAME_ROSTER.filter(function(n){ return nameSlug(n) !== myUid; }).map(function(n){ return '<option value="' + nameSlug(n) + '">' + n + '</option>'; }).join('');
  }
  trkFillWho();
  function trkRenderPanel(){
    var c = trkCfg;
    Array.from(document.querySelectorAll('#trkWho button')).forEach(function(b){ b.classList.toggle('on', !!c[b.getAttribute('data-w')]); });
    if (c.who && !trkWhoSel.querySelector('option[value="' + c.who + '"]')) trkWhoSel.insertAdjacentHTML('beforeend', '<option value="' + c.who + '">' + c.who + '</option>');   // (a name that isn't on the member list)
    trkWhoSel.value = c.who || ''; trkWhoSel.classList.toggle('on', !!c.who);
    document.getElementById('trkStopMinBox').hidden = !c.stops;
    document.getElementById('trkStopMin').value = String(c.stopMin); document.getElementById('trkStopMinVal').textContent = c.stopMin + ' min';
    Array.from(document.querySelectorAll('#trkRange button')).forEach(function(b){ b.classList.toggle('on', b.getAttribute('data-r') === c.range); });
    Array.from(document.querySelectorAll('#trkDash button')).forEach(function(b){ b.classList.toggle('on', (b.getAttribute('data-d') === '1') === !!c.dash); });
    Array.from(document.querySelectorAll('#trkColors button')).forEach(function(b){ var on = b.getAttribute('data-c').toLowerCase() === String(c.color).toLowerCase(); b.classList.toggle('active', on); b.setAttribute('aria-checked', on ? 'true' : 'false'); });
    document.getElementById('trkStopsToggle').checked = !!c.stops;
    var days = Object.keys(trkHist).length + (segPointCount(track.segs) ? 1 : 0);
    var oth = 0; Object.keys(trkOthers).forEach(function(id){ if (trkOthers[id].uid === c.who) oth++; });
    var t = days ? '<b>' + days + '</b> ' + (days === 1 ? 'dag' : 'dagar') + ' sparade av dig på ' + LAKE.name : 'Inga sparade dagar än – spåret sparas när du kör på riktigt (inte i Demo Mode).';
    if (c.who) t += trkOthersMsg ? ' · ' + trkOthersMsg : ' · ' + ((trkWhoSel.selectedOptions[0] || {}).text || c.who) + ': <b>' + oth + '</b> ' + (oth === 1 ? 'dag' : 'dagar') + ' sparade';
    if (demoMode) t = '<b>Demo Mode:</b> spåret syns bara nu och sparas inte (inte i databasen heller). Det försvinner när Demo Mode stängs av.';
    document.getElementById('trkInfo').innerHTML = t;
  }
  function trkShowPanel(open){
    if (open){
      setVisMoreOpen(false);
      if (anPanel.classList.contains('show')) showAnPanel(false);
      if (hmPanel.classList.contains('show')) hmShowPanel(false);
      if (!trkPanel.classList.contains('show') && trkPanel._resetSize) trkPanel._resetSize();
      trkFillWho(); trkRenderPanel(); fetchOthersTracks();
    }
    trkPanel.classList.toggle('show', open);
  }
  sheetSwipe(trkPanel, function(){ trkShowPanel(false); });
  trkPanel.addEventListener('pointerdown', function(e){ e.stopPropagation(); });
  document.getElementById('trkClose').addEventListener('click', function(){ trkShowPanel(false); });
  // the Spår icon in Filter = open the panel (the switch itself is still the toggle on the right)
  trkSwatch.addEventListener('click', function(e){ e.preventDefault(); e.stopPropagation(); trkShowPanel(!trkPanel.classList.contains('show')); });
  document.getElementById('trkOpenBtn').addEventListener('click', function(){ document.getElementById('settingsBackBtn').click(); trkShowPanel(true); });
  function trkChanged(){ trkCfgSave(); trkRenderPanel(); renderTrack(); if (typeof setSums === 'function') setSums(); }
  document.getElementById('trkWho').addEventListener('click', function(e){
    var b = e.target.closest ? e.target.closest('button[data-w]') : null; if (!b) return;
    var k = b.getAttribute('data-w'); trkCfg[k] = !trkCfg[k]; trkChanged();
  });
  trkWhoSel.addEventListener('change', function(){ trkCfg.who = trkWhoSel.value; trkChanged(); fetchOthersTracks(); });
  document.getElementById('trkRange').addEventListener('click', function(e){
    var b = e.target.closest ? e.target.closest('button[data-r]') : null; if (!b) return;
    trkCfg.range = b.getAttribute('data-r'); trkChanged(); fetchOthersTracks();
  });
  document.getElementById('trkDash').addEventListener('click', function(e){
    var b = e.target.closest ? e.target.closest('button[data-d]') : null; if (!b) return;
    trkCfg.dash = b.getAttribute('data-d') === '1'; trkChanged();
  });
  document.getElementById('trkColors').addEventListener('click', function(e){
    var b = e.target.closest ? e.target.closest('button[data-c]') : null; if (!b) return;
    trkCfg.color = b.getAttribute('data-c'); trkChanged();
  });
  document.getElementById('trkStopsToggle').addEventListener('change', function(){ trkCfg.stops = this.checked; trkChanged(); });
  document.getElementById('trkStopMin').addEventListener('input', function(){ trkCfg.stopMin = Math.max(2, Math.min(30, parseInt(this.value, 10) || 5)); trkCfgSave(); document.getElementById('trkStopMinVal').textContent = trkCfg.stopMin + ' min'; renderTrack(); });
  trkRenderPanel();
