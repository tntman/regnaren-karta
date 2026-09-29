from playwright.sync_api import sync_playwright
import fakefb
fakefb.FAKE_FIREBASE_JS = fakefb.FAKE_FIREBASE_JS.replace(
    "wpDocs['w'+i] = { lat:w.lat, lon:w.lon, name:w.name, uid:w.uid,",
    "wpDocs['w'+i] = { lat:w.lat, lon:w.lon, name:w.name, type:w.type, uid:w.uid,")
from fakefb import new_page

results = []
def check(name, cond, info=''):
    results.append(bool(cond))
    print(('PASS ' if cond else 'FAIL ') + name + ('  -- ' + str(info) if info != '' else ''))

ME=(58.88951,15.77759)
cfg={'waypoints':[
 {'lat':58.8898,'lon':15.7784,'name':'Min gös','uid':'filip','by':'Filip','type':'gos'},
 {'lat':58.8891,'lon':15.7766,'name':'Min markering','uid':'filip','by':'Filip'},
 {'lat':58.8893,'lon':15.7772,'name':'Calles gädda','uid':'k','by':'Calle','type':'gadda'},
 {'lat':58.8889,'lon':15.7800,'name':'Calles abborre','uid':'k','by':'Calle','type':'abborre'}]}

def pins(pg):
    return pg.evaluate("""() => Array.from(document.querySelectorAll('#waypoints .wpPin')).map(e => ({
        t: e.getAttribute('data-type'), other: e.classList.contains('wpPin--other'), op: getComputedStyle(e).opacity }))""")

with sync_playwright() as p:
    b,ctx,pg,errs=new_page(p,geo=ME,cfg=cfg,name='Filip')
    pg.wait_for_timeout(500)
    check('filter closed by default', not pg.is_visible('#visMore') and pg.get_attribute('#visMoreBtn','aria-expanded') == 'false')
    ps = pins(pg)
    check('all 4 spots shown by default', len(ps) == 4, ps)
    check("everything 100 % by default", all(x['op'] == '1' for x in ps), ps)
    pg.screenshot(path='shot_filter_closed.png')
    pg.click('#visMoreBtn'); pg.wait_for_timeout(250)
    check('filter opens', pg.is_visible('#visMore') and pg.get_attribute('#visMoreBtn','aria-expanded') == 'true')
    boxes = pg.eval_on_selector_all('#visTypes input', 'els => els.map(e => e.getAttribute("data-type") + ":" + e.checked)')
    check('6 type toggles (incl. Träffpunkt and Hem; no Fara -- it is never hidden), all on', boxes == ['mark:true','abborre:true','gadda:true','gos:true','meet:true','hem:true'], boxes)
    check('100 % selected by default', pg.inner_text('#othersOpacitySeg .active') == '100 %')
    check('no filter dot while everything is shown', not pg.is_visible('.visMoreDot'))
    pg.screenshot(path='shot_filter_open.png')

    pg.click('#visTypes label:has-text("Gädda") .toggle'); pg.wait_for_timeout(200)
    ps = pins(pg)
    check('Gädda off -> gädda spot hidden', len(ps) == 3 and not any(x['t'] == 'gadda' for x in ps), ps)
    check('filter dot shows something is filtered', pg.is_visible('.visMoreDot'))
    pg.click('#othersOpacitySeg button[data-op="0.5"]'); pg.wait_for_timeout(150)
    check("50 % -> others' spots half see-through, mine not", all(x['op'] == ('0.5' if x['other'] else '1') for x in pins(pg)), pins(pg))
    pg.screenshot(path='shot_filter_used.png')

    pg.reload(); pg.wait_for_timeout(1200)
    check('after reload (rotation): menu still open', pg.is_visible('#visMore'))
    ps = pins(pg)
    check('after reload: Gädda still hidden, 50 % kept', len(ps) == 3 and pg.inner_text('#othersOpacitySeg .active') == '50 %' and all(x['op'] == ('0.5' if x['other'] else '1') for x in ps), ps)

    # new spot while its type is filtered out
    pg.click('#visTypes label:has-text("Markering") .toggle'); pg.wait_for_timeout(200)
    n = len(pins(pg))
    pg.click('#addHereBtn'); pg.wait_for_timeout(900)
    check('new Markering spot visible while editing, even with Markering off', len(pins(pg)) == n + 1, pins(pg))
    pg.click('#wpSave'); pg.wait_for_timeout(400)
    check('saving it turns Markering back on', pg.eval_on_selector('#visTypes input[data-type="mark"]', 'e=>e.checked') and sum(1 for x in pins(pg) if x['t']=='mark') == 2, pins(pg))
    # log still lists everything
    pg.click('#menuBtn'); pg.click('#menuItemLog'); pg.wait_for_timeout(300)
    check('log still lists hidden types', pg.evaluate("document.querySelectorAll('#logList .logItem').length") == 5)
    pg.click('#logBackBtn'); pg.wait_for_timeout(200)

    pg.click('#visMoreBtn'); pg.wait_for_timeout(200)
    check('filter closes again', not pg.is_visible('#visMore'))

    # landscape: open panel fits on screen
    pg.click('#visMoreBtn'); pg.wait_for_timeout(100)
    for w,h in [(844,390),(667,375)]:
        pg.set_viewport_size({'width':w,'height':h}); pg.wait_for_timeout(400)
        r = pg.eval_on_selector('#visPanel', 'e=>{var r=e.getBoundingClientRect();return [r.top,r.bottom,e.scrollHeight>e.clientHeight]}')
        check('landscape %dx%d: panel fits (scrolls if needed)' % (w,h), r[1] <= h, r)
        pg.screenshot(path='shot_filter_land_%d.png' % w)
    check('no page errors', not errs, errs)
    b.close()
print('\n%d/%d passed' % (sum(results), len(results)))
