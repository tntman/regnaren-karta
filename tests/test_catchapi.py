# The heat map's catches from Fiskfiskarnas API (made up by fakefb.FakeApi): the history (dashboard.php)
# only for this lake, kept on the phone; fetched again only by the rules (no copy / a competition on or
# due and > 1 h / > 1 day); live (tavling.php bootstrap) while a competition is on, annulled catches gone;
# the API down -> the copy; Inställningar -> Fångstdata shows it all, "Hämta nu" fetches.
from playwright.sync_api import sync_playwright
import fakefb, json, time, datetime
from fakefb import new_page
results = []
def check(name, cond, info=''):
    results.append(bool(cond)); print(('PASS ' if cond else 'FAIL ') + name + ('  -- ' + str(info) if info != '' else ''))

B1 = (58.887421, 15.775569); B4 = (58.88651, 15.777774); B3 = (58.887269, 15.772629)
def ms(day, h, m): return int(__import__('calendar').timegm((2026, 9, day, h, m, 0))) * 1000
TODAY = datetime.date.today().isoformat()
HIST = [fakefb.api_row(ms(26, 9, i), 'regnaren1', 'Filip', 'abborre', 30 + i, B4[0] + i * 0.00004, B4[1]) for i in range(5)]
HIST += [fakefb.api_row(ms(26, 10, 0), 'vitten1', 'Olle', 'gadda', 80, B1[0], B1[1], lake='Östra Vitten'),   # in Regnaren's map, other lake
         fakefb.api_row(ms(26, 10, 1), 'malar1', 'Olle', 'gadda', 81, B1[0], B1[1], lake='Mälaren'),
         fakefb.api_row(ms(26, 10, 2), 'regnaren1', 'Pia', 'gos', 55, B1[0], B1[1], lake='')]                  # no lake name: by the place
def comp(cid, name, date, status, water='Regnaren'):
    return {'competition_id': cid, 'competition_name': name, 'date': date, 'status': status, 'water': water}

def info(pg): return pg.inner_text('#ctInfo')
def n_catches(pg): l = pg.evaluate('window.__ffCatches()'); return None if l is None else len(l)
def set_age(pg, minutes):   # the phone's copy fetched <minutes> ago
    pg.evaluate("m => { var k = 'ffmap_catches_v1', c = JSON.parse(localStorage.getItem(k)); c.at = Date.now() - m * 60000; localStorage.setItem(k, JSON.stringify(c)); }", minutes)
def reload(pg): pg.reload(); pg.wait_for_timeout(2200)

