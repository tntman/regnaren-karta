from playwright.sync_api import sync_playwright
from fakefb import new_page
results = []
def check(name, cond, info=''):
    results.append(bool(cond)); print(('PASS ' if cond else 'FAIL ') + name + ('  -- ' + str(info) if info != '' else ''))
ME = (58.88951, 15.77759)
def north(m, base=ME): return (base[0] + m/111320.0, base[1])
OFF = "() => { var d = document.getElementById('dot'), s = document.getElementById('stage').getBoundingClientRect(); return Math.hypot(parseFloat(d.style.left) - s.width/2, parseFloat(d.style.top) - s.height/2); }"
HIDE = """() => { Object.defineProperty(document, 'visibilityState', { value: 'hidden', configurable: true }); document.dispatchEvent(new Event('visibilitychange')); }"""
SHOW = """() => { Object.defineProperty(document, 'visibilityState', { value: 'visible', configurable: true }); document.dispatchEvent(new Event('visibilitychange')); }"""
with sync_playwright() as p:
    b, ctx, pg, errs = new_page(p, geo=ME, name='Filip', cfg={'waypoints': [{'lat':58.8893,'lon':15.7770,'name':'Grundet','uid':'kalle','by':'Calle','type':'gos'}]})
    ctx.add_init_script("Object.defineProperty(navigator, 'standalone', { value: true, configurable: true });")
    pg.reload(); pg.wait_for_timeout(1200)
    pg.evaluate("""() => { var g = navigator.geolocation, o = g.getCurrentPosition.bind(g), c = g.clearWatch.bind(g);
        g.getCurrentPosition = function(s, e, opt){ window.__gcp = (window.__gcp||0) + 1; window.__gcpOpts = opt; return o(s, e, opt); };
        g.clearWatch = function(id){ window.__cw = (window.__cw||0) + 1; return c(id); }; }""")
    pg.wait_for_timeout(2000)
    check('not following before the button', not pg.eval_on_selector('#locateBtn', 'e=>e.classList.contains("tracking")'))
    pg.click('#locateBtn'); pg.wait_for_timeout(800)
    check('GPS button: following (button marked)', pg.eval_on_selector('#locateBtn', 'e=>e.classList.contains("tracking")'))
    check('GPS button: fresh position asked for (maximumAge 0)', pg.evaluate('window.__gcp') >= 1 and pg.evaluate('window.__gcpOpts.maximumAge') == 0)
    check('GPS button: the watch is started again', pg.evaluate('window.__cw') >= 1)
    # the boat goes 400 m north -> the map goes along, the dot stays in the middle
    ctx.set_geolocation({'latitude': north(400)[0], 'longitude': ME[1], 'accuracy': 5}); pg.wait_for_timeout(1800)
    check('following: the dot stays in the middle as the boat moves', pg.evaluate(OFF) < 6, pg.evaluate(OFF))
    # zooming keeps following
    pg.mouse.move(195, 300); pg.mouse.wheel(0, -300); pg.wait_for_timeout(300)
    ctx.set_geolocation({'latitude': north(450)[0], 'longitude': ME[1], 'accuracy': 5}); pg.wait_for_timeout(1800)
    check('zooming: still following', pg.eval_on_selector('#locateBtn', 'e=>e.classList.contains("tracking")') and pg.evaluate(OFF) < 6, pg.evaluate(OFF))
    # survives rotation (the home-screen app reloads)
    for w, h in ((844, 390), (390, 844)):
        pg.set_viewport_size({'width': w, 'height': h})
        pg.evaluate("window.dispatchEvent(new Event('orientationchange'))")
        pg.wait_for_load_state('load'); pg.wait_for_timeout(1500)
    check('rotation: still following', pg.evaluate("performance.getEntriesByType('navigation')[0].type") == 'reload' and pg.eval_on_selector('#locateBtn', 'e=>e.classList.contains("tracking")'))
    pg.evaluate("""() => { var g = navigator.geolocation, o = g.getCurrentPosition.bind(g), c = g.clearWatch.bind(g);
        g.getCurrentPosition = function(s, e, opt){ window.__gcp = (window.__gcp||0) + 1; window.__gcpOpts = opt; return o(s, e, opt); };
        g.clearWatch = function(id){ window.__cw = (window.__cw||0) + 1; return c(id); }; }""")
    # dragging the map stops following
    pg.mouse.move(195, 480); pg.mouse.down(); pg.mouse.move(195, 400, steps=6); pg.mouse.up(); pg.wait_for_timeout(300)
    check('drag: no longer following', not pg.eval_on_selector('#locateBtn', 'e=>e.classList.contains("tracking")'))
    off0 = pg.evaluate(OFF)
    ctx.set_geolocation({'latitude': north(600)[0], 'longitude': ME[1], 'accuracy': 5}); pg.wait_for_timeout(1800)
    check('not following: the map stays put as the boat moves', pg.evaluate(OFF) > off0 + 20, (off0, pg.evaluate(OFF)))
    # a press again -> following again
    pg.click('#locateBtn'); pg.wait_for_timeout(900)
    check('press again: following and centred', pg.eval_on_selector('#locateBtn', 'e=>e.classList.contains("tracking")') and pg.evaluate(OFF) < 6, pg.evaluate(OFF))
    # going to a spot elsewhere stops following
    pg.evaluate("document.getElementById('menuItemLog').click()"); pg.wait_for_timeout(500)
    pg.click('#logList .logItem'); pg.wait_for_timeout(300)
    check('going to a spot: no longer following', not pg.eval_on_selector('#locateBtn', 'e=>e.classList.contains("tracking")'))
    # coming back to the app starts the GPS watch again
    pg.evaluate('window.__cw = 0'); pg.evaluate(HIDE); pg.wait_for_timeout(5500); pg.evaluate(SHOW); pg.wait_for_timeout(500)
    check('back in the app: the watch is started again', pg.evaluate('window.__cw') >= 1)
    check('no page errors', not errs, errs)
    b.close()
print('\n%d/%d passed' % (sum(results), len(results)))
