  /* ================= Testläge (Demo Mode) – the made-up competition =================
     Everyone in Demo Mode shares a database of their own (TEST_MODE, 10-core.js; tools/NOTES_TESTLAGE.md).
     Its config/<lake> doc has a field "test" -- the admin's made-up competition, read by every test phone:
       { comp: { id, name, date, status: 'planned' | 'active' | 'finished' } | null,
         catches: [rows like Fiskfiskarnas API's: timestamp, competitionId, name, species, cm, lat, lng, lake, approved, imageUrl?],
         voids: [the timestamp of an annulled catch], lt: [{ lat, lon, t }] (lightning strikes) }
     The catches go through the ordinary code (catchGet answers from here: testApi), so the heat map, the
     live catches, "Senaste fisk" etc. work as in a real competition; the strikes likewise (ltFetch ->
     testStrikes). Admin -> Testläge changes it. The test boats, the automatic catches and the approaching
     storm run on the admin's phone only, while the app is open. */
  var TEST_IMG = new URL('icon-512.png', location.href).href;   // ("Med bild": a picture that's in the app)
  var TEST_EMPTY = '{"comp":null,"catches":[],"voids":[],"lt":[]}';
  var TEST_MAX_CATCHES = 500;
  var testState = JSON.parse(TEST_EMPTY);

  // config/<lake>.test changed (cfgDoc's snapshot, 26-sync.js) -> the catches and strikes again, now
  function testApply(t){
    if (!TEST_MODE) return;
    testState = Object.assign(JSON.parse(TEST_EMPTY), t || {});
    if (catchLive) catchLive.at = 0;   // (the live catches: fetched again at once, not in 30 s)
    loadHistory();
    ltFetch();
    testRender();
  }
  // Fiskfiskarnas API, made up from testState (catchGet, 66-catches.js)
  function testApi(path){
    var c = testState.comp, rows = c ? testState.catches.filter(function(x){ return x.competitionId === c.id; }) : [];
    if (path.indexOf('dashboard.php') === 0){
      var voided = {}; testState.voids.forEach(function(ts){ voided[ts] = 1; });
      return { heatmap: c && c.status === 'finished' ? rows.filter(function(x){ return x.approved && !voided[x.timestamp]; }) : [],
               competitions: c ? [{ competition_id: c.id, competition_name: c.name, date: c.date, status: c.status, water: LAKE.name }] : [],
               anglers: [], anglerStats: [], dashboard: [], results: [], records: [] };
    }
    if (path.indexOf('action=bootstrap') >= 0)   // (an annulled catch: a VOID row pointing at it, as in the real API)
      return { ok: true, catches: rows.concat(testState.voids.map(function(ts){ return { timestamp: ts + '|void', displayValue: 'VOID', voidRef: ts }; })) };
    return {};
  }
  // the strikes of the last 30 min (ltFetch, 52-lightning.js)
  function testStrikes(){
    var now = Date.now();
    return testState.lt.filter(function(s){ return now - s.t < LT_WIN_MIN * 60000; })
      .map(function(s){ return { lat: s.lat, lon: s.lon, t: s.t, k: s.lat + ',' + s.lon + ',' + s.t }; });
  }

  // ---- the admin's changes: the whole "test" field, written at once ----
  var testStatusEl = document.getElementById('testStatus');
  function testMsg(t){ testStatusEl.textContent = t; }
  function testSave(){
    if (!USE_FIREBASE || !cfgDoc){ testMsg('Ingen anslutning till testdatabasen – ändringen sparades inte.'); return; }
    var now = Date.now();
    testState.lt = testState.lt.filter(function(s){ return now - s.t < LT_WIN_MIN * 60000; });
    if (testState.catches.length > TEST_MAX_CATCHES) testState.catches = testState.catches.slice(-TEST_MAX_CATCHES);
    addUsage('w', 1);
    // (posIntervalS: the rule for config wants it in every write)
    cfgDoc.set({ posIntervalS: posIntervalS, test: testState, updatedBy: userName || '', updatedAt: firebase.firestore.FieldValue.serverTimestamp() }, { merge: true })
      .catch(function(e){ testMsg('Kunde inte spara (' + ((e && e.code) || 'fel') + ').'); });
  }
  function testSetComp(status){
    if (!testState.comp) testState.comp = { id: 'test-' + Date.now().toString(36), name: 'Testtävling', date: '', status: '' };
    testState.comp.status = status; testState.comp.date = catchTodayIso();
    testSave();
  }

  // ---- who can catch: you, the other phones in Demo Mode, the test boats ----
  function testBoats(){
    var out = [], now = Date.now();
    if (lastOwnLatLon) out.push({ key: 'me', name: userName || 'Du', lat: lastOwnLatLon.lat, lon: lastOwnLatLon.lon });
    Object.keys(boatPositions).forEach(function(id){
      var b = boatPositions[id], bot = testBots.filter(function(x){ return x.id === id; })[0];
      if (bot) out.push({ key: id, name: bot.name, lat: bot.lat, lon: bot.lon, bot: bot });
      else if (now - b.updatedAt < BOAT_GRAY_MS) out.push({ key: id, name: b.name || id, lat: b.lat, lon: b.lon });
    });
    testBots.forEach(function(x){ if (!boatPositions[x.id]) out.push({ key: x.id, name: x.name, lat: x.lat, lon: x.lon, bot: x }); });
    return out;
  }
  function testRandCm(sp){ return Math.round(sp === 'abborre' ? 18 + Math.random() * 28 : sp === 'gadda' ? 45 + Math.random() * 65 : 35 + Math.random() * 40); }
  // a catch at the boat (a few metres off) or anywhere on the water; a test boat then sends "Senaste fisk"
  function testAddCatch(b, sp, cm, ok, img, random){
    var ll = random || !b ? randomDemoPoint() : b, cosLat = Math.cos(ll.lat * Math.PI / 180);
    if (!random && b){ ll = { lat: ll.lat + (Math.random() - 0.5) * 30 / 111320, lon: ll.lon + (Math.random() - 0.5) * 30 / (111320 * cosLat) }; }
    if (!testState.comp) testSetComp('active');   // (a catch needs a competition: one starts)
    var row = { timestamp: new Date().toISOString(), competitionId: testState.comp.id, name: b ? b.name : (userName || 'Du'), species: sp, cm: cm,
                lat: +ll.lat.toFixed(6), lng: +ll.lon.toFixed(6), lake: LAKE.name, approved: !!ok };
    if (img) row.imageUrl = TEST_IMG;
    testState.catches.push(row);
    testSave();
    if (b && b.bot && ok) testBotWrite(b.bot, { msg: msgFishText({ sp: sp, cm: cm }), msgAt: Date.now(), msgSp: sp, msgImg: img ? TEST_IMG : null });
    testMsg(row.name + ': ' + hmSpName(sp) + ' ' + cm + ' cm' + (ok ? '' : ' (inte godkänd)') + ' inlagd.');
  }

  // ---- test boats: positions/bot_1..5, driven from this phone ----
  var TEST_BOTS_KEY = 'lake_' + LAKE_ID + '_test_bots_v1', TEST_AUTO_KEY = 'ffmap_test_auto_v1';
  var testBots = [], testBotTimer = null, testAutoTimer = null, testStorm = null;
  function testBotsSet(n){
    var keep = testBots.slice(0, n);
    testBots.slice(n).forEach(function(b){ testBotWrite(b, { updatedAt: firebase.firestore.Timestamp.fromMillis(0), msg: null, msgAt: 0 }); });
    var saved = []; try { saved = JSON.parse(localStorage.getItem(TEST_BOTS_KEY) || '[]') || []; } catch(e){}
    for (var i = keep.length; i < n; i++){
      var p = saved[i] && isFinite(saved[i].lat) ? saved[i] : randomDemoPoint();
      keep.push({ id: 'bot_' + (i + 1), name: 'Testbåt ' + (i + 1), lat: p.lat, lon: p.lon, cLat: p.lat, cLon: p.lon, hd: Math.random() * 360, turn: 0,
                  kn: 2 + Math.random() * 3, wAt: 0, f: i % 2 ? i - 1 : -1,   // (f: every second boat sits in the one before = "same boat")
                  msgAt: Date.now() + (2 + Math.random() * 5) * 60000 });
    }
    testBots = keep;
    testBotsRemember();
    clearInterval(testBotTimer); testBotTimer = n ? setInterval(testBotsTick, 1000) : null;
    testRender();
  }
  function testBotsRemember(){
    try { if (testBots.length) localStorage.setItem(TEST_BOTS_KEY, JSON.stringify(testBots.map(function(b){ return { lat: b.lat, lon: b.lon }; }))); else localStorage.removeItem(TEST_BOTS_KEY); } catch(e){}
  }
  function testBotWrite(b, extra){
    if (!USE_FIREBASE || !posCol) return;
    b.wAt = Date.now();
    addUsage('w', 1);
    posCol.doc(b.id).set(Object.assign({ lat: b.lat, lon: b.lon, name: b.name, uid: b.id, lake: LAKE_ID,
      updatedAt: firebase.firestore.FieldValue.serverTimestamp() }, extra || {}), { merge: true }).catch(function(){});
  }
  // like the demo boat (44-demo-motion.js): a few knots, turning gently, back towards its spot, never onto land
  function testBotsTick(){
    var now = Date.now();
    testBots.forEach(function(b){
      var cosLat = Math.cos(b.lat * Math.PI / 180), lead = b.f >= 0 && testBots[b.f];
      if (lead){ b.lat = lead.lat + 0.00003; b.lon = lead.lon + 0.00003; if (now - b.wAt >= posIntervalS * 1000) testBotWrite(b); return; }
      b.turn = (b.turn + (Math.random() - 0.5) * 4) * 0.85;
      var dN = (b.cLat - b.lat) * 111320, dE = (b.cLon - b.lon) * 111320 * cosLat;
      if (Math.sqrt(dN * dN + dE * dE) > 500){
        var diff = ((Math.atan2(dE, dN) * 180 / Math.PI - b.hd + 540) % 360) - 180;
        b.turn += Math.max(-10, Math.min(10, diff)) * 0.5;
      }
      b.hd = (b.hd + b.turn + 360) % 360;
      if (!demoWaterAhead(b.lat, b.lon, b.hd, 30)){
        for (var a = 20; a <= 180; a += 20){
          if (demoWaterAhead(b.lat, b.lon, b.hd + a, 30)){ b.hd = (b.hd + a) % 360; break; }
          if (demoWaterAhead(b.lat, b.lon, b.hd - a, 30)){ b.hd = (b.hd - a + 360) % 360; break; }
        }
        b.turn = 0;
      }
      var ms = b.kn / KN_PER_MS, h = b.hd * Math.PI / 180;
      b.lat += ms * Math.cos(h) / 111320; b.lon += ms * Math.sin(h) / (111320 * cosLat);
      if (now >= b.msgAt){   // now and then a quick message
        b.msgAt = now + (3 + Math.random() * 6) * 60000;
        testBotWrite(b, { msg: MSG_TEXTS[Math.floor(Math.random() * MSG_TEXTS.length)], msgAt: now, msgSp: null, msgImg: null });
      } else if (now - b.wAt >= posIntervalS * 1000) testBotWrite(b);
    });
    testBotsRemember();
  }
  // automatic catches: every 30 s someone catches something (a test boat first, otherwise anyone)
  function testAutoSet(on){
    try { localStorage.setItem(TEST_AUTO_KEY, on ? '1' : '0'); } catch(e){}
    clearInterval(testAutoTimer); testAutoTimer = on ? setInterval(testAutoTick, 30000) : null;
    testRender();
  }
  function testAutoTick(){
    var all = testBoats(), bots = all.filter(function(b){ return b.bot; }), pick = bots.length ? bots : all;
    if (!pick.length) return;
    var b = pick[Math.floor(Math.random() * pick.length)];
    var sp = Math.random() < 0.6 ? 'abborre' : Math.random() < 0.75 ? 'gadda' : 'gos', cm = testRandCm(sp);
    testAddCatch(b, sp, cm, sp !== 'abborre' || cm >= 25, false, false);   // (a perch under 25 cm isn't counted)
  }

  // ---- lightning: a strike this far from you, in some direction; "Åskan närmar sig" = one a minute, closer each time ----
  function testStrike(km, br){
    var ref = ltRef(), h = br * Math.PI / 180;
    testState.lt.push({ lat: +(ref.lat + km * Math.cos(h) / 111.32).toFixed(5), lon: +(ref.lon + km * Math.sin(h) / (111.32 * Math.cos(ref.lat * Math.PI / 180))).toFixed(5), t: Date.now() });
    testSave();
    testMsg('Blixt ' + km + ' km bort (' + wxCompass(br) + ').');
  }
  function testStormSet(on){
    if (testStorm){ clearInterval(testStorm.timer); testStorm = null; }
    if (on){ testStorm = { br: Math.random() * 360, km: 25 }; testStormTick(); if (testStorm) testStorm.timer = setInterval(testStormTick, 60000); }
    testRender();
  }
  function testStormTick(){
    testStrike(testStorm.km, testStorm.br + (Math.random() - 0.5) * 30);
    testStorm.km -= 3;
    if (testStorm.km < 1) testStormSet(false);
  }

  // ---- Rensa: no spots, no boats, no competition, no strikes -- for everyone in Demo Mode ----
  function testReset(){
    if (!confirm('Rensa testläget? Testplatser, båtar, meddelanden, tävlingen, fångsterna och blixtarna tas bort för alla i Demo Mode.')) return;
    testBotsSet(0); testAutoSet(false); testStormSet(false);
    if (USE_FIREBASE && fsCol) waypoints.forEach(function(w){ if (w.id) fsCol.doc(String(w.id)).delete().catch(function(){}); });
    if (USE_FIREBASE && posCol) allPositions.forEach(function(p){
      addUsage('w', 1);
      posCol.doc(p.docId).set({ updatedAt: firebase.firestore.Timestamp.fromMillis(p.uid === myUid ? Date.now() : 0), msg: null, msgAt: 0 }, { merge: true }).catch(function(){});
    });
    ownMsg = null; renderMessages();
    testState = JSON.parse(TEST_EMPTY);
    testSave();
    testMsg('Testläget är rensat.');
  }

  // ---- the card (Admin -> Testläge; only in Demo Mode) ----
  var testCard = document.getElementById('adminTestCard'), testWhoEl = document.getElementById('testWho');
  function testSeg(id, val){
    Array.prototype.forEach.call(document.querySelectorAll('#' + id + ' button'), function(b){ var on = b.getAttribute('data-v') === val; b.classList.toggle('active', on); b.setAttribute('aria-checked', on ? 'true' : 'false'); });
  }
  function testRender(){
    testCard.hidden = !TEST_MODE;
    if (!TEST_MODE) return;
    var c = testState.comp, voided = {}, n = 0, nv = 0, now = Date.now();
    testState.voids.forEach(function(ts){ voided[ts] = 1; });
    testState.catches.forEach(function(x){ if (c && x.competitionId === c.id){ if (voided[x.timestamp]) nv++; else n++; } });
    testSeg('testCompSeg', c ? c.status : '');
    testSeg('testBotSeg', String(testBots.length));
    testSeg('testAutoSeg', testAutoTimer ? '1' : '0');
    document.getElementById('testStorm').textContent = testStorm ? 'Stoppa åskan (' + Math.max(1, testStorm.km) + ' km)' : 'Åskan närmar sig';
    document.getElementById('testInfo').textContent = !USE_FIREBASE ? 'Testdatabasen är inte kopplad (FIREBASE_TEST_CONFIG i 14-spots.js) – inget delas än.' :
      (c ? c.name + ' · ' + ({ planned: 'planerad', active: 'pågår', finished: 'avslutad' }[c.status] || '') + ' · ' + n + (n === 1 ? ' fångst' : ' fångster') + (nv ? ' (' + nv + ' annullerade)' : '') : 'Ingen tävling') +
      ' · ' + testState.lt.filter(function(s){ return now - s.t < LT_WIN_MIN * 60000; }).length + ' blixtar senaste 30 min';
    // who: rebuilt only when the boats change (not while someone is choosing)
    var boats = testBoats(), sig = boats.map(function(b){ return b.key + '=' + b.name; }).join('|');
    if (testWhoEl.getAttribute('data-sig') !== sig){
      var cur = testWhoEl.value;
      testWhoEl.textContent = '';
      boats.forEach(function(b){ var o = document.createElement('option'); o.value = b.key; o.textContent = b.key === 'me' ? b.name + ' (du)' : b.name; testWhoEl.appendChild(o); });
      if (cur && boats.some(function(b){ return b.key === cur; })) testWhoEl.value = cur;
      testWhoEl.setAttribute('data-sig', sig);
    }
  }
  function testSegClick(id, fn){
    document.getElementById(id).addEventListener('click', function(e){ var b = e.target.closest ? e.target.closest('button[data-v]') : null; if (b) fn(b.getAttribute('data-v')); });
  }
  testSegClick('testCompSeg', testSetComp);
  testSegClick('testBotSeg', function(v){ testBotsSet(+v); });
  testSegClick('testAutoSeg', function(v){ testAutoSet(v === '1'); });
  document.getElementById('testAddCatch').addEventListener('click', function(){
    var key = testWhoEl.value, b = testBoats().filter(function(x){ return x.key === key; })[0];
    var sp = document.getElementById('testSp').value, cm = parseFloat(String(document.getElementById('testCm').value).replace(',', '.'));
    if (!(cm > 0 && cm < 250)) cm = testRandCm(sp);
    testAddCatch(b, sp, cm, document.getElementById('testOk').checked, document.getElementById('testImg').checked, document.getElementById('testWhere').value === 'rand');
  });
  document.getElementById('testVoidCatch').addEventListener('click', function(){
    var voided = {}; testState.voids.forEach(function(ts){ voided[ts] = 1; });
    var last = testState.catches.filter(function(x){ return !voided[x.timestamp]; }).pop();
    if (!last){ testMsg('Ingen fångst att annullera.'); return; }
    testState.voids.push(last.timestamp); testSave();
    testMsg(last.name + 's ' + hmSpName(catchSpecies(last.species)) + ' ' + last.cm + ' cm annullerad.');
  });
  Array.prototype.forEach.call(document.querySelectorAll('#testStrikes button[data-km]'), function(b){
    b.addEventListener('click', function(){ testStrike(+b.getAttribute('data-km'), Math.random() * 360); });
  });
  document.getElementById('testStorm').addEventListener('click', function(){ testStormSet(!testStorm); });
  document.getElementById('testLtClear').addEventListener('click', function(){ testState.lt = []; testSave(); testMsg('Blixtarna borttagna.'); });
  document.getElementById('testReset').addEventListener('click', testReset);
  // the admin's own test boats and automatic catches carry on after a reload (the phone turned)
  if (TEST_MODE && isAdminUnlocked()){
    var tb = 0; try { tb = JSON.parse(localStorage.getItem(TEST_BOTS_KEY) || '[]').length; } catch(e){}
    if (tb) setTimeout(function(){ testBotsSet(tb); }, 0);   // (after every file has run: the depth data, the messages)
    try { if (localStorage.getItem(TEST_AUTO_KEY) === '1') setTimeout(function(){ testAutoSet(true); }, 0); } catch(e){}
  }
  // the banner: a real competition going on (this phone's real copy of the catches) -> you can't be seen by the others
  if (TEST_MODE) setTimeout(function(){
    var c = null; try { c = JSON.parse(localStorage.getItem(CATCH_REAL_KEY) || 'null'); } catch(e){}
    document.getElementById('demoBannerWarn').hidden = !(c && c.v === 3 && Date.now() - c.at < 12 * 3600e3 && (c.comps || []).some(function(x){ return x.status === 'active'; }));
  }, 0);
  window.__ffTest = function(){ return { on: TEST_MODE, project: FIREBASE_CONFIG.projectId, state: testState, auto: !!testAutoTimer, storm: !!testStorm,
    bots: testBots.map(function(b){ return { id: b.id, lat: b.lat, lon: b.lon }; }), wps: waypoints.map(function(w){ return w.name; }), boats: Object.keys(boatPositions) }; };
