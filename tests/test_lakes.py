# Several lakes: lake menu, switching (page reload), per-lake map/depth/waypoints/boats,
# detail tiles when zoomed in, and the lake staying chosen through a rotation reload.
from playwright.sync_api import sync_playwright
import fakefb, json, re
from fakefb import new_page
results = []
def check(name, cond, info=''):
    results.append(bool(cond)); print(('PASS ' if cond else 'FAIL ') + name + ('  -- ' + str(info) if info != '' else ''))

REG = (58.88951, 15.77759)
# Genesis depth labels on flat bottom (lakes/vagsfjarden/raw/depth_labels.json): lat, lon, depth
VAGS_POINTS = [(62.918945, 18.266337, 18.0), (62.922594, 18.248602, 33.0), (62.921788, 18.259352, 37.0)]
VAGS = VAGS_POINTS[0][:2]
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
    check('lake menu lists both lakes, Regnaren first', lakes == ['Regnaren', 'Vågsfjärden'], lakes)
    check('starts on Regnaren (as before)', src() == 'lakes/regnaren/map_v2_s1.jpg')
    check("Regnaren shows only Regnaren's spot", titles(pg) == ['Regnarplatsen'])
    check("Regnaren uses its own position interval (30 s)", pos_interval(pg) == '30/null', pos_interval(pg))

    # ---- switch to Vågsfjärden
    ctx.set_geolocation({'latitude': VAGS[0], 'longitude': VAGS[1], 'accuracy': 5})
    pg.click('#menuBtn'); pg.click('#lakeList .menuItem[data-lake-id="vagsfjarden"]')
    pg.wait_for_load_state('load'); pg.wait_for_timeout(1500)
    check('switching reloads with the Vågsfjärden map', src() == 'lakes/vagsfjarden/map_v1_s1.jpg' and pg.eval_on_selector('#mapImg', 'e=>e.naturalWidth') == 2786, src())
    check('name kept (no login again)', not pg.evaluate("[].some.call(document.querySelectorAll('.show'), function(e){ return /name/i.test(e.id); })"),
          pg.evaluate("[].map.call(document.querySelectorAll('.show'), function(e){ return e.id; })"))
    check("only Vågsfjärden's spot", titles(pg) == ['Vågsgrundet'])
    check("Vågsfjärden without a setting: the default 20 s (not Regnaren's 30)", pos_interval(pg) == '30/20', pos_interval(pg))
    boats = pg.eval_on_selector_all('#boatsLayer .boatPip', 'e=>e.map(x=>x.textContent)')
    check("only the boat on Vågsfjärden (Pia), not Calle on Regnaren", any('Pia' in x for x in boats) and not any('Calle' in x for x in boats), boats)
    check('weather card named after the lake', pg.inner_text('#wxTitle') == 'Väder vid Vågsfjärden')
    check('title = the lake', pg.inner_text('#lakeTitle') == 'VÅGSFJÄRDEN', pg.inner_text('#lakeTitle'))
    ticks = pg.eval_on_selector_all('#legendTicks span', 'e=>e.map(x=>x.textContent)')
    check('depth scale 0-40 m', ticks == ['0 m', '20 m', '40 m'], ticks)
    n_styles = pg.eval_on_selector_all('#mapStyleList .styleOpt', 'e=>e.length')
    check('9 map styles (incl. C-MAP original, vegetation, hardness)', n_styles == 9, n_styles)
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
    check('no detail pieces at the normal zoom', pg.eval_on_selector_all('#detailLayer img', 'e=>e.length') == 0)
    pg.mouse.move(195, 422)
    for i in range(12):
        pg.mouse.wheel(0, -400); pg.wait_for_timeout(60)
    pg.wait_for_timeout(1500)
    tiles = pg.eval_on_selector_all('#detailLayer img', 'e=>e.map(x=>[x.getAttribute("src"), x.naturalWidth, x.classList.contains("ok")])')
    check('zoomed in: full-resolution pieces on screen', 0 < len(tiles) <= 12 and all('tiles_v1/s1/' in t[0] and t[1] == 512 and t[2] for t in tiles), tiles)
    pg.screenshot(path='shot_lake_detail.png')
    pg.click('#menuBtn'); pg.click('#menuItemSettings'); pg.wait_for_timeout(200)
    pg.click('#mapStyleList .styleOpt[data-style="g1"]'); pg.wait_for_timeout(1200)
    pg.click('#settingsBackBtn'); pg.wait_for_timeout(1200)
    tiles = pg.eval_on_selector_all('#detailLayer img', 'e=>e.map(x=>x.getAttribute("src"))')
    check('another style -> its own pieces', tiles and all('tiles_v1/g1/' in t for t in tiles), tiles)
    check('style choice is per lake', src() == 'lakes/vagsfjarden/map_v1_g1.jpg')

    # ---- a reload (rotation) keeps the lake; then back to Regnaren
    pg.reload(); pg.wait_for_timeout(1500)
    check('after a reload: still Vågsfjärden', src() == 'lakes/vagsfjarden/map_v1_g1.jpg', src())
    pg.click('#menuBtn'); pg.click('#lakeList .menuItem[data-lake-id="regnaren"]')
    pg.wait_for_load_state('load'); pg.wait_for_timeout(1500)
    check("back on Regnaren: its map, its style and its spot", src() == 'lakes/regnaren/map_v2_s1.jpg' and titles(pg) == ['Regnarplatsen'], src())
    check('no page errors', not errs, errs)
    b.close()

    # ---- ?lake= in the address picks a lake directly
    b, ctx, pg, errs = new_page(p, geo=REG, cfg=cfg, name='Filip')
    pg.goto('http://localhost:8899/index.html?lake=vagsfjarden'); pg.wait_for_timeout(1200)
    check('?lake=vagsfjarden opens that lake', pg.get_attribute('#mapImg', 'src') == 'lakes/vagsfjarden/map_v1_s1.jpg')
    pg.goto('http://localhost:8899/index.html?lake=nonsense'); pg.wait_for_timeout(1200)
    check('an unknown lake falls back to the remembered one', pg.get_attribute('#mapImg', 'src') == 'lakes/vagsfjarden/map_v1_s1.jpg')
    b.close()
print('\n%d/%d passed' % (sum(results), len(results)))
