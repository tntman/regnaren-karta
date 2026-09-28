from playwright.sync_api import sync_playwright
from fakefb import new_page
import numpy as np, math
results = []
def check(name, cond, info=''):
    results.append(bool(cond)); print(('PASS ' if cond else 'FAIL ') + name + ('  -- ' + str(info) if info != '' else ''))

# ---- geo helpers (same projection as the app) ----
ZOOM, TILE = 16, 256; N = 2 ** ZOOM
XT, YT, CX0, CY0 = 35618, 19409, 1853, 4026
def full_to_latlon(col, row):
    xg = col + CX0 + XT * TILE; yg = row + CY0 + YT * TILE
    lon = xg / (N * TILE) * 360 - 180
    n = math.pi - 2 * math.pi * yg / (N * TILE)
    lat = math.degrees(math.atan(math.sinh(n)))
    return lat, lon
e = np.load('../data/raw/depth_raw.npz')['elevation_m'].astype('float32'); o = np.load('../data/raw/depth_raw.npz')['water']
dep = -e
def pick(target):
    # a water point well inside the lake whose surroundings (±40 px) are all close to target depth
    rows, cols = np.where(o & (np.abs(dep - target) < 0.15))
    for r, c in zip(rows[::211], cols[::211]):
        win = dep[r-40:r+41, c-40:c+41]; ow = o[r-40:r+41, c-40:c+41]
        if win.shape == (81, 81) and ow.all() and np.abs(win - target).max() < 0.6:
            return r, c
    return None
deep = pick(8.0); shallow = pick(2.0)
print('points', deep, shallow)

with sync_playwright() as p:
    la, lo = full_to_latlon(deep[1], deep[0])
    b, ctx, pg, errs = new_page(p, geo=(la, lo), cfg={'waypoints':[{'lat':la,'lon':lo,'name':'Djupet','uid':'filip','by':'Filip','type':'gos'}]}, name='Filip')
    pg.wait_for_timeout(1800)
    # ---- filter menu ----
    check('filter menu closed at start: only the Filter button', not pg.is_visible('#visMore') and not pg.is_visible('#toggleMine'))
    pg.click('#visMoreBtn'); pg.wait_for_timeout(200)
    check('open: Mina/Andras/Båtar/Namn/Djup/Spår + types', all(pg.is_visible('label:has(#%s)' % i) for i in ['toggleMine','toggleOthers','toggleBoats','toggleNames','toggleDepth','toggleTrack']))
    pg.screenshot(path='feat_filter_open.png')
    pg.click('label:has(#toggleBoats) .toggle'); pg.click('#visMoreBtn'); pg.wait_for_timeout(200)
    check('Båtar off -> dot on the closed Filter button', pg.is_visible('.visMoreDot'))
    pg.click('#visMoreBtn'); pg.click('label:has(#toggleBoats) .toggle'); pg.click('#visMoreBtn'); pg.wait_for_timeout(150)
    # ---- depth ----
    dv = pg.inner_text('#depthVal')
    check('depth under you ~8 m at a deep spot', abs(float(dv.replace(',', '.')) - 8.0) < 0.5, dv)
    pg.screenshot(path='feat_depth.png')
    pg.evaluate("document.querySelector('#waypoints .wpPin').click()"); pg.wait_for_timeout(400)
    meta = pg.inner_text('#wpMeta')
    check('spot sheet shows the depth there', 'Djup 8' in meta or 'Djup 7,9' in meta or 'Djup 7,8' in meta, meta)
    pg.click('#wpCancel'); pg.wait_for_timeout(300)
    la2, lo2 = full_to_latlon(shallow[1], shallow[0])
    ctx.set_geolocation({'latitude': la2, 'longitude': lo2, 'accuracy': 5}); pg.wait_for_timeout(1800)
    dv = pg.inner_text('#depthVal')
    check('...and ~2 m at a shallow spot', abs(float(dv.replace(',', '.')) - 2.0) < 0.5, dv)
    pg.click('#visMoreBtn'); pg.click('label:has(#toggleDepth) .toggle'); pg.wait_for_timeout(200)
    check('Djup off -> depth hidden, knots still shown', not pg.is_visible('#depthVal') and pg.is_visible('#speedVal'))
    pg.click('label:has(#toggleDepth) .toggle'); pg.click('#visMoreBtn'); pg.wait_for_timeout(200)
    # ---- track ----
    lat, lon = la2, lo2
    for i in range(14):
        lat += 10 / 111320.0; ctx.set_geolocation({'latitude': lat, 'longitude': lon, 'accuracy': 5}); pg.wait_for_timeout(700)
    d = pg.get_attribute('#trackLayer .trkLine', 'd') or ''
    check('track drawn while driving', d.count('L') >= 8, d[:60])
    pg.screenshot(path='feat_track.png')
    pg.click('#visMoreBtn'); pg.click('label:has(#toggleTrack) .toggle'); pg.wait_for_timeout(150)
    check('Spår off -> line hidden', not pg.is_visible('#trackLayer .trkLine'))
    pg.click('label:has(#toggleTrack) .toggle'); pg.click('#visMoreBtn'); pg.wait_for_timeout(200)
    pg.evaluate("document.dispatchEvent(new Event('visibilitychange'))")
    pg.reload(); pg.wait_for_timeout(1800)
    d2 = pg.get_attribute('#trackLayer .trkLine', 'd') or ''
    check('track kept after reload / rotation', d2.count('L') >= 8, d2[:40])
    check('filter menu closed again after a fresh start', not pg.is_visible('#visMore'))
    pg.on('dialog', lambda dlg: dlg.accept())
    pg.click('#menuBtn'); pg.click('#menuItemSettings'); pg.wait_for_timeout(200)
    pg.click('#trackClearBtn'); pg.wait_for_timeout(200)
    check('Settings "Börja om" wipes the track so far', 'L' not in (pg.get_attribute('#trackLayer .trkLine', 'd') or ''), pg.get_attribute('#trackLayer .trkLine', 'd'))
    pg.click('#settingsBackBtn'); pg.wait_for_timeout(200)
    for i in range(5):
        lat += 10 / 111320.0; ctx.set_geolocation({'latitude': lat, 'longitude': lon, 'accuracy': 5}); pg.wait_for_timeout(700)
    d3 = pg.get_attribute('#trackLayer .trkLine', 'd') or ''
    check('...and keeps recording from where you are', d3.startswith('M') and d3.count('M') == 1 and d3.count('L') >= 4, d3[:60])
    # ---- offline start (service worker) ----
    ok = pg.evaluate("() => navigator.serviceWorker.ready.then(r => !!r.active)")
    pg.wait_for_timeout(2500)   # let it save its copy
    ctx.set_offline(True)
    pg.reload(); pg.wait_for_timeout(2500)
    check('service worker installed', ok)
    check('app opens with NO network (from the saved copy)', pg.title() == 'FF Map' and pg.is_visible('#visMoreBtn') and pg.eval_on_selector('#mapImg', 'e=>e.naturalWidth') == 3600)
    ctx.set_offline(False)
    check('no page errors', not [e for e in errs if 'firebase' not in e.lower()], errs)
    b.close()
print('\n%d/%d passed' % (sum(results), len(results)))
