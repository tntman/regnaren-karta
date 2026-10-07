# Tävlingsnotisen (was the lock until 2026-10-07, tools/PLAN_TAVLINGSLAS.md): spots can always be added / changed /
# removed. Outside a competition on the lake (more than a week before / after one) the first change of the day shows a
# note -- no competition now (the next one), Demo Mode, private fishing and open competitions welcome -- and "Fortsätt"
# does what you were doing. At most once a day per lake. Never in Demo Mode, for admin, or when the app doesn't know.
from playwright.sync_api import sync_playwright
import fakefb, datetime
from fakefb import new_page
results = []
def check(name, cond, info=''):
    results.append(bool(cond)); print(('PASS ' if cond else 'FAIL ') + name + ('  -- ' + str(info) if info != '' else ''))

B3 = (58.887269, 15.772629); B1 = (58.887421, 15.775569)
WD = ['måndag', 'tisdag', 'onsdag', 'torsdag', 'fredag', 'lördag', 'söndag']
MON = ['januari', 'februari', 'mars', 'april', 'maj', 'juni', 'juli', 'augusti', 'september', 'oktober', 'november', 'december']
def day(n): return (datetime.date.today() + datetime.timedelta(days=n)).isoformat()
def comp(i, n, status): return {'competition_id': 'r%d' % i, 'competition_name': 'Regnaren %d' % i, 'date': day(n), 'status': status, 'water': 'Regnaren'}
def lock(pg): return pg.evaluate('window.__ffLock()')
def shown(pg, sel): return pg.eval_on_selector(sel, 'e => e.classList.contains("show")')
def docs(pg): return sorted(pg.evaluate('Object.keys(window.__wpDocs).map(k => window.__wpDocs[k].name)'))
def long_press(pg): pg.mouse.move(150, 300); pg.mouse.down(); pg.wait_for_timeout(700); pg.mouse.up(); pg.wait_for_timeout(600)
def forget(pg): pg.evaluate("localStorage.removeItem('ffmap_compnote_v1')")   # (as if a day had gone by)
def refetch(ctx, pg, comps, down=False):   # (new competitions from the API: the phone's copy away, then a reload)
    ctx.api.competitions = comps; ctx.api.down = down
    pg.evaluate("localStorage.removeItem('ffmap_catches_v1')"); forget(pg); pg.reload(); pg.wait_for_timeout(2500)
def open_mine(pg):
    s = pg.evaluate('window.__ffGeo.screenOf(%f, %f)' % B1); pg.mouse.click(s[0], s[1] - 12); pg.wait_for_timeout(500)

