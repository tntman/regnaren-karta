import os
# Playwright's own Chromium, or set CHROMIUM=/path/to/chromium
LAUNCH = {'executable_path': os.environ['CHROMIUM']} if os.environ.get('CHROMIUM') else {}

# SAFETY: never let a test reach the real Firebase. With internet access the real
# SDK (www.gstatic.com/firebasejs) would load, replace the fake below and write to
# the live database. Every test imports this module, so patch new_context here:
# each context blocks the Firebase SDK and all Google APIs before any page loads.
# Requests made by the app's service worker (e.g. after a reload) skip
# context.route(), so service workers are blocked unless a test asks for them
# (service_workers='allow'); the fake below is also locked against replacement.
BLOCKED_HITS = []
def _block(route):
    BLOCKED_HITS.append(route.request.url)
    route.abort()
def block_real_firebase(ctx):
    for pat in ('**/firebasejs/**', '**/*.googleapis.com/**', '**/*.firebaseio.com/**',
                '**/*.firebaseapp.com/**'):
        ctx.route(pat, _block)
    # lightning (FMI): never the real service -- a test that needs strikes routes it
    # itself (a later route wins)
    ctx.route('**/opendata.fmi.fi/**', lambda r: r.abort())
    # weather (Open-Meteo): never the real one either -- the page fetches it at load, BEFORE a test can route
    # it, and a late real answer was saved over the test's own weather (Vindkant/test_wind flaky). A test
    # that needs weather routes it itself (a later route wins)
    ctx.route('**/api.open-meteo.com/**', lambda r: r.abort())
    # Fiskfiskarnas API (the heat map's catches): never the real one -- new_page serves a fake (FakeApi)
    ctx.route('**/fiskfiskarna.se/**', lambda r: r.abort())
    return ctx
# The real admin code is never written in the tests. Instead the test browser
# treats TEST_PIN as correct: SHA-256 of it is answered with the hash that is in
# the built page. (Init script, so it also works after reloads via the service worker.)
import re as _re
TEST_PIN = '583921'   # (must not occur anywhere in the page -- test_admin checks that)
_PAGE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'docs', 'index.html')
_PIN_HASH = _re.search(r"ADMIN_PIN_HASH = '([0-9a-f]{64})'", open(_PAGE, encoding='utf-8').read()).group(1)
TEST_PIN_JS = """(function(){
  if (!(window.crypto && crypto.subtle && window.TextDecoder)) return;
  var H = '%s', T = 'ffmap-admin:%s', orig = crypto.subtle.digest.bind(crypto.subtle);
  crypto.subtle.digest = function(alg, data){
    try { if (new TextDecoder().decode(data) === T){
      var b = new Uint8Array(32); for (var i = 0; i < 32; i++) b[i] = parseInt(H.substr(i*2, 2), 16);
      return Promise.resolve(b.buffer); } } catch(e){}
    return orig(alg, data);
  };
})();""" % (_PIN_HASH, TEST_PIN)

from playwright.sync_api import Browser as _Browser
if not getattr(_Browser, '_ffGuarded', False):
    _orig_new_context = _Browser.new_context
    def _guarded_new_context(self, *a, **kw):
        kw.setdefault('service_workers', 'block')
        help_seen = kw.pop('help_seen', True)
        splash = kw.pop('splash', False)
        lock = kw.pop('lock', False)
        ctx = block_real_firebase(_orig_new_context(self, *a, **kw))
        ctx.add_init_script(TEST_PIN_JS)
        if not lock:    # the competition lock (66-catches.js) is off in the tests -- test_lock: new_page(cfg={'lock': True})
            ctx.add_init_script("window.__ffNoLock = true;")
        if help_seen:   # Hjälp opens by itself the first time -- tests start as if it's been read (test_help: help_seen=False)
            ctx.add_init_script("try { if (!localStorage.getItem('ffmap_help_seen_v1')) localStorage.setItem('ffmap_help_seen_v1', '999'); } catch(e){}")
        if not splash:   # the start film (35-splash.js, 3.5 s, every time a name is chosen) and the start picture: not in the tests (test_splash: splash=True)
            ctx.add_init_script("window.__ffNoSplash = true; window.__ffNoBoot = true;")
        # Inställningar in sections: the tests start with them all open (test_extras checks closing / opening)
        ctx.add_init_script("try { if (!localStorage.getItem('ffmap_settings_open_v1')) localStorage.setItem('ffmap_settings_open_v1', '[\"map\", \"boat\", \"warn\", \"an\", \"catch\", \"off\", \"adv\"]'); } catch(e){}")
        return ctx
    _Browser.new_context = _guarded_new_context
    _Browser._ffGuarded = True

