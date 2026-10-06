# Testläge = Demo Mode (js/37-testmode.js, tools/NOTES_TESTLAGE.md): switching reloads into a Firebase project
# of its own (here: the fake starts that project empty / from cfg.testDb), the phone's copies have their own keys,
# no track sync, no Fiskfiskarna / FMI; the admin's card drives a made-up competition, test boats and strikes.
import json
from playwright.sync_api import sync_playwright
import fakefb
from fakefb import new_page
results = []
def check(name, cond, info=''):
    results.append(bool(cond)); print(('PASS ' if cond else 'FAIL ') + name + ('  -- ' + str(info) if info != '' else ''))
ME = (58.88951, 15.77759)
cfg = {
  'waypoints': [{'lat': 58.8898, 'lon': 15.7784, 'name': 'Riktig plats', 'uid': 'kalle', 'by': 'Calle'}],
  'positions': [{'uid': 'kalle', 'name': 'Calle', 'lat': 58.8960, 'lon': 15.7820, 'ageMin': 1}],
  'testDb': {'waypoints': [{'lat': 58.8893, 'lon': 15.7770, 'name': 'Testplats', 'uid': 'pia', 'by': 'Pia'}],
             'positions': [{'uid': 'pia', 'name': 'Pia', 'lat': 58.8930, 'lon': 15.7800, 'ageMin': 0}]},
  'api': {'competitions': [{'competition_id': 'r1', 'competition_name': 'Riktig', 'date': '2026-10-04', 'status': 'active', 'water': 'Regnaren'}], 'live': {'r1': []}}}
def T(pg): return pg.evaluate('__ffTest()')
def settings(pg):
    if not pg.is_visible('#settingsView'): pg.click('#menuBtn'); pg.click('#menuItemSettings'); pg.wait_for_timeout(300)
def toggle_demo(pg):   # (a reload: Inställningar opens again, as after turning the phone -> closed here)
    settings(pg)
    with pg.expect_navigation(timeout=8000): pg.click('#demoModeToggle')
    pg.wait_for_selector('#settingsView.show', timeout=5000); pg.wait_for_timeout(1200)
    pg.click('#settingsBackBtn'); pg.wait_for_timeout(300)
def admin(pg):
    settings(pg); pg.click('#adminOpenBtn'); pg.wait_for_timeout(300)
    if pg.is_visible('#pinInput'): pg.fill('#pinInput', fakefb.TEST_PIN); pg.press('#pinInput', 'Enter')
    pg.wait_for_timeout(500)
def test_doc(pg, k): return pg.evaluate("window.__cfgDoc && window.__cfgDoc.test ? window.__cfgDoc.test[%s] : null" % json.dumps(k))

