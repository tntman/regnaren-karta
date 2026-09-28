# "Blixtar" (Filter, on by default): lightning from FMI (mocked here -- the real
# service is blocked in every test by fakefb). Warning under the weather chip
# (red < 10 km, orange < 30 km), radar, ⚡ on the map, a marker at the screen edge
# towards the nearest strike when it's off screen; nothing at all when it's quiet.
from playwright.sync_api import sync_playwright
import fakefb, json, math, time
from fakefb import new_page
import test_weather as _tw
results = []
def check(name, cond, info=''):
    results.append(bool(cond)); print(('PASS ' if cond else 'FAIL ') + name + ('  -- ' + str(info) if info != '' else ''))
REG = (58.88951, 15.77759)
KM_LAT, KM_LON = 1 / 111.2, 1 / (111.32 * math.cos(math.radians(REG[0])))

def fmi_xml(strikes):
    """strikes: (km east, km north, minutes ago) from REG -> FMI's simple WFS answer"""
    els = []
    for i, (e, n, ago) in enumerate(strikes):
        t = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(time.time() - ago * 60))
        els.append("""<wfs:member><BsWfs:BsWfsElement gml:id="BsWfsElement.1.%d.1"><BsWfs:Location>
 <gml:Point gml:id="BsWfsElementP.1.%d.1" srsDimension="2" srsName="http://www.opengis.net/def/crs/EPSG/0/4258">
  <gml:pos>%.5f %.5f </gml:pos></gml:Point></BsWfs:Location>
 <BsWfs:Time>%s</BsWfs:Time><BsWfs:ParameterName>peak_current</BsWfs:ParameterName><BsWfs:ParameterValue>-11.0</BsWfs:ParameterValue>
</BsWfs:BsWfsElement></wfs:member>""" % (i, i, REG[0] + n * KM_LAT, REG[1] + e * KM_LON, t))
    return ('<?xml version="1.0" encoding="UTF-8"?><wfs:FeatureCollection timeStamp="x" numberMatched="%d" numberReturned="%d" '
            'xmlns:wfs="http://www.opengis.net/wfs/2.0" xmlns:gml="http://www.opengis.net/gml/3.2" xmlns:BsWfs="http://xml.fmi.fi/schema/wfs/2.0">%s</wfs:FeatureCollection>'
            % (len(els), len(els), ''.join(els)))

STORM = [(2.5, 0, 0.5),                       # nearest: 2,5 km east, just now
         (10, 10, 3), (11, 9, 8), (12, 12, 20),  # north-east
         (0, -45, 5),                         # 45 km away: outside 30 km
         (1, 1, 40)]                          # 40 min old: gone

def page_with(p, strikes):
    b, ctx, pg, errs = new_page(p, geo=REG, cfg={}, name=None)
    data = _tw.wx_json()
    ctx.route('**/api.open-meteo.com/**', lambda r: r.fulfill(status=200, content_type='application/json', body=json.dumps(data), headers={'Access-Control-Allow-Origin': '*'}))
    hits = []
    def fmi(route):
        hits.append(route.request.url)
        route.fulfill(status=200, content_type='text/xml; charset=UTF-8', body=fmi_xml(strikes), headers={'Access-Control-Allow-Origin': '*'})
    ctx.route('**/opendata.fmi.fi/**', fmi)
    pg.evaluate("localStorage.removeItem('ffmap_weather_v1')")
    pg.reload(); pg.wait_for_timeout(600); fakefb.login(pg, 'Filip'); pg.wait_for_timeout(1500)
    return b, ctx, pg, errs, hits

def lt_on(pg):   # (flips the switch)
    pg.click('#visMoreBtn'); pg.wait_for_timeout(200)
    pg.click('label:has(#toggleLightning) .toggle'); pg.click('#visMoreBtn'); pg.wait_for_timeout(1200)