FAKE_FIREBASE_JS = r"""
(function(){
  var cfg = window.__fakeCfg || {};
  window.__posWrites = [];
  window.__wpSets = [];
  window.__wpAdds = 0;
  window.__fromCache = false;
  var now = Date.now();
  function ts(ms){ return { toMillis: function(){ return ms; } }; }
  var posDocs = {};
  (cfg.positions || []).forEach(function(p){
    posDocs[p.uid] = { lat:p.lat, lon:p.lon, name:p.name, uid:p.uid, lake:p.lake||'regnaren', device:p.device, updatedAt: ts(now - (p.ageMin||0)*60000) };
    if (p.msg){ posDocs[p.uid].msg = p.msg; posDocs[p.uid].msgAt = now - (p.msgAgeMin||0)*60000; posDocs[p.uid].msgSp = p.msgSp; posDocs[p.uid].msgImg = p.msgImg; }   // (a quick message; a catch: species, photo)
  });
  var wpDocs = {};
  (cfg.waypoints || []).forEach(function(w, i){
    wpDocs['w'+i] = { lat:w.lat, lon:w.lon, name:w.name, uid:w.uid, by:w.by||w.uid, lake:w.lake||'regnaren', createdAt: ts(now - 3600000) };
    ['type', 'expiresAt'].forEach(function(k){ if (w[k] !== undefined && wpDocs['w'+i][k] === undefined) wpDocs['w'+i][k] = w[k]; });
  });
  window.__wpDocs = wpDocs;
  var wpListeners = [], posListeners = [];
  function snapOf(docs){
    return { metadata: { fromCache: window.__fromCache }, size: Object.keys(docs).length,
      forEach: function(fn){ Object.keys(docs).forEach(function(id){ fn({ id:id, data:function(){ return docs[id]; } }); }); } };
  }
  function fireWp(){ wpListeners.forEach(function(cb){ cb(snapOf(wpDocs)); }); }
  function firePos(){ posListeners.forEach(function(cb){ cb(snapOf(posDocs)); }); }
  window.__fireWp = fireWp; window.__posDocs = posDocs; window.__firePos = firePos;
  window.__setFromCache = function(v){ window.__fromCache = v; fireWp(); };
  window.__addPos = function(p){
    posDocs[p.uid] = { lat:p.lat, lon:p.lon, name:p.name, uid:p.uid, lake:p.lake||'regnaren', device:p.device, updatedAt: ts(Date.now() - (p.ageMin||0)*60000) };
    if (p.msg){ posDocs[p.uid].msg = p.msg; posDocs[p.uid].msgAt = Date.now() - (p.msgAgeMin||0)*60000; posDocs[p.uid].msgSp = p.msgSp; posDocs[p.uid].msgImg = p.msgImg; }
    firePos();
  };
  function listen(list, docs, a, b){
    var cb = (typeof a === 'function') ? a : b;
    list.push(cb); cb(snapOf(docs)); return function(){};
  }
  var autoId = 0;
  var wpCol = {
    add: function(){ window.__wpAdds++; return new Promise(function(){}); },
    onSnapshot: function(a, b){ return listen(wpListeners, wpDocs, a, b); },
    get: function(){ window.__wpGets = (window.__wpGets || 0) + 1; return Promise.resolve(snapOf(wpDocs)); },
    doc: function(id){
      id = id || ('auto' + (++autoId));
      return {
        id: id,
        // like real Firestore offline: the promise never resolves, but the
        // local listener sees the write immediately (latency compensation)
        set: function(d){ window.__wpSets.push(id); wpDocs[id] = Object.assign({}, d, { createdAt: null }); fireWp(); return new Promise(function(){}); },
        update: function(d){ Object.assign(wpDocs[id], d); fireWp(); return Promise.resolve(); },
        delete: function(){ delete wpDocs[id]; fireWp(); return Promise.resolve(); }
      };
    }
  };
  var posCol = {
    onSnapshot: function(a, b){ return listen(posListeners, posDocs, a, b); },
    get: function(){ return Promise.resolve(snapOf(posDocs)); },
    doc: function(id){
      return { set: function(d){
        window.__posWrites.push({ t: Date.now(), id: id, lat: d.lat, lon: d.lon, device: d.device, lake: d.lake, msg: d.msg, msgAt: d.msgAt, msgSp: d.msgSp, msgImg: d.msgImg,
          updatedAtMs: (d.updatedAt && d.updatedAt.__epoch) ? d.updatedAt.ms : null });
        var merged = Object.assign({}, posDocs[id] || {}, d);
        merged.updatedAt = (d.updatedAt && d.updatedAt.__epoch) ? ts(d.updatedAt.ms) : ts(Date.now());
        posDocs[id] = merged; firePos(); return Promise.resolve();
      }, update: function(d){
        window.__posUpdates = (window.__posUpdates || []); window.__posUpdates.push({ id: id, updatedAtMs: (d.updatedAt && d.updatedAt.__epoch) ? d.updatedAt.ms : null });
        // (also kept over a reload -- Demo Mode on/off reloads right after expiring your boat; with the project it went to)
        try { var L = JSON.parse(sessionStorage.getItem('__fbUpdates') || '[]'); L.push({ id: id, project: window.__fbProject, found: !!posDocs[id], updatedAtMs: (d.updatedAt && d.updatedAt.__epoch) ? d.updatedAt.ms : null }); sessionStorage.setItem('__fbUpdates', JSON.stringify(L)); } catch(e){}
        if (!posDocs[id]){ var e = new Error('not-found'); e.code = 'not-found'; return Promise.reject(e); }
        var m = Object.assign({}, posDocs[id], d);
        m.updatedAt = (d.updatedAt && d.updatedAt.__epoch) ? ts(d.updatedAt.ms) : ts(Date.now());
        posDocs[id] = m; firePos(); return Promise.resolve();
      } };
    }
  };
  var usageDocs = {};
  (cfg.usage || []).forEach(function(u){ usageDocs[u.day + '_' + u.device] = u; });
  window.__usageDocs = usageDocs;
  function denied(){ var e = new Error('denied'); e.code = 'permission-denied'; return Promise.reject(e); }
  var usageCol = {
    doc: function(id){ return { set: function(d){ if (window.__usageDenied) return denied(); usageDocs[id] = Object.assign({}, d); return Promise.resolve(); } }; },
    where: function(field, op, val){ return { get: function(){
      if (window.__usageDenied) return denied();
      var hits = {}; Object.keys(usageDocs).forEach(function(k){ if (usageDocs[k][field] === val) hits[k] = usageDocs[k]; });
      return Promise.resolve(snapOf(hits));
    } }; }
  };
  window.__cfgDoc = cfg.config ? JSON.parse(JSON.stringify(cfg.config)) : null;
  window.__cfgSets = [];
  var cfgListeners = [];
  function cfgSnap(){ var d = window.__cfgDoc; return { exists: !!d, data: function(){ return d; }, metadata: { fromCache: false } }; }
  window.__setCfg = function(d){ window.__cfgDoc = d; cfgListeners.forEach(function(l){ l.cb(cfgSnap()); }); };
  var configCol = { get: function(){ var d = {}; if (window.__cfgDoc) d['regnaren'] = window.__cfgDoc; return Promise.resolve(snapOf(d)); }, doc: function(id){
    // cfg.configByLake = { regnaren: {...}, ... }: a different config/<lake> per lake
    if (cfg.configByLake && !window.__cfgPicked){ window.__cfgPicked = true; window.__cfgDoc = cfg.configByLake[id] ? JSON.parse(JSON.stringify(cfg.configByLake[id])) : null; }
    return {
    onSnapshot: function(a, b, c){
      var cb = (typeof a === 'function') ? a : b, eb = (typeof a === 'function') ? b : c;
      if (window.__cfgDenied){ setTimeout(function(){ var e = new Error('denied'); e.code = 'permission-denied'; eb && eb(e); }, 0); return function(){}; }
      cfgListeners.push({ cb: cb }); setTimeout(function(){ cb(cfgSnap()); }, 0); return function(){};
    },
    set: function(d){
      window.__cfgSets.push(JSON.parse(JSON.stringify(Object.assign({}, d, { updatedAt: null }))));
      if (window.__cfgDenied){ var e = new Error('denied'); e.code = 'permission-denied'; return Promise.reject(e); }
      var nd = Object.assign({}, window.__cfgDoc || {}, { posIntervalS: d.posIntervalS });
      if (d.lockOff !== undefined) nd.lockOff = d.lockOff;   // (the competition lock off for everyone, admin)
      if (d.test !== undefined) nd.test = JSON.parse(JSON.stringify(d.test));   // (the test mode's competition, 37-testmode.js)
      window.__setCfg(nd); return Promise.resolve();
    } }; } };
  // tracks (the Spår, one doc per person + lake + day): cfg.tracks = { '<docId>': {lake, uid, name, day, pts, st, n, lakeDay, ownKey}, ... }
  window.__trackDocs = JSON.parse(JSON.stringify(cfg.tracks || {})); window.__trackSets = []; window.__trackGets = [];
  function tracksQuery(conds){ return {
    where: function(f, op, v){ return tracksQuery(conds.concat([[f, op, v]])); },
    get: function(){
      window.__trackGets.push(conds.map(function(c){ return c.join(' '); }).join(' & '));
      var hits = {};
      Object.keys(window.__trackDocs).forEach(function(id){
        var d = window.__trackDocs[id], ok = true;
        conds.forEach(function(c){ var x = d[c[0]]; ok = ok && (c[1] === '>=' ? x >= c[2] : c[1] === '<=' ? x <= c[2] : x === c[2]); });
        if (ok) hits[id] = d;
      });
      return Promise.resolve(snapOf(hits));
    } }; }
  var tracksCol = {
    where: function(f, op, v){ return tracksQuery([[f, op, v]]); },
    get: function(){ return tracksQuery([]).get(); },
    doc: function(id){ return { set: function(d){
      window.__trackSets.push({ id: id, t: Date.now(), n: d.n, day: d.day, pts: d.pts, st: d.st, lakeDay: d.lakeDay, ownKey: d.ownKey, uid: d.uid, lake: d.lake });
      window.__trackDocs[id] = JSON.parse(JSON.stringify(Object.assign({}, d, { updatedAt: null }))); return Promise.resolve();
    } }; }
  };
  // trackusers/<lake> (who has tracks on the lake): cfg.trackusers = { regnaren: { users: { calle: {u:'calle', n:'Calle'} } } }
  window.__trackUsersDocs = JSON.parse(JSON.stringify(cfg.trackusers || {})); window.__trackUserGets = 0; window.__trackUserSets = [];
  var trackUsersCol = { get: function(){ return Promise.resolve(snapOf(window.__trackUsersDocs)); }, doc: function(id){ return {
    get: function(){ window.__trackUserGets++; var d = window.__trackUsersDocs[id]; return Promise.resolve({ exists: !!d, data: function(){ return d; }, metadata: { fromCache: false } }); },
    set: function(d, opt){
      window.__trackUserSets.push(JSON.parse(JSON.stringify(d)));
      var cur = window.__trackUsersDocs[id] || { users: {} }; cur.users = Object.assign({}, cur.users, d.users || {}); window.__trackUsersDocs[id] = cur; return Promise.resolve();
    } }; } };
  var fake = {
    // the project it was started with (the test mode = Demo Mode has its own, 14-spots.js): another project
    // = another database -> it starts empty (cfg.testDb = what's in it, like the rest of cfg)
    initializeApp: function(c){
      window.__fbProject = c && c.projectId;
      if (window.__fbProject !== 'regnaren-b8b6a'){
        var t = cfg.testDb || {};
        Object.keys(posDocs).forEach(function(k){ delete posDocs[k]; });
        Object.keys(wpDocs).forEach(function(k){ delete wpDocs[k]; });
        (t.positions || []).forEach(function(p){ posDocs[p.uid] = { lat:p.lat, lon:p.lon, name:p.name, uid:p.uid, lake:p.lake||'regnaren', updatedAt: ts(Date.now() - (p.ageMin||0)*60000) }; });
        (t.waypoints || []).forEach(function(w, i){ wpDocs['t'+i] = { lat:w.lat, lon:w.lon, name:w.name, uid:w.uid, by:w.by||w.uid, lake:w.lake||'regnaren', type:w.type, createdAt: ts(Date.now() - 3600000) }; });
        window.__cfgDoc = t.config ? JSON.parse(JSON.stringify(t.config)) : null;
      }
      return {};
    },
    auth: function(){ return { signInAnonymously: function(){ return Promise.resolve(); }, onAuthStateChanged: function(cb){ cb({ uid:'anon' }); } }; },
    firestore: function(){ return { collection: function(n){ return n === 'positions' ? posCol : (n === 'usage' ? usageCol : (n === 'config' ? configCol : (n === 'tracks' ? tracksCol : (n === 'trackusers' ? trackUsersCol : wpCol)))); }, enablePersistence: function(){ return Promise.resolve(); } }; }
  };
  fake.firestore.FieldValue = { serverTimestamp: function(){ return {}; } };
  fake.firestore.Timestamp = { fromMillis: function(ms){ return { __epoch: true, ms: ms }; } };
  // SAFETY: locked, so the real Firebase SDK can never replace the fake
  // even if it gets loaded somehow (then it just fails, harmlessly).
  Object.defineProperty(window, 'firebase', { value: fake, writable: false, configurable: false });
})();
"""

