# The menu's Sjö and Tävling (28-menu.js, Filip 2026-11-05): two rows at the top, each opening its own list.
# Tävling automatically = the one going on on this lake, else Mälaren Open on Mälaren / Fiskfiskarna Open elsewhere;
# one chosen yourself instead. Sjö automatically = the GPS changes the lake at once
# (a note, "Tillbaka till ..." turns it off); a lake chosen yourself turns it off too.
import datetime, time
from playwright.sync_api import sync_playwright
import fakefb
from fakefb import new_page
results = []
def check(name, cond, info=''):
    results.append(bool(cond)); print(('PASS ' if cond else 'FAIL ') + name + ('  -- ' + str(info) if info != '' else ''))

B3 = (58.887269, 15.772629); SIBBO = (58.783, 17.306)
TODAY = datetime.date.today().isoformat()
def comp(cid, name, date, status, water):
    return {'competition_id': cid, 'competition_name': name, 'date': date, 'status': status, 'water': water}
OPENS = [{'id': 'ffopen27', 'serie': 'fiskfiskarna_open', 'namn': 'Fiskfiskarna Open 2027', 'start': '2026-01-01', 'slut': '2099-12-31', 'status': 'aktiv'},
         {'id': 'ffopen26', 'serie': 'fiskfiskarna_open', 'namn': 'Fiskfiskarna Open 2026', 'start': '2026-01-01', 'slut': '2026-10-31', 'status': 'avslutad'},
         {'id': 'malopen', 'serie': 'malaren_open', 'namn': 'Mälaren Open', 'start': '2026-01-01', 'slut': '2099-12-31', 'status': 'aktiv'}]
COMPS = [comp('regn2', 'Regnaren 2', TODAY, 'active', 'Regnaren'), comp('sibbo7', 'Sibbo 7', 'TBD', 'planned', 'Sibbo'),
         comp('regn1', 'Regnaren 1', '2026-09-25', 'done', 'Regnaren')]
def menu_rows(pg): return pg.text_content('#lakeList')
def sub(pg): return pg.text_content('#menuSub')   # (not inner_text: the headings are in capitals on screen)
def lake_of(pg): return pg.evaluate("localStorage.getItem('ffmap_lake_v1')")

