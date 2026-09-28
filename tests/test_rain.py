from playwright.sync_api import sync_playwright
import fakefb, json, datetime
from fakefb import login
import test_weather as _tw
results = []
def check(name, cond, info=''):
    results.append(bool(cond)); print(('PASS ' if cond else 'FAIL ') + name + ('  -- ' + str(info) if info != '' else ''))
with sync_playwright() as p:
    b = p.chromium.launch(**__import__('fakefb').LAUNCH)
    ctx = b.new_context(viewport={'width':390,'height':844}, device_scale_factor=2, has_touch=True, is_mobile=True, geolocation={'latitude':58.8868,'longitude':15.7776,'accuracy':5}, permissions=['geolocation'])
    ctx.add_init_script('window.__fakeCfg = {};'); ctx.add_init_script(fakefb.FAKE_FIREBASE_JS)
    reqs = []
    def h(r):
        reqs.append(r.request.url); r.fulfill(status=200, content_type='application/json', body=json.dumps(_tw.wx_json()), headers={'Access-Control-Allow-Origin': '*'})
    ctx.route('**/api.open-meteo.com/**', h)
    pg = ctx.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.goto('http://localhost:8899/index.html'); pg.wait_for_timeout(500); login(pg, 'Filip'); pg.wait_for_timeout(1500)
    check('asks for rain (mm + chance)', 'precipitation_probability' in reqs[0] and 'precipitation' in reqs[0])
    exp = (datetime.datetime.now().replace(minute=0) + datetime.timedelta(hours=2)).strftime('%H')
    chip = pg.inner_text('#wxChip').replace('\n', ' ')
    check('chip: rain drop + when it starts ("kl %s")' % exp, ('kl ' + exp) in chip, chip)
    pg.evaluate("document.getAnimations().forEach(a => { try { a.pause(); a.currentTime = 700; } catch(e){} })")
    pg.screenshot(path='rain_chip.png')
    pg.click('#wxChip'); pg.wait_for_timeout(300)
    tiles = pg.eval_on_selector_all('.wxH', 'els => els.map(e => e.innerText.replace(/\\n/g, " "))')
    print('   tiles:', tiles)
    check('hour columns show mm + % when rain is expected', 'mm' in tiles[0] and '80 %' in tiles[0] and 'mm' in tiles[2] and 'mm' not in tiles[4], tiles)
    pg.screenshot(path='rain_card.png')
    check('no page errors', not errs, errs)
    b.close()
print('\n%d/%d passed' % (sum(results), len(results)))
