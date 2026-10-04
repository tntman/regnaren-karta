from playwright.sync_api import sync_playwright
import fakefb, json, math, datetime, time
fakefb.FAKE_FIREBASE_JS = fakefb.FAKE_FIREBASE_JS.replace(
    "wpDocs['w'+i] = { lat:w.lat, lon:w.lon, name:w.name, uid:w.uid, by:w.by||w.uid, lake:w.lake||'regnaren', createdAt: ts(now - 3600000) };",
    "wpDocs['w'+i] = { lat:w.lat, lon:w.lon, name:w.name, type:w.type, uid:w.uid, by:w.by||w.uid, lake:w.lake||'regnaren', createdAt: ts(w.at || (now - 3600000)) };")
from fakefb import login
import importlib, test_weather as _tw  # reuse the weather mock
results = []
def check(name, cond, info=''):
    results.append(bool(cond)); print(('PASS ' if cond else 'FAIL ') + name + ('  -- ' + str(info) if info != '' else ''))
FAR = (59.30, 18.05)
at = int(datetime.datetime(2026, 9, 23, 14, 5).timestamp() * 1000)
cfg = {'waypoints': [{'lat':58.8893,'lon':15.7770,'name':'Calles','uid':'kalle','by':'Calle','type':'gadda','at':at},
                     {'lat':58.8898,'lon':15.7784,'name':'Min','uid':'filip','by':'Filip','type':'gos','at':at}]}
with sync_playwright() as p:
    b = p.chromium.launch(**__import__('fakefb').LAUNCH)
    ctx = b.new_context(viewport={'width':390,'height':844}, has_touch=True, is_mobile=True, geolocation={'latitude':FAR[0],'longitude':FAR[1],'accuracy':8}, permissions=['geolocation'])
    ctx.add_init_script('window.__fakeCfg = ' + json.dumps(cfg) + ';'); ctx.add_init_script(fakefb.FAKE_FIREBASE_JS)
    ctx.route('**/api.open-meteo.com/**', lambda r: r.fulfill(status=200, content_type='application/json', body=json.dumps(_tw.wx_json()), headers={'Access-Control-Allow-Origin': '*'}))
    pg = ctx.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.goto('http://localhost:8899/index.html'); pg.wait_for_timeout(500); login(pg, 'Filip'); pg.wait_for_timeout(1500)
    # sheet dates
    pg.evaluate("document.querySelector('#waypoints .wpPin--other').click()"); pg.wait_for_timeout(400)
    m1 = pg.inner_text('#wpMeta'); pg.click('#wpCancel'); pg.wait_for_timeout(300)
    pg.evaluate("document.querySelector('#waypoints .wpPin:not(.wpPin--other)').click()"); pg.wait_for_timeout(400)
    m2 = pg.inner_text('#wpMeta'); pg.click('#wpCancel'); pg.wait_for_timeout(300)
    check("someone else's spot: 'Sparad av Calle · 23 sep. 14:05 · … bort'", m1.startswith('Sparad av Calle · 23 sep. 14:05') and 'bort' in m1, m1)
    check("your own spot: same info, 'Sparad av dig · 23 sep. 14:05 · … bort'", m2.startswith('Sparad av dig · 23 sep. 14:05') and 'bort' in m2, m2)
    # weather: card replaces the chip, source/time in the header
    chip_top = pg.eval_on_selector('#wxChip', 'e=>e.getBoundingClientRect().top')
    pg.click('#wxChip'); pg.wait_for_timeout(300)
    check('open: chip hidden, card in its place', not pg.is_visible('#wxChip') and abs(pg.eval_on_selector('#wxCard', 'e=>e.getBoundingClientRect().top') - chip_top) < 1)
    check('"Open-Meteo · uppdaterad HH:MM" up in the header', pg.inner_text('#wxSrc').startswith('Open-Meteo · uppdaterad ') and pg.query_selector('.wxFoot') is None, pg.inner_text('#wxSrc'))
    pg.screenshot(path='wx_card2.png')
    pg.click('#wxClose'); pg.wait_for_timeout(200)
    check('✕: card gone, chip back', pg.is_visible('#wxChip') and not pg.is_visible('#wxCard'))
    # demo mode: always on the water
    pg.click('#menuBtn'); pg.click('#menuItemSettings'); pg.wait_for_timeout(200)
    depths = []
    for i in range(4):   # (on / off = a reload into the test mode and back, Inställningar open again)
        with pg.expect_navigation(timeout=8000): pg.click('#demoModeToggle')
        pg.wait_for_selector('#settingsView.show', timeout=5000)
        if pg.is_checked('#demoModeToggle'):
            try: pg.wait_for_function("document.getElementById('depthVal').textContent !== '–'", timeout=3000)
            except Exception: pass
            depths.append(pg.inner_text('#depthVal'))
            with pg.expect_navigation(timeout=8000): pg.click('#demoModeToggle')
            pg.wait_for_selector('#settingsView.show', timeout=5000)
    ok = all(d not in ('–',) and (d == '10+' or float(d.replace(',', '.')) >= 1.4) for d in depths)
    check('Demo Mode always starts on the water (≥1,5 m)', ok and len(depths) >= 4, depths)
    # motion keeps to the water for a while
    with pg.expect_navigation(timeout=8000): pg.click('#demoModeToggle')
    pg.wait_for_selector('#settingsView.show', timeout=5000)
    pg.click('#settingsBackBtn'); pg.wait_for_timeout(200)
    seen = []
    for i in range(45):
        pg.wait_for_timeout(1000); seen.append(pg.inner_text('#depthVal'))
    check('simulated boat stays on the water (45 s)', all(d != '–' for d in seen), seen[-10:])
    check('no page errors', not errs, errs)
    b.close()
print('\n%d/%d passed' % (sum(results), len(results)))
