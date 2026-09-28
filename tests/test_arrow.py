from playwright.sync_api import sync_playwright
import fakefb, math
fakefb.FAKE_FIREBASE_JS = fakefb.FAKE_FIREBASE_JS.replace(
    "wpDocs['w'+i] = { lat:w.lat, lon:w.lon, name:w.name, uid:w.uid,",
    "wpDocs['w'+i] = { lat:w.lat, lon:w.lon, name:w.name, type:w.type, uid:w.uid,")
from fakefb import new_page
results = []
def check(name, cond, info=''):
    results.append(bool(cond)); print(('PASS ' if cond else 'FAIL ') + name + ('  -- ' + str(info) if info != '' else ''))
ME0 = (58.88951, 15.77759)
ME = (ME0[0] - 300/111320.0, ME0[1] + 60/(111320.0*math.cos(math.radians(ME0[0]))))
def off(dn, de): return (ME[0] + dn/111320.0, ME[1] + de/(111320.0*math.cos(math.radians(ME[0]))))
W = []
for (dn, de, t, mine) in [(60,-70,'gos',True),(-55,45,'abborre',True),(25,55,'mark',False),(-20,-60,'abborre',False),(75,20,'gadda',False),(-70,-10,'gos',False)]:
    la, lo = off(dn, de); W.append({'lat':la,'lon':lo,'name':t,'type':t,'uid':'filip' if mine else 'kalle','by':'Filip' if mine else 'Calle'})
P = []
for (dn, de, name, age) in [(110,-40,'Calle',1),(-100,70,'Pia',25)]:
    la, lo = off(dn, de); P.append({'uid':name.lower(),'name':name,'lat':la,'lon':lo,'ageMin':age})
cfg = {'waypoints': W, 'positions': P}

def arrow(pg):
    return pg.evaluate("""() => { var m = document.getElementById('marker'); var a = document.getElementById('dotArrow');
      return { moving: m.classList.contains('moving'), rot: a.style.transform, arrowVis: getComputedStyle(a).display !== 'none',
               dotVis: getComputedStyle(document.getElementById('dotCenter')).display !== 'none' }; }""")
def rot(a):
    try: return float(a['rot'].replace('rotate(', '').replace('deg)', '')) % 360
    except Exception: return None

with sync_playwright() as p:
    b, ctx, pg, errs = new_page(p, geo=ME, cfg=cfg, name='Filip')
    pg.wait_for_timeout(600)
    a = arrow(pg); check('at start (never driven): arrow shown, pointing north', a['arrowVis'] and not a['dotVis'] and rot(a) == 0, a)
    d = pg.evaluate("[document.querySelector('#dotArrow .arrowBody').getBoundingClientRect().height, document.querySelector('.boatPip .boatDot').getBoundingClientRect().height, getComputedStyle(document.getElementById('dot')).backgroundColor]")
    check('just the arrow (no disc), ~17-18 px tall', 16.5 < d[0] < 18.5 and d[2] == 'rgba(0, 0, 0, 0)', d)
    rings = pg.evaluate("""() => ['accRing','dotGlow','dotGlow2'].map(id => getComputedStyle(document.getElementById(id)).display)""")
    check('only one ring (the expanding pulse)', rings == ['none','block','none'], rings)
    cc = pg.evaluate("""() => { var a = document.querySelector('#dotArrow .arrowBody').getBoundingClientRect(); var g = document.getElementById('dotGlow').getBoundingClientRect();
        return [a.left + a.width/2 - (g.left + g.width/2), a.top + a.height/2 - (g.top + g.height/2)]; }""")
    check('ring expands from the centre of the arrow', abs(cc[0]) < 1 and abs(cc[1]) < 1, cc)
    pg.screenshot(path='shot_arrow_still.png')
    lat, lon = ME
    for i in range(10):
        lat += 1.03 / 111320.0; ctx.set_geolocation({'latitude': lat, 'longitude': lon, 'accuracy': 5}); pg.wait_for_timeout(1000)
    a = arrow(pg); r = rot(a)
    check('driving north: arrow pointing up (~0°)', a['arrowVis'] and r is not None and min(r, 360 - r) < 12, a)
    for i in range(12):
        lon += 1.03 / (111320.0 * math.cos(math.radians(lat))); ctx.set_geolocation({'latitude': lat, 'longitude': lon, 'accuracy': 5}); pg.wait_for_timeout(1000)
    a = arrow(pg); r = rot(a)
    check('turning east: arrow turns to ~90°', r is not None and abs(r - 90) < 15, a)
    pg.wait_for_timeout(700)
    pg.screenshot(path='shot_arrow_moving.png')
    pg.wait_for_timeout(10000)
    a = arrow(pg); check('stopped: arrow stays, keeps the last direction (~90°)', a['arrowVis'] and abs(rot(a) - 90) < 15, a)
    pg.reload(); pg.wait_for_timeout(1500)
    a = arrow(pg); check('after a restart/rotation: still pointing the last way (~90°)', a['arrowVis'] and abs(rot(a) - 90) < 15, a)
    # tapping one of the others' small circles opens it
    c = pg.eval_on_selector('#waypoints .wpPin--other.wpPin--gadda', 'e=>{var r=e.getBoundingClientRect();return [r.left+r.width/2,r.top+r.height/2,r.width]}')
    pg.mouse.click(c[0], c[1]); pg.wait_for_timeout(400)
    check("tapping someone else's circle opens its sheet", pg.eval_on_selector('#wpSheet', 'e=>e.classList.contains("show")') and pg.inner_text('#wpTypeSeg .active') == 'Gädda', c)
    pg.click('#wpCancel'); pg.wait_for_timeout(300)
    # circle is centred on the spot, about half the size of my pin
    sz = pg.evaluate("""() => { var o = document.querySelector('#waypoints .wpPin--other').getBoundingClientRect(); var m = document.querySelector('#waypoints .wpPin:not(.wpPin--other)').getBoundingClientRect(); return [o.width, m.width]; }""")
    check("others' spots 70 % the size of my pins", abs(sz[0] / sz[1] - 0.7) < 0.03, sz)
    bd = pg.eval_on_selector('.boatPip:not(.boatPip--stale) .boatDot', 'e=>getComputedStyle(e).transform')
    check('boats are diamonds (rotated 45°)', bd.startswith('matrix(0.7') or 'matrix(0.70' in bd, bd)
    check('no page errors', not errs, errs)
    b.close()
print('\n%d/%d passed' % (sum(results), len(results)))
