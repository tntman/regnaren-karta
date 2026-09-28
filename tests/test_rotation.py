from playwright.sync_api import sync_playwright
import fakefb, json
JS = fakefb.FAKE_FIREBASE_JS.replace(
    "wpDocs['w'+i] = { lat:w.lat, lon:w.lon, name:w.name, uid:w.uid,",
    "wpDocs['w'+i] = { lat:w.lat, lon:w.lon, name:w.name, type:w.type, uid:w.uid,")
# like real Firestore with persistence: the phone's own (pending) writes survive a reload
JS = JS.replace("  var wpListeners = [], posListeners = [];", """  try { var saved = JSON.parse(sessionStorage.getItem('__stubWp') || 'null');
    if (saved){ wpDocs = {}; Object.keys(saved).forEach(function(k){ var d = saved[k]; d.createdAt = d.createdAtMs ? ts(d.createdAtMs) : null; delete d.createdAtMs; wpDocs[k] = d; }); } } catch(e){}
  function persistWp(){ var o = {}; Object.keys(wpDocs).forEach(function(k){ var d = Object.assign({}, wpDocs[k]); d.createdAtMs = d.createdAt && d.createdAt.toMillis ? d.createdAt.toMillis() : null; delete d.createdAt; o[k] = d; });
    try { sessionStorage.setItem('__stubWp', JSON.stringify(o)); } catch(e){} }
  var wpListeners = [], posListeners = [];""")
JS = JS.replace("function fireWp(){ wpListeners.forEach", "function fireWp(){ persistWp(); wpListeners.forEach")
fakefb.FAKE_FIREBASE_JS = JS
from fakefb import new_page, login

results = []
def check(name, cond, info=''):
    results.append(bool(cond))
    print(('PASS ' if cond else 'FAIL ') + name + ('  -- ' + str(info) if info != '' else ''))

ME = (58.88951, 15.77759)
cfg = {'waypoints': [dict(lat=58.8898 + i*0.0004, lon=15.7784 + (i%5)*0.0006, name='Plats %d' % i, uid='kalle', by='Calle',
                         type=['mark','abborre','gadda','gos'][i%4]) for i in range(24)]
                    + [{'lat':58.8893,'lon':15.7770,'name':'Min grund','uid':'filip','by':'Filip','type':'gos'}]}

def rotate(pg, w, h):
    pg.set_viewport_size({'width': w, 'height': h})
    pg.evaluate("window.dispatchEvent(new Event('orientationchange')); if (screen.orientation) screen.orientation.dispatchEvent(new Event('change'));")
    pg.wait_for_load_state('load')
    pg.wait_for_timeout(1500)
    pg.wait_for_timeout(1700)   # (reload cooldown is 3 s)

def reloads(pg): return pg.evaluate("performance.getEntriesByType('navigation')[0].type")