# Fiskfiskarnas API, made up: ctx.api (tests change it while they run).
#   heatmap = dashboard.php's heatmap rows, competitions = its competitions,
#   live = { competitionId: bootstrap catches }, down = True -> every call fails; hits = the URLs asked for.
#   anglers/anglerStats/dashboard/results/records = the profiles (dashboard.php), as the real API has them.
class FakeApi:
    def __init__(self, cfg):
        self.heatmap = list(cfg.get('heatmap', [])); self.competitions = list(cfg.get('competitions', []))
        self.live = dict(cfg.get('live', {})); self.down = False; self.hits = []
        self.prof = {k: cfg.get(k, []) for k in ('anglers', 'anglerStats', 'dashboard', 'results', 'records')}
    def n(self, what): return len([u for u in self.hits if what in u])
    def handle(self, route):
        import json
        url = route.request.url; self.hits.append(url)
        if self.down: return route.abort()
        if 'dashboard.php' in url: body = dict(self.prof, heatmap=self.heatmap, competitions=self.competitions)
        elif 'action=bootstrap' in url:
            cid = __import__('urllib.parse').parse.unquote(url.split('competitionId=')[1].split('&')[0])
            body = {'ok': cid in self.live, 'catches': self.live.get(cid, []), 'participants': []} if cid in self.live else {'ok': False, 'error': 'okänd tävling'}
        else: return route.abort()
        route.fulfill(status=200, content_type='application/json', headers={'Access-Control-Allow-Origin': '*'}, body=json.dumps(body))
