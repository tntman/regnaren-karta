# Under ytan (js/72-ar.js): last in the map-style list (hold the map button) -> full screen, the bottom in 3D (three.js)
# around you, the camera's picture behind (refused here -> without). The depth straight ahead follows the phone; the
# settings are remembered; ✕ closes all of it. Demo Mode: a new spot's sheet has "Båten hit" -> the demo boat goes there.
import json
from playwright.sync_api import sync_playwright
from fakefb import new_page
results = []
def check(name, cond, info=''):
    results.append(bool(cond)); print(('PASS ' if cond else 'FAIL ') + name + ('  -- ' + str(info) if info != '' else ''))
B3 = (58.887269, 15.772629); B1 = (58.887421, 15.775569)
def A(pg, o=None): return pg.evaluate('window.__ffAr(%s)' % (json.dumps(o) if o else ''))
def hold_map_btn(pg):
    bb = pg.locator('#mapTypeBtn').bounding_box(); pg.mouse.move(bb['x'] + 20, bb['y'] + 20); pg.mouse.down(); pg.wait_for_timeout(700); pg.mouse.up(); pg.wait_for_timeout(300)

with sync_playwright() as p:
    b, ctx, pg, errs = new_page(p, geo=B3, name='Filip')
    pg.wait_for_timeout(2500)
    hold_map_btn(pg)
    check('the map-style list has "Under ytan" last', pg.evaluate("[...document.querySelectorAll('#mapTypePop .styleOpt')].pop().textContent").startswith('Under ytan'))
    A(pg, {'alpha': 120, 'beta': 78, 'gamma': 0})
    pg.click('#mapTypePop .arOpt'); pg.wait_for_timeout(2500)
    s = A(pg)
    check('it opens full screen: the bottom built, from your GPS', s['open'] and s['ready'] and s['gps'] and pg.is_visible('#arView') and abs(s['at']['lat'] - B3[0]) < 1e-5, s)
    check('...nothing of the map on top of it', pg.evaluate("(() => { const e = document.elementFromPoint(195, 300); return !!e.closest('#arView'); })()"))
    check('...the camera refused: without it, and it says so', not s['cam'] and 'Kameran' in s['msg'], s)
    d1 = s['depth']; A(pg, {'alpha': 300, 'beta': 70, 'gamma': 0}); pg.wait_for_timeout(800); d2 = A(pg)['depth']
    check('the depth straight ahead, and it changes when the phone turns', d1.endswith('bort') and ' m' in d1 and d1 != d2, (d1, d2))
    pg.fill('#arR', '600'); pg.dispatch_event('#arR', 'input'); pg.wait_for_timeout(300)
    check('Avstånd: shown and remembered', pg.inner_text('#arRVal') == '600 m' and json.loads(pg.evaluate("localStorage.getItem('ffmap_ar_v1')"))['r'] == 600)
    pg.screenshot(path='shot_ar.png')
    pg.click('#arClose'); pg.wait_for_timeout(300)
    check('✕ closes it all', not A(pg)['open'] and not pg.is_visible('#arView'))
    check('no page errors', not errs, errs)
    b.close()

    # Demo Mode: put the boat where you want, then look
    b, ctx, pg, errs = new_page(p, geo=B3, name='Filip')
    pg.evaluate("localStorage.setItem('regnaren_demo_mode_v1', '1'); localStorage.setItem('regnaren_demo_since_v1', String(Date.now())); localStorage.setItem('lake_regnaren_demo_lat_v1', '%f'); localStorage.setItem('lake_regnaren_demo_lon_v1', '%f'); localStorage.setItem('regnaren_demo_move_v1', '1')" % B3); pg.reload(); pg.wait_for_timeout(2500)
    demo = pg.evaluate('window.__ffTest ? __ffTest().on : null')
    s = pg.evaluate('window.__ffGeo.screenOf(%f, %f)' % B1)
    pg.mouse.move(s[0], s[1]); pg.mouse.down(); pg.wait_for_timeout(700); pg.mouse.up(); pg.wait_for_timeout(600)
    check('Demo Mode: a new spot has "Båten hit"', demo and pg.is_visible('#wpBoat'), demo)
    pg.click('#wpBoat'); pg.wait_for_timeout(800)
    hold_map_btn(pg); pg.click('#mapTypePop .arOpt'); pg.wait_for_timeout(2500)
    s = A(pg)
    check('...the boat went there (no spot made, the motion off) and Under ytan looks from it',
          s['gps'] and abs(s['at']['lat'] - B1[0]) < 2e-4 and abs(s['at']['lon'] - B1[1]) < 2e-4 and not pg.is_visible('#wpSheet.show') and not pg.evaluate("document.getElementById('demoMoveToggle').checked"), s)
    check('no page errors', not errs, errs)
    b.close()

    b, ctx, pg, errs = new_page(p, geo=B3, name='Filip')
    pg.wait_for_timeout(2500)
    s = pg.evaluate('window.__ffGeo.screenOf(%f, %f)' % B1)
    pg.mouse.move(s[0], s[1]); pg.mouse.down(); pg.wait_for_timeout(700); pg.mouse.up(); pg.wait_for_timeout(600)
    check('not in Demo Mode: no "Båten hit"', pg.is_visible('#wpSheet') and not pg.is_visible('#wpBoat'))
    b.close()
print('\n%d/%d passed' % (sum(results), len(results)))
