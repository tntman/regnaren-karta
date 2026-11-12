# 3D-karta (js/73-map3d.js): in the map-style list (hold the map button), right after the map styles -> a full-screen
# view of its own: the bottom in 3D (three.js) with the map picture on it, the map's pins and boats copied on top.
# The fingers as in the map apps (one moves the map, a pinch zooms, a twist turns, two up/down tilt), zoomed in = a finer
# mesh; Vatten / Höjd are remembered; ✕ closes all of it.
import json, io, base64, sys, math
import numpy as np
sys.path.insert(0, '../tools')
from land_height import unpack, check as tool_check          # (the land file read here, apart from the app)
from PIL import Image, ImageChops, ImageStat
from playwright.sync_api import sync_playwright
import fakefb
from fakefb import new_page
results = []
def check(name, cond, info=''):
    results.append(bool(cond)); print(('PASS ' if cond else 'FAIL ') + name + ('  -- ' + str(info) if info != '' else ''))
B3 = (58.887269, 15.772629); B1 = (58.887421, 15.775569)
def M(pg, o=None): return pg.evaluate('window.__ffMap3d(%s)' % (json.dumps(o) if o else ''))
def hold_map_btn(pg):
    bb = pg.locator('#mapTypeBtn').bounding_box(); pg.mouse.move(bb['x'] + 20, bb['y'] + 20); pg.mouse.down(); pg.wait_for_timeout(700); pg.mouse.up(); pg.wait_for_timeout(300)
try: tool_check(); tool_ok = True
except AssertionError as e: tool_ok = repr(e)
check("the height tool's own checks: the map turned into Lantmäteriet's squares, the file's packing, which water is a hole", tool_ok is True, tool_ok)