with sync_playwright() as p:
    # ---- Tävling: the one going on on this lake; or one chosen ----
    # (an open one's catches have their own code in Fångstloggen -- found by the name)
    OPEN_ROW = dict(fakefb.api_row(int(time.time() * 1000) - 600000, 'fiskfisk_open_27', 'Calle', 'gadda', 70, B3[0], B3[1]), tav='Fiskfiskarna Open 2027', open=True)
    api = {'competitions': COMPS, 'openTavlingar': OPENS, 'heatmap': [OPEN_ROW], 'live': {'regn2': []}}
    b, ctx, pg, errs = new_page(p, geo=B3, cfg={'api': api}, name='Filip')
    pg.wait_for_timeout(1800)
    check('under the title: the competition (Regnaren 2), title 10 px up', pg.is_visible('#compSub') and pg.inner_text('#compSub') == 'Regnaren 2'
          and pg.evaluate("getComputedStyle(document.getElementById('lakeTitle')).top") == '-10px', pg.inner_text('#compSub'))
    check('...the weather chip 14 px up with it', pg.evaluate("getComputedStyle(document.getElementById('wxChip')).marginTop") == '-2px')
    pg.click('#compSub'); pg.wait_for_timeout(300)
    check('...tap = the menu, Välj tävling', pg.is_visible('#menuSub') and 'Välj tävling' in sub(pg), sub(pg)[:80])
    pg.click('#menuSub [data-back]'); pg.wait_for_timeout(200); pg.click('#menuBtn'); pg.wait_for_timeout(300)
    pg.click('#menuBtn'); pg.wait_for_timeout(300)
    t = menu_rows(pg)
    check('menu: Sjö = Regnaren (auto, du är här), Tävling = Regnaren 2 (auto)', 'Regnaren' in t and 'Du är här' in t and 'Regnaren 2' in t and t.count('auto') == 2, t)
    check('...the other menu rows still there', pg.is_visible('#menuItemLog') and pg.is_visible('#menuItemSettings'))
    pg.click('#lakeList [data-sub="comp"]'); pg.wait_for_timeout(300)
    t = sub(pg)
    check('Tävling: the list in place of the menu (Pågår, Kommande, Avslutade)', not pg.is_visible('#menuItemLog') and 'Pågår' in t and 'Kommande' in t and 'Avslutade' in t, t)
    check('...going on: Regnaren 2 + the open ones still going (not Open 2026)', 'Regnaren 2' in t and 'Fiskfiskarna Open 2027' in t and 'Mälaren Open' in t and 'Open 2026' not in t, t)
    check('...Sibbo 7 coming (datum inte bestämt), Regnaren 1 over', 'Sibbo 7' in t and 'datum inte bestämt' in t and 'Regnaren 1' in t, t)
    pg.click('#menuSub [data-comp="ffopen27"]'); pg.wait_for_timeout(600)
    check('choose Fiskfiskarna Open: chosen (Automatiskt off), its live catches fetched', pg.evaluate("localStorage.getItem('ffmap_comp_v1')") == 'ffopen27'
          and 'mnSw on' not in pg.inner_html('#menuSub') and ctx.api.n('fangstlogg') >= 3, ctx.api.hits[-3:])
    check('...its catches by its name (own code fiskfisk_open_27)', pg.evaluate('__ffLive()') == {'comp': 'ffopen27', 'n': 1}, pg.evaluate('__ffLive()'))
    check('...the title row follows', pg.inner_text('#compSub') == 'Fiskfiskarna Open 2027', pg.inner_text('#compSub'))
    pg.click('#menuSub [data-auto="comp"]'); pg.wait_for_timeout(400)
    check('Automatiskt on again: Regnaren 2', pg.evaluate("localStorage.getItem('ffmap_comp_v1')") is None and 'Regnaren 2' in pg.inner_text('#menuSub .menuItem--active'))
    pg.click('#menuSub [data-back]'); pg.wait_for_timeout(300)
    check('back: the menu again', pg.is_visible('#menuItemLog') and not pg.is_visible('#menuSub'))
    pg.click('#lakeList [data-sub="lake"]'); pg.wait_for_timeout(300)
    t = sub(pg)
    check('Sjö: Automatiskt on, the lakes nearest first, Regnaren "du är här"', 'mnSw on' in pg.inner_html('#menuSub') and t.index('Regnaren') < t.index('Östra Vitten') < t.index('Sibbofjärden') and 'du är här' in t, t)
    pg.click('#menuSub [data-lake-id="vitten"]'); pg.wait_for_load_state('load'); pg.wait_for_timeout(1200)
    check('choose Östra Vitten: that lake, Automatiskt off', lake_of(pg) == 'vitten' and pg.evaluate("localStorage.getItem('ffmap_lake_auto_v1')") == '0')
    pg.evaluate("localStorage.setItem('ffmap_comp_v1', 'ffopen27'); localStorage.setItem('ffmap_auto_day_v1', 'Mon Jan 01 2001')")
    pg.reload(); pg.wait_for_timeout(1200)
    check('a new day: Sjö and Tävling Automatiskt again', pg.evaluate("localStorage.getItem('ffmap_lake_auto_v1')") == '1' and pg.evaluate("localStorage.getItem('ffmap_comp_v1')") is None)
    check('no page errors (1)', not errs, errs)
    b.close()

    # ---- no competition on the lake: the open one -- Mälaren Open on Mälaren ----
    api = {'competitions': COMPS[1:], 'openTavlingar': OPENS}
    b, ctx, pg, errs = new_page(p, geo=B3, cfg={'api': api}, name='Filip')
    pg.wait_for_timeout(1500); pg.click('#menuBtn'); pg.wait_for_timeout(300)
    check('nothing on Regnaren: Fiskfiskarna Open 2027 (auto)', 'Fiskfiskarna Open 2027' in menu_rows(pg) and 'Hela året' in menu_rows(pg), menu_rows(pg))
    pg.goto(pg.url.split('?')[0] + '?lake=malaren'); pg.wait_for_timeout(1800); pg.click('#menuBtn'); pg.wait_for_timeout(300)
    check('on Mälaren: Mälaren Open (auto)', 'Mälaren Open' in menu_rows(pg), menu_rows(pg))
    check('no page errors (2)', not errs, errs)
    b.close()

    # ---- Sjö automatically: the GPS at another lake -> that lake at once, a note, a way back ----
    b, ctx, pg, errs = new_page(p, geo=B3, name='Filip')
    ctx.add_init_script("window.__ffNoLakeAuto = false;")
    pg.reload(); pg.wait_for_timeout(1500)
    check('at Regnaren: stays', lake_of(pg) == 'regnaren')
    check('no competition: no row under the title, title where it was', not pg.is_visible('#compSub') and pg.evaluate("getComputedStyle(document.getElementById('lakeTitle')).top") in ('auto', '0px'))
    ctx.set_geolocation({'latitude': SIBBO[0], 'longitude': SIBBO[1], 'accuracy': 8})
    pg.wait_for_timeout(2500); pg.wait_for_load_state('load'); pg.wait_for_timeout(1200)
    check('at Sibbofjärden: the lake changed at once', lake_of(pg) == 'sibbo' and 'Sibbofjärden' in pg.inner_text('#lakeTitle'), lake_of(pg))
    check('...a note: "Du är vid Sibbofjärden", "Tillbaka till Regnaren"', pg.is_visible('#lakeNote') and 'Du är vid Sibbofjärden' in pg.inner_text('#lakeNote') and 'Tillbaka till Regnaren' in pg.inner_text('#lakeNoteBack'), pg.inner_text('#lakeNote'))
    pg.screenshot(path='shot_lakenote.png')
    pg.click('#lakeNoteBack'); pg.wait_for_load_state('load'); pg.wait_for_timeout(2500)
    check('"Tillbaka": Regnaren again, Automatiskt off -- stays though the GPS is at Sibbo', lake_of(pg) == 'regnaren' and pg.evaluate("localStorage.getItem('ffmap_lake_auto_v1')") == '0', lake_of(pg))
    check('no page errors (3)', not errs, errs)
    b.close()
print('\n%d/%d passed' % (sum(results), len(results)))
