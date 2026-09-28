from playwright.sync_api import sync_playwright
from fakefb import new_page
import numpy as np, math
results = []
def check(name, cond, info=''):
    results.append(bool(cond)); print(('PASS ' if cond else 'FAIL ') + name + ('  -- ' + str(info) if info != '' else ''))
_raw = np.load('../lakes/regnaren/raw/depth_raw.npz')   # full-resolution depth + where it lies (zoom, origin)
ZOOM, TILE = int(_raw['zoom']), 256; N = 2 ** ZOOM; OX, OY = [int(v) for v in _raw['origin']]
def full_to_latlon(col, row):
    xg = col + OX; yg = row + OY
    lon = xg / (N * TILE) * 360 - 180; n = math.pi - 2 * math.pi * yg / (N * TILE)
    return math.degrees(math.atan(math.sinh(n))), lon
e = np.load('../lakes/regnaren/raw/depth_raw.npz')['elevation_m'].astype('float32'); o = np.load('../lakes/regnaren/raw/depth_raw.npz')['water']; dep = -e
rows, cols = np.where(o & (np.abs(dep - 6.0) < 0.15))
pt = None
for r, c in zip(rows[::997], cols[::997]):
    win = dep[r-60:r+61, c-60:c+61]; ow = o[r-60:r+61, c-60:c+61]
    if win.shape == (121, 121) and ow.all() and np.abs(win - 6).max() < 0.8: pt = (r, c); break
LA, LO = full_to_latlon(pt[1], pt[0])
def state(pg):
    return pg.evaluate("""() => ({ show: document.getElementById('probe').classList.contains('show'),
        depth: document.getElementById('probeDepth').innerText, dist: document.getElementById('probeDistTxt').innerText,
        noDist: document.getElementById('probe').classList.contains('noDist'), tr: document.getElementById('probe').style.transform })""")
with sync_playwright() as p:
    b, ctx, pg, errs = new_page(p, geo=(LA, LO), cfg={}, name='Filip')
    pg.wait_for_timeout(1800)
    pg.click('#locateBtn'); pg.wait_for_timeout(900)
    d = pg.eval_on_selector('#dot', 'e=>{var r=e.getBoundingClientRect();return [r.left+r.width/2, r.top+r.height/2]}')
    pill = pg.inner_text('#depthVal')
    pg.mouse.click(d[0], d[1]); pg.wait_for_timeout(250)
    check('no probe during the double-tap wait', not state(pg)['show'])
    pg.wait_for_timeout(300)
    s = state(pg)
    check('single tap -> probe with the depth there (same as the knot-meter depth)', s['show'] and s['depth'].replace(' m', '').strip() == pill, (s, pill))
    check('distance to you: "här"', s['dist'] == 'här' and not s['noDist'], s)
    pg.screenshot(path='probe_1.png')
    pg.mouse.click(d[0] + 60, d[1] - 40); pg.wait_for_timeout(600)
    check('next tap removes it', not state(pg)['show'])
    pg.mouse.click(d[0] + 60, d[1] - 40); pg.wait_for_timeout(600)
    s = state(pg)
    check('tap again -> new probe with a distance in metres', s['show'] and s['dist'].endswith(' m') and s['dist'] != 'här', s)
    pg.screenshot(path='probe_2.png')
    # follows the map when panning
    t1 = state(pg)['tr']; pg.mouse.move(200, 600); pg.mouse.down(); pg.mouse.move(150, 560, steps=4); pg.mouse.up(); pg.wait_for_timeout(200)
    check('probe moves with the map (and a drag does not remove it)', state(pg)['show'] and state(pg)['tr'] != t1)
    pg.mouse.click(30, 700); pg.wait_for_timeout(600)   # remove
    # double tap = zoom, no probe
    sc0 = pg.eval_on_selector('#world', 'e=>e.style.transform')
    pg.mouse.click(200, 400); pg.wait_for_timeout(120); pg.mouse.click(200, 400); pg.wait_for_timeout(700)
    check('double tap zooms and drops no probe', not state(pg)['show'] and pg.eval_on_selector('#world', 'e=>e.style.transform') != sc0)
    # long press = spot sheet, no probe
    pg.mouse.move(220, 450); pg.mouse.down(); pg.wait_for_timeout(700); pg.mouse.up(); pg.wait_for_timeout(600)
    check('long press opens the spot sheet, no probe', pg.eval_on_selector('#wpSheet', 'e=>e.classList.contains("show")') and not state(pg)['show'])
    pg.click('#wpCancel'); pg.wait_for_timeout(400)
    # measuring tool: taps are measure points
    pg.click('#measureBtn'); pg.wait_for_timeout(150)
    pg.mouse.click(200, 380); pg.wait_for_timeout(600)
    check('measuring tool: tap = measure point, no probe', not state(pg)['show'] and pg.evaluate("document.querySelectorAll('#measureLayer .mlPt').length") == 1)
    pg.click('#mpClose'); pg.wait_for_timeout(200)
    # tap that closes the menu
    pg.click('#menuBtn'); pg.wait_for_timeout(150); pg.mouse.click(200, 500); pg.wait_for_timeout(600)
    check('a tap that closes the menu drops no probe', not state(pg)['show'] and not pg.is_visible('#menuPanel'))
    # land
    pg.mouse.click(40, 250); pg.wait_for_timeout(600)
    print('   land probe:', state(pg)['depth'])
    check('no page errors', not errs, errs)
    b.close()
print('\n%d/%d passed' % (sum(results), len(results)))
