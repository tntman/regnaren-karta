# Heatmap (fångster): "Heatmap" last in the map-style list -> a bottom panel (like Kartanalys):
# Värme / Per art / Rutor / Prickar, species + competition filters, the map toned down; a tap on
# a catch opens it (who, when, depth, place; ‹ ›; Åk hit, Liknande); "Heatmap" pill under the
# weather chip; not together with Kartanalys; kept through a rotation, off after a restart.
# (The catches come from Fiskfiskarnas API -- made up by fakefb; the fetching: test_catchapi.py.)
from playwright.sync_api import sync_playwright
import fakefb, json, math
from fakefb import new_page
results = []
def check(name, cond, info=''):
    results.append(bool(cond)); print(('PASS ' if cond else 'FAIL ') + name + ('  -- ' + str(info) if info != '' else ''))

# made-up catches on Regnaren's water (south basin), two competitions
B1 = (58.887421, 15.775569); B4 = (58.88651, 15.777774); B5 = (58.88613, 15.774099); B3 = (58.887269, 15.772629)
def ms(day, h, m): return int(__import__('calendar').timegm((2026, 9, day, h, m, 0))) * 1000
ROWS = []
for i in range(12):   # a cluster at B4 (abborre), 30-45 cm
    ROWS.append([ms(26, 9, i), 'regnaren1', ['Henrik', 'Filip', 'Calle'][i % 3], 'abborre', 30 + i, B4[0] + (i % 4) * 0.00004, B4[1] + (i // 4) * 0.00006])
for i in range(5):    # gädda at B1
    ROWS.append([ms(26, 11, i), 'regnaren1', ['Erika', 'Magnus', 'Henrik', 'Sunbaum', 'Filip'][i], 'gadda', [74, 70, 75, 69, 52][i], B1[0] + i * 0.00003, B1[1]])
ROWS.append([ms(25, 14, 0), 'regnaren1', 'Pia', 'gos', 60, B5[0], B5[1]])
ROWS.append([ms(20, 10, 0), 'fiskfiskOpen', 'Olle', 'gadda', 90, B5[0] + 0.0003, B5[1] + 0.0004])
CATCHES = {'heatmap': [fakefb.api_row(*r) for r in ROWS]}

def size(pg, root, a, b):   # "Storlek": move the two handles (min, max cm)
    pg.evaluate("""([r, a, b]) => [['cm1', b], ['cm0', a], ['cm1', b]].forEach(([k, v]) => { var e = document.querySelector(r + ' input[data-r=' + k + ']'); e.value = v;
      e.dispatchEvent(new Event('input', { bubbles: true })); e.dispatchEvent(new Event('change', { bubbles: true })); })""", [root, a, b])
def heat(pg): return pg.evaluate('window.__ffHeat()')
def open_heat(pg):
    bb = pg.locator('#mapTypeBtn').bounding_box()
    pg.mouse.move(bb['x'] + 20, bb['y'] + 20); pg.mouse.down(); pg.wait_for_timeout(700); pg.mouse.up(); pg.wait_for_timeout(300)
    pg.click('#mapTypePop .hmOpt'); pg.wait_for_timeout(900)
def coloured(pg):
    return pg.evaluate("""() => { var c = document.getElementById('hmLayer'), d = c.getContext('2d').getImageData(0, 0, c.width, c.height).data, n = 0;
      for (var i = 0; i < d.length; i += 4) if (d[i + 3] > 150 && (d[i] > 150 || d[i + 1] > 150)) n++; return n; }""")

with sync_playwright() as p:
    b, ctx, pg, errs = new_page(p, geo=B3, cfg={'api': CATCHES}, name='Filip')
    pg.wait_for_timeout(1500)
    # ---- the map-style list: Heatmap last ----
    bb = pg.locator('#mapTypeBtn').bounding_box()
    pg.mouse.move(bb['x'] + 20, bb['y'] + 20); pg.mouse.down(); pg.wait_for_timeout(700); pg.mouse.up(); pg.wait_for_timeout(300)
    opts = pg.eval_on_selector_all('#mapTypePop .styleOpt', 'e => e.map(x => x.textContent)')
    check('hold the map-style button: "Heatmap" last in the list, "opens a menu"', opts and 'Heatmap' in opts[-1] and 'meny' in opts[-1], opts[-2:])
    check('...the catches fetched once at the start (no copy on the phone yet)', ctx.api.n('dashboard') == 1, ctx.api.hits)
    pg.click('#mapTypePop .hmOpt'); pg.wait_for_timeout(1000)
    h = heat(pg)
    check('tap it: the heat map is on, its panel open, the map style unchanged', h['on'] and h['panel'] and not pg.is_visible('#mapTypePop'), h)
    check('...all of them shown, not fetched again (the copy is fresh)', ctx.api.n('dashboard') == 1 and h['n'] == len(ROWS), (ctx.api.hits, h['n']))
    check('...the map toned down + greyed like Kartanalys', pg.is_visible('#hmLayer') and pg.evaluate("getComputedStyle(document.getElementById('hmSat')).mixBlendMode") == 'saturation')
    check('...Värme: coloured heat on the map', coloured(pg) > 200, coloured(pg))
    res = pg.inner_text('#hmResult')
    check('the panel: 19 catches, 12 abborre, 6 gädda, 1 gös', '19 fångster' in res and '12 abborre' in res and '6 gädda' in res and '1 gös' in res, res)
    comps = pg.eval_on_selector_all('#hmComp button', 'e => e.map(x => x.textContent)')
    check('competitions: Alla, "Regnaren 1 · 25–26 sep", "Fiskfisk Open · 20 sep"', comps == ['Alla', 'Regnaren 1 · 25–26 sep', 'Fiskfisk Open · 20 sep'], comps)
    g = pg.evaluate("(() => { var r = document.querySelector('#hmPanel .grab').getBoundingClientRect(); return [r.left + r.width / 2, r.top + 12]; })()")
    pg.mouse.move(g[0], g[1]); pg.mouse.down(); pg.mouse.move(g[0], g[1] + 25, steps=4); pg.wait_for_timeout(100)
    glow = pg.evaluate("getComputedStyle(document.getElementById('hmPanel')).borderTopColor")
    pg.mouse.move(g[0], g[1], steps=3); pg.mouse.up(); pg.wait_for_timeout(300)
    check('holding the grip of the panel: the top edge glows blue like the other panels', glow == 'rgb(88, 180, 255)', glow)
    edge = pg.evaluate("""() => { var c = document.getElementById('hmLayer'), d = c.getContext('2d').getImageData(0, 0, c.width, c.height).data, n = 0;
      for (var i = 0; i < d.length; i += 4) if (d[i] > 120 && d[i + 1] > 120 && d[i + 2] > 120 && Math.abs(d[i] - d[i + 2]) < 20 && d[i + 3] > 200) n++; return n; }""")
    check('the edge of the lake: a thin white line, like in Kartanalys', edge > 100, edge)
    check('Återställ greyed out while everything is as from the start', pg.is_disabled('#hmReset'))
    pg.evaluate("(() => { var e = document.querySelector('#hmCtl input[data-r=rad]'); e.value = 150; e.dispatchEvent(new Event('input', { bubbles: true })); })()"); pg.wait_for_timeout(300)
    check('...dragging Radie (Värme): ↺ can be pressed at once', pg.is_enabled('#hmReset'))
    pg.click('#hmStyleSeg button[data-s="hex"]'); pg.wait_for_timeout(200); pg.click('#hmStyleSeg button[data-s="heat"]'); pg.wait_for_timeout(200)
    check('settings changed: ↺ Återställ next to ⏻ Stäng av heatmap in the top row', pg.is_enabled('#hmReset') and pg.get_attribute('#hmReset', 'aria-label') == 'Återställ' and pg.get_attribute('#hmOff', 'aria-label') == 'Stäng av heatmap')
    pg.click('#hmReset'); pg.wait_for_timeout(300)
    check('..."Återställ": back to the start (radius 70 m), still on; then greyed out', pg.inner_text('#hmOut_rad') == '70 m' and heat(pg)['on'] and pg.is_disabled('#hmReset'), pg.inner_text('#hmOut_rad'))
    check('...and it says so: the ↺ spins round once', pg.get_attribute('#hmReset', 'aria-label') == 'Återställt' and pg.eval_on_selector('#hmReset', 'e => e.classList.contains("rsDone")'))
    pg.wait_for_timeout(1600)
    check('...then the usual grey ↺', pg.get_attribute('#hmReset', 'aria-label') == 'Återställ' and not pg.eval_on_selector('#hmReset', 'e => e.classList.contains("rsDone")'))
    # ---- "När": a bar per hour, press / drag = a time window filtering the map ----
    nbar = pg.eval_on_selector_all('#hmTime .hmBars i', 'e => e.length')
    check('"När": a bar per hour of the day with catches + "Bäst kl"', nbar >= 2 and pg.is_visible('#hmTime') and 'Bäst kl' in pg.inner_text('#hmTime'), nbar)
    n_all = heat(pg)['n']
    hrs = pg.evaluate("(() => { var r = %s; return r.filter(x => x[1] !== 'fiskfiskOpen').map(x => new Date(x[0]).getHours()); })()" % json.dumps([[r[0], r[1]] for r in ROWS]))
    h0 = min(hrs); n0 = sum(1 for h in hrs if h == h0)
    bb2 = pg.locator('#hmTime .hmBars').bounding_box(); lo = int(pg.get_attribute('#hmTime', 'data-lo')); hi = int(pg.get_attribute('#hmTime', 'data-hi'))
    pg.mouse.click(bb2['x'] + bb2['width'] * ((h0 - lo) + 0.5) / (hi - lo + 1), bb2['y'] + bb2['height'] - 4); pg.wait_for_timeout(300)
    check('press the first hour: only the catches from then on the map; ↺ can be pressed', heat(pg)['n'] == n0 and n0 < n_all and pg.is_enabled('#hmReset') and ('kl %02d–%02d' % (h0, h0 + 1)) in pg.inner_text('#hmResult'), (heat(pg)['n'], n0, n_all))
    pg.mouse.click(bb2['x'] + bb2['width'] * ((h0 - lo) + 0.5) / (hi - lo + 1), bb2['y'] + bb2['height'] - 4); pg.wait_for_timeout(300)
    check('...press the same hour again: all hours', heat(pg)['n'] == n_all, heat(pg)['n'])
    pg.mouse.move(bb2['x'] + 3, bb2['y'] + 40); pg.mouse.down(); pg.mouse.move(bb2['x'] + bb2['width'] - 3, bb2['y'] + 40, steps=8); pg.mouse.up(); pg.wait_for_timeout(300)
    check('drag over all bars: everything again, window still set to the whole day', heat(pg)['n'] == n_all, heat(pg)['n'])
    pg.click('#hmReset'); pg.wait_for_timeout(1800)
    check('the "Heatmap" pill under the weather chip', pg.is_visible('#hmPill') and pg.inner_text('#hmPill').strip() == 'Heatmap' and
          pg.evaluate("document.getElementById('hmPill').getBoundingClientRect().top > document.getElementById('wxChip').getBoundingClientRect().bottom - 1"))
    pg.screenshot(path='shot_heat_heat.png')
    # filters
    pg.click('#hmSp button[data-sp="gadda"]'); pg.wait_for_timeout(300)
    check('Art: Gädda -> 6 catches', heat(pg)['n'] == 6 and '6 fångster' in pg.inner_text('#hmResult'), heat(pg)['n'])
    pg.click('#hmComp button[data-comp="regnaren1"]'); pg.wait_for_timeout(300)
    check('...+ Tävling: Regnaren 1 -> 5', heat(pg)['n'] == 5, heat(pg)['n'])
    pg.click('#hmComp button[data-comp="all"]'); size(pg, '#hmSize', 70, 80); pg.wait_for_timeout(300)
    check('Storlek 70–80 cm (Gädda): 3 catches, said in the result line', heat(pg)['n'] == 3 and '70–80 cm' in pg.inner_text('#hmResult') and pg.inner_text('#hmSize output') == '70–80 cm', pg.inner_text('#hmResult'))
    lim = lambda: pg.evaluate("[+document.querySelector('#hmSize input').min, +document.querySelector('#hmSize input').max]")
    check('...the slider runs from the smallest to the biggest gädda shown (52-90 cm -> 50-90)', lim() == [50, 90], lim())
    pg.click('#hmSp button[data-sp="abborre"]'); pg.wait_for_timeout(300)
    check('Abborre: its own range (all of it) and its own ends (30-41 cm -> 30-45)', pg.inner_text('#hmSize output') == '30–45 cm' and lim() == [30, 45] and heat(pg)['n'] == 12, (pg.inner_text('#hmSize output'), lim()))
    pg.click('#hmSp button[data-sp="gadda"]'); pg.wait_for_timeout(300)
    check('...back to Gädda: still 70–80 cm', pg.inner_text('#hmSize output') == '70–80 cm' and heat(pg)['n'] == 3)
    size(pg, '#hmSize', 85, 130); pg.wait_for_timeout(300)
    check('...the right handle at the end (no upper limit): "85–90 cm" (the biggest written out) -> the 90 cm one', heat(pg)['n'] == 1 and pg.inner_text('#hmSize output') == '85–90 cm', heat(pg)['n'])
    size(pg, '#hmSize', 100, 20); pg.wait_for_timeout(300)
    v = pg.evaluate("[+document.querySelector('#hmSize input[data-r=cm0]').value, +document.querySelector('#hmSize input[data-r=cm1]').value]")
    check('...the handles never pass each other', v[0] <= v[1], v)
    size(pg, '#hmSize', 0, 130); pg.wait_for_timeout(300)
    check('...back to all of it', pg.inner_text('#hmSize output') == '50–90 cm' and heat(pg)['n'] == 6)
    pg.click('#hmSp button[data-sp="all"]'); pg.wait_for_timeout(300)
    # ---- Per art ----
    pg.click('#hmStyleSeg button[data-s="species"]'); pg.wait_for_timeout(400)
    g = pg.eval_on_selector('#hmStyleSeg button.on', 'e => [e.dataset.s, e.classList.contains("segGlide"), parseFloat(e.style.getPropertyValue("--sl"))]')
    check('the chosen tab glides over from the old one (Värme -> Per art: starts one tab to the left)', g[0] == 'species' and g[1] and g[2] < -20, g)
    chips = pg.eval_on_selector_all('#hmSp button', 'e => e.map(x => x.textContent)')
    check('Per art: Art as in the other tabs (Alla first), each species with its colour and count', chips == ['Alla', 'Abborre 12', 'Gädda 6', 'Gös 1'] and pg.inner_text('#hmSp button.on') == 'Alla' and coloured(pg) > 100, chips)
    pg.click('#hmSp button[data-sp="gadda"]'); pg.wait_for_timeout(300)
    check('...Gädda -> 6, and it stays chosen in the other tabs', heat(pg)['n'] == 6, heat(pg)['n'])
    pg.click('#hmStyleSeg button[data-s="heat"]'); pg.wait_for_timeout(300)
    check('...(Värme: still Gädda)', pg.inner_text('#hmSp button.on') == 'Gädda')
    pg.click('#hmSp button[data-sp="all"]'); pg.click('#hmStyleSeg button[data-s="species"]'); pg.wait_for_timeout(300)
    pg.screenshot(path='shot_heat_species.png')
    # ---- Rutor ----
    pg.click('#hmStyleSeg button[data-s="hex"]'); pg.wait_for_timeout(400)
    hx = heat(pg)['hex']; r60 = heat(pg)['hexR']
    check('Rutor: hexagons with the number of catches (all 19 counted)', hx and sum(x['n'] for x in hx) == 19 and max(x['n'] for x in hx) >= 5, hx)
    pg.click('#hmCtl button[data-hx="120"]'); pg.wait_for_timeout(300)
    hx2 = heat(pg)['hex']
    check('...120 m: twice as big (the same 19 catches)', sum(x['n'] for x in hx2) == 19 and abs(heat(pg)['hexR'] / r60 - 2) < 0.01, (r60, heat(pg)['hexR']))
    pg.screenshot(path='shot_heat_hex.png')
    big = max(heat(pg)['hex'], key=lambda x: x['n'])
    pg.click('#hmClose'); pg.wait_for_timeout(400)
    pg.mouse.click(big['x'], big['y']); pg.wait_for_timeout(900)
    h = heat(pg)
    check('tap a hexagon: its catches (biggest first), ‹ › between them', h['card'] and h['card']['n'] == big['n'] and pg.is_visible('#hmCardNav'), h['card'])
    pg.click('#hmCardClose'); pg.wait_for_timeout(300)
    # ---- Prickar ----
    pg.click('#hmPill'); pg.wait_for_timeout(400)
    check('the pill opens the panel again', heat(pg)['panel'])
    pg.click('#hmStyleSeg button[data-s="dots"]'); pg.wait_for_timeout(400)
    pg.screenshot(path='shot_heat_dots.png')
    pg.click('#hmClose'); pg.wait_for_timeout(400)
    gid = [r for r in ROWS if r[3] == 'gadda' and r[4] == 74][0]
    cid = '%d|%s|gadda|74' % (gid[0], gid[2])
    xy = pg.evaluate('(id) => window.__ffHeatScreen(id)', cid)
    pg.mouse.click(xy[0], xy[1]); pg.wait_for_timeout(900)
    card = pg.inner_text('#hmCard')
    check('tap a dot: the catch -- Gädda 74 cm, Erika, 26 sep, place 2 av 5 in Regnaren 1', heat(pg)['card'] and 'Gädda 74 cm' in card and 'Erika' in card and '26/9 13:00' in card and '2 av 5' in card and 'REGNAREN 1' in card, card)
    check('...the depth there', 'DJUP' in card.upper() and ' m' in pg.inner_text('#hmCardData'), pg.inner_text('#hmCardData'))
    check('..."2:a största gäddan i tävlingen" + the others close by', '2:a största gäddan i tävlingen' in card and 'inom 50 m' in card, card)
    pg.screenshot(path='shot_heat_card.png')
    n0 = heat(pg)['card']['n']
    if n0 > 1:
        i0 = heat(pg)['card']['id']; pg.click('#hmCardNext'); pg.wait_for_timeout(200)
        check('› : the next catch there', heat(pg)['card']['id'] != i0)
    pg.click('#hmCardGo'); pg.wait_for_timeout(900)
    check('Åk hit: the lead line on the catch, the heat map stays', pg.eval_on_selector('#probe', 'e => e.classList.contains("show")') and heat(pg)['on'] and not heat(pg)['card'])
    pg.evaluate("document.getElementById('probe').click()"); pg.wait_for_timeout(200)
    # ---- not together with Kartanalys ----
    pg.click('#anBtn'); pg.wait_for_timeout(300)
    check('opening Kartanalys closes the heat map panel', pg.eval_on_selector('#anPanel', 'e => e.classList.contains("show")') and not heat(pg)['panel'])
    pg.click('#anCatSeg button[data-cat="map"]'); pg.click('#anPanel button[data-m="depth"]'); pg.wait_for_timeout(800)
    check('choosing something in Kartanalys: the heat map goes off (and its pill)', not heat(pg)['on'] and not pg.is_visible('#hmPill') and pg.evaluate('window.__ffAnalysis().mode') == 'depth')
    check('...instead the "Kartanalys" pill under the weather chip', pg.is_visible('#anPill') and pg.inner_text('#anPill').strip() == 'Kartanalys' and
          pg.evaluate("document.getElementById('anPill').getBoundingClientRect().top > document.getElementById('wxChip').getBoundingClientRect().bottom - 1"))
    pg.click('#anClose'); pg.wait_for_timeout(300)
    pg.click('#anPill'); pg.wait_for_timeout(300)
    check('tap the pill: the Kartanalys panel', pg.eval_on_selector('#anPanel', 'e => e.classList.contains("show")'))
    pg.click('#anClose'); pg.wait_for_timeout(300)
    # Filter → Lager → Heatmap: only shows / hides it, like Kartanalys (on / off is in its own panel)
    pg.click('#visMoreBtn'); pg.wait_for_timeout(200)
    check('Filter, Lager: a Heatmap switch (on = shown), the heat map itself off', pg.is_visible('label:has(#toggleHeatmap)') and pg.is_checked('#toggleHeatmap') and not heat(pg)['on'])
    pg.click('label:has(#toggleHeatmap) .toggle'); pg.wait_for_timeout(400)
    check('...switching it does not turn the heat map on or open its panel', not heat(pg)['on'] and not heat(pg)['panel'] and not heat(pg)['show'])
    pg.click('label:has(#toggleHeatmap) .toggle'); pg.click('#visMoreBtn'); pg.wait_for_timeout(200)
    open_heat(pg)
    check('the heat map on again (map-style list): Kartanalys off, only the Heatmap pill', heat(pg)['on'] and heat(pg)['panel'] and pg.evaluate('window.__ffAnalysis().mode') is None
          and pg.is_visible('#hmPill') and not pg.is_visible('#anPill'))
    check('...its settings kept (Prickar)', heat(pg)['style'] == 'dots')
    pg.click('#hmClose'); pg.wait_for_timeout(300); pg.click('#visMoreBtn'); pg.wait_for_timeout(200)
    pg.click('label:has(#toggleHeatmap) .toggle'); pg.wait_for_timeout(400)
    check('hidden in Filter: still on, but not drawn, no pill, no panel', heat(pg)['on'] and not heat(pg)['show'] and not heat(pg)['panel'] and not pg.is_visible('#hmPill')
          and not pg.eval_on_selector('#hmLayer', 'e => e.classList.contains("on")'))
    pg.click('#visMoreBtn'); pg.wait_for_timeout(200)
    open_heat(pg)
    check('...its panel says so', 'Dold – slå på Heatmap i Filter' in pg.inner_text('#hmResult'))
    pg.click('#hmOff'); pg.wait_for_timeout(300); open_heat(pg)
    check('turned on by hand again: shown (like choosing a Kartanalys mode), the Filter switch follows', heat(pg)['on'] and heat(pg)['show'] and pg.is_checked('#toggleHeatmap') and pg.is_visible('#hmPill'))
    # the quick button left of the map button: on / off, and the map stays where it is
    pg.click('#hmClose'); pg.wait_for_timeout(300); pg.click('#hmBtn'); pg.wait_for_timeout(300)
    check('shortcut button: heat map off, button not lit', not heat(pg)['on'] and pg.get_attribute('#hmBtn', 'aria-pressed') == 'false')
    tf = pg.evaluate("getComputedStyle(document.getElementById('world')).transform")
    pg.click('#hmBtn'); pg.wait_for_timeout(1200)
    check('shortcut button: on, lit, panel open, left of the map button (one capsule, design A), map not moved', heat(pg)['on'] and heat(pg)['panel'] and pg.get_attribute('#hmBtn', 'aria-pressed') == 'true'
          and pg.evaluate("document.getElementById('hmBtn').getBoundingClientRect().right <= document.getElementById('mapTypeBtn').getBoundingClientRect().left + 0.5")
          and pg.evaluate("getComputedStyle(document.getElementById('world')).transform") == tf)
    legend = pg.evaluate("getComputedStyle(document.querySelector('#hmPill .hmDot')).backgroundImage")
    check('"glöd" scale: violet -> warm white (not the depth colours)', 'rgb(255, 245, 200)' in legend and 'rgb(0, 220, 230)' not in legend, legend)
    # Liknande from a catch
    pg.click('#hmClose'); pg.wait_for_timeout(300)
    xy = pg.evaluate('(id) => window.__ffHeatScreen(id)', cid); pg.mouse.click(xy[0], xy[1]); pg.wait_for_timeout(900)
    pg.click('#hmCardLike'); pg.wait_for_timeout(1500)
    a = pg.evaluate('window.__ffAnalysis()')
    check('Liknande: Kartanalys "Liknande" with the catch as the place, the heat map off', a['mode'] == 'similar' and not heat(pg)['on'] and 'Fångst: Gädda 74 cm' in pg.inner_text('#anPanel'), a)
    check('no page errors', not errs, errs)
    b.close()

    # ---- rotation keeps it, a restart turns it off ----
    b, ctx, pg, errs = new_page(p, geo=B3, cfg={'api': CATCHES}, name='Filip')
    ctx.add_init_script("Object.defineProperty(navigator, 'standalone', { value: true, configurable: true });")
    pg.reload(); pg.wait_for_timeout(1500)
    open_heat(pg)
    pg.click('#hmStyleSeg button[data-s="dots"]'); pg.click('#hmClose'); pg.wait_for_timeout(300)
    xy = pg.evaluate('(id) => window.__ffHeatScreen(id)', cid); pg.mouse.click(xy[0], xy[1]); pg.wait_for_timeout(900)
    pg.evaluate("window.__rc = 1"); pg.set_viewport_size({'width': 844, 'height': 390})
    pg.evaluate("window.dispatchEvent(new Event('orientationchange'))"); pg.wait_for_timeout(1500); pg.wait_for_load_state('load'); pg.wait_for_timeout(2500)
    h = heat(pg)
    check('turning the phone (reload): heat map on, the same catch open', pg.evaluate('window.__rc') is None and h['on'] and h['card'] and h['card']['id'] == cid, h)
    pg.goto('http://localhost:8899/index.html'); pg.wait_for_timeout(2500)
    check('a new start of the app: the heat map off (like Kartanalys)', not heat(pg)['on'] and not pg.is_visible('#hmPill'))
    check('no page errors', not errs, errs)
    b.close()

    # ---- no catches yet ----
    b, ctx, pg, errs = new_page(p, geo=B3, cfg={}, name='Filip')
    pg.wait_for_timeout(1200); open_heat(pg)
    check('no catches for the lake: says so', 'Inga fångster' in pg.inner_text('#hmResult'), pg.inner_text('#hmResult'))
    b.close()

print('\n%d/%d passed' % (sum(results), len(results)))
