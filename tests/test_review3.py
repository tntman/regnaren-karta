from playwright.sync_api import sync_playwright
import fakefb
fakefb.FAKE_FIREBASE_JS = fakefb.FAKE_FIREBASE_JS.replace(
    "update: function(d){ Object.assign(wpDocs[id], d);",
    "update: function(d){ window.__wpUpdates = (window.__wpUpdates||0) + 1; Object.assign(wpDocs[id], d);")
from fakefb import new_page, login

results = []
def check(name, cond, info=''):
    results.append(bool(cond))
    print(('PASS ' if cond else 'FAIL ') + name + ('  -- ' + str(info) if info != '' else ''))

ME = (58.88951, 15.77759)
FAR = (59.30, 18.05)
cfg = {'waypoints': [{'lat':58.8893,'lon':15.7770,'name':'Min grund','uid':'filip','by':'Filip','type':'gos'}]}

def touch(pg, cdp, typ, pts):
    cdp.send('Input.dispatchTouchEvent', {'type': typ, 'touchPoints': [{'x': x, 'y': y, 'id': i} for i, (x, y) in pts]})

with sync_playwright() as p:
    # 1) lifting the fingers after a pinch doesn't add a measure point
    b, ctx, pg, errs = new_page(p, geo=ME, cfg=cfg, name='Filip')
    cdp = ctx.new_cdp_session(pg)
    pg.click('#measureBtn'); pg.wait_for_timeout(150)
    touch(pg, cdp, 'touchStart', [(0, (150, 400))]); touch(pg, cdp, 'touchStart', [(0, (150, 400)), (1, (250, 400))])
    for k in range(1, 6):
        touch(pg, cdp, 'touchMove', [(0, (150 - k*8, 400)), (1, (250 + k*8, 400))]); pg.wait_for_timeout(16)
    touch(pg, cdp, 'touchEnd', [(0, (110, 400))])      # first finger up
    pg.wait_for_timeout(60)
    touch(pg, cdp, 'touchEnd', [])                      # last finger up quickly
    pg.wait_for_timeout(200)
    n = pg.evaluate("document.querySelectorAll('#measureLayer .mlPt').length")
    check('pinch in measure mode adds no stray point', n == 0, n)
    touch(pg, cdp, 'touchStart', [(0, (200, 300))]); pg.wait_for_timeout(50); touch(pg, cdp, 'touchEnd', [])
    pg.wait_for_timeout(150)
    check('a normal tap still adds a point', pg.evaluate("document.querySelectorAll('#measureLayer .mlPt').length") == 1)
    pg.click('#mpClose'); pg.wait_for_timeout(100)

    # 2) touching the map stops a running "centre on me" animation
    pg.mouse.move(200, 500); pg.mouse.down(); pg.mouse.move(60, 700, steps=4); pg.mouse.up(); pg.wait_for_timeout(200)
    pg.click('#locateBtn'); pg.wait_for_timeout(80)
    pg.mouse.move(200, 300); pg.mouse.down(); pg.mouse.move(260, 360, steps=3); pg.mouse.up()
    t1 = pg.eval_on_selector('#world', 'e=>e.style.transform'); pg.wait_for_timeout(600)
    t2 = pg.eval_on_selector('#world', 'e=>e.style.transform')
    check('animation stops when you touch the map', t1 == t2, (t1, t2))

    # 3) Mina off: a new spot still shows while you edit it
    pg.evaluate("document.getElementById('toggleMine').click()"); pg.wait_for_timeout(150)
    n0 = pg.evaluate("document.querySelectorAll('#waypoints .wpPin').length")
    pg.click('#addHereBtn'); pg.wait_for_timeout(900)
    check('new spot visible while editing even with "Mina" off', pg.evaluate("document.querySelectorAll('#waypoints .wpPin').length") == n0 + 1)
    pg.click('#wpCancel'); pg.wait_for_timeout(200)
    pg.evaluate("document.getElementById('toggleMine').click()"); pg.wait_for_timeout(150)

    # 4) saving an unchanged spot costs no write; a change does
    pg.evaluate("window.__wpUpdates = 0")
    pg.evaluate("document.querySelector('#waypoints .wpPin:not(.wpPin--other)').click()"); pg.wait_for_timeout(400)
    pg.click('#wpSave'); pg.wait_for_timeout(200)
    check('unchanged save -> no write', pg.evaluate('window.__wpUpdates') == 0)
    pg.evaluate("document.querySelector('#waypoints .wpPin:not(.wpPin--other)').click()"); pg.wait_for_timeout(400)
    pg.fill('#wpName', 'Min grund 2'); pg.click('#wpSave'); pg.wait_for_timeout(200)
    check('changed save -> one write', pg.evaluate('window.__wpUpdates') == 1)
    check('no page errors (1-4)', not errs, errs); b.close()

    # 5) a name with "/" doesn't break GPS / position sharing / logout
    b, ctx, pg, errs = new_page(p, geo=ME, cfg=cfg, name='Per/Olle')
    pg.wait_for_timeout(1500)
    w = pg.evaluate('window.__posWrites')
    check('"Per/Olle": position shared under a safe id', any(x['id'] == 'per_olle' for x in w), w)
    check('"Per/Olle": own GPS dot shows', pg.eval_on_selector('#marker', 'e=>getComputedStyle(e).display') != 'none')
    pg.click('#menuBtn'); pg.click('#menuItemSettings'); pg.wait_for_timeout(200)
    pg.click('#logoutBtn'); pg.wait_for_timeout(300)
    check('"Per/Olle": logout works', pg.eval_on_selector('#nameModal', 'e=>e.classList.contains("show")'))
    check('no page errors (5)', not errs, errs); b.close()

    # 6) Demo Mode off far from the lake removes the demo boat for the others
    b, ctx, pg, errs = new_page(p, geo=FAR, cfg=cfg, name='Filip')
    pg.wait_for_timeout(800)
    pg.click('#menuBtn'); pg.click('#menuItemSettings'); pg.wait_for_timeout(200)
    pg.click('#demoModeToggle'); pg.wait_for_timeout(1500)
    check('demo position is shared', any(x['id'] == 'filip' for x in pg.evaluate('window.__posWrites')))
    pg.click('#demoModeToggle'); pg.wait_for_timeout(400)
    ups = pg.evaluate('window.__posUpdates') or []
    check('demo off (far away) -> demo boat expired for everyone', any(x['id'] == 'filip' and x['updatedAtMs'] == 0 for x in ups), ups)
    check('no page errors (6)', not errs, errs); b.close()

    # 7) spots saved only on the phone get uploaded once the database is up
    b = p.chromium.launch(**__import__('fakefb').LAUNCH)
    ctx = b.new_context(viewport={'width':390,'height':844}, has_touch=True, is_mobile=True,
                        geolocation={'latitude':ME[0],'longitude':ME[1],'accuracy':8}, permissions=['geolocation'])
    import json, time
    now = int(time.time()*1000)
    local = [{'id':'wpLocal1','lat':58.8899,'lon':15.7790,'name':'Offlinegrund','type':'abborre','uid':'local','by':'Filip','lake':'regnaren','createdAt':now-3600000},
             {'id':'wpAncient','lat':58.8899,'lon':15.7791,'name':'Uråldrig','uid':'local','lake':'regnaren','createdAt':now-90*24*3600000}]
    ctx.add_init_script("if (!sessionStorage.getItem('__seeded')){ sessionStorage.setItem('__seeded','1'); localStorage.setItem('lake_regnaren_waypoints_v1', %s); localStorage.setItem('regnaren_user_name_v1', 'Filip'); }" % json.dumps(json.dumps(local)))
    ctx.add_init_script('window.__fakeCfg = ' + json.dumps(cfg) + ';')
    ctx.add_init_script(fakefb.FAKE_FIREBASE_JS)
    pg = ctx.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.goto('http://localhost:8899/index.html'); pg.wait_for_timeout(1500)
    sets = pg.evaluate('window.__wpSets')
    names = pg.eval_on_selector_all('#waypoints .wpPin', 'e=>e.length')
    left = json.loads(pg.evaluate("localStorage.getItem('lake_regnaren_waypoints_v1')") or '[]')
    check('offline spot uploaded to the shared list', 'wpLocal1' in sets, sets)
    check('...and removed from the phone-only list (ancient one left alone)', [w['id'] for w in left] == ['wpAncient'], left)
    check('no page errors (7)', not errs, errs); b.close()
print('\n%d/%d passed' % (sum(results), len(results)))