with sync_playwright() as p:
    b, ctx, pg, errs = new_page(p, geo=ME, cfg=cfg, name='Filip')
    pg.on('dialog', lambda d: d.accept())
    t = T(pg)
    check('real: the real project, the real spot and boat', not t['on'] and pg.evaluate('window.__fbProject') == 'regnaren-b8b6a' and t['wps'] == ['Riktig plats'] and 'kalle' in t['boats'], t)
    # a real track day not uploaded yet (u = 0): the test mode must leave it alone, else it'd never reach the real database
    pg.evaluate("localStorage.setItem('ffmap_trackhist_v1', JSON.stringify({'2026-10-01': {p: '', s: [], n: 3, u: 0}}))")
    ctx.api.hits.clear()
    toggle_demo(pg)
    t = T(pg)
    check('Demo Mode on = a reload into the test project', t['on'] and pg.evaluate('window.__fbProject') == t['project'] != 'regnaren-b8b6a' and pg.is_visible('#demoBanner'), (t['project'], pg.evaluate('window.__fbProject')))
    ups = pg.evaluate("JSON.parse(sessionStorage.getItem('__fbUpdates') || '[]')")
    check('...your real boat went away for the others first (in the real project)', any(x['id'] == 'filip' and x['updatedAtMs'] == 0 and x['found'] and x['project'] == 'regnaren-b8b6a' for x in ups), ups)
    check('test: only the test spot and the test boat (not the real ones)', t['wps'] == ['Testplats'] and 'pia' in t['boats'] and 'kalle' not in t['boats'], t)
    check('...the demo boat moves (motion on)', pg.evaluate("document.getElementById('demoMoveToggle').checked"))
    pg.evaluate("document.dispatchEvent(new Event('visibilitychange'))"); pg.wait_for_timeout(1500)
    check('no Fiskfiskarna, no track sync in the test mode', ctx.api.n('fiskfiskarna') == 0 and not pg.evaluate('window.__trackSets') and pg.evaluate('window.__trackUserSets.length') == 0,
          (ctx.api.hits, pg.evaluate('window.__trackSets')))
    h = json.loads(pg.evaluate("localStorage.getItem('ffmap_trackhist_v1')"))
    check('...the real track day still waits for the real database (u = 0)', h['2026-10-01']['u'] == 0, h)
    check('the test mode has its own copy of the spots', pg.evaluate("localStorage.getItem('lake_regnaren_wp_synced_v1_test')") == '1')
    w = pg.evaluate('window.__posWrites')
    check('the demo position is shared (in the test project)', any(x['id'] == 'filip' for x in w), w[-1:])
    check('the banner warns: a real competition is on (the phone\'s real copy of the catches)', pg.is_visible('#demoBannerWarn'))
    # --- the admin's card ---
    admin(pg)
    check('Admin: the Testläge card shows', pg.is_visible('#adminTestCard'))
    pg.click('#testCompSeg button[data-v="active"]'); pg.wait_for_timeout(600)
    check('Pågår: the competition is live for everyone', (test_doc(pg, 'comp') or {}).get('status') == 'active', test_doc(pg, 'comp'))
    pg.select_option('#testWho', 'me'); pg.select_option('#testSp', 'gadda'); pg.fill('#testCm', '87'); pg.check('#testImg')
    pg.click('#testAddCatch'); pg.wait_for_timeout(1200)
    c = pg.evaluate("__ffCatches()")
    check('a catch is in: live, 87 cm', '87' in json.dumps(c) and len(test_doc(pg, 'catches')) == 1, json.dumps(c)[:300])
    pg.click('#adminBackBtn'); pg.click('#settingsBackBtn'); pg.wait_for_timeout(300)
    pg.click('#msgBtn'); pg.wait_for_timeout(300)
    check('"Senaste fisk": my catch is first in the quick messages', pg.is_visible('#msgFishBtn') and 'Gädda 87 🐟' in pg.inner_text('#msgFishBtn'))
    pg.click('#msgFishBtn'); pg.wait_for_timeout(300)
    w = pg.evaluate('window.__posWrites')
    check('...sent with the picture (the test mode\'s own)', w and w[-1]['msgSp'] == 'gadda' and (w[-1]['msgImg'] or '').endswith('icon-512.png'), w[-1:])
    admin(pg)
    pg.click('#testVoidCatch'); pg.wait_for_timeout(1200)
    check('Annullera senaste: gone from the live catches', '87' not in json.dumps(pg.evaluate("__ffCatches()")) and len(test_doc(pg, 'voids')) == 1, pg.evaluate("__ffCatches()"))
    # test boats
    pg.click('#testBotSeg button[data-v="3"]'); pg.wait_for_timeout(1500)
    bots0 = T(pg)['bots']; pg.wait_for_timeout(2000); bots1 = T(pg)['bots']
    w = pg.evaluate('window.__posWrites')
    check('3 test boats: positions written, they move', len(bots0) == 3 and set(x['id'] for x in w if x['id'].startswith('bot_')) == {'bot_1', 'bot_2', 'bot_3'} and bots0[0]['lat'] != bots1[0]['lat'], bots1)
    check('...and can catch (in the "who" list)', pg.evaluate("Array.from(document.querySelectorAll('#testWho option')).map(o => o.value).filter(v => v.indexOf('bot_') === 0).length") == 3)
    pg.select_option('#testWho', 'bot_2'); pg.fill('#testCm', '41'); pg.select_option('#testSp', 'abborre'); pg.click('#testAddCatch'); pg.wait_for_timeout(800)
    w = pg.evaluate('window.__posWrites')
    check('a test boat\'s catch: it sends "Senaste fisk"', any(x['id'] == 'bot_2' and x['msg'] == 'Abborre 41 🐟' for x in w), [x for x in w if x['id'] == 'bot_2'][-1:])
    pg.click('#testAutoSeg button[data-v="1"]'); pg.wait_for_timeout(200)
    check('automatic catches: on', T(pg)['auto'])
    pg.click('#testAutoSeg button[data-v="0"]'); pg.wait_for_timeout(200)
    # lightning
    pg.evaluate("window.__ltAlarms = 0")
    pg.click('#testStrikes button[data-km="2"]'); pg.wait_for_timeout(800)
    check('Blixt 2 km: a strike near you -> the alarm', pg.evaluate("window.__ltAlarms || 0") >= 1 and len(test_doc(pg, 'lt')) == 1, pg.evaluate("window.__ltAlarms"))
    pg.click('#testLtClear'); pg.wait_for_timeout(500)
    check('Ta bort blixtar: none left', len(test_doc(pg, 'lt')) == 0)
    pg.click('#testReset'); pg.wait_for_timeout(800)
    w = pg.evaluate('window.__posWrites'); t = T(pg)
    check('Rensa: no test spots, test boats gone, no competition', t['wps'] == [] and not t['bots'] and test_doc(pg, 'comp') is None
          and any(x['id'] == 'bot_1' and x['updatedAtMs'] == 0 for x in w) and any(x['id'] == 'pia' and x['updatedAtMs'] == 0 for x in w), t)
    check('no Fiskfiskarna the whole time in the test mode', ctx.api.n('fiskfiskarna') == 0)
    # --- off again: back to the real project ---
    pg.click('#adminBackBtn'); pg.wait_for_timeout(200)
    with pg.expect_navigation(timeout=8000): pg.click('#demoModeToggle')
    pg.wait_for_timeout(1500)
    t = T(pg)
    check('Demo Mode off = back to the real project and its spot', not t['on'] and pg.evaluate('window.__fbProject') == 'regnaren-b8b6a' and t['wps'] == ['Riktig plats'] and not pg.is_visible('#demoBanner'), t)
    check('no page errors', not errs, errs)
    b.close()

    # not the admin: no card; 15 min gone -> the real project at start
    b, ctx, pg, errs = new_page(p, geo=ME, cfg=cfg, name='Calle')
    toggle_demo(pg)
    settings(pg)
    check('Calle in Demo Mode: no admin, no Testläge card', pg.evaluate('__ffTest().on') and not pg.is_visible('#adminRow') and not pg.is_visible('#adminTestCard'))
    pg.evaluate("localStorage.setItem('regnaren_demo_since_v1', String(Date.now() - 16 * 60000))")
    pg.reload(); pg.wait_for_timeout(1500)
    t = T(pg)
    check('after 15 min: the real project again, Demo Mode off', not t['on'] and pg.evaluate('window.__fbProject') == 'regnaren-b8b6a' and not pg.evaluate("document.getElementById('demoModeToggle').checked"), t)
    check('no page errors (Calle)', not errs, errs)
    b.close()

print('\n%d/%d passed' % (sum(results), len(results)))