with sync_playwright() as p:
    b, ctx, pg, errs, hits = page_with(p, STORM)
    pg.click('#visMoreBtn'); pg.wait_for_timeout(200)
    check('Filter has "Blixtar", on by default', pg.is_visible('label:has(#toggleLightning)') and pg.is_checked('#toggleLightning'))
    pg.click('#visMoreBtn'); pg.wait_for_timeout(300)
    lt_on(pg)          # (off)
    check('turned off: no warning, no radar', not pg.is_visible('#ltPill') and not pg.is_visible('#ltRadar'))
    del hits[:]
    lt_on(pg)          # (on again)
    s = pg.evaluate('window.__ffLightning()')
    check('on: FMI asked once, for the area round the lake and the last half hour',
          len(hits) == 1 and 'lightning' in hits[0] and 'bbox=15.028,58.490,16.528,59.290' in hits[0] and 'starttime=' in hits[0], hits)
    check('the 40 min old one is left out, the 45 km one is not in range', s['n'] == 5 and s['inRange'] == 4, s)
    txt = pg.inner_text('#ltPill')
    check('red warning: "Åska 2,5 km O" · "senaste nyss"', pg.is_visible('#ltPill') and s['red'] and 'Åska 2,5 km O' in txt and 'senaste nyss' in txt, txt)
    check('the radar is shown', pg.is_visible('#ltRadar') and s['radar'])
    rpx = pg.evaluate("""() => { var c = document.getElementById('ltRadarCv'), d = c.getContext('2d').getImageData(0, 0, c.width, c.height).data, y = 0;
                         for (var i = 0; i < d.length; i += 4) if (d[i] > 240 && d[i + 1] > 200 && d[i + 2] < 120 && d[i + 3] > 200) y++; return y; }""")
    check('the radar has the yellow (new) strikes on it', rpx > 10, rpx)
    check('zoomed in: the strike is off screen -> a marker at the right-hand edge with the km',
          s['edge'] and s['edge']['x'] > 300 and abs(s['edge']['km'] - 2.5) < 0.1, s['edge'])
    pg.screenshot(path='shot_lightning_near.png')
    # zoomed out: the strikes on the map
    pg.mouse.move(195, 420)
    for i in range(12):
        pg.mouse.wheel(0, 400); pg.wait_for_timeout(60)
    pg.wait_for_timeout(1200)
    s2 = pg.evaluate('window.__ffLightning()')
    check('zoomed out: ⚡ drawn on the map, no edge marker (the nearest is on screen)', s2['drawn'] >= 1 and s2['edge'] is None, s2)
    lit = pg.evaluate("""() => { var c = document.getElementById('ltLayer'), d = c.getContext('2d').getImageData(0, 0, c.width, c.height).data, n = 0;
                         for (var i = 3; i < d.length; i += 4) if (d[i] > 0) n++; return n; }""")
    check('the map canvas has something on it', lit > 100, lit)
    pg.screenshot(path='shot_lightning_out.png')
    pg.reload(); pg.wait_for_timeout(2200)
    check('stays on after a reload (rotation), fetched again', pg.is_checked('#toggleLightning') and pg.is_visible('#ltPill') and len(hits) == 2, len(hits))
    pg.click('#visMoreBtn'); pg.wait_for_timeout(200)
    pg.click('label:has(#toggleLightning) .toggle'); pg.click('#visMoreBtn'); pg.wait_for_timeout(500)
    s3 = pg.evaluate('window.__ffLightning()')
    check('off again: all gone', not pg.is_visible('#ltPill') and not pg.is_visible('#ltRadar') and s3['drawn'] == 0 and s3['edge'] is None, s3)
    check('no page errors', not errs, errs)
    b.close()
    # only far away: orange
    b, ctx, pg, errs, hits = page_with(p, [(15, 5, 4)])
    pg.wait_for_timeout(300)   # (on by default)
    s = pg.evaluate('window.__ffLightning()'); txt = pg.inner_text('#ltPill')
    check('16 km away: orange warning "Åska 16 km O" · "senaste 4 min sedan"', pg.is_visible('#ltPill') and not s['red'] and 'Åska 16 km O' in txt and '4 min sedan' in txt, txt)
    pg.screenshot(path='shot_lightning_far.png')
    b.close()
    # quiet: nothing at all
    b, ctx, pg, errs, hits = page_with(p, [])
    pg.wait_for_timeout(300)   # (on by default)
    s = pg.evaluate('window.__ffLightning()')
    check('no strikes: no warning, no radar, nothing on the map', len(hits) == 1 and not pg.is_visible('#ltPill') and not pg.is_visible('#ltRadar') and s['drawn'] == 0 and s['edge'] is None, s)
    check('no page errors', not errs, errs)
    b.close()
print('\n%d/%d passed' % (sum(results), len(results)))
