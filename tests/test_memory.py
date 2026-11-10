# Memory (tools/PLAN_MINNE.md -- Mälaren crashed the iPhone): the screen layers hold a full canvas only while
# they're on (12 MB each at 3x), the soft ones at most 2x; Kartanalys keeps Liknande's grids for two radii at most
# and lets go of them when it's switched off; a lake under the budget works on its own depth grid (Mälaren: test_lakes)
from playwright.sync_api import sync_playwright
import fakefb, json
from fakefb import new_page
results = []
def check(name, cond, info=''):
    results.append(bool(cond)); print(('PASS ' if cond else 'FAIL ') + name + ('  -- ' + str(info) if info != '' else ''))
_orig = fakefb._Browser.new_context
def _ctx3(self, *a, **kw):               # (an iPhone's 3x screen)
    kw['device_scale_factor'] = 3
    return _orig(self, *a, **kw)
fakefb._Browser.new_context = _ctx3
B3 = (58.887269, 15.772629)
cfg = {'waypoints': [{'lat': 58.88651, 'lon': 15.777774, 'name': 'Djupa hålet', 'uid': 'filip', 'by': 'Filip', 'type': 'abborre'}]}
SIZE = "(id) => { var c = document.getElementById(id); return c.width + 'x' + c.height; }"
def an(pg): return pg.evaluate('window.__ffAnalysis()')
with sync_playwright() as p:
    b, ctx, pg, errs = new_page(p, geo=B3, cfg=cfg)
    pg.wait_for_timeout(2500)
    W, H = pg.evaluate("[document.getElementById('stage').clientWidth, document.getElementById('stage').clientHeight]")
    off = {k: pg.evaluate(SIZE, k) for k in ('windLayer', 'ltLayer', 'hmLayer', 'hmSat', 'anLayer', 'anSat', 'anGlow', 'fogLayer')}
    check('layers that are off: 1x1 (no 12 MB canvas each)', all(v == '1x1' for v in off.values()), off)
    check('Strandlinje (on): the screen at 2x, not 3x', pg.evaluate(SIZE, 'shoreLayer') == '%dx%d' % (W * 2, H * 2), pg.evaluate(SIZE, 'shoreLayer'))
    pg.click('#anBtn'); pg.wait_for_timeout(300)
    pg.click('#anCatSeg button[data-cat="similar"]'); pg.wait_for_timeout(2500)
    a = an(pg)
    check('Liknande on: Kartanalys at 2x, the shore layer let go (hidden under it)', a['ready'] and pg.evaluate(SIZE, 'anLayer') == '%dx%d' % (W * 2, H * 2) and pg.evaluate(SIZE, 'shoreLayer') == '1x1', (a, pg.evaluate(SIZE, 'anLayer')))
    check('Regnaren (under the budget): Kartanalys on its own depth grid', a['grid'] == '%dx%d' % tuple(json.load(open('../lakes/regnaren/lake.json', encoding='utf-8'))['depth'][k] for k in ('w', 'h')), a['grid'])
    for r in (25, 50, 100, 0):
        pg.click('#anSimR button[data-r="%d"]' % r); pg.wait_for_timeout(1200)
    a = an(pg)
    check('four radii tried: grids kept for two at most (25 m + the last)', a['ready'] and 1 <= a['sim'] <= 2, a['sim'])
    pg.click('#anClear'); pg.wait_for_timeout(600)
    a = an(pg)
    check('Kartanalys off: its grids let go, its canvases 1x1, the shore back', a['sim'] == 0 and pg.evaluate(SIZE, 'anLayer') == '1x1' and pg.evaluate(SIZE, 'shoreLayer') != '1x1', (a['sim'], pg.evaluate(SIZE, 'anLayer')))
    # a drag of the map: the spots move as one layer (not pin by pin), and no new canvas is made per frame
    PIN = "() => { var e = document.querySelector('#waypoints .wpPin'), r = e.getBoundingClientRect(); return [r.left, r.top, e.style.left, document.getElementById('waypoints').style.transform]; }"
    pg.evaluate("window.__cv = 0; var oc = document.createElement; document.createElement = function(t){ if (/canvas/i.test(t)) window.__cv++; return oc.apply(document, arguments); }")
    p0 = pg.evaluate(PIN); x0 = 60 if p0[0] > 195 else 330
    pg.mouse.move(x0, 600); pg.mouse.down(); pg.mouse.move(x0 + 40, 630, steps=5); pg.wait_for_timeout(250)
    p1 = pg.evaluate(PIN)
    check('dragging: the spot follows the map (40 x 30)...', abs(p1[0] - p0[0] - 40) < 1 and abs(p1[1] - p0[1] - 30) < 1, (p0, p1))
    check('...as a layer: the pin itself is not touched', p1[2] == p0[2] and 'translate(40px' in p1[3], p1)
    pg.evaluate("window.__fireWp()"); pg.wait_for_timeout(100); p2 = pg.evaluate(PIN)
    check('new spots mid-drag: placed again, still in the right place', p2[3] == '' and p2[2] != p0[2] and abs(p2[0] - p1[0]) < 1 and abs(p2[1] - p1[1]) < 1, p2)
    pg.mouse.move(x0 + 60, 640, steps=3); pg.wait_for_timeout(150); pg.mouse.up(); pg.wait_for_timeout(400)
    p3 = pg.evaluate(PIN)
    check('finger up: every pin placed again, the layer back', p3[3] == '' and abs(p3[0] - p0[0] - 60) < 1 and abs(p3[1] - p0[1] - 40) < 1, p3)
    check('no canvas made during the drag (the shore line reuses its own)', pg.evaluate('window.__cv') == 0, pg.evaluate('window.__cv'))
    check('no page errors', not errs, errs)
    b.close()
print('%d/%d passed' % (sum(results), len(results)))
