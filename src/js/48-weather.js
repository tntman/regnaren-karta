  /* ---------------- Väder och vind (Open-Meteo, free, no account) ----------------
     Fetched at most every 30 min while the app is open (and when it's opened
     again after that), kept on the phone so the last forecast still shows
     without coverage. Costs nothing in Firebase. */
  var WX_KEY = lakeKey('ffmap_weather_v1', 'weather_v1'), WX_MAX_AGE = 30 * 60 * 1000;
  var WX_URL = 'https://api.open-meteo.com/v1/forecast?latitude=' + LAKE_CENTER_LAT + '&longitude=' + LAKE_CENTER_LON +
    '&current=temperature_2m,apparent_temperature,weather_code,wind_speed_10m,wind_direction_10m,wind_gusts_10m,pressure_msl,precipitation' +
    '&hourly=temperature_2m,wind_speed_10m,wind_direction_10m,wind_gusts_10m,pressure_msl,precipitation,precipitation_probability&daily=sunrise,sunset' +
    '&wind_speed_unit=ms&timezone=Europe%2FStockholm&past_hours=12&forecast_hours=24&forecast_days=2';
  var wx = null, wxFetching = false;
  try { wx = JSON.parse(localStorage.getItem(WX_KEY) || 'null'); } catch(e){}
  var wxChip = document.getElementById('wxChip'), wxCard = document.getElementById('wxCard'), wxBody = document.getElementById('wxBody');
  function wxArrow(dirFrom, size){
    // the arrow shows where the wind is blowing TO (like on a weather map)
    return '<svg class="wxArrow" viewBox="0 0 24 24" width="' + size + '" height="' + size + '" style="transform:rotate(' + Math.round((dirFrom + 180) % 360) + 'deg)"><path d="M12 3l5.5 11.5h-3.8V21h-3.4v-6.5H6.5z" fill="#FFB23F"></path></svg>';
  }
  function wxCompass(d){ return ['N','NO','O','SO','S','SV','V','NV'][Math.round(((d % 360) + 360) % 360 / 45) % 8]; }
  function wxDesc(c){
    if (c === 0) return 'klart'; if (c <= 2) return 'halvklart'; if (c === 3) return 'mulet';
    if (c === 45 || c === 48) return 'dimma'; if (c >= 51 && c <= 57) return 'duggregn'; if (c >= 61 && c <= 67) return 'regn';
    if (c >= 71 && c <= 77) return 'snö'; if (c >= 80 && c <= 82) return 'regnskurar'; if (c >= 85 && c <= 86) return 'snöbyar';
    if (c >= 95) return 'åska'; return '';
  }
  function wxNum(v, dec){ return (Math.round(v * Math.pow(10, dec || 0)) / Math.pow(10, dec || 0)).toFixed(dec || 0).replace('.', ','); }
  function wxHm(ms){ var d = new Date(ms); return ('0' + d.getHours()).slice(-2) + ':' + ('0' + d.getMinutes()).slice(-2); }
  function wxIn(ms){ var m = Math.max(0, Math.round(ms / 60000)); return m < 60 ? m + ' min' : Math.floor(m / 60) + ' h ' + (m % 60) + ' min'; }
  // local "YYYY-MM-DDTHH:MM" (the API's own time zone = Swedish time) -> ms
  function wxT(s){ var p = s.split(/[-T:]/); return new Date(+p[0], +p[1] - 1, +p[2], +p[3] || 0, +p[4] || 0).getTime(); }
  var WX_DROP = '<svg class="wxDrop" viewBox="0 0 24 24" width="11" height="11"><path d="M12 2.5C9 7 6 10.4 6 14.2a6 6 0 0 0 12 0C18 10.4 15 7 12 2.5z" fill="#7cc4ff"></path></svg>';
  // rain in the 3 hours starting at hourly index ix: total mm and highest chance
  function wxRainAt(h, ix, n){
    var mm = 0, pr = 0;
    for (var i = ix; i < Math.min(ix + (n || 3), h.time.length); i++){
      mm += (h.precipitation && h.precipitation[i]) || 0;
      pr = Math.max(pr, (h.precipitation_probability && h.precipitation_probability[i]) || 0);
    }
    return { mm: mm, pr: pr, wet: mm >= 0.2 || pr >= 50 };
  }
  // for the chip: is it raining now, or when does rain start within 3 h?
  function wxRainSoon(){
    var h = wx.data.hourly, now = Date.now(), iNow = -1;
    if (!h.precipitation) return null;
    for (var i = 0; i < h.time.length; i++){ if (wxT(h.time[i]) <= now) iNow = i; }
    if (iNow < 0) return null;
    if ((wx.data.current.precipitation || 0) >= 0.1 || (h.precipitation[iNow] || 0) >= 0.2) return 'nu';
    for (var k = iNow + 1; k <= iNow + 3 && k < h.time.length; k++){
      if ((h.precipitation[k] || 0) >= 0.2 || ((h.precipitation_probability && h.precipitation_probability[k]) || 0) >= 50) return 'kl ' + h.time[k].slice(11, 13);
    }
    return null;
  }
  function wxPressureTrend(){
    // change over the last 3 hours, from the hourly series
    var h = wx.data.hourly, now = Date.now(), iNow = -1, iPast = -1;
    for (var i = 0; i < h.time.length; i++){
      var t = wxT(h.time[i]);
      if (t <= now) iNow = i;
      if (t <= now - 3 * 3600000) iPast = i;
    }
    if (iNow < 0 || iPast < 0) return 0;
    return h.pressure_msl[iNow] - h.pressure_msl[iPast];
  }
  var SHOW_WX_KEY = 'ffmap_show_weather_v1';
  var showWeather = true;
  try { if (localStorage.getItem(SHOW_WX_KEY) === '0') showWeather = false; } catch(e){}
  function renderWeather(){
    var ok = !!(wx && wx.data && wx.data.current) && showWeather;
    wxChip.classList.toggle('show', ok);
    if (!ok){ wxCard.classList.remove('show'); return; }
    var c = wx.data.current, trend = wxPressureTrend();
    var tr = trend > 1 ? '<span class="up">↗</span>' : trend < -1 ? '<span class="down">↘</span>' : '<span class="mut">→</span>';
    wxChip.innerHTML = wxArrow(c.wind_direction_10m, 15) + '<span>' + wxNum(c.wind_speed_10m) + ' <span class="mut">(' + wxNum(c.wind_gusts_10m) + ') m/s</span></span>' +
      '<span class="sep"></span><span>' + wxNum(c.pressure_msl) + ' <span class="mut">hPa</span> ' + tr + '</span>' +
      '<span class="sep"></span><span>' + wxNum(c.temperature_2m) + '°</span>';
    var soon = wxRainSoon();
    if (soon) wxChip.innerHTML += '<span class="sep"></span><span class="rain">' + WX_DROP + soon + '</span>';
    if (!wxCard.classList.contains('show')) return;
    // pressure curve: last 12 h up to now
    var h = wx.data.hourly, now = Date.now(), pts = [];
    for (var i = 0; i < h.time.length; i++){ var t = wxT(h.time[i]); if (t <= now && t >= now - 12.5 * 3600000) pts.push(h.pressure_msl[i]); }
    var spark = '';
    if (pts.length > 1){
      var mn = Math.min.apply(null, pts), mx = Math.max.apply(null, pts), rg = Math.max(2, mx - mn);
      spark = '<svg viewBox="0 0 120 28" width="100%" height="28" style="display:block;margin-top:3px" preserveAspectRatio="none"><polyline points="' +
        pts.map(function(v, k){ return (k / (pts.length - 1) * 120).toFixed(1) + ',' + (24 - (v - mn) / rg * 20).toFixed(1); }).join(' ') +
        '" fill="none" stroke="' + (trend < -1 ? '#FFB23F' : trend > 1 ? '#7fd47f' : '#B7C4C9') + '" stroke-width="2" stroke-linecap="round" vector-effect="non-scaling-stroke"></polyline></svg>';
    }
    var trendTxt = trend > 1 ? '<b class="up">Stiger</b> +' + wxNum(trend) : trend < -1 ? '<b>Sjunker</b> −' + wxNum(-trend) : 'Stabilt ' + (trend >= 0 ? '+' : '−') + wxNum(Math.abs(trend));
    // sun: next event
    var d = wx.data.daily, sunTxt = '', rise = wxT(d.sunrise[0]), set = wxT(d.sunset[0]);
    if (now < rise) sunTxt = 'Soluppgång om ' + wxIn(rise - now);
    else if (now < set) sunTxt = 'Solnedgång om ' + wxIn(set - now);
    else if (d.sunrise[1]) sunTxt = 'Soluppgång om ' + wxIn(wxT(d.sunrise[1]) - now);
    // the next hours: now, +3, +6, +9, +12
    var hours = '', iNow = 0;
    for (var j = 0; j < h.time.length; j++){ if (wxT(h.time[j]) <= now) iNow = j; }
    for (var k = 0; k < 5; k++){
      var ix = iNow + k * 3; if (ix >= h.time.length) break;
      var rn = wxRainAt(h, ix, 3);
      var rainHtml = rn.wet
        ? '<span class="wxRainCol"><span class="wxRain">' + WX_DROP + wxNum(rn.mm, 1) + ' mm</span>' + (rn.pr ? '<small class="wxRain" style="margin-top:0">' + Math.round(rn.pr) + ' %</small>' : '') + '</span>'
        : '<span class="wxRainCol"></span>';
      hours += '<div class="wxH">' + (k ? h.time[ix].slice(11, 13) : 'Nu') + '<b>' + wxNum(h.wind_speed_10m[ix]) + ' m/s</b>' + wxArrow(h.wind_direction_10m[ix], 14) + wxNum(h.temperature_2m[ix]) + '°' + rainHtml + '</div>';
    }
    wxBody.innerHTML =
      '<div class="wxGrid">' +
        '<div class="wxTile"><div class="wxLab">Vind</div><div class="wxBig">' + wxArrow(c.wind_direction_10m, 22) + wxNum(c.wind_speed_10m) + ' <small>m/s</small></div><div class="wxSub">Byar ' + wxNum(c.wind_gusts_10m) + ' m/s · från ' + wxCompass(c.wind_direction_10m) + '</div></div>' +
        '<div class="wxTile"><div class="wxLab">Lufttryck</div><div class="wxBig">' + wxNum(c.pressure_msl) + ' <small>hPa</small></div><div class="wxSub">' + trendTxt + ' hPa på 3 h</div>' + spark + '</div>' +
        '<div class="wxTile"><div class="wxLab">Temperatur</div><div class="wxBig">' + wxNum(c.temperature_2m) + '°</div><div class="wxSub">Känns som ' + wxNum(c.apparent_temperature) + '°' + (wxDesc(c.weather_code) ? ' · ' + wxDesc(c.weather_code) : '') + '</div></div>' +
        '<div class="wxTile"><div class="wxLab">Sol</div><div class="wxBig" style="font-size:16px">☀ ' + wxHm(rise) + ' – ' + wxHm(set) + '</div><div class="wxSub">' + sunTxt + '</div></div>' +
      '</div><div class="wxHours">' + hours + '</div>';
    document.getElementById('wxSrc').textContent = 'Open-Meteo · uppdaterad ' + wxHm(wx.t) + (Date.now() - wx.t > 2 * 3600000 ? ' (utan nät)' : '');
  }
  function fetchWeather(force){
    if (wxFetching) return;
    if (!force && wx && Date.now() - wx.t < WX_MAX_AGE) return;
    if (typeof fetch !== 'function') return;
    wxFetching = true;
    fetch(WX_URL).then(function(r){ return r.ok ? r.json() : null; }).then(function(data){
      wxFetching = false;
      if (!data || !data.current || !data.hourly || !data.daily) return;
      wx = { t: Date.now(), data: data };
      try { localStorage.setItem(WX_KEY, JSON.stringify(wx)); } catch(e){}
      renderWeather();
    }).catch(function(){ wxFetching = false; });
  }
  function setWxOpen(open){
    if (open && !(window.innerHeight <= 520 && window.innerWidth > window.innerHeight)){
      // the big card takes the small chip's place until it's closed with ✕
      var cr = wxChip.getBoundingClientRect();
      if (cr.height) wxCard.style.top = Math.round(cr.top) + 'px';
    } else wxCard.style.top = '';
    wxCard.classList.toggle('show', open);
    wxChip.classList.toggle('hide', open);
    wxChip.setAttribute('aria-expanded', open ? 'true' : 'false');
    if (open) renderWeather();
  }
  wxChip.addEventListener('click', function(e){ e.stopPropagation(); setWxOpen(!wxCard.classList.contains('show')); });
  document.getElementById('wxClose').addEventListener('click', function(){ setWxOpen(false); });
  // a tap anywhere else closes it too; dragging the map doesn't (watch the wind while panning)
  document.addEventListener('click', function(e){
    if (!wxCard.classList.contains('show') || wxCard.contains(e.target) || wxChip.contains(e.target) || mapDraggedJustNow()) return;
    setWxOpen(false);
  });
  var toggleWeatherEl = document.getElementById('toggleWeather');
  toggleWeatherEl.checked = showWeather;
  toggleWeatherEl.addEventListener('change', function(){
    showWeather = toggleWeatherEl.checked;
    try { localStorage.setItem(SHOW_WX_KEY, showWeather ? '1' : '0'); } catch(e){}
    if (!showWeather) setWxOpen(false);
    renderWeather();
  });
  renderWeather();
  setInterval(function(){ if (document.visibilityState !== 'hidden') fetchWeather(false); renderWeather(); }, 60000);

