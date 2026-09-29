# iOS home-screen app, upright: iOS gives the page a window ~a status bar shorter than
# the screen (empty band at the bottom, buttons too high). The app is stretched down by
# the measured gap -- only in the home-screen app and upright; a browser is untouched.
from playwright.sync_api import sync_playwright
import fakefb, json
results = []
def check(name, cond, info=''):
    results.append(bool(cond)); print(('PASS ' if cond else 'FAIL ') + name + ('  -- ' + str(info) if info != '' else ''))
ME = (58.88951, 15.77759)
STANDALONE = "Object.defineProperty(navigator, 'standalone', { value: true, configurable: true });"

def open_app(p, w, h, screen_h, standalone):
    b = p.chromium.launch(**fakefb.LAUNCH)
    ctx = b.new_context(viewport={'width': w, 'height': h}, screen={'width': min(w, h), 'height': screen_h},
                        has_touch=True, is_mobile=True, geolocation={'latitude': ME[0], 'longitude': ME[1], 'accuracy': 8},
                        permissions=['geolocation'])
    ctx.add_init_script('window.__fakeCfg = {};')
    if standalone: ctx.add_init_script(STANDALONE)
    ctx.add_init_script(fakefb.FAKE_FIREBASE_JS)
    pg = ctx.new_page(); errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.goto('http://localhost:8899/index.html'); pg.wait_for_timeout(500)
    fakefb.login(pg, 'Filip'); pg.wait_for_timeout(1200)
    return b, pg, errs

def measure(pg):
    return pg.evaluate("""() => ({ gap: getComputedStyle(document.documentElement).getPropertyValue('--ios-gap').trim(),
        on: document.documentElement.classList.contains('iosGap'),
        app: document.getElementById('app').getBoundingClientRect().bottom,
        stage: document.getElementById('stage').clientHeight,
        locate: document.getElementById('locateBtn').getBoundingClientRect().bottom })""")

with sync_playwright() as p:
    # the bug: window 796 px tall on an 852 px screen (56 px = the status bar)
    b, pg, errs = open_app(p, 393, 796, 852, True)
    m = measure(pg)
    check('home-screen app, upright, 56 px short: stretched down 56 px', m['on'] and m['gap'] == '56px' and abs(m['app'] - 852) < 1 and m['stage'] == 852, m)
    check('...so the buttons move down with it (56 px lower than the window bottom would put them)', m['locate'] > 796 - 60, m)
    pg.screenshot(path='shot_standalone_fix.png', full_page=False)
    # the waypoint sheet reaches the real bottom too
    check('the bottom sheet is stretched as well', pg.evaluate("getComputedStyle(document.getElementById('wpSheet')).bottom") == '-56px')
    check('no page errors', not errs, errs)
    b.close()
    # the same window in a browser (Safari/Chrome): untouched
    b, pg, errs = open_app(p, 393, 796, 852, False)
    m = measure(pg)
    check('in the browser: nothing changed', not m['on'] and m['gap'] == '0px' and abs(m['app'] - 796) < 1, m)
    b.close()
    # home-screen app where the window already fills the screen: nothing to fix
    b, pg, errs = open_app(p, 393, 852, 852, True)
    m = measure(pg)
    check('home-screen app without the gap: nothing changed', not m['on'] and abs(m['app'] - 852) < 1, m)
    b.close()
    # landscape: left alone
    b, pg, errs = open_app(p, 852, 340, 852, True)
    m = measure(pg)
    check('home-screen app on its side: left alone', not m['on'], m)
    b.close()
print('\n%d/%d passed' % (sum(results), len(results)))
