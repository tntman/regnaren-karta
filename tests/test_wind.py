# "Vind och lä" (Filter, off by default): lee lighter + thin edge, wind comets over open
# water; the lee grows in light wind and shrinks in strong wind; under 1,5 m/s all calm.
from playwright.sync_api import sync_playwright
import fakefb, json, copy
from fakefb import new_page
import test_weather as _tw
results = []
def check(name, cond, info=''):
    results.append(bool(cond)); print(('PASS ' if cond else 'FAIL ') + name + ('  -- ' + str(info) if info != '' else ''))
REG = (58.88951, 15.77759)

def page_with_wind(p, ms, frm=250):
    data = _tw.wx_json(); data['current']['wind_speed_10m'] = ms; data['current']['wind_direction_10m'] = frm
    b, ctx, pg, errs = new_page(p, geo=REG, cfg={}, name=None)
    ctx.route('**/api.open-meteo.com/**', lambda r: r.fulfill(status=200, content_type='application/json', body=json.dumps(data), headers={'Access-Control-Allow-Origin': '*'}))
    pg.evaluate("localStorage.removeItem('ffmap_weather_v1')")   # (the first load fetched before the route was there)
    pg.reload(); pg.wait_for_timeout(600); fakefb.login(pg, 'Filip'); pg.wait_for_timeout(1800)
    return b, ctx, pg, errs

def wind_on(pg):
    pg.click('#visMoreBtn'); pg.wait_for_timeout(200)
    pg.click('label:has(#toggleWind) .toggle'); pg.click('#visMoreBtn'); pg.wait_for_timeout(1500)

with sync_playwright() as p:
    b, ctx, pg, errs = page_with_wind(p, 6)
    pg.click('#visMoreBtn'); pg.wait_for_timeout(200)
    check('Filter has "Vind och lä", off by default', pg.is_visible('label:has(#toggleWind)') and not pg.is_checked('#toggleWind') and not pg.is_visible('#windLayer'))
    pg.click('#visMoreBtn'); pg.wait_for_timeout(200)
    wind_on(pg)
    s6 = pg.evaluate('window.__ffWind()')
    check('on: the wind layer is shown, lee + comets drawn (6 m/s)', pg.is_visible('#windLayer') and s6 and 0.02 < s6['leeShare'] < 0.6 and s6['drawn'] > 5, s6)
    lit = pg.evaluate("""() => { var c = document.getElementById('windLayer'), d = c.getContext('2d').getImageData(0, 0, c.width, c.height).data, n = 0;
                         for (var i = 3; i < d.length; i += 4) if (d[i] > 0) n++; return n; }""")
    check('the canvas has something on it', lit > 1000, lit)
    pg.screenshot(path='shot_wind_6.png')
    # zoomed far in: the lee edge is drawn per screen pixel, so it stays smooth
    edge = pg.evaluate("""() => { var c = document.getElementById('windLayer'), dpr = window.devicePixelRatio || 1,
        d = c.getContext('2d').getImageData(0, 0, c.width, c.height).data, best = null, bd = 1e9;
        for (var y = 120 * dpr; y < c.height - 200 * dpr; y += 3) for (var x = 20 * dpr; x < c.width - 20 * dpr; x += 3){
          var k = (y * c.width + x) * 4;
          if (d[k + 3] > 120 && d[k] > 240 && d[k + 1] > 240){ var dd = Math.hypot(x / dpr - 195, y / dpr - 422); if (dd < bd){ bd = dd; best = [x / dpr, y / dpr]; } }
        } return best; }""")
    pg.mouse.move(*(edge or (195, 560)))
    for i in range(14):
        pg.mouse.wheel(0, -400); pg.wait_for_timeout(50)
    pg.wait_for_timeout(1500)
    pg.screenshot(path='shot_wind_6_zoom.png')
    check('zoomed in: still drawn, no errors', pg.evaluate('window.__ffWind()') is not None and not errs, errs)
    # remembered after a reload (rotation)
    pg.reload(); pg.wait_for_timeout(2200)
    check('stays on after a reload', pg.is_checked('#toggleWind') and pg.is_visible('#windLayer'))
    check('no page errors', not errs, errs)
    b.close()
    # the lee depends on the wind speed
    shares = {}
    for ms in (3, 12):
        b, ctx, pg, errs = page_with_wind(p, ms); wind_on(pg)
        shares[ms] = pg.evaluate('window.__ffWind()'); pg.screenshot(path='shot_wind_%d.png' % ms); b.close()
    check('light wind (3 m/s): more lee than in 6 m/s, strong wind (12 m/s): less', shares[3]['leeShare'] > s6['leeShare'] > shares[12]['leeShare'], (shares[3]['leeShare'], s6['leeShare'], shares[12]['leeShare']))
    check('lee distance 3 m/s 400 m / 6 m/s 100 m / 12 m/s 30 m', shares[3]['leeD'] == 400 and abs(s6['leeD'] - 100) < 1 and shares[12]['leeD'] == 30, (shares[3]['leeD'], s6['leeD'], shares[12]['leeD']))
    b, ctx, pg, errs = page_with_wind(p, 1); wind_on(pg)
    s1 = pg.evaluate('window.__ffWind()')
    check('almost no wind (1 m/s): the whole lake calm, no comets', s1['leeShare'] > 0.99 and s1['drawn'] == 0, s1)
    b.close()
print('\n%d/%d passed' % (sum(results), len(results)))
