from playwright.sync_api import sync_playwright
from fakefb import new_page
results = []
def check(name, cond, info=''):
    results.append(bool(cond)); print(('PASS ' if cond else 'FAIL ') + name + ('  -- ' + str(info) if info != '' else ''))
ME = (58.88951, 15.77759)
def filt(pg): return pg.evaluate("[document.getElementById('mapImg').style.filter, document.querySelector('#legend .bar').style.filter]")
with sync_playwright() as p:
    b, ctx, pg, errs = new_page(p, geo=ME, cfg={}, name='Filip')
    check('default 80 % on the map and the depth scale', filt(pg) == ['saturate(0.8)', 'saturate(0.8)'], filt(pg))
    pg.screenshot(path='sat_80.png')
    pg.click('#menuBtn'); pg.click('#menuItemSettings'); pg.wait_for_timeout(200)
    check('slider in Settings shows 80 %', pg.input_value('#mapSatSlider') == '80' and pg.inner_text('#mapSatVal') == '80 %')
    pg.eval_on_selector('#mapSatSlider', 'e=>e.scrollIntoView({block:"center"})'); pg.wait_for_timeout(100)
    pg.screenshot(path='sat_settings.png')
    pg.eval_on_selector('#mapSatSlider', "e=>{e.value='0'; e.dispatchEvent(new Event('input',{bubbles:true}));}")
    check('0 % = greyscale', filt(pg) == ['saturate(0)', 'saturate(0)'] and pg.inner_text('#mapSatVal') == '0 %', filt(pg))
    pg.click('#settingsBackBtn'); pg.wait_for_timeout(200); pg.screenshot(path='sat_0.png')
    pg.reload(); pg.wait_for_timeout(1200)
    check('remembered after reload/rotation', filt(pg) == ['saturate(0)', 'saturate(0)'], filt(pg))
    pg.click('#menuBtn'); pg.click('#menuItemSettings'); pg.wait_for_timeout(200)
    pg.eval_on_selector('#mapSatSlider', "e=>{e.value='100'; e.dispatchEvent(new Event('input',{bubbles:true}));}")
    check('100 % = no filter at all', filt(pg) == ['', ''], filt(pg))
    pg.click('#settingsBackBtn'); pg.wait_for_timeout(200); pg.screenshot(path='sat_100.png')
    check('markers not filtered', pg.evaluate("getComputedStyle(document.getElementById('waypoints')).filter + getComputedStyle(document.getElementById('dot')).filter") == 'nonenone')
    check('no page errors', not errs, errs)
    b.close()
print('\n%d/%d passed' % (sum(results), len(results)))
