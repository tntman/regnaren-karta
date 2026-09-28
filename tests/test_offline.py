# "Ladda ner sjön för offline": the four quick styles, all zoom levels, into a cache of
# its own; pause / go on; the map then works with NO network; "Ta bort" removes it.
from playwright.sync_api import sync_playwright
import fakefb, re
from fakefb import new_page
results = []
def check(name, cond, info=''):
    results.append(bool(cond)); print(('PASS ' if cond else 'FAIL ') + name + ('  -- ' + str(info) if info != '' else ''))
REG = (58.88951, 15.77759)

with sync_playwright() as p:
    b, ctx, pg, errs = new_page(p, geo=REG, cfg={}, name='Filip', sw=True)
    pg.wait_for_timeout(1500)
    pg.click('#menuBtn'); pg.click('#menuItemSettings'); pg.wait_for_timeout(300)
    check('Settings: "Ladda ner Regnaren för offline"', pg.inner_text('#offTitle') == 'Ladda ner Regnaren för offline' and pg.inner_text('#offBtn') == 'Ladda ner', pg.inner_text('#offStatus'))
    n = pg.evaluate("(function(){ return document.getElementById('offStatus').textContent; })()")
    total = int(re.match(r'(\d+) kartbitar', n).group(1))
    check('about 1 200 pieces (4 styles, zoom 14-18)', 900 < total < 1600, n)
    # start, pause after a moment
    pg.click('#offBtn'); pg.wait_for_timeout(700)
    check('downloading: progress bar + "Laddar ner… x av y"', pg.is_visible('#offBar') and pg.inner_text('#offStatus').startswith('Laddar ner'), pg.inner_text('#offStatus'))
    pg.click('#offBtn'); pg.wait_for_timeout(1500)
    st = pg.inner_text('#offStatus')
    check('pause -> "Pausad · x %"', st.startswith('Pausad') and pg.inner_text('#offBtn') == 'Fortsätt', st)
    # go on until done
    pg.click('#offBtn')
    pg.wait_for_function("document.getElementById('offStatus').textContent.indexOf('Klar') === 0", timeout=120000)
    st = pg.inner_text('#offStatus')
    check('done: "Klar · x MB sparat"', st.startswith('Klar') and pg.inner_text('#offBtn') == 'Ta bort', st)
    cached = pg.evaluate("caches.keys().then(ks => Promise.all(ks.filter(k => k.indexOf('ffmap-offline-regnaren-') === 0).map(k => caches.open(k).then(c => c.keys().then(r => r.length)))))")
    check('all pieces in the offline cache', cached and cached[0] >= total, (cached, total))
    # the map with NO network: zoomed in, the pieces come from the phone
    pg.click('#settingsBackBtn'); pg.wait_for_timeout(300)
    pg.evaluate("navigator.serviceWorker.ready"); pg.wait_for_timeout(1500)
    ctx.set_offline(True)
    pg.reload(); pg.wait_for_timeout(2500)
    pg.mouse.move(195, 422)
    for i in range(10):
        pg.mouse.wheel(0, -400); pg.wait_for_timeout(60)
    pg.wait_for_timeout(2000)
    tiles = pg.eval_on_selector_all('#detailLayer img', 'e=>e.map(x=>[x.naturalWidth, x.classList.contains("ok")])')
    check('no network: map + zoomed-in pieces still show', pg.eval_on_selector('#mapImg', 'e=>e.naturalWidth') > 1000 and tiles and all(t[0] == 512 and t[1] for t in tiles), tiles[:4])
    ctx.set_offline(False)
    # remove
    pg.click('#menuBtn'); pg.click('#menuItemSettings'); pg.wait_for_timeout(300)
    pg.click('#offBtn'); pg.wait_for_timeout(800)
    left = pg.evaluate("caches.keys().then(ks => ks.filter(k => k.indexOf('ffmap-offline-') === 0).length)")
    check('"Ta bort": the offline copy is gone, button back to "Ladda ner"', left == 0 and pg.inner_text('#offBtn') == 'Ladda ner', left)
    check('no page errors', not [e for e in errs if 'firebase' not in e.lower() and 'modularAPIs' not in e], errs)
    b.close()
print('\n%d/%d passed' % (sum(results), len(results)))
