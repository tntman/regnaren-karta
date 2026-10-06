# Tävlingslåset (tools/PLAN_TAVLINGSLAS.md): spots can only be added / changed / removed from a week before a
# competition on the lake until a week after it. Open: Demo Mode, admin, and when the app doesn't know.
from playwright.sync_api import sync_playwright
import fakefb, datetime
from fakefb import new_page
results = []
def check(name, cond, info=''):
    results.append(bool(cond)); print(('PASS ' if cond else 'FAIL ') + name + ('  -- ' + str(info) if info != '' else ''))

B3 = (58.887269, 15.772629); B1 = (58.887421, 15.775569)
def day(n): return (datetime.date.today() + datetime.timedelta(days=n)).isoformat()
def comp(i, n, status): return {'competition_id': 'r%d' % i, 'competition_name': 'Regnaren %d' % i, 'date': day(n), 'status': status, 'water': 'Regnaren'}
def lock(pg): return pg.evaluate('window.__ffLock()')
def shown(pg, sel): return pg.eval_on_selector(sel, 'e => e.classList.contains("show")')
def docs(pg): return pg.evaluate('Object.keys(window.__wpDocs).map(k => window.__wpDocs[k].name)')
def long_press(pg): pg.mouse.move(150, 300); pg.mouse.down(); pg.wait_for_timeout(700); pg.mouse.up(); pg.wait_for_timeout(600)
def refetch(ctx, pg, comps, down=False):   # (new competitions from the API: the phone's copy away, then a reload)
    ctx.api.competitions = comps; ctx.api.down = down
    pg.evaluate("localStorage.removeItem('ffmap_catches_v1')"); pg.reload(); pg.wait_for_timeout(2500)
def open_mine(pg):
    s = pg.evaluate('window.__ffGeo.screenOf(%f, %f)' % B1); pg.mouse.click(s[0], s[1] - 12); pg.wait_for_timeout(500)

