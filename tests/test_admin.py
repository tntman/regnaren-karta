import fakefb
from playwright.sync_api import sync_playwright
from fakefb import new_page, login
import time

results = []
def check(name, cond, info=''):
    results.append(bool(cond))
    print(('PASS ' if cond else 'FAIL ') + name + ('  -- ' + str(info) if info != '' else ''))

ME = (58.88951, 15.77759)
cfg = {
  'waypoints': [
    {'lat':58.8898,'lon':15.7784,'name':'Kalles grund','uid':'kalle','by':'Calle'},
    {'lat':58.8893,'lon':15.7770,'name':'Djuphålan','uid':'kalle','by':'Calle'},
    {'lat':58.8890,'lon':15.7800,'name':'Min vik','uid':'filip','by':'Filip'},
    {'lat':58.8900,'lon':15.7760,'name':'Stenen; "bra"','uid':'pia','by':'Pia'}],
  'positions': [
    {'uid':'kalle','name':'Calle','lat':58.8960,'lon':15.7820,'ageMin':1},
    {'uid':'pia','name':'Pia','lat':58.8830,'lon':15.7690,'ageMin':30},
    {'uid':'gammal','name':'Gammal','lat':58.8830,'lon':15.7690,'ageMin':300}]}

with sync_playwright() as p:
    # not Filip -> no admin at all
    b, ctx, pg, errs = new_page(p, geo=ME, cfg=cfg, name='Calle')
    pg.click('#menuBtn'); pg.click('#menuItemSettings'); pg.wait_for_timeout(200)
    check('admin row hidden for other names', not pg.is_visible('#adminRow'))
    b.close()

    b, ctx, pg, errs = new_page(p, geo=ME, cfg=cfg, name='Filip')
    pg.click('#menuBtn'); pg.click('#menuItemSettings'); pg.wait_for_timeout(200)
    check('admin row visible for Filip', pg.is_visible('#adminRow'))
    pg.click('#adminOpenBtn'); pg.wait_for_timeout(300)
    check('PIN asked first', pg.eval_on_selector('#pinModal', 'e=>e.classList.contains("show")'))
    pg.fill('#pinInput', '123456'); pg.click('#pinOk'); pg.wait_for_timeout(300)
    check('wrong PIN rejected', pg.is_visible('#pinError') and not pg.eval_on_selector('#adminView','e=>e.classList.contains("show")'))
    pg.fill('#pinInput', fakefb.TEST_PIN); pg.press('#pinInput', 'Enter'); pg.wait_for_timeout(400)
    check('right PIN opens admin', pg.eval_on_selector('#adminView','e=>e.classList.contains("show")'))
    check('PIN itself not in page source', fakefb.TEST_PIN not in pg.content())

    stats = pg.eval_on_selector_all('.statTile', 'els => els.map(e => e.querySelector(".statLabel").textContent + "=" + e.querySelector(".statValue").textContent)')
    print('   stats:', stats)
    check('stats: 4 spots, users, 1 live boat (+you)', 'Fiskeplatser totalt=4' in stats and 'Användare=4' in stats, stats)
    users = pg.eval_on_selector_all('.adminUserRow', 'els => els.map(e => e.innerText.replace(/\\n/g," | "))')
    for u in users: print('   user:', u)
    check('user list shows statuses + counts', any('Calle' in u and 'På kartan nu' in u and '2 fiskeplatser' in u for u in users)
          and any('Pia' in u and 'Grå på kartan' in u for u in users)
          and any('Gammal' in u and 'Inte på kartan' in u for u in users))
    usage = pg.inner_text('#adminUsage')
    print('   usage:', usage.replace('\n', ' / '))
    check('usage counter shows reads', 'Reads:' in usage)
    pg.screenshot(path='./shot_admin_top.png', full_page=False)

    # hide one boat
    pg.evaluate('window.__posWrites.length = 0')
    pg.on('dialog', lambda d: d.accept())
    pg.click('.adminUserRow:has-text("Calle") button:has-text("Dölj båt")'); pg.wait_for_timeout(300)
    w = pg.evaluate('window.__posWrites')
    check('Dölj båt expires that position', any(x['id'] == 'kalle' and x['updatedAtMs'] == 0 for x in w), w)
    pg.click('#adminHideStale'); pg.wait_for_timeout(300)
    w = pg.evaluate('window.__posWrites')
    check('Dölj grå båtar hides Pia', any(x['id'] == 'pia' and x['updatedAtMs'] == 0 for x in w), w)

    # export GPX / CSV (test the download path: no share sheet, which e.g. Edge on Windows has)
    pg.evaluate("Object.defineProperty(navigator, 'canShare', { value: undefined, configurable: true })")
    with pg.expect_download() as dl:
        pg.click('#adminExportGpx')
    gpx = open(dl.value.path(), encoding='utf-8').read()
    check('GPX export: 4 waypoints, escaped', gpx.count('<wpt ') == 4 and 'Stenen; &quot;bra&quot;' in gpx and 'sparad av Calle' in gpx, dl.value.suggested_filename)
    with pg.expect_download() as dl:
        pg.click('#adminExportCsv')
    csv = open(dl.value.path(), encoding='utf-8-sig').read()
    print('   csv:\n     ' + csv.strip().replace('\n', '\n     '))
    check('CSV export: header + 4 rows', csv.strip().count('\n') == 4 and csv.startswith('Namn;Typ;Latitud'))
    # unlocked admin: can always change / delete someone else's spot (no switch any more)
    check('no "Redigera allas fiskeplatser" switch', pg.query_selector('#adminEditAllToggle') is None)
    pg.click('#adminBackBtn'); pg.click('#settingsBackBtn'); pg.wait_for_timeout(300)
    pg.click('#menuBtn'); pg.click('#menuItemLog'); pg.wait_for_timeout(200)
    pg.click('.logItem:has-text("Kalles grund")'); pg.wait_for_timeout(700)
    pg.evaluate("""() => { var els = document.querySelectorAll('.wpPin--other'); var best=null, bd=1e9;
       els.forEach(e => { var r=e.getBoundingClientRect(); var d=Math.hypot(r.left+r.width/2-195, r.top+r.height/2-422); if(d<bd){bd=d;best=e;} }); best.click(); }""")
    pg.wait_for_timeout(400)
    check("admin can edit someone else's spot (type buttons, Ta bort, Spara + an ADMIN tag)", pg.is_visible('#wpDelete') and pg.is_enabled('#wpName') and pg.is_visible('#wpTypeSeg') and pg.inner_text('#wpMeta .adminTag') == 'ADMIN', pg.inner_text('#wpMeta'))
    bb = pg.eval_on_selector_all('.sheetActs button', 'e => e.filter(x => x.offsetParent).map(x => [x.id, x.getBoundingClientRect().left])')
    check('Ta bort: a bin at the far left, away from Spara', bb[0][0] == 'wpDelete' and bb[-1][0] == 'wpSave', bb)
    pg.click('#wpDelete'); pg.wait_for_timeout(300)
    check('...pressed: the spot gone from the map, "… borttagen · Ångra" -- not deleted in the database yet', pg.is_visible('#undoToast') and 'Kalles grund' in pg.inner_text('#undoTxt') and
          any(d.get('name') == 'Kalles grund' for d in pg.evaluate('Object.values(window.__wpDocs)')))
    pg.click('#undoBtn'); pg.wait_for_timeout(300)
    check('"Ångra": the spot back, nothing deleted', not pg.is_visible('#undoToast') and any(d.get('name') == 'Kalles grund' for d in pg.evaluate('Object.values(window.__wpDocs)')))
    pg.evaluate("""() => { var els = document.querySelectorAll('.wpPin--other'); var best=null, bd=1e9;
       els.forEach(e => { var r=e.getBoundingClientRect(); var d=Math.hypot(r.left+r.width/2-195, r.top+r.height/2-422); if(d<bd){bd=d;best=e;} }); best.click(); }""")
    pg.wait_for_timeout(400); pg.click('#wpDelete'); pg.wait_for_timeout(300)
    pg.click('#menuBtn'); pg.click('#menuItemLog'); pg.wait_for_timeout(300)
    titles = pg.eval_on_selector_all('#logList .logTitle', 'e=>e.map(x=>x.textContent)')
    check('...and delete it (gone from the Logg at once)', 'Kalles grund' not in titles and len(titles) == 3, titles)
    pg.wait_for_timeout(6300)
    check('...after 6 s: really deleted, for everyone', not any(d.get('name') == 'Kalles grund' for d in pg.evaluate('Object.values(window.__wpDocs)')))
    pg.click('#logBackBtn'); pg.wait_for_timeout(200)

    # remembered after reload; lock
    pg.reload(); pg.wait_for_timeout(900)
    pg.click('#menuBtn'); pg.click('#menuItemSettings'); pg.wait_for_timeout(200)
    pg.click('#adminOpenBtn'); pg.wait_for_timeout(300)
    check('unlock remembered on this device', pg.eval_on_selector('#adminView','e=>e.classList.contains("show")') and not pg.eval_on_selector('#pinModal','e=>e.classList.contains("show")'))
    pg.click('#adminLock'); pg.wait_for_timeout(200)
    pg.click('#adminOpenBtn'); pg.wait_for_timeout(300)
    check('after "Lås" the PIN is asked again', pg.eval_on_selector('#pinModal','e=>e.classList.contains("show")'))
    pg.click('#pinCancel'); pg.wait_for_timeout(200)

    # logout -> admin gone for the next person
    pg.click('#logoutBtn'); pg.wait_for_timeout(200)
    login(pg, 'Calle'); pg.wait_for_timeout(600)
    pg.click('#menuBtn'); pg.click('#menuItemSettings'); pg.wait_for_timeout(200)
    check('logged in as someone else -> no admin', not pg.is_visible('#adminRow'))
    check('no page errors', not errs, errs)
    # result first: Playwright 1.35 + Edge can crash while closing after a download
    print('\n%d/%d passed' % (sum(results), len(results)), flush=True)
    b.close()
