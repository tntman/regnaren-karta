# Kartanalys' edges stay smooth while the map is panned zoomed out (like the lee's): the areas are
# drawn from a smooth field (anField) and a line is never thinner than the spacing of the drawn
# points (edgeW). Measured: drag 23 px (finger down = every 2nd px drawn), compare the picture with
# the one before moved 23 px -- a smooth drawing just moves; a beaded one changes (was ~0,5, now ~0,2).
from playwright.sync_api import sync_playwright
import fakefb
from fakefb import new_page
results = []
def check(name, cond, info=''):
    results.append(bool(cond)); print(('PASS ' if cond else 'FAIL ') + name + ('  -- ' + str(info) if info != '' else ''))
GRAB = """(id) => { var c = document.getElementById(id), d = c.getContext('2d').getImageData(0, 0, c.width, c.height).data, o = new Uint8Array(c.width * c.height);
  for (var i = 0; i < o.length; i++) o[i] = d[i * 4 + 3]; window.__grab = window.__grab || []; window.__grab.push({ w: c.width, h: c.height, a: o }); }"""
DIFF = """(dx) => { var A = window.__grab[0], B = window.__grab[1], w = A.w, h = A.h, tot = 0, n = 0;
  for (var y = 160; y < h - 200; y += 2) for (var x = 20; x < w - 20 - dx; x += 2){
    var va = A.a[y * w + x], vb = B.a[y * w + x + dx]; if (va > 20 || vb > 20){ tot += Math.abs(va - vb); n++; } }
  window.__grab = []; return tot / Math.max(1, n); }"""
with sync_playwright() as p:
    b, ctx, pg, errs = new_page(p, geo=(58.88951, 15.77759), cfg={}, name='Filip')
    pg.wait_for_timeout(1500)
    pg.click('#anBtn'); pg.wait_for_timeout(300); pg.click('#anPanel button[data-m="steep"]'); pg.wait_for_timeout(1500)
    pg.click('#anClose'); pg.wait_for_timeout(600)
    pg.mouse.move(150, 450); pg.mouse.down(); pg.mouse.move(160, 450, steps=3); pg.wait_for_timeout(400)
    pg.evaluate(GRAB, 'anLayer')
    pg.mouse.move(183, 450, steps=4); pg.wait_for_timeout(400)
    pg.evaluate(GRAB, 'anLayer')
    pg.mouse.up(); pg.wait_for_timeout(600)
    d = pg.evaluate(DIFF, 23)
    check('zoomed out, panning: Kartanalys edges move along smoothly (no beading/flicker)', d < 0.3, round(d, 3))
    a = pg.evaluate('window.__ffAnalysis()')
    check('...and the areas are still there (Branta kanter found)', a['ready'] and a['n'] > 100, a)
    lit = pg.evaluate("""() => { var c = document.getElementById('anLayer'), d = c.getContext('2d').getImageData(0, 0, c.width, c.height).data, n = 0;
                         for (var i = 0; i < d.length; i += 4) if (d[i] > 150 && d[i + 1] > 150 && d[i + 2] > 150 && d[i + 3] > 90) n++; return n; }""")
    check('standing still again: the white edges and the shore are drawn', lit > 150, lit)
    check('no page errors', not errs, errs)
    b.close()
print('\n%d/%d passed' % (sum(results), len(results)))
