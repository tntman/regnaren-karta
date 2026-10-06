# Kartanalys "Fiska nu": the competitions' catches weighed by how close they are to now (day of the year, any year,
# and time of day) -> the 5 places with the biggest share, % per place, numbered on the map and in a list.
# Species buttons (Alla first), "När" a few hours ahead, too few catches -> a text instead.
from playwright.sync_api import sync_playwright
import fakefb, time, math
from fakefb import new_page
results = []
def check(name, cond, info=''):
    results.append(bool(cond)); print(('PASS ' if cond else 'FAIL ') + name + ('  -- ' + str(info) if info != '' else ''))
B3 = (58.887269, 15.772629)
def an(pg): return pg.evaluate('window.__ffAnalysis()')
def rows(pg): return pg.eval_on_selector_all('#anListBox .li', 'e => e.map(x => x.innerText.replace(/\\s+/g, " "))')

with sync_playwright() as p:
    b, ctx, pg, errs = new_page(p, geo=B3, cfg={}, name='Filip')
    pg.wait_for_timeout(2000)
    # three places in water, far apart
    cand = pg.evaluate("""() => { var out = [];
      for (var la = 58.882; la < 58.893; la += 0.0004) for (var lo = 15.762; lo < 15.792; lo += 0.0006){ var d = __ffGeo.depthAt(la, lo); if (d != null && d > 2) out.push([la, lo]); }
      return out; }""")
    def m(a, c): return math.hypot((a[0] - c[0]) * 111320, (a[1] - c[1]) * 111320 * math.cos(math.radians(a[0])))
    P = [cand[len(cand) // 2]]
    for c in cand:
        if len(P) < 3 and all(m(c, q) > 450 for q in P): P.append(c)
    check('made-up places: three in water, > 450 m apart', len(P) == 3, P)
    now = time.time() * 1000; Y = 365 * 864e5; H = 3600e3
    def near(pl, i): return (pl[0] + (i % 3 - 1) * 0.00008, pl[1] + (i // 3 % 3 - 1) * 0.00012)
    R = [fakefb.api_row(now - Y + i * 60000, 'regnaren1', 'A%d' % i, 'gos', 50, *near(P[0], i)) for i in range(8)]           # a year ago, this hour
    R += [fakefb.api_row(now - Y + 8 * H + i * 60000, 'regnaren1', 'B%d' % i, 'abborre', 30, *near(P[1], i)) for i in range(12)]   # 8 h later in the day
    R += [fakefb.api_row(now - Y - 40 * 864e5 + i * 60000, 'regnaren1', 'C%d' % i, 'gadda', 70, *near(P[2], i)) for i in range(5)]  # 40 days earlier
    ctx.api.heatmap = R
    pg.evaluate("document.getElementById('ctFetch').click()"); pg.wait_for_timeout(600)
    pg.click('#anBtn'); pg.wait_for_timeout(1200)
    segs = pg.eval_on_selector_all('#anCatSeg button', 'e => e.map(x => x.textContent)')
    check('Kartanalys: a fifth tab "Fiska nu", right of Liknande', segs[-2:] == ['Liknande', 'Fiska nu'], segs)
    pg.click('#anCatSeg button[data-cat="now"]'); pg.wait_for_timeout(2000)
    a = an(pg)
    chips = pg.eval_on_selector_all('#anNowChips button', 'e => e.map(x => [x.textContent, x.classList.contains("on")])')
    check('...straight on with Alla; the species with their numbers', a['mode'] == 'n_all' and chips == [['Alla 25', True], ['Abborre 12', False], ['Gädda 5', False], ['Gös 8', False]], (a, chips))
    r = rows(pg)
    check('...a list: the place caught at this time (Gös, a year ago this hour) first, with the biggest %', len(r) >= 2 and r[0].startswith('1') and 'Gös 8' in r[0] and 'Åk hit' in r[0], r)
    pct = [int(x.split('%')[0].split()[-1]) for x in r]
    check('...the % go down the list', pct == sorted(pct, reverse=True) and pct[0] > 50, pct)
    check('...numbered on the map like the list (orange), the places lit', a['ready'] and a['n'] > 0 and pg.eval_on_selector_all('#anLabels .anLbl.now', 'e => e.map(x => x.textContent)') == [str(i + 1) for i in range(len(r))], a)
    check('...the top row: "Bäst nu"', 'Bäst nu' in pg.inner_text('#anResult'), pg.inner_text('#anResult'))
    pg.click('#anPanel .pnInfoBtn'); pg.wait_for_timeout(500)
    info = pg.inner_text('#anPanel .pnInfo')
    check('ⓘ: what it does and what % means, in plain words', 'Fiska nu visar var gruppen har fått mest fisk' in info and 'inte en garanti' in info and 'Underlag' in info, info[:300])
    pg.click('#anPanel .pnInfoBtn'); pg.wait_for_timeout(400)
    # "När": 8 hours ahead -- the abborre caught later in the day come first
    pg.evaluate("() => { var e = document.getElementById('anNowH'); e.value = 8; e.dispatchEvent(new Event('input', { bubbles: true })); }"); pg.wait_for_timeout(1200)
    r8 = rows(pg)
    check('"När" +8 h: the place caught later in the day first ("Bäst kl …")', r8 and 'Abborre 12' in r8[0] and 'Bäst kl' in pg.inner_text('#anResult'), (r8, pg.inner_text('#anResult')))
    pg.evaluate("() => { var e = document.getElementById('anNowH'); e.value = 0; e.dispatchEvent(new Event('input', { bubbles: true })); }"); pg.wait_for_timeout(1000)
    # a species with too few catches: a text, no tips
    pg.click('#anNowChips button[data-m="n_gos"]'); pg.wait_for_timeout(1200)
    check('Gös (8 catches): too few -- a text instead of tips, nothing lit', 'För få' in pg.inner_text('#anResult') and not an(pg)['ready'] and not rows(pg), pg.inner_text('#anResult'))
    pg.click('#anNowChips button[data-m="n_all"]'); pg.wait_for_timeout(1500)
    # tap a row: the map shows the place (the panel stays); "Åk hit": the lead line goes there
    pg.click('#anListBox .li[data-row="2"] .mid'); pg.wait_for_timeout(800)
    check('...tap a row: the panel stays open', pg.is_visible('#anPanel') and pg.evaluate("document.getElementById('anPanel').classList.contains('show')"))
    pg.click('#anListBox .li[data-row="1"] button[data-go]'); pg.wait_for_timeout(800)
    check('..."Åk hit": the panel closes, the place gets the lead line', not pg.evaluate("document.getElementById('anPanel').classList.contains('show')"))
    check('no page errors', not errs, errs)
    b.close()
print('\n%d/%d passed' % (sum(results), len(results)))