with sync_playwright() as p:
    cfg = {'positions': [{'uid': 'pia', 'name': 'Pia', 'lat': 58.8905, 'lon': 15.7850}],
           'waypoints': [{'uid': 'x', 'by': 'Calle', 'name': 'Grundet', 'lat': 58.8880, 'lon': 15.7700, 'type': 'abborre'},
                         {'uid': 'x', 'by': 'Calle', 'name': 'Sten', 'lat': 58.8890, 'lon': 15.7800, 'type': 'fara'}]}
    b, ctx, pg, errs = new_page(p, geo=B3, name='Filip', cfg=cfg)
    pg.wait_for_timeout(2500)
    hold_map_btn(pg)
    opts = pg.evaluate("[...document.querySelectorAll('#mapTypePop .styleOpt')].map(e => e.getAttribute('data-style') ? 'style' : e.textContent)")
    n_styles = opts.count('style')
    check('the map-style list: "3D-karta" right after the map styles (then Heatmap, Under ytan)', opts[n_styles].startswith('3D-karta') and 'Heatmap' in opts[n_styles + 1] and len(opts) == n_styles + 3, opts[n_styles:])
    pg.click('#mapTypePop .m3Opt'); pg.wait_for_timeout(2500)
    s = M(pg)
    check('it opens full screen, the mesh built: at most 400 points a side', s['open'] and s['ready'] and 64 < s['n'] <= 401 and pg.evaluate("!!document.elementFromPoint(195, 300).closest('#m3View')"), s)
    check('...it looks where the map looked (near your boat), north up', abs(s['hit']['at']['lat'] - B3[0]) < 0.01 and s['c']['az'] == 0, s['hit'])
    pg.screenshot(path='shot_map3d.png')
    # the mesh is the bottom: where the middle of the screen meets it, its height = -the depth there
    d = pg.evaluate('window.__ffGeo.depthAt(%f, %f)' % (s['hit']['at']['lat'], s['hit']['at']['lon']))
    check('the mesh is the bottom: the height under the middle of the screen = -the depth there', d is not None and d > 1 and abs(-s['hit']['y'] - d) < 0.3, (s['hit'], d))
    check('your boat, the two spots and the other boat are copied on top (4)', s['marks'] == 4 and pg.locator('#m3Marks .m3Me').count() == 1 and pg.locator('#m3Marks .wpPin').count() == 1 and pg.locator('#m3Marks .wpFara').count() == 1 and pg.locator('#m3Marks .boatPip').count() == 1, s['marks'])
    pg.click('#m3Me'); pg.wait_for_timeout(600)
    bb = pg.locator('#m3Marks .m3Me').bounding_box()
    check('"Till mig": your boat in the middle of the screen', abs(bb['x'] + bb['width'] / 2 - 195) < 3 and abs(bb['y'] + bb['height'] / 2 - 422) < 8, bb)      # (its label is at the arrow, just over the water)
    ob = M(pg)['objs']; kinds = sorted(o['kind'] + ('*' if o['me'] else '') for o in ob)
    check('the marks are 3D objects: a pin, the stop sign, the other boat and your boat (the same arrow), each on the water with a line to the bottom (the other boat is on land here: none)',
          kinds == ['boat', 'boat*', 'fara', 'pin'] and sum(o['line'] for o in ob) == 3 and all(o['y'] >= 0 for o in ob)
          and pg.evaluate("[...document.querySelectorAll('#m3Marks .wpPin, #m3Marks .wpFara')].every(e => getComputedStyle(e).visibility === 'hidden')")
          and pg.evaluate("getComputedStyle(document.querySelector('#m3Marks .boatName')).visibility") == 'visible', (kinds, ob))
    pg.evaluate("DeviceOrientationEvent.requestPermission = () => Promise.resolve('granted'); 0")      # (as when you say yes on an iPhone)
    pg.click('#m3Chips [data-k=compass]'); pg.wait_for_timeout(300)
    for _ in range(25): pg.evaluate("window.dispatchEvent(new DeviceOrientationEvent('deviceorientationabsolute', {alpha: 300, absolute: true}))")      # (the phone points 60 degrees: north-east)
    pg.wait_for_timeout(300); s = M(pg); me = [o for o in s['objs'] if o['me']][0]
    check("Kompass: your arrow turns where the phone points, the compass rose and the wedge along the water with it -- and it is Filter's Kompass",
          s['comp'] and abs(me['hdg'] - 60) < 1 and abs(s['compRot'] + math.radians(60)) < 0.02 and pg.evaluate("window.__ffCompass().on") and pg.evaluate("document.querySelector('#m3Chips [data-k=compass]').classList.contains('on')"), (s['comp'], me, s['compRot']))
    pg.screenshot(path='shot_map3d_compass.png')
    pg.click('#m3Chips [data-k=compass]'); pg.wait_for_timeout(300)
    check('...off again: no compass', not M(pg)['comp'] and not pg.evaluate("window.__ffCompass().on"))
    # the fingers, as in the map apps. What the app draws at a place on the screen is asked of three.js itself (a ray
    # against the mesh) -- apart from the app's own reckoning of what the fingers hold
    c0 = M(pg)['c']; k0 = M(pg)['cam']
    def spot(x, y): return M(pg, {'at': [x, y]})['hit']
    def apart(a, b): return math.hypot((a['at']['lat'] - b['at']['lat']) * 111320, (a['at']['lon'] - b['at']['lon']) * 111320 * math.cos(math.radians(B3[0])))      # m
    def px_m(c): return 2 * c['d'] * math.tan(math.radians(20)) / 844      # m a screen px, at the point looked at
    def mid(sel): bb = pg.locator(sel).bounding_box(); return (bb['x'] + bb['width'] / 2, bb['y'] + bb['height'] / 2)
    def ang(a, b): return math.atan2(b[1] - a[1], b[0] - a[0])      # (on the screen, y down: more = clockwise)
    def drag(a, b):      # one finger (the mouse) from a to b and held there: what it took hold of, and how far (m) that is from the finger then
        pg.mouse.move(*a); pg.mouse.down(); pg.mouse.move(a[0], a[1] - 1); pg.wait_for_timeout(120)      # (its first move only takes hold)
        g = spot(a[0], a[1] - 1); pg.mouse.move(b[0], b[1], steps=8); pg.wait_for_timeout(120)
        return g, apart(g, spot(*b))
    g, off = drag((170, 500), (195, 422)); s = M(pg)      # (a hill south of the strait, to the middle of the screen)
    check('one finger moves the map: the hill it took hold of stays under it -- nothing turns or tilts, and the camera keeps its height though the point looked at is up on land now',
          g['y'] > 5 and s['hit']['y'] > 5 and off < 4 * px_m(c0) and (s['c']['az'], s['c']['tilt']) == (c0['az'], c0['tilt']) and abs(s['cam'][1] - k0[1]) < 0.01, (g, off, px_m(c0), k0, s['cam'], s['hit']))
    pg.mouse.up(); pg.wait_for_timeout(500)
    s2 = M(pg)
    check('...the finger up: the point looked at is on the ground again, where the middle of the screen meets it -- and nothing moved in the picture',
          abs(s2['hit']['d'] / s2['c']['d'] - 1) < 0.01 and max(abs(a - b) for a, b in zip(s2['cam'], s['cam'])) < 0.004 * c0['d'], (s2['hit'], s2['c'], s['cam'], s2['cam']))
    pg.click('#m3Me'); pg.wait_for_timeout(600)
    g, off = drag((195, 422), (150, 250)); pg.mouse.up(); pg.wait_for_timeout(300)
    check('...and up into the far part of the tilted view: the bottom it took hold of is still under the finger', g['y'] < -1 and off < 4 * px_m(c0), (g, off, px_m(c0)))
    pg.click('#m3Me'); M(pg, {'d': 300}); pg.wait_for_timeout(1200)
    c = M(pg)['c']; g, off = drag((195, 440), (230, 330)); pg.mouse.up(); pg.wait_for_timeout(300)
    check("near, over deep water: it is the bottom that stays under the finger (not the water's surface over it)", g['y'] < -3 and off < 4 * px_m(c), (g, off, px_m(c)))
    cdp = ctx.new_cdp_session(pg)
    def touch(typ, pts): cdp.send('Input.dispatchTouchEvent', {'type': typ, 'touchPoints': [{'x': x, 'y': y, 'id': i} for i, (x, y) in enumerate(pts)]})
    def fingers(path, steps=12):      # two fingers down at path(0), along it to path(1), up: how far (m) what was under their middle is from it at the end
        def m(f): a, b = path(f); return ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
        touch('touchStart', path(0)[:1]); touch('touchStart', path(0)); touch('touchMove', path(1 / steps)); pg.wait_for_timeout(80)
        g = spot(*m(1 / steps))      # (their first moves only take hold)
        for k in range(2, steps + 1): touch('touchMove', path(k / steps)); pg.wait_for_timeout(16)
        pg.wait_for_timeout(80); off = apart(g, spot(*m(1)))
        touch('touchEnd', []); pg.wait_for_timeout(300)
        return off
    pg.click('#m3Me'); M(pg, {'tilt': 0.05, 'd': 3000, 'az': 0}); pg.wait_for_timeout(900)      # (straight down: what the fingers do to the picture is plain to see)
    s1 = M(pg); a1 = ang(mid('#m3Marks .m3Me'), mid('#m3Marks .wpFara'))
    off = fingers(lambda f: [(130 + 50 * math.cos(f * 0.8), 300 + 50 * math.sin(f * 0.8)), (130 - 50 * math.cos(f * 0.8), 300 - 50 * math.sin(f * 0.8))])
    s2 = M(pg); a2 = ang(mid('#m3Marks .m3Me'), mid('#m3Marks .wpFara')); turn = s2['c']['az'] - s1['c']['az']
    check('two fingers twisted clockwise, away from the middle of the screen: the map turns clockwise with them, about the point between the fingers -- no zoom, no tilt',
          0.3 < turn < 0.75 and abs((a2 - a1) - turn) < 0.1 and off < 4 * px_m(s1['c']) and abs(s2['cam'][1] / s1['cam'][1] - 1) < 0.002 and s2['c']['tilt'] == s1['c']['tilt'], (turn, a2 - a1, off, s1['cam'], s2['cam']))
    off = fingers(lambda f: [(100 - 60 * f, 300), (160 + 60 * f, 300)])
    s3 = M(pg)
    check('a pinch, the fingers apart to 3 x: it zooms in on the point between them, nothing turns', 0.3 < s3['cam'][1] / s2['cam'][1] < 0.42 and off < 4 * px_m(s3['c']) and (s3['c']['az'], s3['c']['tilt']) == (s2['c']['az'], s2['c']['tilt']), (s2['cam'], s3['cam'], off, px_m(s3['c'])))
    off = fingers(lambda f: [(110 + 60 * f, 560), (210 + 60 * f, 560)])
    s4 = M(pg)
    check('two fingers moved sideways together: the map goes with them (no tilt, turn or zoom)', off < 4 * px_m(s4['c']) and s4['c']['px'] != s3['c']['px'] and (s4['c']['az'], s4['c']['tilt']) == (s3['c']['az'], s3['c']['tilt']) and abs(s4['cam'][1] / s3['cam'][1] - 1) < 0.002, (off, s3['c'], s4['c'], s3['cam'], s4['cam']))
    fingers(lambda f: [(140, 560 - 120 * f), (250, 560 - 120 * f)])
    s5 = M(pg); tl = s5['c']['tilt'] - s4['c']['tilt']
    check('two fingers side by side, both moved up: it tilts towards the horizon, nothing else', 0.5 < tl < 0.62 and s5['c']['az'] == s4['c']['az'] and abs(s5['c']['d'] / s4['c']['d'] - 1) < 0.005 and abs(s5['c']['px'] - s4['c']['px']) + abs(s5['c']['py'] - s4['c']['py']) < 2, (s4['c'], s5['c']))
    fingers(lambda f: [(140 + 14 * f, 560 + 100 * f), (250 + 4 * f, 560 + 80 * f)])      # (as on a phone: a little askew and uneven -- down = back towards straight down)
    s5b = M(pg)
    check('...and a little askew and uneven, as fingers are: it still tilts (back), nothing turns', s5b['c']['tilt'] < s5['c']['tilt'] - 0.3 and s5b['c']['az'] == s5['c']['az'], (s5['c'], s5b['c']))
    s5 = s5b
    pg.click('#m3North'); pg.wait_for_timeout(300)
    check('the north arrow: north up again', M(pg)['c']['az'] == 0)
    pg.keyboard.down('Shift'); pg.mouse.move(195, 300); pg.mouse.down(); pg.mouse.move(275, 340, steps=5); pg.mouse.up(); pg.keyboard.up('Shift'); pg.wait_for_timeout(300)
    s6 = M(pg)
    check('with a mouse: Shift + drag turns and tilts it (the map stays)', s6['c']['az'] != 0 and s6['c']['tilt'] != s5['c']['tilt'] and abs(s6['c']['d'] / s5['c']['d'] - 1) < 0.005 and abs(s6['c']['px'] - s5['c']['px']) + abs(s6['c']['py'] - s5['c']['py']) < 2, (s5['c'], s6['c']))
    def maya(button, alt, a, b):      # a mouse drag as in Maya / Houdini: -> the camera before and after
        k0 = M(pg)['c'].copy()
        if alt: pg.keyboard.down('Alt')
        pg.mouse.move(*a); pg.mouse.down(button=button); pg.mouse.move(*b, steps=6); pg.mouse.up(button=button)
        if alt: pg.keyboard.up('Alt')
        pg.wait_for_timeout(300); return k0, M(pg)['c']
    k0, k1 = maya('left', True, (195, 350), (265, 300))      # (up: it looks straight down here, it can only tilt towards the horizon)
    check('a mouse as in Maya / Houdini: Alt + left drag turns and tilts (the map stays)', k1['az'] != k0['az'] and k1['tilt'] != k0['tilt'] and abs(k1['d'] / k0['d'] - 1) < 0.005, (k0, k1))
    k0, k1 = maya('right', True, (195, 300), (265, 350))
    check('...Alt + right drag zooms (right / down = nearer), nothing turns', k1['d'] < k0['d'] * 0.7 and k1['az'] == k0['az'] and k1['tilt'] == k0['tilt'], (k0, k1))
    k0, k1 = maya('middle', False, (195, 300), (265, 350))
    check('...the middle button moves the map (no turn, no zoom)', (k1['px'], k1['py']) != (k0['px'], k0['py']) and k1['az'] == k0['az'] and abs(k1['d'] / k0['d'] - 1) < 0.005, (k0, k1))
    pg.click('#m3Me'); M(pg, {'d': c0['d'], 'az': 0, 'tilt': c0['tilt']}); pg.wait_for_timeout(800)      # (as it opened, for what follows)
    c1 = M(pg)['c']
    b0 = M(pg)['builds']; r0 = M(pg)['at']['R']
    pg.mouse.move(195, 300); pg.mouse.wheel(0, -900); pg.wait_for_timeout(700)
    s = M(pg)
    check('the wheel zooms in: a mesh for the smaller area, built once when it rests', s['c']['d'] < c1['d'] and s['at']['R'] < r0 and s['builds'] == b0 + 1 and s['n'] <= 401, (c1['d'], s['c']['d'], r0, s['at'], b0, s['builds']))
    # near: the picture is the zoom level's pieces put together (not the map picture enlarged) -- and they sit where the map picture says
    pg.wait_for_timeout(1500)
    z1 = M(pg)['det']['z']
    M(pg, {'d': 300}); pg.wait_for_timeout(1800)
    dt = M(pg, {'pic': True})['det']
    M(pg, {'d': 250, 'tilt': 1.3}); pg.wait_for_timeout(1800)
    nb = M(pg, {'at': [195, 790]})['hit']
    check('near and tilted: the ground nearest you (the bottom of the screen) is in the sharp patch too', nb and nb['inDet'], nb)
    M(pg, {'d': 300, 'tilt': c1['tilt']}); pg.wait_for_timeout(1800); dt = M(pg, {'pic': True})['det']
    check('zoomed in: a sharp patch around the point you look at -- nearer = a deeper zoom level, 300 m away = the deepest (18)', dt and 15 <= z1 < 18 and dt['z'] == 18 and dt['n'] >= 8, dt and (z1, dt['z'], dt['n']))
    lk = json.load(open('../lakes/regnaren/lake.json', encoding='utf-8'))
    base = Image.open('../docs/lakes/regnaren/' + lk['mapFile'].replace('{style}', lk['styles'][0]['id'])).convert('RGB')
    pic = Image.open(io.BytesIO(base64.b64decode(dt['url'].split(',')[1]))).convert('RGB').resize((32, 32), Image.BOX)
    sc = 2 ** (dt['z'] - lk['geo']['zoom'])
    def diff(dx): return sum(ImageStat.Stat(ImageChops.difference(pic, base.crop(((dt['X'] + dx) / sc, dt['Y'] / sc, (dt['X'] + dx + 2048) / sc, (dt['Y'] + 2048) / sc)).resize((32, 32), Image.BOX))).mean) / 3
    check('...the pieces sit where the map picture says (made small it is the same picture; half a patch off it is not)', diff(0) < 14 and diff(0) < diff(1024) * 0.6, (round(diff(0), 1), round(diff(1024), 1)))
    pg.screenshot(path='shot_map3d_near.png')
    # the land: the highest point of the lake's land file stands that high in the mesh
    ld = json.load(open('../lakes/regnaren/land.json', encoding='utf-8'))
    g = unpack(open('../docs/' + ld['file']).read().strip(), ld['w'] * ld['h']).reshape(ld['h'], ld['w']).astype(float)
    g[g > 250] = 0; g = g[5:-5, 5:-5]; j, i = divmod(int(g.argmax()), g.shape[1])
    top = (g[j, i] / 250) ** 2 * ld['max']; TOP = {'px': (i + 5.5) / ld['w'] * lk['geo']['imgW'], 'py': (j + 5.5) / ld['h'] * lk['geo']['imgH'], 'd': 400, 'tilt': 0.05, 'az': 0}
    M(pg, TOP); pg.wait_for_timeout(900)
    s = M(pg)
    check('the land has its height (the land file read apart from the app says the same)', s['land'] and top > 20 and abs(s['hit']['y'] - top) < 3, (top, s['hit']))
    check('...whose heights they are is written in the controls', 'Höjddata' in pg.inner_text('#m3Src'), pg.inner_text('#m3Src'))
    pg.click('#m3Chips [data-k=water]'); pg.fill('#m3Ex', '6'); pg.dispatch_event('#m3Ex', 'input'); pg.wait_for_timeout(400)
    sv = json.loads(pg.evaluate("localStorage.getItem('ffmap_3d_v1')"))
    check('Vatten off and Höjd × 6: shown and remembered', sv == {'ex': 6, 'water': False, 'col': False, 'shadow': False, 'fish': False} and pg.inner_text('#m3ExVal') == '× 6' and not pg.evaluate("document.querySelector('#m3Chips [data-k=water]').classList.contains('on')"), sv)
    pg.screenshot(path='shot_map3d_dry.png')
    M(pg, {'px': 1050, 'py': 420, 'd': 1200, 'tilt': 1.1, 'az': 0.4}); pg.wait_for_timeout(1500)
    def look(): return ImageStat.Stat(Image.open(io.BytesIO(pg.screenshot())).convert('RGB').crop((0, 400, 390, 700))).mean
    a0 = look(); pg.click('#m3Chips [data-k=col]'); pg.wait_for_timeout(600); a1 = look()
    sv = json.loads(pg.evaluate("localStorage.getItem('ffmap_3d_v1')"))
    check('Djupfärg: the bottom coloured by depth instead of the map picture (another picture), shown and remembered',
          sv['col'] is True and pg.evaluate("document.querySelector('#m3Chips [data-k=col]').classList.contains('on')") and sum(abs(x - y) for x, y in zip(a0, a1)) > 15, (a0, a1, sv))
    pg.screenshot(path='shot_map3d_col.png')
    pg.click('#m3Chips [data-k=col]'); pg.wait_for_timeout(300)
    M(pg, {'px': 1000, 'py': 470, 'd': 550, 'tilt': 1.15, 'az': 0.9}); pg.wait_for_timeout(1500)      # (by an island in the lake: its shadow falls on the water's bottom)
    a0 = look(); pg.click('#m3Chips [data-k=shadow]'); pg.wait_for_timeout(800); a1 = look()
    sv = json.loads(pg.evaluate("localStorage.getItem('ffmap_3d_v1')"))
    check('Skuggor: cast shadows (the picture gets darker where hills shade it), shown and remembered',
          sv['shadow'] is True and pg.evaluate("document.querySelector('#m3Chips [data-k=shadow]').classList.contains('on')") and sum(a1) < sum(a0) - 3, (a0, a1, sv))
    pg.screenshot(path='shot_map3d_shadow.png')
    pg.click('#m3Chips [data-k=shadow]'); pg.wait_for_timeout(300)
    M(pg, {'d': 20000, 'tilt': 0.9}); pg.wait_for_timeout(700)
    s = M(pg)
    check('zoomed all the way out: the whole map in one mesh, the map picture itself (no sharp patch)', s['at']['full'] and s['n'] <= 401 and s['det'] is None, (s['at'], s['det']))
    pg.screenshot(path='shot_map3d_lake.png')
    pg.click('#m3Close'); pg.wait_for_timeout(300)
    check('✕ closes it all (the copies gone too)', not M(pg)['open'] and not pg.is_visible('#m3View') and pg.locator('#m3Marks *').count() == 0)
    check('no page errors', not errs, errs)
    b.close()

    # the pieces and the land's heights can't be fetched (no coverage, never looked at): the map picture enlarged, flat land, nothing breaks
    b, ctx, pg, errs = new_page(p, geo=B3, name='Filip')
    ctx.route('**/tiles_v*/**', lambda r: r.abort()); ctx.route('**/land/**', lambda r: r.abort())
    pg.wait_for_timeout(2500)
    hold_map_btn(pg); pg.click('#mapTypePop .m3Opt'); pg.wait_for_timeout(2500)
    M(pg, {'d': 300}); pg.wait_for_timeout(1500)
    s = M(pg)
    check('no pieces to fetch: still drawn (the map picture enlarged), no errors', s['ready'] and s['det'] and s['det']['n'] == 0 and not errs, (s['det'], errs))
    M(pg, TOP); pg.wait_for_timeout(900)
    s = M(pg)
    check('no land heights to fetch: flat land, just over the water', not s['land'] and abs(s['hit']['y'] - 0.3) < 0.01 and not errs, (s['land'], s['hit'], errs))
    b.close()

    # the tracks and Fångster: today's track (on the phone) as a line in 3D, the lake's catches (the heatmap's data) as dots
    import datetime
    day = (datetime.datetime.now() - datetime.timedelta(hours=6)).strftime('%Y-%m-%d'); t0 = int(datetime.datetime.now().timestamp() * 1000) - 3600000
    segs = [[[B3[0] + i * 0.00005, B3[1] + i * 0.0001, t0 + i * 20000] for i in range(30)]]
    rows = [fakefb.api_row(t0 - 86400000 + i * 60000, 'regnaren1', 'Filip', ['abborre', 'gadda', 'gos'][i % 3], 40, B3[0] + i * 0.0001, B3[1]) for i in range(9)]
    b, ctx, pg, errs = new_page(p, geo=B3, name='Filip', cfg={'api': {'heatmap': rows}})
    ctx.add_init_script("if (!sessionStorage.getItem('seeded')){ sessionStorage.setItem('seeded', '1'); localStorage.setItem('ffmap_track_v1', %s); }" % json.dumps(json.dumps({'day': day, 'segs': segs})))
    pg.reload(); pg.wait_for_timeout(2500)
    hold_map_btn(pg); pg.click('#mapTypePop .m3Opt'); pg.wait_for_timeout(2500)
    s = M(pg)
    check("the tracks: today's track is a line in 3D too", s['trk'][0] and s['trk'][0][0] >= 60 and s['trk'][2] >= 1, s['trk'])
    check('Fångster off: no dots', s['fish'] == 0)
    pg.click('#m3Chips [data-k=fish]'); pg.wait_for_timeout(1500)
    check("Fångster: every catch on the lake a dot (the heatmap's data), remembered", M(pg)['fish'] == 9 and json.loads(pg.evaluate("localStorage.getItem('ffmap_3d_v1')"))['fish'] is True, M(pg)['fish'])
    pg.screenshot(path='shot_map3d_fish.png')
    check('no page errors', not errs, errs)
    b.close()

    # a big lake (its map picture is stored at half size and shown at twice that): far out the whole map is there with its
    # picture on -- it came out black (the texture was sized by the picture's size on the page), and there is no fog
    b, ctx, pg, errs = new_page(p, geo=(59.40, 17.58), name='Filip')
    logs = []; pg.on('console', lambda m: logs.append(m.text))
    pg.evaluate("localStorage.setItem('ffmap_lake_v1', 'malaren')"); pg.reload(); pg.wait_for_timeout(3500)
    hold_map_btn(pg); pg.click('#mapTypePop .m3Opt'); pg.wait_for_timeout(3500)
    M(pg, {'d': 15000, 'tilt': 0.6}); pg.wait_for_timeout(1500)
    s = M(pg)
    lum = ImageStat.Stat(Image.open(io.BytesIO(pg.screenshot())).convert('L').crop((40, 250, 350, 650))).mean[0]
    gl = [l for l in logs if 'GL_INVALID' in l]
    check('Mälaren far out: the whole map with its picture on (not black), no graphics errors', s['at']['full'] and lum > 40 and not gl, (s['at'], round(lum), gl[:2]))
    pg.screenshot(path='shot_map3d_malaren.png')
    M(pg, {'d': 3000, 'tilt': 1.2}); pg.wait_for_timeout(1500)
    s = M(pg)
    top = ImageStat.Stat(Image.open(io.BytesIO(pg.screenshot())).convert('L').crop((40, 330, 350, 420))).mean[0]
    check('...nearer and tilted: a fine mesh around the point, the rest of the lake still there behind it (no fog), the land with its heights', not s['at']['full'] and s['n'] <= 401 and s['land'] and top > 40, (s['at'], s['land'], round(top)))
    # water nobody has charted is a hole -- drawn at the surface it stood as big hills beside the charted bottom. A straight
    # edge of the chart is found in the files, apart from the app: a hole in 14 columns of cells, charted water deeper than
    # 3 m in the 8 east of them, in 25 rows. Seen from straight above, three.js is asked what is drawn across that edge
    mk = json.load(open('../lakes/malaren/lake.json', encoding='utf-8')); md = mk['depth']; ml = json.load(open('../lakes/malaren/land.json', encoding='utf-8'))
    dg = unpack(open('../docs/lakes/malaren/' + md['file']).read().strip(), md['w'] * md['h']).reshape(md['h'], md['w'])
    lg = unpack(open('../docs/' + ml['file']).read().strip(), ml['w'] * ml['h']).reshape(ml['h'], ml['w'])
    win = np.lib.stride_tricks.sliding_window_view
    void = win(lg == 252, (25, 14)).all((2, 3)); deep = win((dg < 251) & (dg * md['step'] > 3), (25, 8)).all((2, 3))
    j, i = (int(v) for v in np.argwhere(void[:, :deep.shape[1] - 14] & deep[:, 14:])[0])
    M(pg, {'px': (i + 14) / md['w'] * mk['geo']['imgW'], 'py': (j + 12.5) / md['h'] * mk['geo']['imgH'], 'd': 400, 'tilt': 0.05, 'az': 0}); pg.wait_for_timeout(1800)
    hits = [(dx, M(pg, {'at': [195 + dx, 422]})['hit']) for dx in (-180, -150, -40, -15, 0, 15, 40, 80, 120)]      # (a cell is 28 px here)
    px = Image.open(io.BytesIO(pg.screenshot())).convert('RGB').getpixel((195 - 150, 422))
    check("water nobody has charted is a hole: the bottom goes on a little way past the chart's edge at the depth it has there, then there is nothing -- no wall up to the surface",
          all(h is None for dx, h in hits if dx <= -150) and all(h and h['y'] < -3 for dx, h in hits if dx >= 40) and all(h is None or h['y'] < -3 for dx, h in hits),
          [(dx, h and round(h['y'], 1)) for dx, h in hits])
    check("...the water's surface lies over the hole all the same (Vatten on): dark blue, nothing under it", px[2] > px[0] + 25 and px[0] < 60, px)
    M(pg, {'d': 1500, 'tilt': 1.1}); pg.wait_for_timeout(1800)
    pg.screenshot(path='shot_map3d_hole.png')
    # ...and no pillars at a hole's ragged edge (Filip 2026-11-12: thin bits nobody had charted stood up to the surface from
    # 27 m down). A gap in the chart in deep water is found in the files -- the biggest with nothing shallower than 15 m
    # within 4 cells of it -- and three.js is asked what is drawn over it and 3 cells around it
    from scipy.ndimage import label, find_objects, binary_dilation
    lab, n = label(dg == 252, np.ones((3, 3))); gap = None
    for k, sl in enumerate(find_objects(lab), 1):
        box = (slice(max(0, sl[0].start - 5), sl[0].stop + 5), slice(max(0, sl[1].start - 5), sl[1].stop + 5)); m = lab[box] == k
        if m.sum() < 100 or (gap and m.sum() <= gap[0]): continue
        ring = dg[box][binary_dilation(m, np.ones((3, 3)), iterations=4) & (dg[box] < 251)] * md['step']
        if ring.size and ring.min() > 15 and not (dg[box] == 255).any(): gap = (m.sum(), sl)
    sl = gap[1]; cell = mk['geo']['metersPerPx'] * mk['geo']['fullW'] / md['w']
    M(pg, {'px': (sl[1].start + sl[1].stop) / 2 / md['w'] * mk['geo']['imgW'], 'py': (sl[0].start + sl[0].stop) / 2 / md['h'] * mk['geo']['imgH'], 'd': 600, 'tilt': 0.05, 'az': 0}); pg.wait_for_timeout(1800)
    k = cell / px_m(M(pg)['c']); hw = min(189, ((sl[1].stop - sl[1].start) / 2 + 3) * k); hh = min(240, ((sl[0].stop - sl[0].start) / 2 + 3) * k)      # (k: a cell's px on the screen)
    ys = pg.evaluate("(([hw, hh]) => { const o = []; for (let y = 422 - hh; y <= 422 + hh; y += 9) for (let x = 195 - hw; x <= 195 + hw; x += 9) { const h = window.__ffMap3d({at: [x, y]}).hit; o.push(h ? h.y : null); } return o; })", [hw, hh])
    high = sorted(v for v in ys if v is not None and v > -10)
    check("...and no pillars at a hole's ragged edge: around a gap in the chart in deep water, all that is drawn is far down",
          ys.count(None) > 20 and len(ys) - ys.count(None) > 100 and not high, (gap[0], len(ys), ys.count(None), high[-5:]))
    pg.screenshot(path='shot_map3d_gap.png')
    check('no page errors', not errs, errs)
    b.close()
print('\n%d/%d passed' % (sum(results), len(results)))
