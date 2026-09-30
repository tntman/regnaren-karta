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
        ctx = block_real_firebase(_orig_new_context(self, *a, **kw))
        ctx.add_init_script(TEST_PIN_JS)
        if help_seen:   # Hjälp opens by itself the first time -- tests start as if it's been read (test_help: help_seen=False)
            ctx.add_init_script("try { if (!localStorage.getItem('ffmap_help_seen_v1')) localStorage.setItem('ffmap_help_seen_v1', '999'); } catch(e){}")
        # Inställningar in sections: the tests start with them all open (test_extras checks closing / opening)
        ctx.add_init_script("try { if (!localStorage.getItem('ffmap_settings_open_v1')) localStorage.setItem('ffmap_settings_open_v1', '[\"map\", \"boat\", \"warn\", \"an\", \"off\", \"adv\"]'); } catch(e){}")
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
    if (p.msg){ posDocs[p.uid].msg = p.msg; posDocs[p.uid].msgAt = now - (p.msgAgeMin||0)*60000; }   // (a quick message)
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
  window.__fireWp = fireWp;
  window.__setFromCache = function(v){ window.__fromCache = v; fireWp(); };
  window.__addPos = function(p){
    posDocs[p.uid] = { lat:p.lat, lon:p.lon, name:p.name, uid:p.uid, lake:p.lake||'regnaren', device:p.device, updatedAt: ts(Date.now() - (p.ageMin||0)*60000) };
    if (p.msg){ posDocs[p.uid].msg = p.msg; posDocs[p.uid].msgAt = Date.now() - (p.msgAgeMin||0)*60000; }
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
        window.__posWrites.push({ t: Date.now(), id: id, lat: d.lat, lon: d.lon, device: d.device, lake: d.lake, msg: d.msg, msgAt: d.msgAt,
          updatedAtMs: (d.updatedAt && d.updatedAt.__epoch) ? d.updatedAt.ms : null });
        var merged = Object.assign({}, posDocs[id] || {}, d);
        merged.updatedAt = (d.updatedAt && d.updatedAt.__epoch) ? ts(d.updatedAt.ms) : ts(Date.now());
        posDocs[id] = merged; firePos(); return Promise.resolve();
      }, update: function(d){
        window.__posUpdates = (window.__posUpdates || []); window.__posUpdates.push({ id: id, updatedAtMs: (d.updatedAt && d.updatedAt.__epoch) ? d.updatedAt.ms : null });
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
  var configCol = { doc: function(id){
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
      window.__setCfg(Object.assign({}, window.__cfgDoc || {}, { posIntervalS: d.posIntervalS })); return Promise.resolve();
    } }; } };
  // catches/<lake> (the heat map's catches): cfg.catches = { regnaren: { rows: '<json>', n: 88 }, ... }
  window.__catchDocs = JSON.parse(JSON.stringify(cfg.catches || {})); window.__catchSets = []; window.__catchGets = 0;
  var catchesCol = { doc: function(id){ return {
    get: function(){ window.__catchGets++; var d = window.__catchDocs[id]; return Promise.resolve({ exists: !!d, data: function(){ return d; }, metadata: { fromCache: false } }); },
    set: function(d){ window.__catchSets.push({ id: id, n: d.n }); window.__catchDocs[id] = JSON.parse(JSON.stringify(Object.assign({}, d, { updatedAt: null }))); return Promise.resolve(); }
  }; } };
  var fake = {
    initializeApp: function(){ return {}; },
    auth: function(){ return { signInAnonymously: function(){ return Promise.resolve(); }, onAuthStateChanged: function(cb){ cb({ uid:'anon' }); } }; },
    firestore: function(){ return { collection: function(n){ return n === 'positions' ? posCol : (n === 'usage' ? usageCol : (n === 'config' ? configCol : (n === 'catches' ? catchesCol : wpCol))); }, enablePersistence: function(){ return Promise.resolve(); } }; }
  };
  fake.firestore.FieldValue = { serverTimestamp: function(){ return {}; } };
  fake.firestore.Timestamp = { fromMillis: function(ms){ return { __epoch: true, ms: ms }; } };
  // SAFETY: locked, so the real Firebase SDK can never replace the fake
  // even if it gets loaded somehow (then it just fails, harmlessly).
  Object.defineProperty(window, 'firebase', { value: fake, writable: false, configurable: false });
})();
"""

def new_page(p, geo=None, perms=True, cfg=None, name='Testare', wakelock_stub=False, sw=False, help_seen=True):
    import json
    b = p.chromium.launch(**__import__('fakefb').LAUNCH)
    kw = dict(viewport={'width':390,'height':844}, has_touch=True, is_mobile=True,
              service_workers='allow' if sw else 'block')
    if geo:
        kw['geolocation'] = {'latitude':geo[0], 'longitude':geo[1], 'accuracy':8}
    if perms:
        kw['permissions'] = ['geolocation']
    kw['help_seen'] = help_seen
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
