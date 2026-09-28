from playwright.sync_api import sync_playwright
from fakefb import new_page
import json

results = []
def check(name, cond, info=''):
    results.append(bool(cond))
    print(('PASS ' if cond else 'FAIL ') + name + ('  -- ' + str(info) if info != '' else ''))

ME = (58.88951, 15.77759)
cfg = {'waypoints': [
    {'lat': 58.8898, 'lon': 15.7784, 'name': 'Gammal vik', 'uid': 'filip', 'by': 'Filip'},            # old spot, no type
    {'lat': 58.8893, 'lon': 15.7770, 'name': 'Gös 2', 'uid': 'filip', 'by': 'Filip', 'type': 'gos'},
    {'lat': 58.8890, 'lon': 15.7800, 'name': 'Kalles gäddgrund', 'uid': 'kalle', 'by': 'Calle', 'type': 'gadda'},
]}
# the stub copies only known fields -> patch it to keep "type"
import fakefb
fakefb.FAKE_FIREBASE_JS = fakefb.FAKE_FIREBASE_JS.replace(
    "wpDocs['w'+i] = { lat:w.lat, lon:w.lon, name:w.name, uid:w.uid, by:w.by||w.uid, lake:'regnaren', createdAt: ts(now - 3600000) };",
    "wpDocs['w'+i] = { lat:w.lat, lon:w.lon, name:w.name, type:w.type, uid:w.uid, by:w.by||w.uid, lake:'regnaren', createdAt: ts(now - 3600000) };")
from fakefb import new_page

def pin_info(pg):
    return pg.evaluate("""() => Array.from(document.querySelectorAll('#waypoints .wpPin')).map(e => ({
        cls: e.className, bg: getComputedStyle(e).backgroundColor, border: getComputedStyle(e).borderTopColor,
        radius: getComputedStyle(e).borderTopLeftRadius + '/' + getComputedStyle(e).borderBottomLeftRadius,
        iconShown: getComputedStyle(e.querySelector('.pinHead')).display !== 'none',
        fish: e.querySelector('svg').getAttribute('viewBox') === '0 0 384 384' }))""")

with sync_playwright() as p:
    b, ctx, pg, errs = new_page(p, geo=ME, cfg=cfg, name='Filip')
    pg.wait_for_timeout(500)
    info = pin_info(pg)
    for x in info: print('   pin:', x)
    old = [x for x in info if 'wpPin--mark' in x['cls']]
    check('old spot without type shows as Markering (dot, neutral)', len(old) == 1 and not old[0]['fish'] and old[0]['bg'] == 'rgb(228, 233, 236)')
    gos = [x for x in info if 'wpPin--gos' in x['cls']][0]
    check('Gös pin: #FFD21A + fish', gos['bg'] == 'rgb(255, 210, 26)' and gos['fish'])
    other = [x for x in info if 'wpPin--other' in x['cls']][0]
    check("others' Gädda spot: #35D24A drop shape like mine, no fish", other['bg'] == 'rgb(53, 210, 74)' and other['radius'] == '50%/0px' and not other['iconShown'], other)
    check('pins have a white outline', gos['border'] == 'rgb(255, 255, 255)', gos['border'])

    # new spot
    pg.click('#addHereBtn'); pg.wait_for_timeout(900)
    act = pg.eval_on_selector('#wpTypeSeg .active', 'e=>e.textContent')
    check('new spot: type picker, Markering chosen', act == 'Markering', act)
    check('new spot name "Markering 2" (the old spot counts as a marking)', pg.input_value('#wpName') == 'Markering 2', pg.input_value('#wpName'))
    pg.screenshot(path='./shot_types_sheet.png')
    pg.click('#wpTypeSeg button[data-type="gos"]'); pg.wait_for_timeout(100)
    check('Gös -> "Gös 3" (you already have Gös 2)', pg.input_value('#wpName') == 'Gös 3', pg.input_value('#wpName'))
    pg.click('#wpTypeSeg button[data-type="abborre"]'); pg.wait_for_timeout(100)
    check('Abborre -> "Abborre 1"', pg.input_value('#wpName') == 'Abborre 1', pg.input_value('#wpName'))
    pg.screenshot(path='./shot_types_sheet_abborre.png')
    pg.click('#wpSave'); pg.wait_for_timeout(400)
    info = pin_info(pg)
    ab = [x for x in info if 'wpPin--abborre' in x['cls']]
    check('saved: orange Abborre pin with fish', len(ab) == 1 and ab[0]['bg'] == 'rgb(255, 122, 26)' and ab[0]['fish'])

    # own typed name is kept when switching type
    pg.click('#addHereBtn'); pg.wait_for_timeout(900)
    pg.fill('#wpName', 'Stenen vid udden')
    pg.click('#wpTypeSeg button[data-type="gadda"]'); pg.wait_for_timeout(100)
    check('your own name is kept when you switch type', pg.input_value('#wpName') == 'Stenen vid udden')
    pg.click('#wpSave'); pg.wait_for_timeout(400)

    # someone else's spot: type shown, not changeable
    pg.evaluate("""() => { var e = document.querySelector('#waypoints .wpPin--other'); e.click(); }"""); pg.wait_for_timeout(400)
    dis = pg.eval_on_selector_all('#wpTypeSeg button', 'els => els.every(b => b.disabled)')
    check("someone else's spot: type shown, buttons locked", dis and pg.eval_on_selector('#wpTypeSeg .active', 'e=>e.textContent') == 'Gädda')
    pg.click('#wpCancel'); pg.wait_for_timeout(300)

    # log icons
    pg.click('#menuBtn'); pg.click('#menuItemLog'); pg.wait_for_timeout(300)
    sw = pg.eval_on_selector_all('#logList .logItem', 'els => els.map(e => e.querySelector(".logTitle").textContent + ":" + e.querySelector(".visSwatch").className)')
    for x in sw: print('   log:', x)
    check('log list shows type colours', any('Abborre 1' in x and 'ws-abborre' in x for x in sw) and any('Gammal vik' in x and 'ws-mark' in x for x in sw))
    pg.screenshot(path='./shot_types_log.png')
    pg.click('#logBackBtn'); pg.wait_for_timeout(200)
    pg.screenshot(path='./shot_types_map.png')
    check('no page errors', not errs, errs)
    b.close()
print('\n%d/%d passed' % (sum(results), len(results)))
