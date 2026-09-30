# Heatmap (fångster): "Heatmap" last in the map-style list -> a bottom panel (like Kartanalys):
# Värme / Per art / Rutor / Prickar, species + competition filters, the map toned down; a tap on
# a catch opens it (who, when, depth, place; ‹ ›; Åk hit, Liknande); "Heatmap" pill under the
# weather chip; not together with Kartanalys; kept through a rotation, off after a restart;
# the admin reads catches from a CSV file into Firestore catches/<lake> (no duplicates).
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
CATCHES = {'regnaren': {'rows': json.dumps(ROWS), 'n': len(ROWS)}}

def heat(pg): return pg.evaluate('window.__ffHeat()')
def open_heat(pg):
    bb = pg.locator('#mapTypeBtn').bounding_box()
    pg.mouse.move(bb['x'] + 20, bb['y'] + 20); pg.mouse.down(); pg.wait_for_timeout(700); pg.mouse.up(); pg.wait_for_timeout(300)
    pg.click('#mapTypePop .hmOpt'); pg.wait_for_timeout(900)
def coloured(pg):
    return pg.evaluate("""() => { var c = document.getElementById('hmLayer'), d = c.getContext('2d').getImageData(0, 0, c.width, c.height).data, n = 0;
      for (var i = 0; i < d.length; i += 4) if (d[i + 3] > 150 && (d[i] > 150 || d[i + 1] > 150)) n++; return n; }""")

