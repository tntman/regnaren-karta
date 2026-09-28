from playwright.sync_api import sync_playwright
import fakefb
fakefb.FAKE_FIREBASE_JS = fakefb.FAKE_FIREBASE_JS.replace(
    "    get: function(){ return Promise.resolve(snapOf(posDocs)); },",
    "    get: function(){ window.__posGets = (window.__posGets||0) + 1; return Promise.resolve(snapOf(posDocs)); },")
from fakefb import new_page
results = []
def check(name, cond, info=''):
    results.append(bool(cond)); print(('PASS ' if cond else 'FAIL ') + name + ('  -- ' + str(info) if info != '' else ''))
ME = (58.88951, 15.77759)
NEW = (58.88951 + 300/111320.0, 15.77759)
HIDE = """() => { Object.defineProperty(document, 'visibilityState', { value: 'hidden', configurable: true }); document.dispatchEvent(new Event('visibilitychange')); }"""
SHOW = """() => { Object.defineProperty(document, 'visibilityState', { value: 'visible', configurable: true }); document.dispatchEvent(new Event('visibilitychange')); }"""
with sync_playwright() as p:
    b, ctx, pg, errs = new_page(p, geo=ME, cfg={'positions': [{'uid':'calle','name':'Calle','lat':58.8905,'lon':15.779,'ageMin':1}]}, name='Filip')
    pg.evaluate("""() => { var g = navigator.geolocation, o = g.getCurrentPosition.bind(g);
        g.getCurrentPosition = function(s, e, opt){ window.__gcp = (window.__gcp||0) + 1; window.__gcpOpts = opt; return o(s, e, opt); }; }""")
    pg.wait_for_timeout(2500)
    w0 = pg.evaluate('window.__posWrites')
    check('position shared at start', any(x['id'] == 'filip' for x in w0), len(w0))
    # put the app away, the boat moves 300 m, come back 6 s later
    pg.evaluate(HIDE); pg.wait_for_timeout(300)
    ctx.set_geolocation({'latitude': NEW[0], 'longitude': NEW[1], 'accuracy': 5})
    pg.wait_for_timeout(6000)
    pg.evaluate('window.__posWrites.length = 0; window.__posGets = 0')
    pg.evaluate(SHOW); pg.wait_for_timeout(1200)
    check('on opening: fresh GPS position asked for (maximumAge 0)', pg.evaluate('window.__gcp') >= 1 and pg.evaluate('window.__gcpOpts.maximumAge') == 0)
    check('on opening: nothing shared from the old/cached position while waiting', len(pg.evaluate('window.__posWrites')) == 0, pg.evaluate('window.__posWrites'))
    NEW2 = (NEW[0] + 20/111320.0, NEW[1])
    ctx.set_geolocation({'latitude': NEW2[0], 'longitude': NEW2[1], 'accuracy': 5}); pg.wait_for_timeout(1200)
    w = pg.evaluate('window.__posWrites')
    check('first fresh position is shared at once (not after the 20 s interval)', len(w) >= 1 and abs(w[0]['lat'] - NEW2[0]) < 1e-6, w[:1])
    # safety net: no fresh fix at all after opening -> latest known after 8 s
    pg.evaluate(HIDE); pg.wait_for_timeout(300)
    ctx.set_geolocation({'latitude': NEW[0], 'longitude': NEW[1], 'accuracy': 5}); pg.wait_for_timeout(5800)
    pg.evaluate('window.__posWrites.length = 0'); pg.evaluate(SHOW); pg.wait_for_timeout(9000)
    w = pg.evaluate('window.__posWrites')
    check('no fresh fix within 8 s -> shares the latest known position anyway', len(w) >= 1 and abs(w[0]['lat'] - NEW[0]) < 1e-6, w[:1])
    check('on opening: other boats fetched from the server at once (once per opening)', pg.evaluate('window.__posGets') == 2)
    # a short switch away (< 5 s) doesn't trigger anything
    pg.evaluate('window.__posGets = 0'); pg.evaluate(HIDE); pg.wait_for_timeout(1000); pg.evaluate(SHOW); pg.wait_for_timeout(500)
    check('quick app switch (<5 s): no extra fetch', pg.evaluate('window.__posGets') == 0)
    # pulse setting
    check('pulse ring on by default', pg.eval_on_selector('#dotGlow', 'e=>getComputedStyle(e).display') == 'block')
    pg.click('#menuBtn'); pg.click('#menuItemSettings'); pg.wait_for_timeout(200)
    check('Settings: pulse switch is on', pg.is_checked('#gpsPulseToggle'))
    pg.eval_on_selector('#gpsPulseToggle', 'e=>e.scrollIntoView({block:"center"})'); pg.wait_for_timeout(100)
    pg.screenshot(path='pulse_setting.png')
    pg.click('label[for="gpsPulseToggle"] .toggle'); pg.wait_for_timeout(100)
    check('switch off -> no ring', pg.eval_on_selector('#dotGlow', 'e=>getComputedStyle(e).display') == 'none')
    pg.reload(); pg.wait_for_timeout(1500)
    check('remembered after reload/rotation', pg.eval_on_selector('#dotGlow', 'e=>getComputedStyle(e).display') == 'none' and not pg.is_checked('#gpsPulseToggle'))
    check('no page errors', not errs, errs)
    b.close()
print('\n%d/%d passed' % (sum(results), len(results)))
