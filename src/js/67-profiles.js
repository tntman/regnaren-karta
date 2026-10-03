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
  // the profile of a name in the app (any capitalisation), or null (an unknown name, or nothing fetched yet)
  function profileOf(name){
    catchReadCopy();
    var P = catchHist && catchHist.prof, p = catchPlain(name); if (!P || !p) return null;
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
  function pfCatches(name){ return hmAll().filter(function(c){ return catchPlain(c.who) === catchPlain(name); }); }
  function openProfile(name){
    var p = profileOf(name); if (!p) return false;
    hmCloseCard(); closeMsgCard(); hideBoatInfo();
    pfName = p.n;
    if (!pfCard.classList.contains('show') && pfCard._resetSize) pfCard._resetSize();
    var pic = AVATARS[p.n];
    document.getElementById('pfAva').innerHTML = pic ? '<img src="' + pic + '" alt="">' : escHtml(Array.from(p.n)[0] || '?').toUpperCase();
    document.getElementById('pfName').textContent = p.n;
    document.getElementById('pfSub').textContent = [p.nick && '”' + p.nick + '”', p.y && 'sedan ' + p.y, p.home].filter(Boolean).join(' · ');
    var bio = document.getElementById('pfBio'); bio.textContent = p.bio; bio.hidden = !p.bio;
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
    var boat = pfBoat(p.n), n = pfCatches(p.n).length;
    document.getElementById('pfBoat').textContent = boat && !boat.me ? 'Båten på kartan · uppdaterad ' + timeAgo(boat.updatedAt) : '';
    document.getElementById('pfMap').hidden = !boat;
    var cb = document.getElementById('pfCatches'); cb.hidden = !n; cb.textContent = 'Fångster i ' + LAKE.name + ' (' + n + ')';
    pfCard.classList.add('show');
    return true;
  }
  function closeProfile(){ pfCard.classList.remove('show'); pfName = null; }
  pfCard.addEventListener('pointerdown', function(e){ e.stopPropagation(); });
  sheetSwipe(pfCard, closeProfile);
  document.getElementById('pfClose').addEventListener('click', closeProfile);
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
  function pfMenuItem(){ menuItemProfile.hidden = !profileOf(userName); }
  menuItemProfile.addEventListener('click', function(){ showMapView(); openProfile(userName); });
  menuBtn.addEventListener('click', pfMenuItem);
  catchListeners.push(pfMenuItem);
  window.__ffProfile = function(name){ var p = profileOf(name); return p ? JSON.parse(JSON.stringify(p)) : null; };
