from playwright.sync_api import sync_playwright
import fakefb
from fakefb import new_page
results = []
def check(name, cond, info=''):
    results.append(bool(cond)); print(('PASS ' if cond else 'FAIL ') + name + ('  -- ' + str(info) if info != '' else ''))
ME = (58.88951, 15.77759)

def hdg(pg, h):
    pg.evaluate("h => { var e = new Event('deviceorientation'); e.webkitCompassHeading = h; window.dispatchEvent(e); }", h)
def st(pg): return pg.evaluate("window.__ffCompass()")
def wedge(pg):
    return pg.evaluate("""() => { var w = document.getElementById('compassWedge'), a = w.getBoundingClientRect(), d = document.getElementById('dotArrow').getBoundingClientRect();
        return { disp: getComputedStyle(w).display, tr: w.style.transform, cx: a.left + a.width/2 - (d.left + d.width/2), cy: a.top + a.height/2 - (d.top + d.height/2) }; }""")
def tap(pg): pg.evaluate("document.getElementById('toggleCompass').click()")

with sync_playwright() as p:
    b, ctx, pg, errs = new_page(p, geo=ME, name='Filip')
    pg.wait_for_timeout(800)
    s = st(pg); check('off at start: no wedge', not s['on'] and not s['shown'], s)
    # iOS: permission asked at the tap; denied -> switch goes back off
    pg.evaluate("window.__asked = 0; DeviceOrientationEvent.requestPermission = () => { window.__asked++; return Promise.resolve('denied'); }; 0")
    tap(pg); pg.wait_for_timeout(200)
    check('iOS: permission asked at the tap', pg.evaluate("window.__asked") == 1, pg.evaluate("window.__asked"))
    check('denied: switch back off, short note', not pg.evaluate("document.getElementById('toggleCompass').checked") and 'inte tillåten' in pg.inner_text('#compassLabel'))
    pg.evaluate("DeviceOrientationEvent.requestPermission = () => Promise.resolve('granted'); 0")
    tap(pg); pg.wait_for_timeout(200)
    check('granted: on, but no wedge until a heading arrives', st(pg)['on'] and not st(pg)['shown'], st(pg))
    hdg(pg, 90); pg.wait_for_timeout(100)
    s = st(pg); w = wedge(pg)
    check('wedge shown, pointing east (90)', s['shown'] and abs(s['hdg'] - 90) < 0.5 and 'rotate(90deg)' in w['tr'], (s, w))
    check('wedge centred on the position arrow', abs(w['cx']) < 1.5 and abs(w['cy']) < 1.5, w)
    hdg(pg, 350); pg.wait_for_timeout(50)
    for i in range(30): hdg(pg, 350)
    h = st(pg)['hdg']; check('turns the short way round and settles (350)', abs(h - 350) < 1, h)
    for i in range(30): hdg(pg, 10)
    h = st(pg)['hdg']; check('across north: settles at 10, not via 180', abs(((h - 10 + 180) % 360) - 180) < 1, h)
    wd = st(pg)['w']
    pg.mouse.wheel(0, -400); pg.wait_for_timeout(500)
    check('wedge grows when zooming in (stays 500 m)', st(pg)['w'] > wd, (wd, st(pg)['w']))
    pg.screenshot(path='shot_compass.png')
    # rotation reload (sessionStorage): still on
    pg.reload(); pg.wait_for_timeout(1500)
    check('after a reload: switch still on', st(pg)['on'] and pg.evaluate("document.getElementById('toggleCompass').checked"), st(pg))
    hdg(pg, 200); pg.wait_for_timeout(100)
    check('after a reload: wedge follows again', st(pg)['shown'] and abs(st(pg)['hdg'] - 200) < 0.5, st(pg))
    tap(pg); pg.wait_for_timeout(100)
    s = st(pg); check('off: wedge gone, listener removed', not s['on'] and not s['shown'], s)
    hdg(pg, 45); pg.wait_for_timeout(100)
    check('events after off change nothing', not st(pg)['shown'] and st(pg)['hdg'] is None, st(pg))
    # Android: absolute alpha, no permission call
    pg.evaluate("delete DeviceOrientationEvent.requestPermission")
    tap(pg); pg.wait_for_timeout(100)
    pg.evaluate("() => { var e = new Event('deviceorientationabsolute'); e.absolute = true; e.alpha = 270; window.dispatchEvent(e); }"); pg.wait_for_timeout(100)
    check('Android: alpha 270 = pointing east (90)', st(pg)['shown'] and abs(st(pg)['hdg'] - 90) < 0.5, st(pg))
    check('no page errors', not errs, errs)
    b.close()
print('\n%d/%d passed' % (sum(results), len(results)))