with sync_playwright() as p:
    far = [comp(1, -20, 'done'), comp(5, 20, 'planned')]
    b, ctx, pg, errs = new_page(p, geo=B3, name='Calle', cfg={'lock': True, 'api': {'heatmap': [], 'competitions': far},
        'waypoints': [{'lat': B1[0], 'lon': B1[1], 'name': 'Min plats', 'uid': 'calle', 'by': 'Calle', 'type': 'gadda'}]})
    pg.wait_for_timeout(2500)
    check('no competition within a week: not near', not lock(pg)['near'], lock(pg))
    long_press(pg)
    d = datetime.date.today() + datetime.timedelta(days=20)
    check('long press: the note first (nothing written yet)', shown(pg, '#lockCard') and not shown(pg, '#wpSheet') and docs(pg) == ['Min plats'], docs(pg))
    check('...it says no competition now, and the next one with its day',
          pg.inner_text('#lockTitle') == 'Ingen tävling pågår i Regnaren' and lock(pg)['when'] == 'Nästa tävling i Regnaren: Regnaren 5, %s %d %s.' % (WD[d.weekday()], d.day, MON[d.month - 1]), (pg.inner_text('#lockTitle'), lock(pg)['when']))
    t = pg.inner_text('#lockCard')
    check('...Demo Mode to try; private fishing and open competitions welcome; buttons "Demo Mode" and "Fortsätt"',
          'Demo Mode' in t and 'privat' in t and 'open-tävling' in t and pg.inner_text('#lockDemo') == 'Demo Mode' and pg.inner_text('#lockClose') == 'Fortsätt', t)
    check('..."Demo Mode" on one line (no wrap in the button)', pg.evaluate("(e => { var r = document.createRange(); r.selectNodeContents(e); return new Set(Array.from(r.getClientRects()).map(x => Math.round(x.top))).size === 1; })(document.getElementById('lockDemo'))"))
    pg.screenshot(path='shot_lock.png')
    pg.click('#lockClose'); pg.wait_for_timeout(600)
    check('"Fortsätt": the spot is made and its sheet opens', not shown(pg, '#lockCard') and shown(pg, '#wpSheet') and len(docs(pg)) == 2, docs(pg))
    pg.click('#wpSave'); pg.wait_for_timeout(300)
    open_mine(pg)
    pg.fill('#wpName', 'Nytt namn'); pg.click('#wpSave'); pg.wait_for_timeout(300)
    check('the same day: no note again -- Spara saves straight away', not shown(pg, '#lockCard') and 'Nytt namn' in docs(pg), docs(pg))
    forget(pg); open_mine(pg)
    pg.fill('#wpName', 'Tredje namnet'); pg.click('#wpSave'); pg.wait_for_timeout(300)
    check('a day later: Spara shows the note first, the name not saved yet', shown(pg, '#lockCard') and 'Tredje namnet' not in docs(pg), docs(pg))
    pg.click('#lockClose'); pg.wait_for_timeout(400)
    check('..."Fortsätt": saved', 'Tredje namnet' in docs(pg) and not shown(pg, '#lockCard'), docs(pg))
    forget(pg); open_mine(pg)
    pg.click('#wpDelete'); pg.wait_for_timeout(300)
    check('Ta bort: the note first, the spot stays', shown(pg, '#lockCard') and 'Tredje namnet' in docs(pg))
    pg.click('#lockBackdrop', position={'x': 20, 'y': 20}); pg.wait_for_timeout(300)
    check('...a tap beside it: closed, nothing done', not shown(pg, '#lockCard') and 'Tredje namnet' in docs(pg))
    forget(pg); pg.click('#wpTypeSeg button[data-type="gos"]'); pg.wait_for_timeout(200)
    check('a type button: the note', shown(pg, '#lockCard'))
    pg.click('#lockDemo'); pg.wait_for_timeout(400)
    check('"Demo Mode": Inställningar, Avancerat open, the sheet closed',
          pg.is_visible('#settingsView') and pg.evaluate("document.querySelector('.setSec[data-sec=adv]').open") and not shown(pg, '#lockCard') and not shown(pg, '#wpSheet'))

    refetch(ctx, pg, [comp(5, 6, 'planned')])
    check('a competition in 6 days: near', lock(pg)['near'], lock(pg))
    long_press(pg)
    check('...long press makes a spot and opens it, no note', shown(pg, '#wpSheet') and not shown(pg, '#lockCard'), docs(pg))
    pg.click('#wpSave'); pg.wait_for_timeout(300)
    refetch(ctx, pg, [comp(4, 0, 'active')]);  check('one going on: near', lock(pg)['near'])
    refetch(ctx, pg, [comp(4, -7, 'done')]);   check('ended 7 days ago: still near', lock(pg)['near'])
    refetch(ctx, pg, [comp(4, -8, 'done')]);   check('ended 8 days ago: not near', not lock(pg)['near'])
    refetch(ctx, pg, [], down=True);           check("the API doesn't answer (no copy): no note", lock(pg)['near'])
    refetch(ctx, pg, [{'competition_id': 'r9', 'competition_name': 'Regnaren 9', 'date': 'TBD', 'status': 'planned', 'water': 'Regnaren'}])
    long_press(pg)
    check('a planned one without a date: "(datum inte bestämt)"', lock(pg)['when'] == 'Nästa tävling i Regnaren: Regnaren 9 (datum inte bestämt).', lock(pg)['when'])
    pg.click('#lockClose'); pg.wait_for_timeout(400); pg.click('#wpSave'); pg.wait_for_timeout(300)
    refetch(ctx, pg, [])
    long_press(pg)
    check('none at all: "none planned"', lock(pg)['when'] == 'Ingen tävling i Regnaren är planerad just nu.', lock(pg)['when'])
    pg.click('#lockClose'); pg.wait_for_timeout(400); pg.click('#wpSave'); pg.wait_for_timeout(300)
    pg.evaluate("localStorage.setItem('regnaren_demo_mode_v1', '1'); localStorage.setItem('regnaren_demo_since_v1', String(Date.now()))")
    pg.reload(); pg.wait_for_timeout(2500)
    check('Demo Mode: never the note', lock(pg)['near'])
    check('no page errors', not errs, errs)
    b.close()

    b, ctx, pg, errs = new_page(p, geo=B3, name='Filip', cfg={'lock': True, 'api': {'heatmap': [], 'competitions': far}})
    pg.wait_for_timeout(2500)
    check('Filip, not unlocked: the note like everyone', not lock(pg)['near'])
    pg.evaluate("localStorage.setItem('ffmap_admin_unlock_v1', '%s')" % fakefb._PIN_HASH); pg.reload(); pg.wait_for_timeout(2500)
    check('admin (unlocked): never the note', lock(pg)['near'])
    check('Admin: no "Tävlingslåset" any more (nothing to lock)', pg.query_selector('#adminCompLockSeg') is None)
    b.close()

    b, ctx, pg, errs = new_page(p, geo=B3, cfg={'api': {'heatmap': [], 'competitions': far}})
    pg.wait_for_timeout(2500)
    check('the other tests: no note in the test browser', lock(pg)['near'])
    b.close()
print('\n%d/%d passed' % (sum(results), len(results)))