with sync_playwright() as p:
    far = [comp(1, -20, 'done'), comp(5, 20, 'planned')]
    b, ctx, pg, errs = new_page(p, geo=B3, name='Calle', cfg={'lock': True, 'api': {'heatmap': [], 'competitions': far},
        'waypoints': [{'lat': B1[0], 'lon': B1[1], 'name': 'Min plats', 'uid': 'calle', 'by': 'Calle', 'type': 'gadda'}]})
    pg.wait_for_timeout(2500)
    check('no competition within a week: locked', not lock(pg)['allowed'], lock(pg))
    pg.evaluate("window.__setCfg({ posIntervalS: 20, lockOff: true })"); pg.wait_for_timeout(200)
    check('admin turned the lock off for everyone (config): open', lock(pg)['allowed'])
    pg.evaluate("window.__setCfg({ posIntervalS: 20 })"); pg.wait_for_timeout(200)
    check('...on again: locked', not lock(pg)['allowed'])
    n0 = docs(pg)
    long_press(pg)
    at = datetime.date.today() + datetime.timedelta(days=13)
    check('long press: the lock box instead of a spot, nothing written', shown(pg, '#lockCard') and not shown(pg, '#wpSheet') and docs(pg) == n0, (lock(pg), docs(pg)))
    check('...it says when it opens (a week before the next one)', lock(pg)['when'] == 'Öppnar %d/%d inför Regnaren 5.' % (at.day, at.month), lock(pg)['when'])
    pg.screenshot(path='shot_lock.png')
    pg.click('#lockClose'); pg.wait_for_timeout(300)
    check('Stäng closes it', not shown(pg, '#lockCard'))
    open_mine(pg)
    check('your own spot still opens', shown(pg, '#wpSheet') and pg.input_value('#wpName') == 'Min plats')
    pg.fill('#wpName', 'Nytt namn'); pg.click('#wpSave'); pg.wait_for_timeout(300)
    check('Spara: the lock box, the name unchanged', shown(pg, '#lockCard') and docs(pg) == ['Min plats'], docs(pg))
    pg.click('#lockClose'); pg.wait_for_timeout(300)
    pg.click('#wpTypeSeg button[data-type="gos"]'); pg.wait_for_timeout(200)
    check('a type button: the lock box', shown(pg, '#lockCard')); pg.click('#lockClose'); pg.wait_for_timeout(300)
    pg.click('#wpDelete'); pg.wait_for_timeout(300)
    check('Ta bort: the lock box, the spot stays', shown(pg, '#lockCard') and docs(pg) == ['Min plats'])
    pg.click('#lockDemo'); pg.wait_for_timeout(400)
    check('"Öppna Demo Mode": Inställningar, Avancerat open, the sheet closed',
          pg.is_visible('#settingsView') and pg.evaluate("document.querySelector('.setSec[data-sec=adv]').open") and not shown(pg, '#lockCard') and not shown(pg, '#wpSheet'))

    refetch(ctx, pg, [comp(5, 6, 'planned')])
    check('a competition in 6 days: open', lock(pg)['allowed'], lock(pg))
    long_press(pg)
    check('...long press makes a spot and opens it', shown(pg, '#wpSheet') and not shown(pg, '#lockCard') and len(docs(pg)) == 2, docs(pg))
    pg.click('#wpSave'); pg.wait_for_timeout(300)
    refetch(ctx, pg, [comp(4, 0, 'active')]);  check('one going on: open', lock(pg)['allowed'])
    refetch(ctx, pg, [comp(4, -7, 'done')]);   check('ended 7 days ago: still open', lock(pg)['allowed'])
    refetch(ctx, pg, [comp(4, -8, 'done')]);   check('ended 8 days ago: locked', not lock(pg)['allowed'])
    refetch(ctx, pg, [], down=True);           check("the API doesn't answer (no copy): open", lock(pg)['allowed'])
    refetch(ctx, pg, [])
    check('...answering, no competitions: locked + "none planned"', not lock(pg)['allowed'])
    long_press(pg)
    check('...the box says none is planned', lock(pg)['when'] == 'Ingen tävling i Regnaren är planerad just nu.', lock(pg)['when'])
    pg.evaluate("localStorage.setItem('regnaren_demo_mode_v1', '1'); localStorage.setItem('regnaren_demo_since_v1', String(Date.now()))")
    pg.reload(); pg.wait_for_timeout(2500)
    check('Demo Mode: always open', lock(pg)['allowed'])
    check('no page errors', not errs, errs)
    b.close()

    b, ctx, pg, errs = new_page(p, geo=B3, name='Filip', cfg={'lock': True, 'api': {'heatmap': [], 'competitions': far}})
    pg.wait_for_timeout(2500)
    check('Filip, not unlocked: locked like everyone', not lock(pg)['allowed'])
    pg.evaluate("localStorage.setItem('ffmap_admin_unlock_v1', '%s')" % fakefb._PIN_HASH); pg.reload(); pg.wait_for_timeout(2500)
    check('admin (unlocked): always open', lock(pg)['allowed'])
    pg.evaluate("document.querySelector('#adminCompLockSeg button[data-off=\"1\"]').click()"); pg.wait_for_timeout(300)
    c = pg.evaluate("[window.__cfgSets[window.__cfgSets.length - 1], window.__cfgDoc]")
    check('Admin -> Tävlingslåset "Av för alla": saved in config (with the interval, as the rule wants), the button shows it',
          c[0]['lockOff'] is True and c[0]['posIntervalS'] == 20 and c[1]['lockOff'] is True and
          pg.evaluate("document.querySelector('#adminCompLockSeg button[data-off=\"1\"]').classList.contains('active')") and 'Sparat' in pg.inner_text('#adminCompLockStatus'), c)
    pg.evaluate("document.querySelector('#adminCompLockSeg button[data-off=\"0\"]').click()"); pg.wait_for_timeout(300)
    check('..."På" again', pg.evaluate("window.__cfgDoc.lockOff") is False)
    b.close()

    b, ctx, pg, errs = new_page(p, geo=B3, cfg={'api': {'heatmap': [], 'competitions': far}})
    pg.wait_for_timeout(2500)
    check('the other tests: the lock is off in the test browser', lock(pg)['allowed'])
    b.close()
print('%d/%d passed' % (sum(results), len(results)))
