# Ledare (Filter, Lager): a list under the weather chip + a crown after the leader's name on the map while a
# competition is on; the 5 longest of each species added up, only catches that count; off by default.
from playwright.sync_api import sync_playwright
import fakefb, json, datetime
from fakefb import new_page
results = []
def check(name, cond, info=''):
    results.append(bool(cond)); print(('PASS ' if cond else 'FAIL ') + name + ('  -- ' + str(info) if info != '' else ''))

B3 = (58.887269, 15.772629); B1 = (58.887421, 15.775569); B4 = (58.88651, 15.777774)
TODAY = datetime.date.today().isoformat()
def ms_ago(minutes): return int((datetime.datetime.now() - datetime.timedelta(minutes=minutes)).timestamp() * 1000)
PHOTO = 'https://res.cloudinary.com/demo/image/upload/w_2000,q_auto,f_auto/v1/fisk.jpg'

live = [dict(fakefb.api_row(ms_ago(30), 'regnaren2', 'Filip', 'gadda', 78, B3[0], B3[1]), approved=True),
        dict(fakefb.api_row(ms_ago(20), 'regnaren2', 'Filip', 'abborre', 22, B3[0], B3[1]), approved=False),   # not counted (API)
        dict(fakefb.api_row(ms_ago(15), 'regnaren2', 'Calle', 'gos', 55, B1[0], B1[1]), approved=True),
        dict(fakefb.api_row(ms_ago(12), 'regnaren2', 'Calle', 'gadda', 40, B1[0], B1[1]), approved=True),       # under 50 cm: not counted
        dict(fakefb.api_row(ms_ago(10), 'regnaren2', 'Calle', 'gadda', 60, B1[0], B1[1]), approved=True),
        dict(fakefb.api_row(ms_ago(8), 'regnaren2', 'Olle', 'abborre', 30, B1[0], B1[1]), approved=True),
        # the same competition in another water (Östra Vitten, inside Regnaren's map) and one without GPS: count in Ledare, not on the heat map
        dict(fakefb.api_row(ms_ago(6), 'regnaren2', 'Olle', 'gadda', 55, 58.991037, 15.714671, lake='Östra Vitten'), approved=True),
        dict(fakefb.api_row(ms_ago(5), 'regnaren2', 'Olle', 'abborre', 26, None, None), approved=True)]
comps = [{'competition_id': 'reg2', 'competition_name': 'Regnaren 2', 'date': TODAY, 'status': 'active', 'water': 'Regnaren'}]
with sync_playwright() as p:
    b, ctx, pg, errs = new_page(p, geo=B3, cfg={'api': {'heatmap': [], 'competitions': comps, 'live': {'reg2': live}},
        'positions': [{'uid': 'kalle', 'name': 'Calle', 'lat': B1[0], 'lon': B1[1], 'ageMin': 0},
                      {'uid': 'olle', 'name': 'Olle', 'lat': B1[0] + 0.00003, 'lon': B1[1], 'ageMin': 0},   # same boat as Calle
                      {'uid': 'pia', 'name': 'Pia', 'lat': B1[0] + 0.004, 'lon': B1[1], 'ageMin': 0}]}, name='Filip')
    pg.wait_for_timeout(2500)
    s = pg.evaluate('window.__ffLeader()')
    check('off by default: no list, no crown', not s['on'] and not s['shown'] and not pg.is_visible('#leadPill') and '👑' not in pg.inner_text('#boatsLayer'), s)
    pg.evaluate("document.getElementById('toggleLeader').click()"); pg.wait_for_timeout(500)
    s = pg.evaluate('window.__ffLeader()')
    check('on: Calle leads with 115 (60 pike + 55 zander; the 40 cm pike is under the minimum), then Olle 111 (other water + no GPS count), then Filip 78 (the perch was not approved)',
          s['shown'] and [(r['who'], r['total']) for r in s['list']] == [('Calle', 115), ('Olle', 111), ('Filip', 78)], s)
    cs = pg.evaluate('window.__ffCatches()')
    check('the heat map data: only the catches in this lake (not Östra Vitten, not the one without GPS)', len(cs) == 6 and not any(c['cm'] in (55, 26) and c['who'] == 'Olle' for c in cs), cs)
    t = pg.evaluate("document.getElementById('leadPill').textContent")
    check('the list under the weather chip: no title, the leader with a crown, you in amber', 'Regnaren 2' not in t and 'Ledare' not in t and 'Calle 👑' in t and pg.evaluate("document.querySelector('#leadPill .ldRow.me .ldW').textContent") == 'Filip', t)
    check('the crown after Calle on the map, not after Pia', pg.evaluate("Array.from(document.querySelectorAll('.boatName')).map(e => e.textContent)") == ['Calle 👑Olle', 'Pia'], pg.evaluate("Array.from(document.querySelectorAll('.boatName')).map(e => e.textContent)"))
    pg.evaluate("Array.from(document.querySelectorAll('#leadPill .ldRow')).filter(r => r.textContent.indexOf('Calle') > -1)[0].click()"); pg.wait_for_timeout(1000)
    bx = pg.evaluate("(() => { const r = document.querySelector('.boatPip').getBoundingClientRect(); return [r.x + r.width / 2, r.y + r.height / 2, innerWidth / 2, innerHeight / 2]; })()")
    check('tap a name in the list: the map centres on that boat', abs(bx[0] - bx[2]) < 40 and abs(bx[1] - bx[3]) < 60, bx)
    pg.evaluate("Array.from(document.querySelectorAll('.boatPip')).filter(e => e.textContent.indexOf('Calle') > -1)[0].click()"); pg.wait_for_timeout(800)
    t = pg.evaluate("document.getElementById('boatInfoCatches').textContent")
    check('tap the boat with two in it: one tight box: no title, each name once over their own catches', pg.evaluate("document.getElementById('boatInfoName').hidden") and t.count('Calle') == 1 and t.count('Olle') == 1 and 'Gädda' in t and '60 cm' in t and '30 cm' in t, t)
    check('...one heading for the competition (its name in orange), each row ends with its water',
          t.count('Fångster i tävlingen') == 1 and pg.evaluate("document.querySelector('#boatInfoCatches .pfComp').textContent") == 'Regnaren 2' and '55 cm (Östra Vitten)' in t and '60 cm (Regnaren)' in t, t)
    pg.evaluate("document.querySelector('#boatInfoCatches .biWho[data-who=\"Olle\"]').click()"); pg.wait_for_timeout(500)
    check("...a name in it opens that person's profile", pg.evaluate("document.getElementById('pfCard').classList.contains('show') && document.getElementById('pfName').textContent") == 'Olle')
    pg.evaluate("document.getElementById('pfClose').click()"); pg.wait_for_timeout(300)
    pg.reload(); pg.wait_for_timeout(2500)
    check('the switch is remembered', pg.evaluate("window.__ffLeader().on && document.getElementById('toggleLeader').checked"))
    pg.evaluate("document.getElementById('toggleLeader').click()"); pg.wait_for_timeout(300)
    check('off again: list and crown gone', not pg.is_visible('#leadPill') and '👑' not in pg.inner_text('#boatsLayer'))
    check('no page errors', not errs, errs)
    b.close()
print('%d/%d passed' % (sum(results), len(results)))
