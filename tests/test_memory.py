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
    check('no page errors', not errs, errs)
    b.close()
print('%d/%d passed' % (sum(results), len(results)))
