import os
# Playwright's own Chromium, or set CHROMIUM=/path/to/chromium
LAUNCH = {'executable_path': os.environ['CHROMIUM']} if os.environ.get('CHROMIUM') else {}

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
    posDocs[p.uid] = { lat:p.lat, lon:p.lon, name:p.name, uid:p.uid, lake:'regnaren', device:p.device, updatedAt: ts(now - (p.ageMin||0)*60000) };
  });
  var wpDocs = {};
  (cfg.waypoints || []).forEach(function(w, i){
    wpDocs['w'+i] = { lat:w.lat, lon:w.lon, name:w.name, uid:w.uid, by:w.by||w.uid, lake:'regnaren', createdAt: ts(now - 3600000) };
  });
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
    posDocs[p.uid] = { lat:p.lat, lon:p.lon, name:p.name, uid:p.uid, lake:'regnaren', device:p.device, updatedAt: ts(Date.now() - (p.ageMin||0)*60000) };
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
        window.__posWrites.push({ t: Date.now(), id: id, lat: d.lat, lon: d.lon, device: d.device,
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
  var configCol = { doc: function(id){ return {
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
  window.firebase = {
    initializeApp: function(){ return {}; },
    auth: function(){ return { signInAnonymously: function(){ return Promise.resolve(); }, onAuthStateChanged: function(cb){ cb({ uid:'anon' }); } }; },
    firestore: function(){ return { collection: function(n){ return n === 'positions' ? posCol : (n === 'usage' ? usageCol : (n === 'config' ? configCol : wpCol)); }, enablePersistence: function(){ return Promise.resolve(); } }; }
  };
  window.firebase.firestore.FieldValue = { serverTimestamp: function(){ return {}; } };
  window.firebase.firestore.Timestamp = { fromMillis: function(ms){ return { __epoch: true, ms: ms }; } };
})();
"""

def new_page(p, geo=None, perms=True, cfg=None, name='Testare', wakelock_stub=False):
    import json
    b = p.chromium.launch(**__import__('fakefb').LAUNCH)
    kw = dict(viewport={'width':390,'height':844}, has_touch=True, is_mobile=True)
    if geo:
        kw['geolocation'] = {'latitude':geo[0], 'longitude':geo[1], 'accuracy':8}
    if perms:
        kw['permissions'] = ['geolocation']
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
