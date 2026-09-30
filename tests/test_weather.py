from playwright.sync_api import sync_playwright
import fakefb, json, math, datetime
from fakefb import login
results = []
def check(name, cond, info=''):
    results.append(bool(cond)); print(('PASS ' if cond else 'FAIL ') + name + ('  -- ' + str(info) if info != '' else ''))
ME = (58.88951 - 420/111320.0, 15.77759 - 250/(111320.0*math.cos(math.radians(58.889))))
def wx_json():
    now = datetime.datetime.now().replace(minute=0, second=0, microsecond=0)
    times = [now + datetime.timedelta(hours=h) for h in range(-12, 24)]
    f = lambda t: t.strftime('%Y-%m-%dT%H:%M')
    return {'current': {'temperature_2m': 14.2, 'apparent_temperature': 12.1, 'weather_code': 2, 'wind_speed_10m': 4.3, 'wind_direction_10m': 225, 'wind_gusts_10m': 7.1, 'pressure_msl': 1014.2, 'precipitation': 0},
            'hourly': {'time': [f(t) for t in times], 'temperature_2m': [14 - abs(h) * 0.2 for h in range(-12, 24)],
                       'wind_speed_10m': [4 + (h % 5) * 0.4 for h in range(-12, 24)], 'wind_direction_10m': [225 + h for h in range(-12, 24)],
                       'wind_gusts_10m': [7] * 36, 'pressure_msl': [1018 - (h + 12) * 0.35 for h in range(-12, 24)],
                       'precipitation': [(0.4 + 0.2 * (h - 2)) if 2 <= h <= 7 else 0 for h in range(-12, 24)],
                       'precipitation_probability': [80 if 2 <= h <= 7 else (30 if h == 1 else 5) for h in range(-12, 24)]},
            'daily': {'sunrise': [f(now.replace(hour=6, minute=52)), f((now + datetime.timedelta(days=1)).replace(hour=6, minute=54))],
                      'sunset': [f(now.replace(hour=19, minute=8)), f((now + datetime.timedelta(days=1)).replace(hour=19, minute=5))]}}
calls = []
def _main():
    with sync_playwright() as p:
      b = p.chromium.launch(**__import__('fakefb').LAUNCH)
      ctx = b.new_context(viewport={'width':390,'height':844}, device_scale_factor=2, has_touch=True, is_mobile=True,
          geolocation={'latitude':ME[0],'longitude':ME[1],'accuracy':5}, permissions=['geolocation'])
      ctx.add_init_script('window.__fakeCfg = {};'); ctx.add_init_script(fakefb.FAKE_FIREBASE_JS)
      def handle(route):
          calls.append(route.request.url); route.fulfill(status=200, content_type='application/json', body=json.dumps(wx_json()), headers={'Access-Control-Allow-Origin': '*'})
      ctx.route('**/api.open-meteo.com/**', handle)
      pg = ctx.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
      pg.goto('http://localhost:8899/index.html'); pg.wait_for_timeout(500); login(pg, 'Filip'); pg.wait_for_timeout(1800)
      check('weather fetched once at start (wind in m/s, Swedish time)', len(calls) == 1 and 'wind_speed_unit=ms' in calls[0] and 'Europe%2FStockholm' in calls[0], calls)
      chip = pg.inner_text('#wxChip')
      check('chip: wind (gusts), pressure, temp', '4 (7) m/s' in chip.replace('\n', ' ') and '1014' in chip and '14°' in chip, chip)
      check('chip: falling pressure arrow', pg.query_selector('#wxChip .down') is not None)
      cr = pg.eval_on_selector('#wxChip', 'e=>e.getBoundingClientRect().left'); mr = pg.eval_on_selector('#menuBtn', 'e=>e.getBoundingClientRect().left')
      check('chip flush with the left margin (same as the menu button)', abs(cr - mr) < 1, (cr, mr))
      pg.evaluate("document.getAnimations().forEach(a => { try { a.pause(); a.currentTime = 700; } catch(e){} })")
      pg.screenshot(path='wx_real_chip.png')
      pg.click('#wxChip'); pg.wait_for_timeout(300)
      body = pg.inner_text('#wxCard')
      check('details open: wind from SV, gusts, pressure falling, sun times, 5 hours', 'från SV' in body and 'Byar 7' in body and 'Sjunker' in body and '06:52' in body and body.count('m/s') >= 6, body.replace('\n', ' | ')[:200])
      pg.screenshot(path='wx_real_card.png')
      pg.click('#wxClose'); pg.wait_for_timeout(200)
      check('✕ closes', not pg.is_visible('#wxCard'))
      pg.click('#wxChip'); pg.wait_for_timeout(300)
      pg.mouse.move(200, 600); pg.mouse.down(); pg.mouse.move(260, 640, steps=8); pg.mouse.up(); pg.wait_for_timeout(200)
      check('dragging the map: the card stays', pg.is_visible('#wxCard'))
      pg.wait_for_timeout(600); pg.mouse.click(200, 600); pg.wait_for_timeout(300)
      check('a tap on the map closes it', not pg.is_visible('#wxCard'))
      # offline: the last forecast stays
      pg.unroute('**/api.open-meteo.com/**'); ctx.route('**/api.open-meteo.com/**', lambda r: r.abort())
      pg.reload(); pg.wait_for_timeout(1800)
      check('no coverage: last forecast still shown', pg.is_visible('#wxChip') and '1014' in pg.inner_text('#wxChip'))
      check('no refetch within 30 min', len(calls) == 1)
      check('no page errors', not errs, errs)
      b.close()
    print('\n%d/%d passed' % (sum(results), len(results)))
if __name__ == '__main__':
    _main()
