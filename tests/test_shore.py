# Strandlinje (Inställningar -> Kartan, on by default): the lake's edge as a thin white line on the plain map, like
# Heatmap and Kartanalys draw it; not drawn under them (they have their own).
from playwright.sync_api import sync_playwright
from fakefb import new_page
results = []
def check(name, cond, info=''):
    results.append(bool(cond)); print(('PASS ' if cond else 'FAIL ') + name + ('  -- ' + str(info) if info != '' else ''))

B3 = (58.887269, 15.772629)
WHITE = """() => { var c = document.getElementById('shoreLayer'), d = c.getContext('2d').getImageData(0, 0, c.width, c.height).data, n = 0;
  for (var i = 0; i < d.length; i += 4) if (d[i] > 200 && d[i + 1] > 200 && d[i + 2] > 200 && d[i + 3] > 40) n++; return n; }"""
def on(pg): return pg.evaluate("document.getElementById('shoreLayer').classList.contains('on')")
with sync_playwright() as p:
    b, ctx, pg, errs = new_page(p, geo=B3, cfg={'api': {'heatmap': [], 'competitions': []}})
    pg.wait_for_timeout(3000)
    n = pg.evaluate(WHITE)
    check('on by default: a white line on the plain map', on(pg) and pg.evaluate("document.getElementById('toggleShore').checked") and n > 100, n)
    pg.screenshot(path='shot_shore.png')
    pg.click('#anBtn'); pg.wait_for_timeout(300)
    pg.click('#anCatSeg button[data-cat="map"]'); pg.click('#anPanel button[data-m="depth"]'); pg.wait_for_timeout(800)
    check('Kartanalys on: not drawn (it has its own)', not on(pg))
    pg.click('#anClose'); pg.evaluate("document.querySelector('#anPanel [data-m=\"depth\"]').click()"); pg.wait_for_timeout(500)
    pg.evaluate("document.getElementById('toggleShore').click()"); pg.wait_for_timeout(300)
    check('Inställningar: off -> gone, the summary says so', not on(pg) and 'ingen strandlinje' in pg.inner_text('#setSum-map'), pg.inner_text('#setSum-map'))
    pg.reload(); pg.wait_for_timeout(2500)
    check('...remembered', not on(pg) and not pg.evaluate("document.getElementById('toggleShore').checked"))
    check('no page errors', not errs, errs)
    b.close()
print('%d/%d passed' % (sum(results), len(results)))
