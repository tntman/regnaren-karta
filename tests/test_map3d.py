# 3D-karta (js/73-map3d.js): in the map-style list (hold the map button), right after the map styles -> a full-screen
# view of its own: the bottom in 3D (three.js) with the map picture on it, the map's pins and boats copied on top.
# A drag turns it, the wheel (a pinch) zooms, zoomed in = a finer mesh; Vatten / Höjd are remembered; ✕ closes all of it.
import json, io, base64, sys
sys.path.insert(0, '../tools')
from land_height import unpack          # (the land file read here, apart from the app)
from PIL import Image, ImageChops, ImageStat
from playwright.sync_api import sync_playwright
from fakefb import new_page
results = []
def check(name, cond, info=''):
    results.append(bool(cond)); print(('PASS ' if cond else 'FAIL ') + name + ('  -- ' + str(info) if info != '' else ''))
B3 = (58.887269, 15.772629); B1 = (58.887421, 15.775569)
def M(pg, o=None): return pg.evaluate('window.__ffMap3d(%s)' % (json.dumps(o) if o else ''))
def hold_map_btn(pg):
    bb = pg.locator('#mapTypeBtn').bounding_box(); pg.mouse.move(bb['x'] + 20, bb['y'] + 20); pg.mouse.down(); pg.wait_for_timeout(700); pg.mouse.up(); pg.wait_for_timeout(300)

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
    check('"Till mig": your boat in the middle of the screen', abs(bb['x'] + bb['width'] / 2 - 195) < 3 and abs(bb['y'] + bb['height'] / 2 - 422) < 3, bb)
    c0 = M(pg)['c']
    pg.mouse.move(195, 300); pg.mouse.down(); pg.mouse.move(275, 340, steps=5); pg.mouse.up(); pg.wait_for_timeout(300)
    c1 = M(pg)['c']
    check('a drag: sideways turns it, up/down tilts it', c1['az'] != c0['az'] and c1['tilt'] != c0['tilt'] and c1['d'] == c0['d'], (c0, c1))
    pg.click('#m3North'); pg.wait_for_timeout(300)
    check('the north arrow: north up again', M(pg)['c']['az'] == 0)
    b0 = M(pg)['builds']; r0 = M(pg)['at']['R']
    pg.mouse.move(195, 300); pg.mouse.wheel(0, -900); pg.wait_for_timeout(700)
    s = M(pg)
    check('the wheel zooms in: a mesh for the smaller area, built once when it rests', s['c']['d'] < c1['d'] and s['at']['R'] < r0 and s['builds'] == b0 + 1 and s['n'] <= 401, (c1['d'], s['c']['d'], r0, s['at'], b0, s['builds']))
    # near: the picture is the zoom level's pieces put together (not the map picture enlarged) -- and they sit where the map picture says
    pg.wait_for_timeout(1500)
    z1 = M(pg)['det']['z']
    M(pg, {'d': 300}); pg.wait_for_timeout(1800)
    dt = M(pg, {'pic': True})['det']
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
    top = g[j, i] * ld['step']; TOP = {'px': (i + 5.5) / ld['w'] * lk['geo']['imgW'], 'py': (j + 5.5) / ld['h'] * lk['geo']['imgH'], 'd': 400, 'tilt': 0.05, 'az': 0}
    M(pg, TOP); pg.wait_for_timeout(900)
    s = M(pg)
    check('the land has its height (the land file read apart from the app says the same)', s['land'] and top > 20 and abs(s['hit']['y'] - top) < 3, (top, s['hit']))
    check('...whose heights they are is written in the controls', 'Höjddata' in pg.inner_text('#m3Src'), pg.inner_text('#m3Src'))
    pg.click('#m3Chips [data-k=water]'); pg.fill('#m3Ex', '6'); pg.dispatch_event('#m3Ex', 'input'); pg.wait_for_timeout(400)
    sv = json.loads(pg.evaluate("localStorage.getItem('ffmap_3d_v1')"))
    check('Vatten off and Höjd × 6: shown and remembered', sv == {'ex': 6, 'water': False} and pg.inner_text('#m3ExVal') == '× 6' and not pg.evaluate("document.querySelector('#m3Chips [data-k=water]').classList.contains('on')"), sv)
    pg.screenshot(path='shot_map3d_dry.png')
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
print('\n%d/%d passed' % (sum(results), len(results)))
