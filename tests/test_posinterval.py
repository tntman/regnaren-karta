from playwright.sync_api import sync_playwright
from fakefb import new_page
results = []
def check(name, cond, info=''):
    results.append(bool(cond))
    print(('PASS ' if cond else 'FAIL ') + name + ('  -- ' + str(info) if info != '' else ''))
ME = (58.88951, 15.77759)

def drive(pg, ctx, secs):
    lat = ME[0]
    for i in range(secs):
        lat += 1.03 / 111320.0   # ~2 kn north
        ctx.set_geolocation({'latitude': lat, 'longitude': ME[1], 'accuracy': 5})
        pg.wait_for_timeout(1000)

def gaps(pg):
    t = [x['t'] for x in pg.evaluate('window.__posWrites') if x['id'] == 'filip']
    return [round((b - a) / 1000, 1) for a, b in zip(t, t[1:])]

with sync_playwright() as p:
    # default (no shared setting yet): every 20 s while moving
    b, ctx, pg, errs = new_page(p, geo=ME, cfg={}, name='Filip')
    drive(pg, ctx, 46)
    g = gaps(pg)
    check('default: moving boat shares every ~20 s (not 8 s)', len(g) >= 1 and all(19.5 <= x <= 26 for x in g), g)
    # admin page
    pg.click('#menuBtn'); pg.click('#menuItemSettings'); pg.wait_for_timeout(200)
    pg.click('#adminOpenBtn'); pg.wait_for_timeout(200); pg.fill('#pinInput', '851006'); pg.press('#pinInput', 'Enter'); pg.wait_for_timeout(400)
    check('admin shows 20 s selected', pg.inner_text('#adminPosIntervalSeg .active') == '20 s')
    print('   est:', pg.inner_text('#adminPosIntervalEst'))
    pg.click('#adminPosIntervalSeg button[data-s="30"]'); pg.wait_for_timeout(300)
    check('choosing 30 s saves it for everyone', pg.evaluate('window.__cfgSets')[-1]['posIntervalS'] == 30 and 'Sparat' in pg.inner_text('#adminPosIntervalStatus'), pg.evaluate('window.__cfgSets'))
    check('...and on this phone', pg.evaluate("localStorage.getItem('ffmap_pos_interval_s_v1')") == '30')
    pg.evaluate("window.__setCfg({posIntervalS: 60})"); pg.wait_for_timeout(200)
    check('a change from another admin phone shows up live', pg.inner_text('#adminPosIntervalSeg .active') == '60 s')
    el = pg.query_selector('#adminPosIntervalSeg'); el.scroll_into_view_if_needed(); pg.wait_for_timeout(200)
    pg.screenshot(path='shot_posinterval_admin.png')
    check('no page errors', not errs, errs); b.close()

    # shared setting 10 s is picked up by a normal phone
    b, ctx, pg, errs = new_page(p, geo=ME, cfg={'config': {'posIntervalS': 10}}, name='Filip')
    drive(pg, ctx, 34)
    g = gaps(pg)
    check('shared 10 s setting used by every phone', len(g) >= 2 and all(9.5 <= x <= 15 for x in g), g)
    check('remembered for offline starts', pg.evaluate("localStorage.getItem('ffmap_pos_interval_s_v1')") == '10')
    b.close()

    # rules not updated yet
    b, ctx, pg, errs = new_page(p, geo=ME, cfg={}, name='Filip')
    pg.evaluate("window.__cfgDenied = true"); pg.reload(); pg.wait_for_timeout(1200)
    pg.evaluate("window.__cfgDenied = true")
    pg.click('#menuBtn'); pg.click('#menuItemSettings'); pg.wait_for_timeout(200)
    pg.click('#adminOpenBtn'); pg.wait_for_timeout(200)
    if pg.is_visible('#pinInput'): pg.fill('#pinInput', '851006'); pg.press('#pinInput', 'Enter'); pg.wait_for_timeout(400)
    pg.click('#adminPosIntervalSeg button[data-s="10"]'); pg.wait_for_timeout(300)
    st = pg.inner_text('#adminPosIntervalStatus')
    check('missing Firestore rule -> clear message, still applied on this phone', 'config' in st and pg.inner_text('#adminPosIntervalSeg .active') == '10 s', st)
    check('no page errors (denied)', not errs, errs); b.close()
print('\n%d/%d passed' % (sum(results), len(results)))
