# Kraschlogg (Inställningar -> Avancerat -> Senaste krasch): a line of what the app was doing is written to
# localStorage while it runs; a run that never closed cleanly (iOS crash = no pagehide) is shown at the next start.
from playwright.sync_api import sync_playwright
from fakefb import new_page
results = []
def check(name, cond, info=''):
    results.append(bool(cond)); print(('PASS ' if cond else 'FAIL ') + name + ('  -- ' + str(info) if info != '' else ''))

LOG = "JSON.parse(localStorage.getItem('ffmap_crashlog_v1') || 'null')"
with sync_playwright() as p:
    b, ctx, pg, errs = new_page(p, geo=(58.887269, 15.772629))
    # a "crash": on the next load, before the app runs, the log says the last run never closed
    ctx.add_init_script("""if (sessionStorage.getItem('fakeCrash')){ sessionStorage.removeItem('fakeCrash');
      localStorage.setItem('ffmap_crashlog_v1', JSON.stringify({ t: Date.now(), lake: 'malaren', up: 61, zoom: 17.2, level: 17,
        tiles: 88, peak: 140, zooms: 33, imgs: 95, canvasMP: 1.5, style: 's1', an: '', hm: false, err: '', clean: false })); }""")
    pg.wait_for_timeout(2500)
    o = pg.evaluate(LOG)
    check('written while running, not clean', o and o['clean'] is False and o['tiles'] >= 0 and o['lake'] == 'regnaren', o)
    check('no crash yet', pg.inner_text('#crashText') == 'Ingen krasch sparad.' and pg.evaluate("document.getElementById('crashCopyBtn').hidden"))
    pg.reload(); pg.wait_for_timeout(1500)
    check('a normal reload (pagehide) is not a crash', pg.inner_text('#crashText') == 'Ingen krasch sparad.', pg.inner_text('#crashText'))
    pg.evaluate("sessionStorage.setItem('fakeCrash', '1')"); pg.reload(); pg.wait_for_timeout(1500)
    t = pg.inner_text('#crashText')
    check('after a crash: shown with zoom and pieces', 'malaren' in t and 'zoom 17.2' in t and 'bitar 88 (max 140)' in t, t)
    check('...with a copy button', not pg.evaluate("document.getElementById('crashCopyBtn').hidden"))
    pg.reload(); pg.wait_for_timeout(1500)
    check('...still there after a normal reload', 'bitar 88' in pg.inner_text('#crashText'))
    check('no page errors', not errs, errs)
    b.close()
print('%d/%d passed' % (sum(results), len(results)))