with sync_playwright() as p:
    b, ctx, pg, errs = new_page(p, geo=ME, cfg=cfg, name='Filip')
    ctx.add_init_script("Object.defineProperty(navigator, 'standalone', { value: true, configurable: true });")
    pg.reload(); pg.wait_for_timeout(1200)
    check('standalone flag set (rotation reloads)', pg.evaluate('navigator.standalone') is True)
    reload_count = pg.evaluate("window.__rc = 1")

    # ---- change everything away from its default ----
    pg.click('#toggleOthers .. >> xpath=..') if False else None
    pg.evaluate("document.getElementById('toggleBoats').click()")
    pg.click('#visMoreBtn'); pg.wait_for_timeout(150)
    pg.click('#visTypes label:has-text("Abborre") .toggle')
    pg.click('#othersOpacitySeg button[data-op="0.5"]')
    pg.click('#menuBtn'); pg.click('#menuItemSettings'); pg.wait_for_timeout(200)
    pg.click('#wpSizeSeg button[data-size="1"]')
    pg.click('#demoModeToggle'); pg.wait_for_timeout(2500)
    pg.click('#adminOpenBtn'); pg.wait_for_timeout(200); pg.fill('#pinInput', fakefb.TEST_PIN); pg.press('#pinInput', 'Enter'); pg.wait_for_timeout(300)
    pg.click('#adminBackBtn'); pg.wait_for_timeout(200)
    pg.fill('#cruiseInput', '3,5')   # typed, NOT committed (still focused)
    pg.evaluate("document.getElementById('settingsBody').scrollTop = 180")
    before = pg.evaluate("""() => ({
      boats: document.getElementById('toggleBoats').checked, namesDisabled: document.getElementById('visRowNames').classList.contains('disabled'),
      types: Array.from(document.querySelectorAll('#visTypes input')).map(e => e.checked),
      op: document.querySelector('#othersOpacitySeg .active').textContent,
      size: document.querySelector('#wpSizeSeg .active').textContent,
      demo: document.getElementById('demoModeToggle').checked, move: document.getElementById('demoMoveToggle').checked,
      demoLat: document.getElementById('demoLatInput').value,
      scroll: document.getElementById('settingsBody').scrollTop,
      speed: document.getElementById('speedVal').textContent })""")
    print('   before:', before)
    wb = pg.evaluate('window.__posWrites'); last_w = max([x['t'] for x in wb] or [0])

    # ---- rotate #1 (in Settings) ----
    rotate(pg, 844, 390)
    check('page really reloaded', pg.evaluate('window.__rc') is None)
    after = pg.evaluate("""() => ({
      boats: document.getElementById('toggleBoats').checked, namesDisabled: document.getElementById('visRowNames').classList.contains('disabled'),
      types: Array.from(document.querySelectorAll('#visTypes input')).map(e => e.checked),
      op: document.querySelector('#othersOpacitySeg .active').textContent,
      size: document.querySelector('#wpSizeSeg .active').textContent,
      demo: document.getElementById('demoModeToggle').checked, move: document.getElementById('demoMoveToggle').checked,
      demoLat: document.getElementById('demoLatInput').value,
      scroll: document.getElementById('settingsBody').scrollTop,
      speed: document.getElementById('speedVal').textContent })""")
    print('   after: ', after)
    check('Båtar off + Namn disabled kept', after['boats'] == before['boats'] == False and after['namesDisabled'])
    check('type filter kept', after['types'] == before['types'] == [True, False, True, True, True, True], after['types'])
    check('opacity 50 % kept', after['op'] == '50 %')
    check('filter still open', pg.is_visible('#visMore'))
    check('pin size Stor kept', after['size'] == before['size'] == 'Stor', after['size'])
    check('Demo Mode + motion kept', after['demo'] and after['move'])
    check('half-typed cruise 3,5 was saved', pg.input_value('#cruiseInput') == '3,5' and pg.evaluate("localStorage.getItem('ffmap_cruise_kn_v1')") == '3.5', pg.input_value('#cruiseInput'))
    check('Settings still open, same scroll', pg.eval_on_selector('#settingsView', 'e=>e.classList.contains("show")') and abs(after['scroll'] - 180) < 2, after['scroll'])
    check('knot meter kept its value (not reset to 0,0)', after['speed'] != '0,0', after['speed'])
    try:
        dlat = abs(float(after['demoLat'].replace(',', '.')) - float(before['demoLat'].replace(',', '.'))) * 111320
    except Exception: dlat = 1e9
    check('demo boat continues from where it was (< 60 m)', dlat < 60, '%.0f m' % dlat)
    wa = pg.evaluate('window.__posWrites')
    check('no extra position write because of the rotation (keeps the 8 s rhythm)', last_w and all(x['t'] - last_w >= 7900 for x in wa), [x['t'] - last_w for x in wa])
    check('admin still unlocked', pg.evaluate("localStorage.getItem('ffmap_admin_unlock_v1')") is not None)
    pg.screenshot(path='shot_rot_settings_land.png')

    # ---- rotate #2 with the admin page open ----
    pg.click('#adminOpenBtn'); pg.wait_for_timeout(300)
    rotate(pg, 390, 844)
    check('admin page still open after rotation', pg.eval_on_selector('#adminView', 'e=>e.classList.contains("show")'))
    pg.click('#adminBackBtn'); pg.click('#settingsBackBtn'); pg.wait_for_timeout(200)
    pg.click('#demoModeToggle') if False else None

    # ---- log scrolled ----
    pg.click('#menuBtn'); pg.click('#menuItemLog'); pg.wait_for_timeout(300)
    pg.evaluate("document.getElementById('logList').scrollTop = 400")
    sc = pg.evaluate("document.getElementById('logList').scrollTop")
    rotate(pg, 844, 390)
    check('log still open with same scroll', pg.eval_on_selector('#logView', 'e=>e.classList.contains("show")')
          and abs(pg.evaluate("document.getElementById('logList').scrollTop") - sc) < 2, (sc, pg.evaluate("document.getElementById('logList').scrollTop")))
    pg.click('#logBackBtn'); pg.wait_for_timeout(200)

    # ---- measurement ----
    pg.click('#measureBtn'); pg.mouse.click(200, 200); pg.mouse.click(300, 250); pg.wait_for_timeout(150)
    m1 = pg.inner_text('#mpMain')
    rotate(pg, 390, 844)
    check('measurement kept', pg.is_visible('#measurePanel') and pg.evaluate("document.querySelectorAll('#measureLayer .mlPt').length") == 2, pg.inner_text('#mpMain') + ' / ' + m1)
    pg.click('#mpClose'); pg.wait_for_timeout(150)

    # ---- new spot sheet: type + typed name ----
    pg.click('#addHereBtn'); pg.wait_for_timeout(900)
    pg.click('#wpTypeSeg button[data-type="gos"]'); pg.fill('#wpName', 'Nya grundet'); pg.wait_for_timeout(100)
    rotate(pg, 844, 390)
    ok = pg.eval_on_selector('#wpSheet', 'e=>e.classList.contains("show")')
    check('spot sheet reopened after rotation', ok)
    check('...with typed name and chosen type', ok and pg.input_value('#wpName') == 'Nya grundet' and pg.inner_text('#wpTypeSeg .active') == 'Gös',
          (pg.input_value('#wpName'), pg.inner_text('#wpTypeSeg .active') if ok else ''))
    n0 = pg.evaluate("document.querySelectorAll('#waypoints .wpPin').length")
    pg.click('#wpCancel'); pg.wait_for_timeout(300)
    check('"Avbryt" still removes the new spot', pg.evaluate("document.querySelectorAll('#waypoints .wpPin').length") == n0 - 1)

    # ---- name modal ----
    pg.click('#menuBtn'); pg.click('#menuItemSettings'); pg.wait_for_timeout(200)
    pg.click('#logoutBtn'); pg.wait_for_timeout(300)
    pg.click('.nameChip--other'); pg.fill('#nameInput', 'Kalle Anka')
    rotate(pg, 390, 844)
    check('name picker kept "Annat namn" + typed text', pg.eval_on_selector('#nameModal', 'e=>e.classList.contains("show")') and pg.input_value('#nameInput') == 'Kalle Anka', pg.input_value('#nameInput'))
    pg.click('#nameSave'); pg.wait_for_timeout(500)
    check('logged in as the typed name', 'Kalle Anka' in pg.inner_text('#headerUser'))
    check('no page errors', not errs, errs)
    b.close()
print('\n%d/%d passed' % (sum(results), len(results)))
