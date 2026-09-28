from playwright.sync_api import sync_playwright
import fakefb, json
from fakefb import login
import test_weather as _tw
results = []
def check(name, cond, info=''):
    results.append(bool(cond)); print(('PASS ' if cond else 'FAIL ') + name + ('  -- ' + str(info) if info != '' else ''))
with sync_playwright() as p:
    b = p.chromium.launch(**__import__('fakefb').LAUNCH)
    ctx = b.new_context(viewport={'width':390,'height':844}, has_touch=True, is_mobile=True, geolocation={'latitude':58.8868,'longitude':15.7776,'accuracy':5}, permissions=['geolocation'])
    ctx.add_init_script('window.__fakeCfg = {};'); ctx.add_init_script(fakefb.FAKE_FIREBASE_JS)
    ctx.route('**/api.open-meteo.com/**', lambda r: r.fulfill(status=200, content_type='application/json', body=json.dumps(_tw.wx_json()), headers={'Access-Control-Allow-Origin': '*'}))
    pg = ctx.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.goto('http://localhost:8899/index.html'); pg.wait_for_timeout(500); login(pg, 'Filip'); pg.wait_for_timeout(1500)
    check('weather chip shown by default', pg.is_visible('#wxChip'))
    pg.click('#visMoreBtn'); pg.wait_for_timeout(150)
    check('Filter has "Väder", on', pg.is_visible('label:has(#toggleWeather)') and pg.is_checked('#toggleWeather'))
    pg.screenshot(path='wxt_filter.png')
    pg.click('label:has(#toggleWeather) .toggle'); pg.wait_for_timeout(150)
    check('Väder off -> chip gone', not pg.is_visible('#wxChip'))
    pg.reload(); pg.wait_for_timeout(1500)
    check('stays off after reload/rotation', not pg.is_visible('#wxChip') and not pg.is_checked('#toggleWeather'))
    check('track opacity 60 % by default', pg.evaluate("document.getElementById('trackLayer').style.opacity") == '0.6')
    pg.click('#menuBtn'); pg.click('#menuItemSettings'); pg.wait_for_timeout(200)
    check('Settings slider shows 60 %', pg.input_value('#trackOpSlider') == '60' and pg.inner_text('#trackOpVal') == '60 %')
    pg.eval_on_selector('#trackOpSlider', 'e=>e.scrollIntoView({block:"center"})'); pg.wait_for_timeout(100)
    pg.screenshot(path='wxt_settings.png')
    pg.eval_on_selector('#trackOpSlider', "e=>{e.value='90'; e.dispatchEvent(new Event('input',{bubbles:true}));}")
    check('slider 90 % -> track 0.9', pg.evaluate("document.getElementById('trackLayer').style.opacity") == '0.9')
    pg.reload(); pg.wait_for_timeout(1500)
    check('remembered', pg.evaluate("document.getElementById('trackLayer').style.opacity") == '0.9')
    check('no page errors', not errs, errs)
    b.close()
print('\n%d/%d passed' % (sum(results), len(results)))
