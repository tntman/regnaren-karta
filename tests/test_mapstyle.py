from playwright.sync_api import sync_playwright
from fakefb import new_page
import json
REG_W = json.load(open('../lakes/regnaren/lake.json', encoding='utf-8'))['geo']['imgW']
results = []
def check(name, cond, info=''):
    results.append(bool(cond)); print(('PASS ' if cond else 'FAIL ') + name + ('  -- ' + str(info) if info != '' else ''))
with sync_playwright() as p:
    b, ctx, pg, errs = new_page(p, geo=(58.8868, 15.7776), cfg={}, name='Filip')
    pg.wait_for_timeout(1500)
    src = lambda: pg.eval_on_selector('#mapImg', 'e=>e.getAttribute("src")')
    check('default style: the zoom-14 map loaded', src() == 'lakes/regnaren/map_v4_s1.jpg' and pg.eval_on_selector('#mapImg', 'e=>e.naturalWidth') == REG_W)
    pz = pg.evaluate("fetch('index.html').then(r => r.text()).then(t => t.length)")   # (the file: the DOM also holds the pictures of the name picker)
    check('page itself is small now (map not inside it)', pz < 1000000, pz)   # (design A added ~15 kB of CSS, the start picture's logo ~27 kB)
    pg.click('#menuBtn'); pg.click('#menuItemSettings'); pg.wait_for_timeout(200)
    n = pg.evaluate("document.querySelectorAll('#mapStyleList .styleOpt').length")
    check('Settings lists 8 styles with previews (no Natt)', n == 8 and pg.evaluate("Array.from(document.querySelectorAll('#mapStyleList img')).every(i => i.naturalWidth > 0)"))
    pg.eval_on_selector('#mapStyleList', 'e=>e.scrollIntoView({block:"start"})'); pg.wait_for_timeout(150)
    pg.screenshot(path='mapstyle_settings.png')
    pg.click('.styleOpt[data-style="s3"]'); pg.wait_for_timeout(1200)
    check('choose Sjökort -> map_v1_s3.jpg + legend colours follow', src() == 'lakes/regnaren/map_v4_s3.jpg' and 'rgb(223, 243, 251)' in pg.eval_on_selector('#legend .bar', 'e=>e.style.background'))
    pg.click('.styleOpt[data-style="s5"]'); pg.wait_for_timeout(1200)
    check('Flygfoto + linjer -> no colour bar, "Djupkurvor var 1 m"', src() == 'lakes/regnaren/map_v4_s5.jpg' and pg.eval_on_selector('#legend', 'e=>e.classList.contains("noBar")'))
    # like having no coverage the first time: the style's picture can't be fetched
    # (blocked in this browser only -- the file stays, so tests can run side by side)
    pg.route('**/map_v*_s6.jpg', lambda r: r.abort())
    pg.click('.styleOpt[data-style="s6"]'); pg.wait_for_timeout(1500)
    pg.unroute('**/map_v*_s6.jpg')
    check('a style that cannot load (no coverage): old map kept + message', src() == 'lakes/regnaren/map_v4_s5.jpg' and pg.is_visible('#mapStyleMsg'), (src(), pg.inner_text('#mapStyleMsg'), pg.evaluate('navigator.onLine')))
    pg.click('.styleOpt[data-style="s3"]'); pg.wait_for_timeout(800)
    check('an already used style switches back instantly', src() == 'lakes/regnaren/map_v4_s3.jpg')
    pg.click('.styleOpt[data-style="s2"]'); pg.wait_for_timeout(1200)
    pg.reload(); pg.wait_for_timeout(1800)
    check('choice remembered after reload/rotation', src() == 'lakes/regnaren/map_v4_s2.jpg')
    pg.click('#settingsBackBtn') if pg.is_visible('#settingsBackBtn') else None
    pg.screenshot(path='mapstyle_s2_map.png')
    check('no page errors', not errs, errs)
    b.close()
print('\n%d/%d passed' % (sum(results), len(results)))
