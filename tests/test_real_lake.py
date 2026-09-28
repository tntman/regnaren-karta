# A whole "day on the lake" with REAL (emulated) GPS -- Demo Mode is never touched.
from playwright.sync_api import sync_playwright
from fakefb import new_page
import math
results = []
def check(name, cond, info=''):
    results.append(bool(cond)); print(('PASS ' if cond else 'FAIL ') + name + ('  -- ' + str(info) if info != '' else ''))
HOME = (59.30, 18.05)                    # far away (Stockholm)
LAKE = (58.88951 - 300/111320.0, 15.77759)
def mine(pg): return [x for x in pg.evaluate('window.__posWrites') if x['id'] == 'filip']
with sync_playwright() as p:
    b, ctx, pg, errs = new_page(p, geo=HOME, cfg={'positions': [{'uid':'calle','name':'Calle','lat':LAKE[0]+0.002,'lon':LAKE[1],'ageMin':1}]}, name='Filip')
    pg.wait_for_timeout(3000)
    check('Demo Mode is OFF', not pg.evaluate("document.getElementById('demoModeToggle').checked") and not pg.is_visible('#demoBanner'))
    check('at home: "km från Regnaren" shown, no dot, nothing shared', pg.is_visible('#farAway') and 'km' in pg.inner_text('#farAway')
          and pg.eval_on_selector('#marker', 'e=>getComputedStyle(e).display') == 'none' and not mine(pg), pg.inner_text('#farAway'))
    # arrive at the lake
    ctx.set_geolocation({'latitude': LAKE[0], 'longitude': LAKE[1], 'accuracy': 6}); pg.wait_for_timeout(2500)
    check('at the lake: message gone, GPS arrow shown', not pg.is_visible('#farAway') and pg.eval_on_selector('#marker', 'e=>getComputedStyle(e).display') == 'block')
    w = mine(pg)
    check('at the lake: your position shared at once', len(w) == 1 and abs(w[0]['lat'] - LAKE[0]) < 1e-6, w)
    check('"Lägg till på min position" + GPS button enabled', pg.is_enabled('#addHereBtn') and pg.is_enabled('#locateBtn'))
    check('Calle\'s boat visible', 'Calle' in ' '.join(pg.eval_on_selector_all('.boatName', 'e=>e.map(x=>x.innerText)')))
    # drive north at ~3 kn for 45 s
    lat = LAKE[0]; t0 = len(w)
    for i in range(45):
        lat += 1.54 / 111320.0
        ctx.set_geolocation({'latitude': lat, 'longitude': LAKE[1], 'accuracy': 6}); pg.wait_for_timeout(1000)
    w = mine(pg); ts = [x['t'] for x in w]; gaps = [round((b2 - a) / 1000) for a, b2 in zip(ts, ts[1:])]
    check('driving: shared every ~20 s', len(w) >= 3 and all(19 <= g <= 24 for g in gaps), gaps)
    sp = pg.inner_text('#speedVal')
    check('knot meter ~3 kn', 2.5 <= float(sp.replace(',', '.')) <= 3.5, sp)
    rot = pg.evaluate("document.getElementById('dotArrow').style.transform")
    check('arrow points north', rot.startswith('rotate(0') or rot.startswith('rotate(1') or rot.startswith('rotate(35') or rot.startswith('rotate(-'), rot)
    # anchor for 70 s (GPS keeps sending the same spot)
    n = len(w)
    for i in range(70):
        ctx.set_geolocation({'latitude': lat, 'longitude': LAKE[1], 'accuracy': 6}); pg.wait_for_timeout(1000)
    w2 = mine(pg)[n:]
    check('anchored: shared about once a minute (keeps your boat alive)', 1 <= len(w2) <= 2, len(w2))
    check('anchored: knot meter 0,0', pg.inner_text('#speedVal') == '0,0')
    # another boat moves -> you see it move
    pg.evaluate("window.__addPos({uid:'calle', name:'Calle', lat:%f, lon:%f})" % (LAKE[0] + 0.004, LAKE[1]))
    pg.wait_for_timeout(300)
    check("another boat's new position shows up live", pg.evaluate("document.querySelectorAll('.boatPip').length") >= 1)
    check('you are never shown as a boat yourself', 'Filip' not in ' '.join(pg.eval_on_selector_all('.boatName', 'e=>e.map(x=>x.innerText)')))
    check('no page errors', not errs, errs)
    b.close()
print('\n%d/%d passed' % (sum(results), len(results)))