with sync_playwright() as p:
    b, ctx, pg, errs = new_page(p, geo=B3, cfg={'catches': CATCHES}, name='Filip')
    pg.wait_for_timeout(1500)
    # ---- the map-style list: Heatmap last ----
    bb = pg.locator('#mapTypeBtn').bounding_box()
    pg.mouse.move(bb['x'] + 20, bb['y'] + 20); pg.mouse.down(); pg.wait_for_timeout(700); pg.mouse.up(); pg.wait_for_timeout(300)
    opts = pg.eval_on_selector_all('#mapTypePop .styleOpt', 'e => e.map(x => x.textContent)')
    check('hold the map-style button: "Heatmap" last in the list, "opens a menu"', opts and 'Heatmap' in opts[-1] and 'meny' in opts[-1], opts[-2:])
    check('...no catches fetched before it is used', pg.evaluate('window.__catchGets') == 0)
    pg.click('#mapTypePop .hmOpt'); pg.wait_for_timeout(1000)
    h = heat(pg)
    check('tap it: the heat map is on, its panel open, the map style unchanged', h['on'] and h['panel'] and not pg.is_visible('#mapTypePop'), h)
    check('...the catches fetched once (1 read)', pg.evaluate('window.__catchGets') == 1 and h['n'] == len(ROWS), (pg.evaluate('window.__catchGets'), h['n']))
    check('...the map toned down + greyed like Kartanalys', pg.is_visible('#hmLayer') and pg.evaluate("getComputedStyle(document.getElementById('hmSat')).mixBlendMode") == 'saturation')
    check('...Värme: coloured heat on the map', coloured(pg) > 200, coloured(pg))
    pg.wait_for_timeout(700)
    top = pg.evaluate("document.getElementById('hmPanel').getBoundingClientRect().top")
    ys = [pg.evaluate('(id) => window.__ffHeatScreen(id)', '%d|%s|%s|%s' % (r[0], r[2], r[3], r[4]))[1] for r in ROWS]
    check('...the catches were hidden behind the panel: the map moved so they show above it', all(120 < y < top for y in ys), (top, [round(y) for y in ys][:6]))
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
    pg.evaluate("(() => { var e = document.querySelector('#hmCtl input[data-r=rad]'); e.value = 150; e.dispatchEvent(new Event('input', { bubbles: true })); })()"); pg.wait_for_timeout(300)
    pg.click('#hmStyleSeg button[data-s="hex"]'); pg.wait_for_timeout(200); pg.click('#hmStyleSeg button[data-s="heat"]'); pg.wait_for_timeout(200)
    check('settings changed: "Återställ" next to "Stäng av heatmap"', pg.is_enabled('#hmReset') and pg.inner_text('#hmReset') == '↺ Återställ')
    pg.click('#hmReset'); pg.wait_for_timeout(300)
    check('..."Återställ": back to the start (radius 70 m), still on; then greyed out', pg.inner_text('#hmOut_rad') == '70 m' and heat(pg)['on'] and pg.is_disabled('#hmReset'), pg.inner_text('#hmOut_rad'))
    check('the "Heatmap" pill under the weather chip', pg.is_visible('#hmPill') and pg.inner_text('#hmPill').strip() == 'Heatmap' and
          pg.evaluate("document.getElementById('hmPill').getBoundingClientRect().top > document.getElementById('wxChip').getBoundingClientRect().bottom - 1"))
    pg.screenshot(path='shot_heat_heat.png')
    # filters
    pg.click('#hmSp button[data-sp="gadda"]'); pg.wait_for_timeout(300)
    check('Art: Gädda -> 6 catches', heat(pg)['n'] == 6 and '6 fångster' in pg.inner_text('#hmResult'), heat(pg)['n'])
    pg.click('#hmComp button[data-comp="regnaren1"]'); pg.wait_for_timeout(300)
    check('...+ Tävling: Regnaren 1 -> 5', heat(pg)['n'] == 5, heat(pg)['n'])
    pg.click('#hmSp button[data-sp="all"]'); pg.click('#hmComp button[data-comp="all"]'); pg.wait_for_timeout(300)
    # ---- Per art ----
    pg.click('#hmStyleSeg button[data-s="species"]'); pg.wait_for_timeout(400)
    chips = pg.eval_on_selector_all('#hmSp button', 'e => e.map(x => x.textContent)')
    check('Per art: a colour per species, toggles with counts', chips == ['Abborre 12', 'Gädda 6', 'Gös 1'] and coloured(pg) > 100, chips)
    pg.click('#hmSp button[data-spt="abborre"]'); pg.wait_for_timeout(300)
    check('...abborre off -> 7', heat(pg)['n'] == 7, heat(pg)['n'])
    pg.click('#hmSp button[data-spt="abborre"]'); pg.wait_for_timeout(200)
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
    pg.click('#anClose'); pg.wait_for_timeout(300)
    open_heat(pg)
    check('the heat map on again: Kartanalys off', heat(pg)['on'] and pg.evaluate('window.__ffAnalysis().mode') is None)
    check('...its settings kept (Prickar)', heat(pg)['style'] == 'dots')
    # Liknande from a catch
    pg.click('#hmClose'); pg.wait_for_timeout(300)
    xy = pg.evaluate('(id) => window.__ffHeatScreen(id)', cid); pg.mouse.click(xy[0], xy[1]); pg.wait_for_timeout(900)
    pg.click('#hmCardLike'); pg.wait_for_timeout(1500)
    a = pg.evaluate('window.__ffAnalysis()')
    check('Liknande: Kartanalys "Liknande" with the catch as the place, the heat map off', a['mode'] == 'similar' and not heat(pg)['on'] and 'Fångst: Gädda 74 cm' in pg.inner_text('#anPanel'), a)
    check('no page errors', not errs, errs)
    b.close()

    # ---- rotation keeps it, a restart turns it off ----
    b, ctx, pg, errs = new_page(p, geo=B3, cfg={'catches': CATCHES}, name='Filip')
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
    check('no catches for the lake: says so, and where the admin reads them in', 'Inga fångster' in pg.inner_text('#hmResult') and 'Admin' in pg.inner_text('#hmResult'), pg.inner_text('#hmResult'))
    b.close()

    # ---- the admin reads a CSV file in ----
    CSV = ('timestamp,competitionId,name,species,cm,lat,lng,lake,,\n'
           '2026-09-26T09:00:00.000Z,regnaren1,Henrik,Abborre,33,"58,886510","15,777774",Regnaren,,// kommentar\n'
           '2026-09-26T09:05:00.000Z,regnaren1,Filip,Gadda,71,58.887421,15.775569,Regnaren,,\n'
           '2026-09-26T09:06:00.000Z,regnaren1,Filip,Gädda,40,,,Regnaren,,\n'
           '2026-05-22T09:00:00.000Z,vagsfjarden4,Camilla,Gos,55,62.92,18.27,Vågsfjärden,,\n'
           '2026-03-28T13:32:32.019Z,malarenOpen,Stisse,Gadda,96,59.452845,17.549482,Mälaren,,\n'
           '2026-09-27T10:07:52.901Z,regnaren1,Filip,Gadda,63,58.99150217888783,15.72027356365297,Östra Vitten,,\n')
    b, ctx, pg, errs = new_page(p, geo=B3, cfg={}, name='Filip')
    pg.wait_for_timeout(1200)
    pg.click('#menuBtn'); pg.click('#menuItemSettings'); pg.wait_for_timeout(200)
    pg.click('#adminOpenBtn'); pg.wait_for_timeout(200); pg.fill('#pinInput', fakefb.TEST_PIN); pg.press('#pinInput', 'Enter'); pg.wait_for_timeout(500)
    check('Admin: "Fångster (heatmap)" with a CSV button', pg.is_visible('#adminCatchBtn') and 'Fångster' in pg.inner_text('#adminBody'))
    pg.set_input_files('#adminCatchFile', files=[{'name': 'fangster.csv', 'mimeType': 'text/csv', 'buffer': CSV.encode('utf-8')}]); pg.wait_for_timeout(1200)
    st = pg.inner_text('#adminCatchStatus')
    docs = pg.evaluate('window.__catchDocs')
    check('read in: Regnaren 2 new, Vågsfjärden 1 new; skipped: 2 in other lakes, 1 without position', 'Regnaren: 2 nya' in st and 'Vågsfjärden: 1 nya' in st and '2 i sjöar som inte finns' in st and '1 utan position' in st, st)
    rr = json.loads(docs['regnaren']['rows'])
    check('...stored in catches/regnaren (comma decimals read right, "Gadda" -> gadda)', len(rr) == 2 and abs(rr[0][5] - 58.88651) < 1e-6 and rr[1][3] == 'gadda', rr)
    pg.set_input_files('#adminCatchFile', files=[{'name': 'fangster.csv', 'mimeType': 'text/csv', 'buffer': CSV.encode('utf-8')}]); pg.wait_for_timeout(1200)
    st = pg.inner_text('#adminCatchStatus')
    check('the same file again: nothing new, nothing written twice', 'inga nya' in st and len(pg.evaluate('window.__catchSets')) == 2, (st, pg.evaluate('window.__catchSets')))
    pg.click('#adminBackBtn'); pg.click('#settingsBackBtn'); pg.wait_for_timeout(300)
    open_heat(pg)
    check('...and the heat map shows them (2 in Regnaren)', heat(pg)['n'] == 2, heat(pg))
    check('no page errors', not errs, errs)
    b.close()
print('\n%d/%d passed' % (sum(results), len(results)))