def api_row(t_ms, comp, who, sp, cm, lat, lon, lake='Regnaren'):
    # one row like dashboard.php's heatmap (and bootstrap's catches)
    import datetime
    ts = datetime.datetime.utcfromtimestamp(t_ms / 1000.0).strftime('%Y-%m-%dT%H:%M:%S.') + '%03dZ' % (t_ms % 1000)
    return {'timestamp': ts, 'competitionId': comp, 'name': who, 'species': {'gadda': 'Gadda', 'abborre': 'Abborre', 'gos': 'Gos'}.get(sp, sp), 'cm': cm, 'lat': lat, 'lng': lon, 'lake': lake}

def new_page(p, geo=None, perms=True, cfg=None, name='Testare', wakelock_stub=False, sw=False, help_seen=True, splash=False):
    import json
    b = p.chromium.launch(**__import__('fakefb').LAUNCH)
    kw = dict(viewport={'width':390,'height':844}, has_touch=True, is_mobile=True,
              service_workers='allow' if sw else 'block')
    if geo:
        kw['geolocation'] = {'latitude':geo[0], 'longitude':geo[1], 'accuracy':8}
    if perms:
        kw['permissions'] = ['geolocation']
    kw['help_seen'] = help_seen
    kw['splash'] = splash
    kw['lock'] = bool((cfg or {}).get('lock'))
    ctx = b.new_context(**kw)
    ctx.add_init_script('window.__fakeCfg = ' + json.dumps(cfg or {}) + ';')
    if wakelock_stub:
        ctx.add_init_script("""
          window.__wakeReqs = 0;
          Object.defineProperty(navigator, 'wakeLock', { value: { request: function(){
            window.__wakeReqs++;
            var l = { released:false, addEventListener: function(){}, release: function(){ return Promise.resolve(); } };
            return Promise.resolve(l);
          } }, configurable: true });
        """)
    ctx.add_init_script(FAKE_FIREBASE_JS)
    ctx.api = FakeApi((cfg or {}).get('api', {}))
    ctx.route('**/fiskfiskarna.se/**', ctx.api.handle)   # (a later route wins over the block above)
    pg = ctx.new_page()
    errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.goto('http://localhost:8899/index.html')
    pg.wait_for_timeout(500)
    if name:
        login(pg, name)
        pg.wait_for_timeout(900)
    return b, ctx, pg, errs

def login(pg, name):
    chip = pg.query_selector('.nameChip[data-name="%s"]' % name)
    if chip:
        chip.click()
    else:
        pg.click('.nameChip--other'); pg.fill('#nameInput', name)
    pg.click('#nameSave')
