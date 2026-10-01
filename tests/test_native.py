# The app (src/js/11-native.js) with a fake Capacitor: detail tiles from GitHub Pages and saved on
# the phone, the row "Dela position när appen är minimerad", the background-GPS watcher, and the
# background write through Firestore's REST API. (Nothing here reaches GitHub or Google: routed.)
from playwright.sync_api import sync_playwright
import os, fakefb
from fakefb import new_page
results = []
def check(name, cond, info=''):
    results.append(bool(cond)); print(('PASS ' if cond else 'FAIL ') + name + ('  -- ' + str(info) if info != '' else ''))
REG = (58.88951, 15.77759)
DOCS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'docs')
REMOTE = 'https://tntman.github.io/regnaren-karta/'

FAKE_CAP = r"""
window.__cap = { writes: [], http: [], watchers: [], removed: [] };
window.Capacitor = {
  isNativePlatform: function(){ return true; },
  convertFileSrc: function(u){ return u.replace('file:///data/files', 'http://localhost:8899/__appfiles'); },
  registerPlugin: function(name){
    if (name === 'Filesystem') return {
      getUri: function(){ return Promise.resolve({ uri: 'file:///data/files' }); },
      writeFile: function(o){ __cap.writes.push(o.path); return Promise.resolve({}); },
      rmdir: function(){ return Promise.resolve(); }
    };
    return {
      addWatcher: function(o, cb){ __cap.watchers.push(o); window.__bgFix = cb; return Promise.resolve('w' + __cap.watchers.length); },
      removeWatcher: function(o){ __cap.removed.push(o.id); return Promise.resolve(); }
    };
  },
  Plugins: { CapacitorHttp: { post: function(o){ __cap.http.push(JSON.parse(JSON.stringify(o))); return Promise.resolve({ status: 200, data: {} }); } } }
};
"""

APPFILES = 'http://localhost:8899/__appfiles/'   # (the fake "files on the phone")
def serve_remote(route):
    u = route.request.url
    path = u[len(REMOTE if u.startswith(REMOTE) else APPFILES):].split('?')[0]
    f = os.path.join(DOCS, *path.split('/'))
    if os.path.exists(f):
        route.fulfill(status=200, body=open(f, 'rb').read(), headers={'access-control-allow-origin': '*', 'content-type': 'image/jpeg'})
    else:
        route.fulfill(status=404, body='')

