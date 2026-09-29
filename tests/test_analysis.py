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
    check('one panel with every analysis + the presets', pg.is_visible('#anPanel') and chips == ['Djup', 'Branta kanter', 'Toppar & hålor', 'Växter', 'Hård botten', 'Vindkant', 'Liknande', 'Abborre', 'Gädda', 'Gös'], chips)
    a = pick(pg, 'depth')
    check('Djup 4–6 m: a share of the lake lit, the rest toned down', a['ready'] and a['n'] > 1000 and '4,0–6,0 m' in a['text'] and lit(pg) > 10000, a)
    n46 = a['n']
    check('the depth range: one bar in the depth colours with two handles (like the legend)', pg.is_visible('#anControls .anDual') and len(pg.query_selector_all('#anControls .anKnob')) == 2)
    r = pg.eval_on_selector('#anControls .anDual', 'e => { var r = e.getBoundingClientRect(); return [r.left, r.top, r.width, r.height]; }')
    dmax = float(pg.inner_text('#anControls .anTicks span:last-child').replace(' m', '').replace(',', '.'))
    k = pg.eval_on_selector_all('#anControls .anKnob', 'e => e.map(x => { var r = x.getBoundingClientRect(); return [r.left + r.width / 2, r.top + r.height / 2]; })')[1]
    pg.mouse.move(k[0], k[1]); pg.mouse.down(); pg.mouse.move(r[0] + r[2] * 9 / dmax, k[1], steps=8); pg.mouse.up(); pg.wait_for_timeout(600)
    a = an(pg)
    check('drag the right handle to 9 m: more of the lake', a['n'] > n46 and '4,0–9,0 m' in a['text'], a['text'])
    check('"Mörkare": how dark the rest of the map is (72 % from start)', pg.is_visible('#anDim') and pg.input_value('#anDim') == '0.72')
    dark = pg.evaluate("(() => { var c = document.getElementById('anLayer'); return c.getContext('2d').getImageData(5, 5, 1, 1).data[3]; })()")
    pg.evaluate("(() => { var e = document.getElementById('anDim'); e.value = 0.4; e.dispatchEvent(new Event('input', { bubbles: true })); })()"); pg.wait_for_timeout(300)
    light = pg.evaluate("(() => { var c = document.getElementById('anLayer'); return c.getContext('2d').getImageData(5, 5, 1, 1).data[3]; })()")
    check('...lighter when turned down', light < dark - 40, (dark, light))
    check('the rest of the map is also greyed (a saturation layer)', pg.evaluate("getComputedStyle(document.getElementById('anSat')).mixBlendMode") == 'saturation' and pg.is_visible('#anSat'))
    pg.screenshot(path='shot_an_depth.png')
    a = pick(pg, 'steep'); check('Branta kanter: steep parts found', a['ready'] and a['n'] > 100, a)
    a = pick(pg, 'tops'); check('Toppar & hålor: labelled on the map', a['ready'] and a['labels'] >= 4, a)
    def setr(i, v): pg.evaluate("([i, v]) => { var e = document.getElementById(i); e.value = v; e.dispatchEvent(new Event('input', { bubbles: true })); }", [i, v])
    setr('anTopH', 2.5); setr('anHoleD', 3.5); pg.wait_for_timeout(700)
    a2 = an(pg); check('sliders for how much higher / lower: stricter = fewer', a2['labels'] < a['labels'], (a['labels'], a2['labels']))
    setr('anTopH', 1); setr('anHoleD', 1.3); pg.wait_for_timeout(700)
    lbl = pg.query_selector('.anLbl')
    pg.evaluate("document.querySelector('.anLbl').click()"); pg.wait_for_timeout(600)
    check('tap a label: the lead line is dropped there, the panel closes', pg.eval_on_selector('#probe', 'e => e.classList.contains("show")') and not pg.eval_on_selector('#anPanel', 'e => e.classList.contains("show")'))
    pg.click('#anBtn'); pg.wait_for_timeout(300)
    a = pick(pg, 'veg', 2500); check('Växter: where there is vegetation (Genesis, fetched when needed), no sliders', a['ready'] and a['n'] > 50 and not pg.query_selector('#anControls .anDual'), a)
    a = pick(pg, 'hard'); check('Hård botten', a['ready'] and a['n'] > 100, a)
    setr('anHmin', 4); pg.wait_for_timeout(700)
    a2 = an(pg); check('hard bottom: a slider for how hard (+ a depth range)', a2['n'] < a['n'] and 'Mycket hård' in a2['text'] and pg.is_visible('#anControls .anDual'), (a['n'], a2['n'], a2['text']))
    a = pick(pg, 'wind'); check('Vindkant: from the weather wind (6 m/s SV)', a['ready'] and a['n'] > 100 and 'SV' in a['text'], a)
    a = pick(pg, 'similar'); check('Liknande: like "Djupa hålet", a list of places', a['ready'] and a['list'] >= 1 and 'Djupa hålet' in a['text'], a)
    pg.screenshot(path='shot_an_similar.png')
    pg.click('#anResult button[data-go="1"]'); pg.wait_for_timeout(700)
    check('"Åk hit" from the list: the lead line there (no extra card)', pg.eval_on_selector('#probe', 'e => e.classList.contains("show")') and pg.query_selector('#navCard') is None)
    pg.click('#anBtn'); pg.wait_for_timeout(300)
    g = pg.eval_on_selector('#anPanel .grab', 'e => { var r = e.getBoundingClientRect(); return [r.left + r.width / 2, r.top + 4]; }')
    pg.mouse.move(g[0], g[1]); pg.mouse.down(); pg.mouse.move(g[0], g[1] + 180, steps=10); pg.mouse.up(); pg.wait_for_timeout(500)
    check('swipe the panel down: it closes (like a spot sheet)', not pg.eval_on_selector('#anPanel', 'e => e.classList.contains("show")'))
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
    # a spot's sheet: "Hitta liknande" opens the analysis on "Liknande" for that spot
    pg.evaluate("n => { var id = Object.keys(window.__wpDocs).filter(k => window.__wpDocs[k].name === n)[0]; document.querySelector('#waypoints [data-id=' + JSON.stringify(id) + ']').click(); }", 'Djupa hålet')
    pg.wait_for_timeout(400)
    check('a spot sheet: "Åk hit" and "Hitta liknande"', pg.is_visible('#wpGo') and pg.is_visible('#wpLike'))
    pg.click('#wpLike'); pg.wait_for_timeout(1500)
    a = an(pg)
    check('"Hitta liknande": the analysis opens on Liknande for that spot', pg.eval_on_selector('#anPanel', 'e => e.classList.contains("show")') and a['mode'] == 'similar' and 'Djupa hålet' in a['text'] and a['list'] >= 1, a)
    f = pg.eval_on_selector_all('#anSimF button', 'e => e.map(x => x.textContent + (x.classList.contains("on") ? "+" : ""))')
    r = pg.eval_on_selector_all('#anSimR button', 'e => e.map(x => x.textContent + (x.classList.contains("on") ? "+" : ""))')
    check('Liknande: choose what to compare (all on) and the area (right under the spot by default)', f == ['Djup+', 'Lutning+', 'Botten+', 'Växter+', 'Topp/håla+'] and r[0] == 'Bara platsen+', (f, r))
    pg.click('#anSimR button[data-r="50"]'); pg.wait_for_timeout(2500)
    a2 = an(pg); check('...50 m round it', 'inom 50 m' in a2['text'] and a2['list'] >= 1, a2)
    pg.click('#anSimF button[data-f="h"]'); pg.wait_for_timeout(1200)
    a3 = an(pg); check('...without the bottom: not compared any more', 'botten' not in a3['text'].split(':', 1)[1].replace('jämn botten', ''), a3['text'])
    for k in 'dsvt': pg.click('#anSimF button[data-f="%s"]' % k); pg.wait_for_timeout(200)
    pg.wait_for_timeout(1200)
    check('...nothing chosen: says to choose something', 'Välj minst en' in an(pg)['text'])
    check('no page errors', not errs, errs)
    b.close()
print('\n%d/%d passed' % (sum(results), len(results)))
