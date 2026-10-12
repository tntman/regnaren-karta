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
    pg.wait_for_timeout(800); n = A(pg)['n']
    check('...the bottom as fine as the depth data: one point per cell (Regnaren ~4,9 m: 1200 m = ~243)', 235 <= n <= 250, n)
    pg.screenshot(path='shot_ar.png')
    on = lambda: {b.get_attribute('data-k'): 'on' in (b.get_attribute('class') or '') for b in pg.query_selector_all('#arChips [data-k]')}
    check('the switches: grid, surface, sticks, lead on; depth lines off', on() == {'grid': True, 'surf': True, 'sticks': True, 'lod': True, 'iso': False}, on())
    pg.click('#arChips [data-k=iso]'); pg.click('#arChips [data-k=sticks]'); pg.wait_for_timeout(300)
    c = A(pg)['cfg']
    check('...a tap switches one, remembered', c['iso'] is True and c['sticks'] is False and on()['iso'] and not on()['sticks'] and json.loads(pg.evaluate("localStorage.getItem('ffmap_ar_v1')"))['iso'] is True, c)
    pg.wait_for_timeout(500)
    check('...the lead off: no "under dig" label', (pg.click('#arChips [data-k=lod]'), pg.wait_for_timeout(400), not pg.is_visible('#arPlumb'))[2])
    pg.click('#arChips [data-k=lod]'); pg.click('#arChips [data-k=sticks]')
    g = pg.locator('#arCtl .arGrab').bounding_box(); gx, gy = g['x'] + g['width'] / 2, g['y'] + g['height'] / 2
    pg.mouse.move(gx, gy); pg.mouse.down(); pg.mouse.move(gx, gy + 120, steps=6); pg.mouse.up(); pg.wait_for_timeout(400)
    check('the grip: dragged down = only the grip left (the sliders gone), remembered', pg.evaluate("document.getElementById('arCtl').classList.contains('min')") and not pg.is_visible('#arR') and A(pg)['cfg'].get('min') is True)
    pg.screenshot(path='shot_ar_min.png')
    pg.click('#arCtl .arGrab'); pg.wait_for_timeout(400)
    check('...a tap on it: the sliders back', pg.is_visible('#arR') and not A(pg)['cfg'].get('min'))
    pg.set_viewport_size({'width': 844, 'height': 390}); pg.wait_for_timeout(800)
    check('lying down: the controls in the right corner, not over the ring in the middle', pg.evaluate("(() => { const e = document.elementFromPoint(innerWidth / 2, innerHeight / 2 + 25); return !e.closest('#arCtl'); })()") and A(pg)['depth'].endswith('bort'), A(pg)['depth'])
    pg.set_viewport_size({'width': 390, 'height': 844}); pg.wait_for_timeout(500)
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
