# Kartanalys ("Hitta ställen"): the button bottom right (where "uppdatera" was) opens one
# panel with every map analysis -- depth range, steep edges, tops & holes, vegetation edge,
# hard bottom, wind edge, "like my spot", and presets (Abborre/Gädda/Gös). What matches is
# lit, the rest toned down; "Kartanalys" in Filter shows/hides it; remembered per lake.
from playwright.sync_api import sync_playwright
import fakefb, json
from fakefb import new_page
import test_weather as _tw
results = []
def check(name, cond, info=''):
    results.append(bool(cond)); print(('PASS ' if cond else 'FAIL ') + name + ('  -- ' + str(info) if info != '' else ''))
B3 = (58.887269, 15.772629)                      # on Regnaren's water (south basin)
cfg = {'waypoints': [{'lat': 58.88651, 'lon': 15.777774, 'name': 'Djupa hålet', 'uid': 'filip', 'by': 'Filip', 'type': 'abborre'}]}

def an(pg): return pg.evaluate('window.__ffAnalysis()')
def pick(pg, m, wait=1300):
    pg.click('#anPanel button[data-m="%s"]' % m); pg.wait_for_timeout(wait); return an(pg)
def lit(pg):
    return pg.evaluate("""() => { var c = document.getElementById('anLayer'); if (!c.classList.contains('on')) return 0;
      var d = c.getContext('2d').getImageData(0, 0, c.width, c.height).data, n = 0; for (var i = 3; i < d.length; i += 4) if (d[i] > 0) n++; return n; }""")

with sync_playwright() as p:
    b, ctx, pg, errs = new_page(p, geo=B3, cfg=cfg, name=None)
    wx = _tw.wx_json(); wx['current']['wind_speed_10m'] = 6; wx['current']['wind_direction_10m'] = 225
    ctx.route('**/api.open-meteo.com/**', lambda r: r.fulfill(status=200, content_type='application/json', body=json.dumps(wx), headers={'Access-Control-Allow-Origin': '*'}))
    pg.evaluate("localStorage.removeItem('ffmap_weather_v1')"); pg.reload(); pg.wait_for_timeout(600); fakefb.login(pg, 'Filip'); pg.wait_for_timeout(2500)
    check('the analysis button is where "uppdatera" was; that one is gone', pg.is_visible('#anBtn') and pg.query_selector('#refreshBtn') is None)
    pg.click('#visMoreBtn'); pg.wait_for_timeout(200)
    check('Filter: "Kartanalys" (on) and "Håll skärmen tänd" (off)', pg.is_checked('#toggleAnalysis') and not pg.is_checked('#toggleWake'))
    pg.click('#visMoreBtn'); pg.wait_for_timeout(200)
    check('nothing chosen yet: nothing drawn', an(pg)['mode'] is None and lit(pg) == 0)
    pg.click('#anBtn'); pg.wait_for_timeout(400)
    chips = pg.eval_on_selector_all('#anChips button', 'e => e.map(x => x.textContent)') + pg.eval_on_selector_all('#anPresets button', 'e => e.map(x => x.textContent)')
    check('one panel with every analysis + the presets', pg.is_visible('#anPanel') and chips == ['Djup', 'Branta kanter', 'Toppar & hålor', 'Växtkant', 'Hård botten', 'Vindkant', 'Liknande', 'Abborre', 'Gädda', 'Gös'], chips)
    a = pick(pg, 'depth')
    check('Djup 4–6 m: a share of the lake lit, the rest toned down', a['ready'] and a['n'] > 1000 and '4,0–6,0 m' in a['text'] and lit(pg) > 10000, a)
    n46 = a['n']
    pg.evaluate("(() => { var e = document.getElementById('anHi'); e.value = 9; e.dispatchEvent(new Event('input', { bubbles: true })); })()"); pg.wait_for_timeout(600)
    a = an(pg)
    check('drag "Till" to 9 m: more of the lake', a['n'] > n46 and '4,0–9,0 m' in a['text'], a['text'])
    pg.screenshot(path='shot_an_depth.png')
    a = pick(pg, 'steep'); check('Branta kanter: steep parts found', a['ready'] and a['n'] > 100, a)
    a = pick(pg, 'tops'); check('Toppar & hålor: labelled on the map', a['ready'] and a['labels'] >= 4, a)
    lbl = pg.query_selector('.anLbl')
    pg.evaluate("document.querySelector('.anLbl').click()"); pg.wait_for_timeout(600)
    check('tap a label: the lead line is dropped there, the panel closes', pg.eval_on_selector('#probe', 'e => e.classList.contains("show")') and not pg.eval_on_selector('#anPanel', 'e => e.classList.contains("show")'))
    pg.click('#anBtn'); pg.wait_for_timeout(300)
    a = pick(pg, 'veg', 2500); check('Växtkant (Genesis vegetation, fetched when needed)', a['ready'] and a['n'] > 50, a)
    a = pick(pg, 'hard'); check('Hård botten', a['ready'] and a['n'] > 100, a)
    a = pick(pg, 'wind'); check('Vindkant: from the weather wind (6 m/s SV)', a['ready'] and a['n'] > 100 and 'SV' in a['text'], a)
    a = pick(pg, 'similar'); check('Liknande: like "Djupa hålet", a list of places', a['ready'] and a['list'] >= 1 and 'Djupa hålet' in a['text'], a)
    pg.screenshot(path='shot_an_similar.png')
    pg.click('#anResult button[data-go="1"]'); pg.wait_for_timeout(700)
    check('"Åk hit" from the list: navigating there (card + lead line)', pg.is_visible('#navCard') and 'Liknande #1' in pg.inner_text('#navName') and pg.eval_on_selector('#probe', 'e => e.classList.contains("show")'))
    pg.click('#navClose'); pg.wait_for_timeout(300)
    check('✕ ends it (card and lead line gone)', not pg.is_visible('#navCard') and not pg.eval_on_selector('#probe', 'e => e.classList.contains("show")'))
    pg.click('#anBtn'); pg.wait_for_timeout(300)
    for m in ('abborre', 'gadda', 'gos'):
        a = pick(pg, m); check('preset %s: combined, says it is rules of thumb' % m, a['ready'] and a['n'] > 50 and 'Tumregler' in pg.inner_text('#anResult'), a)
    # Filter shows/hides it (keeps the choice)
    pg.click('#anClose'); pg.wait_for_timeout(200)
    pg.click('#visMoreBtn'); pg.wait_for_timeout(200); pg.click('label:has(#toggleAnalysis) .toggle'); pg.click('#visMoreBtn'); pg.wait_for_timeout(300)
    check('Filter "Kartanalys" off: hidden, choice kept', lit(pg) == 0 and an(pg)['mode'] == 'gos')
    pg.click('#visMoreBtn'); pg.wait_for_timeout(200); pg.click('label:has(#toggleAnalysis) .toggle'); pg.click('#visMoreBtn'); pg.wait_for_timeout(300)
    check('...on again: shown', lit(pg) > 1000)
    pg.reload(); pg.wait_for_timeout(3000)
    check('after a reload: the same analysis', an(pg)['mode'] == 'gos' and an(pg)['ready'] and lit(pg) > 1000, an(pg))
    pg.click('#anBtn'); pg.wait_for_timeout(300); pg.click('#anClear'); pg.wait_for_timeout(300)
    check('"Rensa": nothing chosen, nothing drawn', an(pg)['mode'] is None and lit(pg) == 0)
    check('no page errors', not errs, errs)
    b.close()
print('\n%d/%d passed' % (sum(results), len(results)))
