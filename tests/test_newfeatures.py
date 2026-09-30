# New things: the "Fara" spot type, the "Träffpunkt" beacon (gone after an hour),
# the lead line's distance + time by WATER (with the lake outline from
# OpenStreetMap where Genesis has no depth data), and the quick map-style button.
from playwright.sync_api import sync_playwright
import fakefb, json, math, time, re
import numpy as np
from fakefb import new_page
from scipy import ndimage
results = []
def check(name, cond, info=''):
    results.append(bool(cond)); print(('PASS ' if cond else 'FAIL ') + name + ('  -- ' + str(info) if info != '' else ''))

# ---- points on Regnaren (full-resolution depth data: where it is + water / lake masks)
raw = np.load('../lakes/regnaren/raw/depth_raw.npz')
Z = int(raw['zoom']); OX, OY = [int(v) for v in raw['origin']]; N = 256 * 2 ** Z
water, lake = raw['water'], raw['lake']
def ll(col, row):
    xg, yg = col + OX, row + OY
    return math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * yg / N)))), xg / N * 360 - 180
SC = 2 ** (Z - 16)       # places below are given in zoom-16 px; the depth data may be finer
def snap(mask, c, r, need=12):
    c, r, need, win = int(c * SC), int(r * SC), need * SC, 300 * SC
    inner = ndimage.binary_erosion(mask[max(0, r - win):r + win, max(0, c - win):c + win], iterations=need)
    ys, xs = np.where(inner); i = np.argmin((xs - (c - max(0, c - win))) ** 2 + (ys - (r - max(0, r - win))) ** 2)
    return xs[i] + max(0, c - win), ys[i] + max(0, r - win)
A = snap(water, 300, 560)                      # you: west basin
B = snap(water, 1560, 700)                     # target: across a headland (straight line crosses land)
U = snap(lake & ~water, 600, 380, need=20)     # lake that Genesis has no depth for
bird = math.hypot(B[0] - A[0], B[1] - A[1]) * 156543.03392 * math.cos(math.radians(ll(*A)[0])) / 2 ** Z
LA, LB, LU = ll(*A), ll(*B), ll(*U)
now = time.time() * 1000
cfg = {'waypoints': [
    {'lat': LB[0] + 0.0015, 'lon': LB[1], 'name': 'Stenen', 'uid': 'filip', 'by': 'Filip', 'type': 'fara'},   # (not where the lead line goes)
    {'lat': LA[0] + 0.0004, 'lon': LA[1] - 0.0015, 'name': 'Grundet', 'uid': 'kalle', 'by': 'Calle', 'type': 'fara'},
    {'lat': LU[0], 'lon': LU[1], 'name': 'Viken', 'uid': 'filip', 'by': 'Filip', 'type': 'mark'},
    {'lat': LA[0] + 0.001, 'lon': LA[1], 'name': 'Lunch', 'uid': 'kalle', 'by': 'Calle', 'type': 'meet', 'expiresAt': now + 30 * 60000},
    {'lat': LA[0] - 0.001, 'lon': LA[1], 'name': 'Gammal lunch', 'uid': 'kalle', 'by': 'Calle', 'type': 'meet', 'expiresAt': now - 60000},
    {'lat': LA[0], 'lon': LA[1] + 0.002, 'name': 'Min förra', 'uid': 'filip', 'by': 'Filip', 'type': 'meet', 'expiresAt': now + 50 * 60000}]}

GEO = json.load(open('../lakes/regnaren/lake.json', encoding='utf-8'))['geo']
def screen_of(pg, col, row):
    """where a full-resolution point is on the screen now (map picture = zoom GEO.zoom)"""
    f = 2 ** (Z - GEO['zoom'])
    ix, iy = (col + OX) / f - GEO['originX'], (row + OY) / f - GEO['originY']
    t = pg.eval_on_selector('#world', 'e=>e.style.transform')
    ox, oy, s = [float(v) for v in re.findall(r'-?[\d.]+', t)[:3]]
    return ox + ix * s, oy + iy * s