with sync_playwright() as p:
    # ---- no competition: the history, this lake only, kept ----
    b, ctx, pg, errs = new_page(p, geo=B3, cfg={'api': {'heatmap': HIST, 'competitions': [comp('regnaren1', 'Regnaren 1', '2026-09-26', 'done'), comp('vitten1', 'Vitten 1', TODAY, 'active', 'Östra Vitten')]}}, name='Filip')
    pg.wait_for_timeout(1500)
    check('start: the history fetched once, no live (no competition on the lake)', ctx.api.n('dashboard') == 1 and ctx.api.n('bootstrap') == 0, ctx.api.hits)
    ids = [c['who'] + c['sp'] for c in pg.evaluate('window.__ffCatches()')]
    check('...6 catches: Regnaren\'s 5 + the one with no lake name; not Östra Vitten / Mälaren inside the map', len(ids) == 6 and 'Pia' + 'gos' in ids and 'Olle' + 'gadda' not in ids, ids)
    t = info(pg)
    check('Fångstdata: 6 in Regnaren, 8 in all, the copy\'s size, next fetch in a day', '6 i Regnaren · 8 totalt' in t and 'kB i telefonen' in t and '(ett dygn)' in t, t)
    check('...competitions: the last one (Regnaren 1), not Vitten\'s; live off', 'Regnaren 1 · 2026-09-26' in t and 'Vitten' not in t and 'av – ingen tävling pågår' in t, t)
    check('...today: 1 call for the history, some data', 'historik 1 · live 0' in t and '≈ ' in t, t)
    check('the line under the title: "6 fångster · hämtade hh:mm"', pg.inner_text('#setSum-catch').startswith('6 fångster · Hämtade') or '6 fångster · hämtade' in pg.inner_text('#setSum-catch'), pg.inner_text('#setSum-catch'))
    reload(pg)
    check('reload with a fresh copy: not fetched again, the catches still there', ctx.api.n('dashboard') == 1 and n_catches(pg) == 6, (ctx.api.hits, n_catches(pg)))
    set_age(pg, 120); reload(pg)
    check('copy 2 h old, no competition: not fetched (a day)', ctx.api.n('dashboard') == 1, ctx.api.hits)
    set_age(pg, 25 * 60); reload(pg)
    check('copy 25 h old: fetched again', ctx.api.n('dashboard') == 2, ctx.api.hits)
    # ---- the API down: the copy ----
    ctx.api.down = True; set_age(pg, 25 * 60); reload(pg)
    t = info(pg)
    check('API down: the copy\'s 6 catches shown, "ingen anslutning" in Fångstdata', n_catches(pg) == 6 and 'ingen anslutning' in t, (n_catches(pg), t))
    ctx.api.down = False
    ctx.api.heatmap = HIST + [fakefb.api_row(ms(27, 9, 0), 'regnaren1', 'Calle', 'gadda', 70, B4[0], B4[1])]
    pg.evaluate("document.getElementById('ctFetch').click()"); pg.wait_for_timeout(800)
    check('"Hämta nu": fetched, the new catch there, the error gone', n_catches(pg) == 7 and 'Senaste fel' not in info(pg), (n_catches(pg), info(pg)))
    check('no page errors (1)', not errs, errs)
    b.close()

    # ---- a planned competition today: every hour ----
    b, ctx, pg, errs = new_page(p, geo=B3, cfg={'api': {'heatmap': HIST, 'competitions': [comp('regnaren2', 'Regnaren 2', TODAY, 'planned')]}}, name='Filip')
    pg.wait_for_timeout(1500)
    check('planned today: shown under the competitions, next fetch in an hour', 'planerad ' + TODAY in info(pg) and '(tävling)' in info(pg), info(pg))
    set_age(pg, 30); reload(pg)
    check('...copy 30 min old: not fetched', ctx.api.n('dashboard') == 1, ctx.api.hits)
    set_age(pg, 120); reload(pg)
    check('...copy 2 h old: fetched', ctx.api.n('dashboard') == 2, ctx.api.hits)
    check('no page errors (2)', not errs, errs)
    b.close()

    # ---- a competition on: live ----
    v1 = fakefb.api_row(ms(27, 8, 0), 'regnaren3', 'Henrik', 'gadda', 77, B1[0], B1[1])
    v2 = fakefb.api_row(ms(27, 8, 5), 'regnaren3', 'Erika', 'abborre', 41, B4[0], B4[1])
    bad = fakefb.api_row(ms(27, 8, 9), 'regnaren3', 'Magnus', 'gos', 99, B4[0], B4[1])
    void = dict(fakefb.api_row(ms(27, 8, 12), 'regnaren3', 'Magnus', 'gos', 0, None, None), displayValue='VOID', voidRef=bad['timestamp'])
    b, ctx, pg, errs = new_page(p, geo=B3, cfg={'api': {'heatmap': HIST, 'competitions': [comp('regnaren3', 'Regnaren 3', TODAY, 'active')], 'live': {'regnaren3': [v1, v2, bad, void]}}}, name='Filip')
    pg.wait_for_timeout(1500)
    ids = [c['who'] for c in pg.evaluate('window.__ffCatches()')]
    check('active competition: live fetched at the start, its 2 catches added (8)', ctx.api.n('bootstrap') == 1 and len(ids) == 8 and 'Henrik' in ids and 'Erika' in ids, (ctx.api.hits, ids))
    check('...the annulled catch and its VOID row not there', 'Magnus' not in ids, ids)
    t = info(pg)
    check('Fångstdata: live on, every 5 min (heat map off), 2 live catches', 'på – Regnaren 3 pågår' in t and 'var 5:e min' in t and '2 fångster' in t, t)
    check('the line under the title: "Live: Regnaren 3"', 'Live: Regnaren 3' in pg.inner_text('#setSum-catch'), pg.inner_text('#setSum-catch'))
    pg.evaluate("document.getElementById('hmBtn').click()"); pg.wait_for_timeout(500)
    pg.evaluate("document.getElementById('menuItemSettings').click()"); pg.wait_for_timeout(300)
    check('heat map on: every 30 s', 'var 30:e s' in info(pg), info(pg))
    check('...its result line says Live', 'Live' in pg.inner_text('#hmResult'), pg.inner_text('#hmResult'))
    ctx.api.live['regnaren3'] = [v1, v2, bad, void, fakefb.api_row(ms(27, 9, 0), 'regnaren3', 'Calle', 'gos', 50, B4[0], B4[1])]
    pg.wait_for_timeout(31500)
    check('...30 s later: fetched again, the new live catch there', ctx.api.n('bootstrap') == 2 and n_catches(pg) == 9, (ctx.api.n('bootstrap'), n_catches(pg)))
    check('no page errors (3)', not errs, errs)
    b.close()

print('\n%d/%d passed' % (sum(results), len(results)))