with sync_playwright() as p:
    b, ctx, pg, errs = new_page(p, geo=REG, cfg={}, name='Filip')
    check('web: no app row in Settings', pg.query_selector('#toggleBgShare') is None)
    ctx.route(REMOTE + '**', serve_remote)
    ctx.route(APPFILES + '**', serve_remote)
    ctx.add_init_script(FAKE_CAP)
    pg.reload(); pg.wait_for_timeout(1500)

    # Settings → Båten
    pg.click('#menuBtn'); pg.click('#menuItemSettings'); pg.wait_for_timeout(300)
    first = pg.eval_on_selector('.setSec[data-sec="boat"] .setSecBody', 'e => e.firstElementChild.innerText')
    check('app: "Dela position när appen är minimerad" first in Båten, on', 'Dela position när appen är minimerad' in first and pg.is_checked('#toggleBgShare'), first[:60])
    pg.click('#settingsBackBtn'); pg.wait_for_timeout(300)

    # the watcher (at the lake, name chosen)
    pg.wait_for_function('window.__cap.watchers.length > 0', timeout=8000)
    w = pg.evaluate('__cap.watchers[0]')
    check('at the lake: background watcher with the notification "FF Map delar din position"', w['backgroundTitle'] == 'FF Map delar din position' and w['distanceFilter'] == 0, w)

    # tiles: from GitHub Pages, saved on the phone
    pg.mouse.move(195, 422)
    for i in range(8):
        pg.mouse.wheel(0, -400); pg.wait_for_timeout(60)
    pg.wait_for_timeout(2500)
    srcs = pg.eval_on_selector_all('#detailLayer img', 'e => e.map(x => [x.src, x.naturalWidth])')
    check('zoomed in: detail tiles from GitHub Pages and they load', srcs and all(s.startswith(REMOTE + 'lakes/regnaren/tiles_v') and n == 512 for s, n in srcs), srcs[:2])
    writes = pg.evaluate('__cap.writes')
    check('...and every one is saved on the phone', writes and all(x.startswith('lakes/regnaren/tiles_v') for x in writes) and len(writes) >= len(srcs), (len(writes), len(srcs)))
    check('the overview map is the packed one (not the net)', pg.eval_on_selector('#mapImg', 'e => e.getAttribute("src")').startswith('lakes/regnaren/map_v'))

    # setting off -> watcher removed; on -> again
    pg.click('#menuBtn'); pg.click('#menuItemSettings'); pg.wait_for_timeout(300)
    pg.click('label[for="toggleBgShare"]'); pg.wait_for_timeout(300)
    check('setting off: watcher removed, remembered', pg.evaluate('__cap.removed.length') == 1 and pg.evaluate("localStorage.getItem('ffmap_app_bg_share_v1')") == '0')
    pg.click('label[for="toggleBgShare"]'); pg.wait_for_timeout(300)
    check('setting on: watcher again', pg.evaluate('__cap.watchers.length') == 2)
    pg.click('#settingsBackBtn'); pg.wait_for_timeout(300)

    # in the background: the position goes through the REST API, not the SDK
    pg.evaluate("""(function(){ var orig = firebase.auth; firebase.auth = function(){ var a = orig(); a.currentUser = { refreshToken: 'r1',
        getIdTokenResult: function(){ return Promise.resolve({ token: 't1', expirationTime: new Date(Date.now() + 3600000).toUTCString() }); } }; return a; }; })()""")
    sdk0 = len(pg.evaluate('__posWrites'))
    pg.evaluate("document.dispatchEvent(new Event('pause'))")
    pg.wait_for_timeout(21500)   # (the 20 s interval since the last write)
    pg.evaluate("__bgFix({ latitude: %f, longitude: %f, accuracy: 5, speed: 2, bearing: 90, time: Date.now() })" % (REG[0] + 0.001, REG[1]))
    pg.wait_for_timeout(500)
    http = [h for h in pg.evaluate('__cap.http') if 'documents:commit' in h['url']]
    ok = False
    if http:
        wr = http[-1]['data']['writes'][0]
        f = wr['update']['fields']
        ok = (http[-1]['headers']['Authorization'] == 'Bearer t1' and wr['update']['name'].endswith('/documents/positions/filip')
              and abs(f['lat']['doubleValue'] - (REG[0] + 0.001)) < 1e-9 and f['name']['stringValue'] == 'Filip' and f['lake']['stringValue'] == 'regnaren'
              and 'updatedAt' not in f and wr['updateTransforms'][0] == {'fieldPath': 'updatedAt', 'setToServerValue': 'REQUEST_TIME'})
    check('minimized: position written with the REST API (server time), not the SDK', ok and len(pg.evaluate('__posWrites')) == sdk0, http[-1] if http else pg.evaluate('__cap.http'))
    pg.evaluate("document.dispatchEvent(new Event('resume'))")

    # next start: the saved tiles are used
    pg.wait_for_timeout(1200)
    pg.reload(); pg.wait_for_timeout(1500)
    pg.mouse.move(195, 422)
    for i in range(8):
        pg.mouse.wheel(0, -400); pg.wait_for_timeout(60)
    pg.wait_for_timeout(1500)
    srcs = pg.eval_on_selector_all('#detailLayer img', 'e => e.map(x => x.getAttribute("src"))')
    check('next start: saved tiles come from the phone', srcs and any(s.startswith('http://localhost:8899/__appfiles/lakes/regnaren/tiles_v') for s in srcs), srcs[:2])
    check('no page errors', not errs, errs)
    b.close()
print('\n%d/%d passed' % (sum(results), len(results)))
