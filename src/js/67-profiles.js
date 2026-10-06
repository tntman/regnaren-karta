  /* ================= Profiler: a fisher's page =================
     From Fiskfiskarnas API (dashboard.php, fetched with the history in 66-catches.js -- no extra calls):
     anglers (name, nickname, since, home water, bio), anglerStats (wins, competitions, biggest fish),
     dashboard (this season: rank, ELO), results (the latest competitions), records (the club's records).
     Kept in the phone's copy as one small record per name (profPack). A bottom panel (#pfCard) opens from:
     a boat on the map, Profil in the menu (yourself), Vem in a catch, who wrote a quick message.
     The link to the app = the name (the member list in the app is the same list). */
  var PF_SP = { pike: 'gadda', perch: 'abborre', zander: 'gos' };
  // anglerStats' keys have å/ä/ö, spaces, capitals and signs ('TOPGädda', '100+Gäddor', 'WIN(A)'): found by their plain name
  function profKey(o, want){ var p = catchPlain(want); for (var k in o) if (catchPlain(k) === p) return o[k]; return null; }
  function profNum(v){ var n = catchNum(v); return n == null ? null : n; }
  function profPack(d){
    var byId = {}, out = {};
    (d.anglers || []).forEach(function(a){
      if (!a || !a.name) return;
      byId[a.angler_id] = out[a.name] = { n: a.name, nick: a.nickname || '', y: a.joined_year || '', home: a.home_water || '', bio: a.bio_short || '', res: [], rec: [] };
    });
    (d.anglerStats || []).forEach(function(s){
      var p = byId[s.angler_id]; if (!p) return;
      p.win = profNum(profKey(s, 'WIN(A)')); p.winp = String(profKey(s, 'WIN%') || ''); p.comps = profNum(profKey(s, 'TÄVLING(Antal)'));
      p.top = { gadda: profNum(profKey(s, 'TOPGädda')), abborre: profNum(profKey(s, 'TOPAbborre')), gos: profNum(profKey(s, 'TOPGös')) };
    });
    (d.dashboard || []).forEach(function(x){
      var p = byId[x.angler_id]; if (p && x.competition_id === 'total'){ p.rank = x.rank; p.elo = x.elo_out; p.season = x.season; }
    });
    (d.results || []).forEach(function(r){ var p = byId[r.angler_id]; if (p) p.res.push({ c: r.competition_name || '', d: r.competition_date || '', r: r.rank, t: r.totl }); });
    (d.records || []).forEach(function(r){
      var p = byId[r.angler_id], sp = PF_SP[catchPlain(r.RECORD_ART)];
      if (p && sp) p.rec.push({ sp: sp, cm: profNum(r.RECORD_CM), on: String(r.RECORD_ACTIVE).toUpperCase() === 'TRUE' });
    });
    Object.keys(out).forEach(function(k){ out[k].res = out[k].res.sort(function(a, b){ return a.d < b.d ? 1 : -1; }).slice(0, 5); });
    return out;
  }
  // the fetched profiles, or null (nothing fetched yet). Demo Mode: the real copy's (only read) or its own, from "Ladda in data"
  var PF_DEMO_KEY = 'ffmap_prof_demo_v1';
  function profStore(){
    if (!TEST_MODE){ catchReadCopy(); return catchHist && catchHist.prof; }
    var P = null;
    try { P = JSON.parse(localStorage.getItem(PF_DEMO_KEY) || 'null'); var c = JSON.parse(localStorage.getItem(CATCH_REAL_KEY) || 'null');
      if (!P && c && c.v >= 3) P = c.prof; } catch(e){}
    return P;
  }
  // the profile of a name in the app (any capitalisation), or null (an unknown name, or nothing fetched yet)
  function profileOf(name){
    var P = profStore(), p = catchPlain(name); if (!P || !p) return null;
    for (var k in P) if (catchPlain(k) === p) return P[k];
    return null;
  }

  // a catch's photo (Cloudinary) in a panel: loaded only when the panel opens; no photo / offline -> nothing shown
  function catchImg(el, url){
    el.onerror = function(){ el.hidden = true; el.removeAttribute('src'); };
    if (url){ if (el.getAttribute('src') !== url) el.src = url; el.hidden = false; } else { el.hidden = true; el.removeAttribute('src'); }
  }

  // ---- the panel ----
  var pfCard = document.getElementById('pfCard'), pfName = null;
  function pfCm(v){ return String(v).replace('.', ',') + ' cm'; }
  function pfOrd(n){ return n + ((n % 10 === 1 || n % 10 === 2) && n % 100 !== 11 && n % 100 !== 12 ? ':a' : ':e'); }
  function pfDate(d){ var m = /^(\d{4})-(\d\d)-(\d\d)/.exec(d || ''); return m ? (+m[3]) + '/' + (+m[2]) + (m[1] !== String(new Date().getFullYear()) ? ' -' + m[1].slice(2) : '') : ''; }
  // their boat on the map now (yourself: your own position)
  function pfBoat(name){
    if (catchPlain(name) === catchPlain(userName)) return lastOwnLatLon ? { me: true, lat: lastOwnLatLon.lat, lon: lastOwnLatLon.lon } : null;
    var now = Date.now(), best = null;
    Object.keys(boatPositions || {}).forEach(function(id){
      var b = boatPositions[id];
      if (catchPlain(b.name) === catchPlain(name) && now - b.updatedAt <= BOAT_REMOVE_MS && (!best || b.updatedAt > best.updatedAt)) best = b;
    });
    return best;
  }
  // (catchData.comp: caught in this lake + the lake's competitions in other waters -- a competition can move lake)
  function pfCatches(name, list){ return (list || (catchData ? catchData.comp : [])).filter(function(c){ return catchPlain(c.who) === catchPlain(name); }); }
  // someone's catches in this lake and its competitions, newest first (the boat box and the profile): "● Gädda 78 cm   26/9 13:00"
  // a competition's name (the live one, or the lake's in the copy), and the water a catch was taken in
  function pfCompName(id){
    if (catchLive && catchLive.comp === id && catchLive.name) return catchLive.name;
    var c = catchHist ? catchHist.comps.filter(function(x){ return x.id === id; })[0] : null; return (c && c.name) || '';
  }
  function pfCompHead(id){ var n = pfCompName(id); return '<div class="pfH">' + (n ? 'Fångster i tävlingen <em class="pfComp">' + escHtml(n) + '</em>' : 'Fångster') + '</div>'; }
  function pfWater(c){
    var id = c.lat != null ? catchLakeOf(c) : null, L = id ? LAKES.filter(function(x){ return x.id === id; })[0] : null;
    return L ? L.name : c.lake || '';
  }
  // (heads: "Fångster i tävlingen X" over each competition's rows; every row ends with its water: "(Östra Vitten)")
  function pfCatchRows(name, max, list, heads){ max = max || 8;   // (list: these catches instead -- the boat box: the live competition's)
    var l = pfCatches(name, list).sort(function(a, b){ return b.t - a.t; }), prev = null;
    return l.slice(0, max).map(function(c){
      var h = heads && c.comp !== prev ? pfCompHead(c.comp) : ''; prev = c.comp;
      var w = pfWater(c);
      return h + '<div class="pfRow"><span><span class="hmSpDot" style="background:rgb(' + HM_COL[c.sp] + ')"></span>' + hmSpName(c.sp) + ' <small>' + hmWhen(c.t) + '</small></span><b>' + pfCm(c.cm) + (w ? ' <small class="pfLake">(' + escHtml(w) + ')</small>' : '') + '</b></div>';
    }).join('') + (l.length > max ? '<div class="pfRow"><span><small>+ ' + (l.length - max) + ' till</small></span></div>' : '');
  }
  // always opens (any name): without a profile only the name, their catches and boat (+ "Ladda in data" when none are fetched)
  var pfLoadErr = '';
  function openProfile(name){
    if (!name) return false;
    var p = profileOf(name), none = !p; p = p || { n: name, res: [], rec: [] };
    hmCloseCard(); closeMsgCard(); hideBoatInfo();
    pfName = p.n;
    if (!pfCard.classList.contains('show') && pfCard._resetSize) pfCard._resetSize();
    var pic = AVATARS[p.n];
    document.getElementById('pfAva').innerHTML = pic ? '<img src="' + pic + '" alt="">' : escHtml(Array.from(p.n)[0] || '?').toUpperCase();
    document.getElementById('pfName').textContent = p.n;
    document.getElementById('pfSub').textContent = [p.nick && '”' + p.nick + '”', p.y && 'sedan ' + p.y, p.home].filter(Boolean).join(' · ');
    var bio = document.getElementById('pfBio'); bio.textContent = p.bio || ''; bio.hidden = !p.bio;
    var have = !!profStore(), busy = TEST_MODE ? pfDemoBusy : catchLoading;
    document.getElementById('pfStats').hidden = none; document.getElementById('pfNone').hidden = !none;
    document.getElementById('pfNoneTxt').textContent = busy ? 'Laddar profilerna…' : pfLoadErr || (have ? 'Ingen profil hos Fiskfiskarna.' : 'Profilerna är inte inladdade på den här telefonen.');
    document.getElementById('pfLoad').hidden = have || busy;
    document.getElementById('pfData').innerHTML = [
      ['Rank ' + (p.season || ''), p.rank ? pfOrd(p.rank) : '–'], ['ELO', p.elo ? Math.round(p.elo) : '–'],
      ['Segrar', p.win != null ? p.win + (p.winp ? ' · ' + p.winp.replace('%', ' %') : '') : '–'], ['Tävlingar', p.comps != null ? p.comps : '–']
    ].map(function(t){ return '<div class="wpTile"><i>' + escHtml(t[0]) + '</i><b>' + escHtml(String(t[1])) + '</b></div>'; }).join('');
    var top = HM_SP.filter(function(x){ return p.top && p.top[x[0]]; });
    document.getElementById('pfTop').innerHTML = top.length ? top.map(function(x){
      var rec = p.rec.some(function(r){ return r.sp === x[0] && r.on && r.cm === p.top[x[0]]; });
      return '<div class="pfRow"><span><span class="hmSpDot" style="background:rgb(' + HM_COL[x[0]] + ')"></span>' + x[1] + '</span><b>' + pfCm(p.top[x[0]]) + (rec ? ' <em class="pfRec">★ Klubbrekord</em>' : '') + '</b></div>';
    }).join('') : '<div class="pfRow"><span>Inga ännu</span></div>';
    document.getElementById('pfRes').innerHTML = p.res.length ? p.res.map(function(r){
      return '<div class="pfRow"><span>' + escHtml(r.c) + ' <small>' + pfDate(r.d) + '</small></span><b>' + (r.r ? pfOrd(r.r) : '–') + (r.t ? ' · ' + pfCm(r.t) : '') + '</b></div>';
    }).join('') : '<div class="pfRow"><span>Inga ännu</span></div>';
    var boat = pfBoat(p.n), n = pfCatches(p.n).length, pl = document.getElementById('pfList');
    pl.innerHTML = n ? pfCatchRows(p.n, 8, null, true) : '';
    document.getElementById('pfBoat').textContent = boat && !boat.me ? 'Båten på kartan · uppdaterad ' + timeAgo(boat.updatedAt) : '';
    document.getElementById('pfMap').hidden = !boat;
    document.getElementById('pfGo').hidden = !boat || !!boat.me;
    var nh = hmAll().filter(function(c){ return catchPlain(c.who) === catchPlain(p.n); }).length;   // (the button: the heat map = only this lake)
    var cb = document.getElementById('pfCatches'); cb.hidden = !nh; cb.textContent = 'Fångster i ' + LAKE.name + ' (' + nh + ')';
    pfCard.classList.add('show');
    return true;
  }
  function closeProfile(){ pfCard.classList.remove('show'); pfName = null; pfLoadErr = ''; }
  // "Ladda in data": the history (with the profiles); Demo Mode: only the profiles, from the real API (only read, never the real copy)
  var pfDemoBusy = false;
  function pfReopen(){ if (pfName && pfCard.classList.contains('show')) openProfile(pfName); }
  document.getElementById('pfLoad').addEventListener('click', function(){
    pfLoadErr = '';
    if (!TEST_MODE){ loadCatches(true); pfReopen(); return; }
    pfDemoBusy = true; pfReopen();
    catchGet('dashboard.php', 'h', function(err, d){
      pfDemoBusy = false;
      if (!err && d && Array.isArray(d.anglers)){ try { localStorage.setItem(PF_DEMO_KEY, JSON.stringify(profPack(d))); } catch(e){} }
      else pfLoadErr = 'Kunde inte ladda (' + (err ? catchErrOf(err).msg : 'oväntat svar') + ').';
      pfReopen();
    }, true);
  });
  catchListeners.push(function(){ if (!document.getElementById('pfNone').hidden){ if (catchErr) pfLoadErr = 'Kunde inte ladda (' + catchErr.msg + ').'; pfReopen(); } });
  pfCard.addEventListener('pointerdown', function(e){ e.stopPropagation(); });
  sheetSwipe(pfCard, closeProfile);
  document.getElementById('pfClose').addEventListener('click', closeProfile);
  document.getElementById('pfGo').addEventListener('click', function(){   // Åk hit: the lead line on their boat
    var b = pfName && pfBoat(pfName), n = pfName; closeProfile(); if (!b || b.me) return;
    var p = latLonToImgPx(b.lat, b.lon); startNav(n, p.x, p.y);
  });
  document.getElementById('pfMap').addEventListener('click', function(){
    var b = pfName && pfBoat(pfName); closeProfile(); if (!b) return;
    if (b.me) centerOnFix(); else centerOnWaypoint(b);
  });
  document.getElementById('pfCatches').addEventListener('click', function(){   // the heat map, only their catches
    var n = pfName; closeProfile(); if (!n) return;
    hmSet.who = n; hmSet.style = 'dots'; hmSave(); hmHeatCache = null; hmSetOn(true, true);
  });
  // Profil in the menu: yourself (only when there is a profile for your name)
  var menuItemProfile = document.getElementById('menuItemProfile');
  function pfMenuItem(){ menuItemProfile.hidden = !userName; }
  menuItemProfile.addEventListener('click', function(){ showMapView(); openProfile(userName); });
  menuBtn.addEventListener('click', pfMenuItem);
  catchListeners.push(pfMenuItem);
  window.__ffProfile = function(name){ var p = profileOf(name); return p ? JSON.parse(JSON.stringify(p)) : null; };