def bring_to_centre(pg, col, row):
    x, y = screen_of(pg, col, row)
    pg.mouse.move(300, 600); pg.mouse.down(); pg.mouse.move(300 + 195 - x, 600 + 422 - y, steps=12); pg.mouse.up(); pg.wait_for_timeout(700)
    return screen_of(pg, col, row)
def set_type_shown(pg, label, on):
    pg.click('#visMoreBtn'); pg.wait_for_timeout(200)
    cb = pg.query_selector('#visTypes input[aria-label="%s"]' % label)
    if cb.is_checked() != on: pg.click('#visTypes label:has(input[aria-label="%s"])' % label); pg.wait_for_timeout(150)
    pg.click('#visMoreBtn'); pg.wait_for_timeout(300)

def pin_rect(pg, name):
    return pg.evaluate("""n => { var ids = Object.keys(window.__wpDocs).filter(k => window.__wpDocs[k].name === n);
        var el = ids.length && document.querySelector('#waypoints [data-id="' + ids[0] + '"]'); if (!el) return null;
        var r = el.getBoundingClientRect(); return [r.left, r.top, r.width, r.height, el.className]; }""", name)

with sync_playwright() as p:
    b, ctx, pg, errs = new_page(p, geo=LA, cfg=cfg, name='Filip')
    pg.wait_for_timeout(1500)
    # ---- Fara
    r, r2 = pin_rect(pg, 'Stenen'), pin_rect(pg, 'Grundet')
    check('Fara: a red stop sign (8 corners) with a white X, not a drop', r and r[4] == 'wpFara' and
          pg.evaluate("document.querySelector('.wpFara svg path').getAttribute('fill')") == '#E5322D' and
          pg.evaluate("document.querySelector('.wpFara svg path').getAttribute('d')").startswith('M8 1.6h8l6.4 6.4v8L16 22.4H8L1.6 16V8z'), r)
    check("Fara: the same for everyone's (yours and Calle's look and size alike)", r2 and r2[4] == 'wpFara' and abs(r[2] - r2[2]) < 0.5, (r, r2))
    check("Fara: about others' size, a bit bigger (~21 px at Normal), on top of the other spots",
          18 <= r[2] <= 24 and pg.evaluate("getComputedStyle(document.querySelector('.wpFara')).zIndex") == '3', r)
    # filters never hide a Fara
    pg.click('#visMoreBtn'); pg.wait_for_timeout(200)
    check('Filter has no Fara switch', pg.query_selector('#visTypes input[data-type="fara"]') is None)
    pg.click('label:has(#toggleMine) .toggle'); pg.click('label:has(#toggleOthers) .toggle'); pg.wait_for_timeout(300)
    check('Mina + Andras off: the Fara spots still show (the rest do not)', pin_rect(pg, 'Stenen') and pin_rect(pg, 'Grundet') and not pin_rect(pg, 'Viken'))
    pg.screenshot(path='shot_fara_filtered.png')
    pg.click('label:has(#toggleMine) .toggle'); pg.click('label:has(#toggleOthers) .toggle'); pg.click('#visMoreBtn'); pg.wait_for_timeout(300)
    # tap someone else's Fara: the sheet opens on it
    pg.evaluate("n => { var ids = Object.keys(window.__wpDocs).filter(k => window.__wpDocs[k].name === n); document.querySelector('#waypoints [data-id=\"' + ids[0] + '\"]').click(); }", 'Grundet')
    pg.wait_for_timeout(400)
    check("tapping a Fara opens it", pg.input_value('#wpName') == 'Grundet' and pg.eval_on_selector('#wpSheet', 'e=>e.classList.contains("show")'))
    pg.click('#wpCancel'); pg.wait_for_timeout(300)
    # ---- Träffpunkt
    beacons = pg.eval_on_selector_all('#waypoints .wpBeacon', 'e=>e.map(x=>x.querySelector(".bcTag").textContent)')
    check("Träffpunkt: a beacon with rings + 'name · who · minutes left'", any(re.match(r'^Lunch · Calle · (29|30) min kvar$', t) for t in beacons) and
          pg.eval_on_selector_all('#waypoints .wpBeacon .bcRing', 'e=>e.length') >= 3, beacons)
    check('an hour gone: not shown (on the map or in the log)', not any('Gammal' in t for t in beacons))
    pg.click('#menuBtn'); pg.click('#menuItemLog'); pg.wait_for_timeout(300)
    logt = pg.eval_on_selector_all('#logList .logTitle', 'e=>e.map(x=>x.textContent)')
    check('...and not in the log', 'Gammal lunch' not in logt and 'Lunch' in logt, logt)
    pg.click('#logBackBtn'); pg.wait_for_timeout(200)
    # someone else's Träffpunkt can't be removed (not admin)
    pg.evaluate("Array.from(document.querySelectorAll('#waypoints .wpBeacon')).filter(e => e.querySelector('.bcTag').textContent.indexOf('Lunch ') === 0)[0].click()"); pg.wait_for_timeout(400)
    check("someone else's Träffpunkt: no delete button", pg.eval_on_selector('#wpSheet', 'e=>e.classList.contains("show")') and not pg.is_visible('#wpDelete'))
    pg.click('#wpCancel'); pg.wait_for_timeout(300)
    # a new one of your own: long press -> Träffpunkt -> save; your previous one goes
    pg.mouse.move(150, 300); pg.mouse.down(); pg.wait_for_timeout(700); pg.mouse.up(); pg.wait_for_timeout(600)
    types = pg.eval_on_selector_all('#wpTypeSeg button', 'e=>e.map(x=>x.textContent.trim())')
    check('type picker has Fara and Träffpunkt 1 h', 'Fara' in types and 'Träffpunkt 1 h' in types, types)
    pg.click('#wpTypeSeg button[data-type="meet"]'); pg.wait_for_timeout(150)
    check('the sheet says it is shown for an hour', 'Syns för alla i 1 h' in pg.inner_text('#wpMeta'), pg.inner_text('#wpMeta'))
    pg.fill('#wpName', 'Fika'); pg.click('#wpSave'); pg.wait_for_timeout(600)
    mine = pg.evaluate("Object.values(window.__wpDocs).filter(d => d.uid === 'filip' && d.type === 'meet').map(d => [d.name, Math.round((d.expiresAt - Date.now()) / 60000)])")
    check('your new Träffpunkt: an hour from now, and only one (the old one removed)', mine == [['Fika', 60]], mine)
    beacons = pg.eval_on_selector_all('#waypoints .wpBeacon', 'e=>e.map(x=>x.querySelector(".bcTag").textContent)')
    check("shown as 'Fika · du · 60 min kvar'", 'Fika · du · 60 min kvar' in beacons, beacons)
    pg.screenshot(path='shot_beacon.png')

    # ---- lead line: distance + time by water
    set_type_shown(pg, 'Markering', False)   # (so a tap there hits the map, not the pin)
    tx, ty = bring_to_centre(pg, *B)
    pg.mouse.click(tx, ty); pg.wait_for_timeout(900)
    dist = pg.inner_text('#probeDistTxt'); tm = pg.inner_text('#probeTime')
    km = float(dist.replace(' km', '').replace(',', '.')) * 1000 if 'km' in dist else float(dist.replace(' m', ''))
    pts = pg.eval_on_selector('#routeLayer .rtLine', 'e=>e.getAttribute("points")').split()
    check('distance BY WATER: longer than as the crow flies (around the headland)', km > bird * 1.04, (dist, round(bird)))
    check('the route is drawn from you to the lead line, with turns', len(pts) >= 3, len(pts))
    check('time to get there shown (your cruising speed when still)', re.match(r'^\d+ min$|^\d+ h \d\d min$', tm) is not None and pg.is_visible('#probeTime'), tm)
    t_still = tm
    # moving at ~6 kn -> the time follows your speed
    lat, lon = LA
    for k in range(8):
        lon += 3.1 / (111320 * math.cos(math.radians(lat))); ctx.set_geolocation({'latitude': lat, 'longitude': lon, 'accuracy': 5}); pg.wait_for_timeout(1000)
    tm2 = pg.inner_text('#probeTime')
    check('the time is redone as you move, at your speed', tm2 != t_still and re.match(r'^\d+ min$', tm2), (t_still, tm2))
    pg.screenshot(path='shot_route.png')
    tx, ty = screen_of(pg, *B)
    pg.mouse.click(tx, ty); pg.wait_for_timeout(700)
    check('lead line removed -> the route goes too', pg.eval_on_selector('#routeLayer .rtLine', 'e=>e.getAttribute("points")') == '')
    # the lake where Genesis has no depth: "Okänt djup", not "Land"
    ux, uy = bring_to_centre(pg, *U)
    pg.mouse.click(ux, uy); pg.wait_for_timeout(800)
    check('lake without depth data: "Okänt djup" (OpenStreetMap outline)', pg.inner_text('#probeDepth') == 'Okänt djup', pg.inner_text('#probeDepth'))
    check('...and you still get the way there by water', pg.eval_on_selector('#routeLayer .rtLine', 'e=>e.getAttribute("points")') != '')
    pg.mouse.click(ux, uy); pg.wait_for_timeout(600)
    set_type_shown(pg, 'Markering', True)

    # ---- quick map-style button
    src = lambda: pg.get_attribute('#mapImg', 'src')
    seen = []
    for k in range(4):
        pg.click('#mapTypeBtn'); pg.wait_for_timeout(900)
        seen.append((src().split('_')[-1], pg.inner_text('#mapTypeToast')))
    check('tap: Förenklad -> Bottenhårdhet -> Vegetation -> Djupfärger', [s[0] for s in seen] == ['s2.jpg', 'c1.jpg', 'v1.jpg', 's1.jpg'] and
          [s[1] for s in seen] == ['Förenklad', 'Bottenhårdhet', 'Vegetation', 'Djupfärger'], seen)
    bb = pg.eval_on_selector('#mapTypeBtn', 'e=>{var r=e.getBoundingClientRect();return [r.left+r.width/2,r.top+r.height/2]}')
    vis = pg.eval_on_selector('#visPanel', 'e=>e.getBoundingClientRect().left')
    check('the button sits just left of Filter', bb[0] < vis and vis - bb[0] < 40, (bb, vis))
    pg.mouse.move(*bb); pg.mouse.down(); pg.wait_for_timeout(700); pg.mouse.up(); pg.wait_for_timeout(400)
    opts = pg.eval_on_selector_all('#mapTypePop .styleOpt[data-style]', 'e=>e.length')
    check('hold: all map styles to choose from (+ Heatmap last)', pg.is_visible('#mapTypePop') and opts == 8 and pg.eval_on_selector('#mapTypePop .styleOpt:last-child', 'e => e.classList.contains("hmOpt")'), opts)
    pg.screenshot(path='shot_maptype_pop.png')
    pg.click('#mapTypePop .styleOpt[data-style="g1"]'); pg.wait_for_timeout(1000)
    check('...pick one', src().endswith('_g1.jpg') and not pg.is_visible('#mapTypePop'), src())
    pg.click('#mapTypeBtn'); pg.wait_for_timeout(900)
    check('from another style a tap goes to Djupfärger', src().endswith('_s1.jpg'), src())
    check('no page errors', not errs, errs)
    b.close()
print('\n%d/%d passed' % (sum(results), len(results)))
