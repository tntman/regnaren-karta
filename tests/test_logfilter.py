# Logg: the filter on top -- search (name or who), Alla/Mina/Andras, the types as Filter's dots. Only the list; who + types kept.
from playwright.sync_api import sync_playwright
from fakefb import new_page
results = []
def check(name, cond, info=''):
    results.append(bool(cond)); print(('PASS ' if cond else 'FAIL ') + name + ('  -- ' + str(info) if info != '' else ''))

B3 = (58.887269, 15.772629)
T = [('abborre', 'Kanten vid udden', 'Testare'), ('gadda', 'Vassen norr', 'Calle'), ('mark', 'Grund 3 m', 'Testare'), ('gos', 'Djuphålan', 'Olle'),
     ('abborre', 'Stenrevet', 'Calle'), ('fara', 'Sten under ytan', 'Pia'), ('hem', 'Bryggan', 'Testare')]
wps = [{'lat': B3[0] + i * 0.0004, 'lon': B3[1], 'name': n, 'uid': 'testare' if who == 'Testare' else who.lower(), 'by': who, 'type': t}
       for i, (t, n, who) in enumerate(T)]
def rows(pg): return sorted(pg.evaluate("Array.from(document.querySelectorAll('#logList .logTitle')).map(e => e.textContent)"))
def count(pg): return pg.evaluate("(e => e.hidden ? '' : e.textContent)(document.getElementById('logCount'))")
def dot(pg, t): pg.click('#logTypes input[data-type="%s"]' % t); pg.wait_for_timeout(200)

with sync_playwright() as p:
    b, ctx, pg, errs = new_page(p, geo=B3, cfg={'waypoints': wps})
    pg.wait_for_timeout(2500)
    pg.evaluate("document.getElementById('menuItemLog').click()"); pg.wait_for_timeout(500)
    check('all 7, no count line, "Alla" chosen, 7 type dots all filled', len(rows(pg)) == 7 and count(pg) == '' and
          pg.evaluate("document.querySelector('#logWhoSeg .active').textContent") == 'Alla' and pg.evaluate("document.querySelectorAll('#logTypes input:checked').length") == 7)
    pg.click('#logWhoSeg button[data-who="mine"]'); pg.wait_for_timeout(200)
    check('Mina: only yours, "Visar 3 av 7"', rows(pg) == ['Bryggan', 'Grund 3 m', 'Kanten vid udden'] and count(pg) == 'Visar 3 av 7', (rows(pg), count(pg)))
    pg.click('#logWhoSeg button[data-who="others"]'); pg.wait_for_timeout(200)
    check('Andras: the others', rows(pg) == ['Djuphålan', 'Sten under ytan', 'Stenrevet', 'Vassen norr'], rows(pg))
    dot(pg, 'fara')
    check('a type dot off: that type gone (Fara too -- only the list)', 'Sten under ytan' not in rows(pg) and len(rows(pg)) == 3, rows(pg))
    pg.click('#logWhoSeg button[data-who="all"]'); pg.fill('#logSearch', 'calle'); pg.wait_for_timeout(200)
    check('search a person', rows(pg) == ['Stenrevet', 'Vassen norr'], rows(pg))
    pg.fill('#logSearch', 'STEN'); pg.wait_for_timeout(200)
    check('search a name (any case; Fara still off)', rows(pg) == ['Stenrevet'], rows(pg))
    pg.fill('#logSearch', 'du'); pg.wait_for_timeout(200)
    check('"du" = your own', rows(pg) == ['Bryggan', 'Grund 3 m', 'Kanten vid udden'], rows(pg))
    pg.fill('#logSearch', 'xyz'); pg.wait_for_timeout(200)
    check('nothing found: a line saying so', rows(pg) == [] and 'Inga platser med det här filtret' in pg.inner_text('#logList'))
    pg.fill('#logSearch', '')
    check('the map unchanged: Fara still on the map', pg.evaluate("document.querySelectorAll('#waypoints .wpFara').length") >= 1)
    pg.reload(); pg.wait_for_timeout(2500)
    pg.evaluate("document.getElementById('menuItemLog').click()"); pg.wait_for_timeout(500)
    check('after a restart: the types kept (Fara off), Alla, search empty', len(rows(pg)) == 6 and count(pg) == 'Visar 6 av 7' and pg.input_value('#logSearch') == '', (rows(pg), count(pg)))
    pg.click('#logEmpty' if pg.query_selector('#logEmpty') else '#logList .logItem')
    check('tap a row: the map', pg.evaluate("!document.getElementById('logView').classList.contains('show')"))
    check('no page errors', not errs, errs)
    b.close()
print('\n%d/%d passed' % (sum(results), len(results)))
