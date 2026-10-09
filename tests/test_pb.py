# PB under a competition (js/71-pb.js): a counted live catch longer than the person's earlier best of the species
# (profile TOP, history, earlier live) = PB; the first fish of a species is not. Yours: a card + "Skicka snabbmess" (the
# bubble's rainbow edge), confetti until closed. Someone else's: a note at the top + confetti for an hour; ✕ = it fades over 30 s.
from playwright.sync_api import sync_playwright
import fakefb, datetime
from fakefb import new_page
results = []
def check(name, cond, info=''):
    results.append(bool(cond)); print(('PASS ' if cond else 'FAIL ') + name + ('  -- ' + str(info) if info != '' else ''))

B3 = (58.887269, 15.772629); B1 = (58.887421, 15.775569)
TODAY = datetime.date.today().isoformat()
def ms_ago(m): return int((datetime.datetime.now() - datetime.timedelta(minutes=m)).timestamp() * 1000)
def fish(m, who, sp, cm, ok=True): return dict(fakefb.api_row(ms_ago(m), 'reg5', who, sp, cm, B1[0], B1[1]), approved=ok)
comps = [{'competition_id': 'reg5', 'competition_name': 'Regnaren 5', 'date': TODAY, 'status': 'active', 'water': 'Regnaren'}]
prof = {'anglers': [{'angler_id': 'A2', 'name': 'Olle'}], 'anglerStats': [{'angler_id': 'A2', 'TOPGädda': 95.0}]}
live = [fish(50, 'Calle', 'gadda', 85), fish(3, 'Calle', 'gadda', 92),      # Calle: 85 then 92 = PB
        fish(4, 'Olle', 'gadda', 90),                                         # Olle: TOP 95 in the profile -> no PB
        fish(5, 'Pia', 'abborre', 40),                                        # Pia: her first perch -> no PB
        fish(40, 'Pia', 'gos', 50), fish(2, 'Pia', 'gos', 60, ok=False)]      # not counted -> no PB
def api(): return dict(prof, heatmap=[], competitions=comps, live={'reg5': live})
def pb(pg): return pg.evaluate('window.__ffPb()')

with sync_playwright() as p:
    b, ctx, pg, errs = new_page(p, geo=B3, name='Filip', cfg={'api': api()})
    pg.wait_for_timeout(3000)
    s = pb(pg)
    check("someone else's PB: the note at the top (as Hotzone's) with who, the fish and the earlier best; confetti; no card",
          s['note'] == 'Calle fick PB! | Gädda 92 cm · förra bästa 85 cm' and s['confetti'] and not s['card'] and pg.evaluate("document.getElementById('pbNote').classList.contains('topNote')"), s)
    check('...only Calle (TOP 95 / a first fish / not counted: nothing)', s['on']['c']['who'] == 'Calle', s['on'])
    check('...the confetti never takes a tap', pg.evaluate("getComputedStyle(document.getElementById('pbConf')).pointerEvents") == 'none')
    pg.screenshot(path='shot_pb_andra.png')
    pg.click('#pbNoteClose'); pg.wait_for_timeout(300); s = pb(pg)
    check('✕: the note gone, the confetti fades over 30 s', s['note'] is None and s['confetti'] and s['fade'] == 30, s)
    pg.reload(); pg.wait_for_timeout(3000); s = pb(pg)
    check('after a reload: closed stays closed, no confetti', s['note'] is None and not s['confetti'] and not s['card'], s)
    check('no page errors', not errs, errs)
    b.close()

    b, ctx, pg, errs = new_page(p, geo=B3, name='Calle', cfg={'api': api()})
    pg.wait_for_timeout(3000)
    s = pb(pg)
    check('your PB: the card (Grattis, the fish, your earlier best), confetti, no note',
          s['card'] and s['note'] is None and s['confetti'] and pg.inner_text('#pbFish') == 'Gädda 92 cm' and pg.inner_text('#pbWas') == 'Ditt förra bästa: 85 cm', s)
    check('...it says the confetti stops when closed', 'Konfettin slutar när du stänger rutan' in pg.inner_text('#pbCard'))
    pg.screenshot(path='shot_pb_mitt.png')
    pg.click('#pbSend'); pg.wait_for_timeout(600); s = pb(pg)
    w = pg.evaluate('window.__posWrites.filter(x => x.msg).slice(-1)[0]')
    check('"Skicka snabbmess": the card closed, the message "PB! Gädda 92 🎉" with the PB mark', not s['card'] and w and w['msg'] == 'PB! Gädda 92 🎉' and w['msgPb'] is True and w['msgSp'] == 'gadda', w)
    check('...the confetti stops at once', not pb(pg)['confetti'] or pb(pg)['fade'] < 1, pb(pg))
    check('...your bubble has the rainbow edge', pg.evaluate("!!document.querySelector('#msgLayer .msgBub.pb')"))
    check('no page errors', not errs, errs)
    b.close()

    b, ctx, pg, errs = new_page(p, geo=B3, name='Filip', cfg={'api': api(), 'positions': [
        {'uid': 'kalle', 'name': 'Calle', 'lat': B1[0], 'lon': B1[1], 'ageMin': 0, 'msg': 'PB! Gädda 92 🎉', 'msgAgeMin': 1, 'msgSp': 'gadda', 'msgPb': True},
        {'uid': 'pia', 'name': 'Pia', 'lat': B1[0] + 0.004, 'lon': B1[1], 'ageMin': 0, 'msg': 'Fisk!!!', 'msgAgeMin': 1}]})
    pg.wait_for_timeout(3000)
    check("someone's PB message: the rainbow edge; an ordinary one not", pg.evaluate("document.querySelectorAll('#msgLayer .msgBub.pb').length") == 1 and pg.evaluate("document.querySelectorAll('#msgLayer .msgBub').length") == 2)
    b.close()

    b, ctx, pg, errs = new_page(p, geo=B3, name='Filip', cfg={'api': dict(api(), competitions=[dict(comps[0], status='planned')])})
    pg.wait_for_timeout(3000)
    check('no competition going on: nothing', pb(pg)['note'] is None and not pb(pg)['confetti'] and not pb(pg)['card'], pb(pg))
    b.close()
print('\n%d/%d passed' % (sum(results), len(results)))
