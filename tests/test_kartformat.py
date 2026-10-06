# The new map format (tools/PLAN_KARTFORMAT.md): every detail piece = the style's base (colours) + the level's
# lines on top (shared by the styles; Bottenhårdhet has its own light ones). Above baseMax (zoom 17) there are
# only lines -- the z17 base enlarged under them -- so every style gets zoom 18.
from playwright.sync_api import sync_playwright
from fakefb import new_page
import json, re
LK = json.load(open('../lakes/regnaren/lake.json', encoding='utf-8'))
results = []
def check(name, cond, info=''):
    results.append(bool(cond)); print(('PASS ' if cond else 'FAIL ') + name + ('  -- ' + str(info) if info != '' else ''))
D = LK['detail']
check('lake.json: bases + lines, baseMax 17, no Flygfoto + linjer', D.get('lines') and D['baseMax'] == 17 and
      [L['base'] for L in D['levels']] == [True, True, True, False] and 's5' not in [s['id'] for s in LK['styles']] and
      [s.get('lines') for s in LK['styles'] if s['id'] == 'c1'] == ['lines_w'], (D.get('lines'), [s['id'] for s in LK['styles']]))

def pieces(pg):
    return pg.eval_on_selector_all('#detailLayer img', 'e=>e.filter(x=>x.style.zIndex>=2).map(x=>[x.getAttribute("src"), x.naturalWidth, x.classList.contains("ok"), +x.style.zIndex])')
def zoom_to(pg, level):
    pg.mouse.move(195, 422)
    for i in range(30):
        lv = int(pg.inner_text('#zoomLabel').split('L')[-1])
        if lv == level: break
        pg.mouse.wheel(0, -120 if lv < level else 120); pg.wait_for_timeout(120)
    pg.wait_for_timeout(1800)

with sync_playwright() as p:
    b, ctx, pg, errs = new_page(p, geo=(58.8868, 15.7776), cfg={}, name='Filip')
    pg.wait_for_timeout(1500)
    zoom_to(pg, 16)
    t = pieces(pg)
    base = [x for x in t if re.search(r'tiles_v[56]/z16/s1/\d+_\d+\.webp$', x[0])]
    lines = [x for x in t if re.search(r'tiles_v[56]/z16/lines/\d+_\d+\.webp$', x[0])]
    check('zoom 16: Djupfärger base pieces + zoom-16 lines on top, all loaded', base and lines and len(base) == len(lines) and
          all(x[1] == 512 + 2 * D["pad"] and x[2] for x in base + lines) and all(x[3] == 2 for x in base) and all(x[3] == 3 for x in lines), t[:6])
    zoom_to(pg, 18)
    t = pieces(pg)
    base = [x for x in t if '/z17/s1/' in x[0]]; lines = [x for x in t if '/z18/lines/' in x[0]]
    check('zoom 18: the z17 base (enlarged) under the zoom-18 lines', base and lines and len(t) == len(base) + len(lines) and
          all(x[2] for x in t), t[:6])
    # the pieces sit exactly (no 1 px stretch): a piece's inside ends where the next one's starts, for lines and bases
    geo = pg.evaluate("""Array.from(document.querySelectorAll('#detailLayer img')).filter(x => x.style.zIndex >= 2).map(x => {
        var m = /translate\\(([-\\d.e]+)px, ?([-\\d.e]+)px\\)/.exec(x.style.transform), w = parseFloat(x.style.width);
        var cr = /(\\d+)_(\\d+)\\.webp/.exec(x.getAttribute('src')), k = +cr[1], rr = +cr[2], z = +/\\/z(\\d+)\\//.exec(x.getAttribute('src'))[1];
        return [z, x.getAttribute('src').indexOf('/lines') > 0, k, +m[1], w, rr]; })""")
    gaps = []
    for a in geo:
        for b2 in geo:
            if a[0] == b2[0] and a[1] == b2[1] and a[5] == b2[5] and b2[2] == a[2] + 1:
                inner = a[4] * 512 / (512 + 2 * D['pad'])            # the inside of a piece on screen
                gaps.append(round(b2[3] - a[3] - inner, 3))
    check('neighbouring pieces meet exactly (no stretch, no gap)', gaps and all(abs(g) < 0.01 for g in gaps), gaps[:8])
    pg.screenshot(path='shot_kartformat_z18.png')
    # a style that had no zoom 18 before (only s1/g1 did): now it has
    pg.evaluate("document.querySelector('#mapTypeBtn')")
    pg.click('#menuBtn'); pg.click('#menuItemSettings'); pg.wait_for_timeout(200)
    pg.click('#mapStyleList .styleOpt[data-style="s3"]'); pg.wait_for_timeout(1200)
    pg.click('#settingsBackBtn'); pg.wait_for_timeout(1800)
    t = pieces(pg)
    check('Sjökort at zoom 18: its own z17 base + the same zoom-18 lines', t and any('/z17/s3/' in x[0] for x in t) and
          any('/z18/lines/' in x[0] for x in t) and not any('/s1/' in x[0] for x in t) and all(x[2] for x in t), t[:6])
    pg.click('#menuBtn'); pg.click('#menuItemSettings'); pg.wait_for_timeout(200)
    pg.click('#mapStyleList .styleOpt[data-style="c1"]'); pg.wait_for_timeout(1200)
    pg.click('#settingsBackBtn'); pg.wait_for_timeout(1800)
    t = pieces(pg)
    check('Bottenhårdhet: the light lines (lines_w)', t and any('/z18/lines_w/' in x[0] for x in t) and
          not any('/z18/lines/' in x[0] for x in t) and all(x[2] for x in t), t[:6])
    pg.screenshot(path='shot_kartformat_c1.png')
    check('no page errors', not errs, errs)
    b.close()
print('\n%d/%d passed' % (sum(results), len(results)))
