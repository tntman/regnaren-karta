# Several lakes: lake menu, switching (page reload), per-lake map/depth/waypoints/boats,
# detail tiles when zoomed in, and the lake staying chosen through a rotation reload.
from playwright.sync_api import sync_playwright
import fakefb, json, re, math
from fakefb import new_page
VAGS_W = json.load(open('../lakes/vagsfjarden/lake.json', encoding='utf-8'))['geo']['imgW']
results = []
def check(name, cond, info=''):
    results.append(bool(cond)); print(('PASS ' if cond else 'FAIL ') + name + ('  -- ' + str(info) if info != '' else ''))

REG = (58.88951, 15.77759)
# Genesis depth labels on flat bottom (lakes/vagsfjarden/raw/depth_labels.json): lat, lon, depth
VAGS_POINTS = [(62.918945, 18.266337, 18.0), (62.922594, 18.248602, 33.0), (62.921788, 18.259352, 37.0)]
VAGS = VAGS_POINTS[0][:2]
# ... and on Sjösjön (lakes/sjosjon/raw/depth_labels.json)
SJO_POINTS = [(62.571371, 17.816885, 6.5), (62.575661, 17.817024, 10.3), (62.569854, 17.813666, 13.5)]
cfg = {
  'waypoints': [
    {'lat': 58.8898, 'lon': 15.7784, 'name': 'Regnarplatsen', 'uid': 'kalle', 'by': 'Calle'},
    {'lat': VAGS[0] + 0.001, 'lon': VAGS[1], 'name': 'Vågsgrundet', 'uid': 'kalle', 'by': 'Calle', 'lake': 'vagsfjarden'}],
  'positions': [
    {'uid': 'kalle', 'name': 'Calle', 'lat': 58.8905, 'lon': 15.779, 'ageMin': 1},
    {'uid': 'pia', 'name': 'Pia', 'lat': VAGS[0] + 0.002, 'lon': VAGS[1], 'ageMin': 1, 'lake': 'vagsfjarden'}],
  # Regnaren's admin chose 30 s; Vågsfjärden has no setting -> 20 s there
  'configByLake': {'regnaren': {'posIntervalS': 30}}}

def pos_interval(pg):
    return pg.evaluate("localStorage.getItem('ffmap_pos_interval_s_v1') + '/' + localStorage.getItem('lake_vagsfjarden_pos_interval_s_v1')")

def titles(pg):
    pg.click('#menuBtn'); pg.click('#menuItemLog'); pg.wait_for_timeout(300)
    t = pg.eval_on_selector_all('#logList .logTitle', 'e=>e.map(x=>x.textContent)')
    pg.click('#logBackBtn'); pg.wait_for_timeout(200)
    return t

with sync_playwright() as p:
    b, ctx, pg, errs = new_page(p, geo=REG, cfg=cfg, name='Filip')
    src = lambda: pg.get_attribute('#mapImg', 'src')
    lakes = pg.eval_on_selector_all('#lakeList .menuItem', 'e=>e.map(x=>x.textContent.trim())')
    check('lake menu lists all lakes, Regnaren first', lakes == ['Regnaren', 'Mälaren', 'Sibbofjärden', 'Sjösjön', 'Vågsfjärden', 'Östra Vitten'], lakes)
    pg.wait_for_function("(document.getElementById('mapImg').getAttribute('src') || '').length > 0", timeout=15000)
    check('starts on Regnaren (as before)', src() == 'lakes/regnaren/map_v5_s1.jpg', src())
    check("Regnaren shows only Regnaren's spot", titles(pg) == ['Regnarplatsen'])
    check("Regnaren uses its own position interval (30 s)", pos_interval(pg) == '30/null', pos_interval(pg))

    # ---- switch to Vågsfjärden
    ctx.set_geolocation({'latitude': VAGS[0], 'longitude': VAGS[1], 'accuracy': 5})
    pg.click('#menuBtn'); pg.click('#lakeList .menuItem[data-lake-id="vagsfjarden"]')
    pg.wait_for_load_state('load'); pg.wait_for_timeout(1500)
    check('switching reloads with the Vågsfjärden map', src() == 'lakes/vagsfjarden/map_v4_s1.jpg' and pg.eval_on_selector('#mapImg', 'e=>e.naturalWidth') == VAGS_W, src())
    check('name kept (no login again)', not pg.evaluate("[].some.call(document.querySelectorAll('.show'), function(e){ return /name/i.test(e.id); })"),
          pg.evaluate("[].map.call(document.querySelectorAll('.show'), function(e){ return e.id; })"))
    check("only Vågsfjärden's spot", titles(pg) == ['Vågsgrundet'])
    check("Vågsfjärden without a setting: the default 20 s (not Regnaren's 30)", pos_interval(pg) == '30/20', pos_interval(pg))
    boats = pg.eval_on_selector_all('#boatsLayer .boatPip', 'e=>e.map(x=>x.textContent)')
    check("only the boat on Vågsfjärden (Pia), not Calle on Regnaren", any('Pia' in x for x in boats) and not any('Calle' in x for x in boats), boats)
    check('weather card named after the lake', pg.inner_text('#wxTitle') == 'Väder vid Vågsfjärden')
    check('title = the lake', pg.inner_text('#lakeTitle') == 'Vågsfjärden', pg.inner_text('#lakeTitle'))
    ticks = pg.eval_on_selector_all('#legendTicks span', 'e=>e.map(x=>x.textContent)')
    check("legend runs to the lake's own max depth (Vågsfjärden ~37 m -> 0 / 20 / 40 m)", ticks == ['0 m', '20 m', '40 m'], ticks)
    bar = pg.eval_on_selector('#legend .bar', 'e=>e.style.background')
    # the colours follow the fixed scale: 10 m (blue #1f4fd6) sits a quarter of the way along 0-40 m
    check('legend colours = the fixed scale for those depths (10 m blue at 25 %)', 'rgb(31, 79, 214) 25%' in bar, bar[:200])
    n_styles = pg.eval_on_selector_all('#mapStyleList .styleOpt', 'e=>e.length')
    check('7 map styles (incl. C-MAP original, vegetation, hardness; no Natt, no Flygfoto + linjer)', n_styles == 7, n_styles)
    w = [x for x in pg.evaluate('window.__posWrites') if x['id'] == 'filip']
    check('your position is shared tagged with the lake', w and w[-1]['lake'] == 'vagsfjarden', w[-1:] if w else w)
    pg.screenshot(path='shot_lake_vags.png')

    # ---- depth: under you, compared with Genesis' own depth labels
    for la, lo, want in VAGS_POINTS:
        ctx.set_geolocation({'latitude': la, 'longitude': lo, 'accuracy': 5}); pg.wait_for_timeout(1500)
        got = pg.inner_text('#depthVal')
        v = float(got.replace(',', '.')) if re.match(r'^[0-9]+,?[0-9]*$', got) else None
        check('depth at a %g m label: %s m' % (want, got), v is not None and abs(v - want) <= 1.0, got)

    # ---- zoom in: sharper pieces appear, only for what's on screen
    zf = lambda s: float(s.split()[0].replace(',', '.'))          # "15,3 × L 14"
    lv = lambda s: int(s.split('L ')[-1])
    rnd = lambda x: int(math.floor(x + 0.5))
    z_start = pg.inner_text('#zoomLabel')
    check('zoom + level shown next to the scale; level = the zoom, rounded', '×' in z_start and lv(z_start) == min(18, max(14, rnd(zf(z_start)))), z_start)
    # all the way out: the zoom-14 picture only (12-13 are never used)
    pg.mouse.move(195, 422)
    for i in range(12):
        pg.mouse.wheel(0, 400); pg.wait_for_timeout(60)
    pg.wait_for_timeout(800)
    z0 = pg.inner_text('#zoomLabel')
    check('zoomed all the way out: lager 14, no pieces on top', z0.endswith('L 14') and zf(z0) < 14 and pg.eval_on_selector_all('#detailLayer img', 'e=>e.length') == 0, z0)
    pg.mouse.move(195, 422)
    for i in range(12):
        pg.mouse.wheel(0, -400); pg.wait_for_timeout(60)
    pg.wait_for_timeout(1500)
    tiles = pg.eval_on_selector_all('#detailLayer img', 'e=>e.map(x=>[x.getAttribute("src"), x.naturalWidth, x.classList.contains("ok")])')
    check('zoomed in: full-resolution pieces on screen', 0 < len(tiles) <= 24 and all(re.search(r'tiles_v4/z1[5-8]/(s1|lines)/', t[0]) and t[1] == 528 and t[2] for t in tiles), tiles)
    z1 = pg.inner_text('#zoomLabel')
    check('zoom level goes up, and the level (lines) with it, like Genesis', zf(z1) > zf(z0) + 1 and lv(z1) == min(18, rnd(zf(z1))) and all('/z%d/' % lv(z1) in t[0] for t in tiles if '/lines/' in t[0]) and any('/lines/' in t[0] for t in tiles), (z0, z1))
    pg.screenshot(path='shot_lake_detail.png')
    pg.click('#menuBtn'); pg.click('#menuItemSettings'); pg.wait_for_timeout(200)
    pg.click('#mapStyleList .styleOpt[data-style="g1"]'); pg.wait_for_timeout(1200)
    pg.click('#settingsBackBtn'); pg.wait_for_timeout(1200)
    tiles = pg.eval_on_selector_all('#detailLayer img', 'e=>e.map(x=>x.getAttribute("src"))')
    check('another style -> its own pieces', tiles and all('/g1/' in t or '/lines/' in t for t in tiles) and any('/g1/' in t for t in tiles), tiles)
    check('style choice is per lake', src() == 'lakes/vagsfjarden/map_v4_g1.jpg')

    # ---- a reload (rotation) keeps the lake; then back to Regnaren
    pg.reload(); pg.wait_for_timeout(1500)
    check('after a reload: still Vågsfjärden', src() == 'lakes/vagsfjarden/map_v4_g1.jpg', src())
    pg.click('#menuBtn'); pg.click('#lakeList .menuItem[data-lake-id="regnaren"]')
    pg.wait_for_load_state('load'); pg.wait_for_timeout(1500)
    check("back on Regnaren: its map, its style and its spot", src() == 'lakes/regnaren/map_v5_s1.jpg' and titles(pg) == ['Regnarplatsen'], src())
    # the same max zoom on every lake: Regnaren too goes to 18,6 and uses its zoom-18 level
    pg.mouse.move(195, 422)
    for i in range(20):
        pg.mouse.wheel(0, -500); pg.wait_for_timeout(50)
    pg.wait_for_timeout(1500)
    zmax = pg.inner_text('#zoomLabel')
    check('Regnaren: max zoom 18,6 and lager 18 (same as every lake)', abs(zf(zmax) - 18.6) < 0.05 and lv(zmax) == 18, zmax)
    check('no page errors', not errs, errs)
    b.close()

    # ---- ?lake= in the address picks a lake directly
    b, ctx, pg, errs = new_page(p, geo=REG, cfg=cfg, name='Filip')
    pg.goto('http://localhost:8899/index.html?lake=vagsfjarden'); pg.wait_for_timeout(1200)
    check('?lake=vagsfjarden opens that lake', pg.get_attribute('#mapImg', 'src') == 'lakes/vagsfjarden/map_v4_s1.jpg')
    pg.goto('http://localhost:8899/index.html?lake=nonsense'); pg.wait_for_timeout(1200)
    check('an unknown lake falls back to the remembered one', pg.get_attribute('#mapImg', 'src') == 'lakes/vagsfjarden/map_v4_s1.jpg')
    b.close()

    # ---- Sjösjön: opens, and the depth matches Genesis' own labels
    b, ctx, pg, errs = new_page(p, geo=SJO_POINTS[0][:2], cfg=cfg, name='Filip')
    pg.goto('http://localhost:8899/index.html?lake=sjosjon'); pg.wait_for_timeout(1500)
    check('?lake=sjosjon opens Sjösjön', pg.get_attribute('#mapImg', 'src') == 'lakes/sjosjon/map_v2_s1.jpg' and pg.inner_text('#lakeTitle') == 'Sjösjön', pg.get_attribute('#mapImg', 'src'))
    for la, lo, want in SJO_POINTS:
        ctx.set_geolocation({'latitude': la, 'longitude': lo, 'accuracy': 5}); pg.wait_for_timeout(1500)
        got = pg.inner_text('#depthVal')
        v = float(got.replace(',', '.')) if re.match(r'^[0-9]+,?[0-9]*$', got) else None
        check('Sjösjön: depth at a %g m label: %s m' % (want, got), v is not None and abs(v - want) <= 1.0, got)
    ticks = pg.eval_on_selector_all('#legendTicks span', 'e=>e.map(x=>x.textContent)')
    check('Sjösjön legend: 0 / 7 / 14 m (max 13,5 m)', ticks == ['0 m', '7 m', '14 m'], ticks)
    check('Sjösjön: no page errors', not errs, errs)
    b.close()
    # ---- Sibbofjärden: opens, and the depth matches Genesis' own labels (lakes/sibbo/raw/depth_labels.json #20, #41, #53)
    SIB_POINTS = [(58.777728, 17.29557, 4.0), (58.786086, 17.307876, 8.0), (58.779502, 17.311438, 10.5)]
    b, ctx, pg, errs = new_page(p, geo=SIB_POINTS[0][:2], cfg=cfg, name='Filip')
    pg.goto('http://localhost:8899/index.html?lake=sibbo'); pg.wait_for_timeout(1500)
    check('?lake=sibbo opens Sibbofjärden', pg.get_attribute('#mapImg', 'src') == 'lakes/sibbo/map_v2_s1.jpg' and pg.inner_text('#lakeTitle') == 'Sibbofjärden', pg.get_attribute('#mapImg', 'src'))
    for la, lo, want in SIB_POINTS:
        ctx.set_geolocation({'latitude': la, 'longitude': lo, 'accuracy': 5}); pg.wait_for_timeout(1500)
        got = pg.inner_text('#depthVal')
        v = float(got.replace(',', '.')) if re.match(r'^[0-9]+,?[0-9]*$', got) else None
        check('Sibbofjärden: depth at a %g m label: %s m' % (want, got), v is not None and abs(v - want) <= 1.0, got)
    ticks = pg.eval_on_selector_all('#legendTicks span', 'e=>e.map(x=>x.textContent)')
    check('Sibbofjärden legend: 0 / 4 / 8 / 12 m (max 11,2 m)', ticks == ['0 m', '4 m', '8 m', '12 m'], ticks)
    check('Sibbofjärden: no page errors', not errs, errs)
    b.close()
    # ---- Mälaren (a grid 3x Regnaren's): Kartanalys + zooming in and out stays within memory -- it used ~400 MB and
    # the iPhone closed the page (2026-10-07); now ~160 MB
    b, ctx, pg, errs = new_page(p, cfg=cfg, name='Filip')
    pg.goto('http://localhost:8899/index.html?lake=malaren'); pg.wait_for_timeout(3000)
    pg.click('#anBtn'); pg.wait_for_timeout(1000); pg.click('#anChips button[data-m="depth"]'); pg.wait_for_timeout(5000); pg.click('#anClose'); pg.wait_for_timeout(500)
    peak = 0
    for d in [-300] * 10 + [300] * 10:
        pg.mouse.move(195, 400); pg.mouse.wheel(0, d); pg.wait_for_timeout(300)
        peak = max(peak, pg.evaluate('performance.memory.usedJSHeapSize') / 1e6)
    check('Mälaren: Kartanalys Djup, zoom in and out -- under 260 MB (was ~400: the phone closed the page)', 0 < peak < 260 and pg.evaluate('window.__ffAnalysis().ready'), round(peak))
    check('Mälaren: no page errors', not errs, errs)
    b.close()
print('\n%d/%d passed' % (sum(results), len(results)))
