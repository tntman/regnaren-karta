# "Åk hit" (from a spot's sheet), "Håll skärmen tänd" (Filter, off by default), quick
# messages (small button at the bottom, bubbles at the boats for 15 min, tap to take
# back / hide) and the lightning alarm (Inställningar: Av/5/10/20 km, sound, vibration).
from playwright.sync_api import sync_playwright
import fakefb, json, math, time
from fakefb import new_page
import test_weather as _tw
results = []
def check(name, cond, info=''):
    results.append(bool(cond)); print(('PASS ' if cond else 'FAIL ') + name + ('  -- ' + str(info) if info != '' else ''))
B3 = (58.887269, 15.772629); B1 = (58.887421, 15.775569); B4 = (58.88651, 15.777774)
cfg = {'waypoints': [{'lat': B4[0], 'lon': B4[1], 'name': 'Djupa hålet', 'uid': 'filip', 'by': 'Filip', 'type': 'abborre'}],
       'positions': [{'uid': 'kalle', 'name': 'Calle', 'lat': B1[0], 'lon': B1[1], 'ageMin': 0, 'msg': 'Hugg! 🎣', 'msgAgeMin': 2},
                     {'uid': 'pia', 'name': 'Pia', 'lat': B1[0] + 0.001, 'lon': B1[1], 'ageMin': 0, 'msg': 'Kommer 🚤', 'msgAgeMin': 20}]}

# (from test_lightning: made-up FMI answers)
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

def page_with(p, strikes):
    b, ctx, pg, errs = new_page(p, geo=REG, cfg={}, name=None)
    data = _tw.wx_json()
    ctx.route('**/api.open-meteo.com/**', lambda r: r.fulfill(status=200, content_type='application/json', body=json.dumps(data), headers={'Access-Control-Allow-Origin': '*'}))
    hits = []; fixed = {}
    def fmi(route):
        hits.append(route.request.url)
        body = fixed.setdefault('xml', fmi_xml(strikes))     # (the same strikes, same times, every fetch -- like FMI)
        route.fulfill(status=200, content_type='text/xml; charset=UTF-8', body=body, headers={'Access-Control-Allow-Origin': '*'})
    ctx.route('**/opendata.fmi.fi/**', fmi)
    pg.evaluate("localStorage.removeItem('ffmap_weather_v1')")
    pg.reload(); pg.wait_for_timeout(600); fakefb.login(pg, 'Filip'); pg.wait_for_timeout(1500)
    return b, ctx, pg, errs, hits


with sync_playwright() as p:
    b, ctx, pg, errs = new_page(p, geo=B3, cfg=cfg, name='Filip', wakelock_stub=True)
    pg.wait_for_timeout(1500)
    # ---- Åk hit
    pg.evaluate("n => { var id = Object.keys(window.__wpDocs).filter(k => window.__wpDocs[k].name === n)[0]; document.querySelector('#waypoints [data-id=\"' + id + '\"]').click(); }", 'Djupa hålet')
    pg.wait_for_timeout(400)
    check('a spot\'s sheet has "Åk hit"', pg.is_visible('#wpGo'))
    pg.click('#wpGo'); pg.wait_for_timeout(900)
    info = pg.inner_text('#navInfo')
    check('"Åk hit": the card with the name, distance by water and time; the lead line there', pg.is_visible('#navCard') and pg.inner_text('#navName') == 'Djupa hålet' and 'sjövägen' in info and pg.eval_on_selector('#probe', 'e => e.classList.contains("show")'), (pg.is_visible('#navCard'), pg.inner_text('#navName'), info, pg.eval_on_selector('#probe', 'e => e.classList.contains("show")')))
    pg.screenshot(path='shot_nav.png')
    ctx.set_geolocation({'latitude': B1[0], 'longitude': B1[1], 'accuracy': 5}); pg.wait_for_timeout(1500)
    info2 = pg.inner_text('#navInfo')
    check('moving: distance updated', info2 != info, (info, info2))
    pg.click('#navClose'); pg.wait_for_timeout(300)
    check('✕: navigation ended', not pg.is_visible('#navCard') and not pg.eval_on_selector('#probe', 'e => e.classList.contains("show")'))
    # ---- Håll skärmen tänd
    pg.click('#visMoreBtn'); pg.wait_for_timeout(200)
    check('"Håll skärmen tänd" in Filter, off by default, nothing requested', not pg.is_checked('#toggleWake') and pg.evaluate('window.__wakeReqs') == 0)
    pg.click('label:has(#toggleWake) .toggle'); pg.wait_for_timeout(300)
    check('on: the screen is kept on', pg.evaluate('window.__wakeReqs') == 1 and pg.evaluate('window.__ffWake()')['held'])
    pg.click('label:has(#toggleWake) .toggle'); pg.click('#visMoreBtn'); pg.wait_for_timeout(300)
    check('off again: let go', not pg.evaluate('window.__ffWake()')['held'])
    # ---- quick messages
    msgs = pg.evaluate('window.__ffMsgs()')
    check("Calle's message (2 min old) shows at his boat; Pia's (20 min) is too old", any('Hugg!' in m['t'] and 'Calle' in m['t'] for m in msgs) and not any('Pia' in m['t'] for m in msgs), msgs)
    check('the message button is a small button at the bottom', pg.is_visible('#msgBtn') and not pg.is_visible('#msgPop'))
    pg.click('#msgBtn'); pg.wait_for_timeout(200)
    opts = pg.eval_on_selector_all('#msgPop button', 'e => e.map(x => x.textContent)')
    check('tap it: the choices', pg.is_visible('#msgPop') and 'Hugg! 🎣' in opts and 'Åker in 🏠' in opts, opts)
    pg.evaluate('window.__posWrites.length = 0')
    pg.click('#msgPop button:has-text("Åker in")'); pg.wait_for_timeout(400)
    w = [x for x in pg.evaluate('window.__posWrites') if x.get('msg')]
    check('sent with your position (for everyone)', w and w[-1]['msg'] == 'Åker in 🏠' and w[-1]['lat'] and not pg.is_visible('#msgPop'), w)
    check('your bubble at your boat', any(m['k'] == 'me' and 'Åker in' in m['t'] for m in pg.evaluate('window.__ffMsgs()')))
    pg.screenshot(path='shot_msgs.png')
    pg.evaluate('window.__posWrites.length = 0')
    pg.evaluate("document.querySelector('.msgBub.mine').click()"); pg.wait_for_timeout(300)
    w = pg.evaluate('window.__posWrites')
    check('tap your bubble: taken back for everyone', not any(m['k'] == 'me' for m in pg.evaluate('window.__ffMsgs()')) and w and w[-1]['msg'] is None, w)
    pg.evaluate("document.querySelector('.msgBub').click()"); pg.wait_for_timeout(300)
    check("tap Calle's: hidden for you", not pg.evaluate('window.__ffMsgs()'))
    check('no page errors', not errs, errs)
    b.close()
    # your own message comes back from the database (e.g. after a reload / on another phone)
    b, ctx, pg, errs = new_page(p, geo=B3, cfg={'positions': [{'uid': 'filip', 'name': 'Filip', 'lat': B3[0], 'lon': B3[1], 'ageMin': 0, 'msg': 'Fika? ☕', 'msgAgeMin': 1}]}, name='Filip')
    pg.wait_for_timeout(1500)
    check('your message from the database shows at your boat', any(m['k'] == 'me' and 'Fika' in m['t'] for m in pg.evaluate('window.__ffMsgs()')), pg.evaluate('window.__ffMsgs()'))
    b.close()
    # not at the lake: no message is sent
    b, ctx, pg, errs = new_page(p, geo=(59.33, 18.06), cfg={}, name='Filip')
    pg.wait_for_timeout(1200); pg.evaluate('window.__posWrites.length = 0')
    pg.click('#msgBtn'); pg.click('#msgPop button:has-text("Hugg")'); pg.wait_for_timeout(300)
    check('away from the lake: nothing sent, a note instead', not [x for x in pg.evaluate('window.__posWrites') if x.get('msg')] and pg.is_visible('#msgToast'))
    b.close()

    # ---- lightning alarm: a strike 3 km away, 1 min old
    b, ctx, pg, errs, hits = page_with(p, [(3, 0.5, 1), (15, 5, 2)])
    pg.wait_for_timeout(800)
    check('a strike 3 km away (alarm at 10 km by default): the red warning', pg.is_visible('#ltAlarm') and '3,0 km' in pg.inner_text('#ltAlarmMain') and pg.evaluate('window.__ltAlarms') == 1, pg.inner_text('#ltAlarm'))
    pg.screenshot(path='shot_lt_alarm.png')
    pg.click('#ltAlarmOk'); pg.wait_for_timeout(200)
    pg.evaluate('window.__ffLightningFetch()'); pg.wait_for_timeout(800)
    check('OK closes it; the same strike does not warn again', not pg.is_visible('#ltAlarm') and pg.evaluate('window.__ltAlarms') == 1, (pg.is_visible('#ltAlarm'), pg.evaluate('window.__ltAlarms')))
    pg.click('#menuBtn'); pg.click('#menuItemSettings'); pg.wait_for_timeout(300)
    check('Inställningar: Åskvarning 10 km, sound + vibration on', pg.inner_text('#ltAlarmSeg .active') == '10 km' and pg.is_checked('#ltAlarmSound') and pg.is_checked('#ltAlarmVib'))
    pg.click('#ltAlarmSeg button[data-km="0"]'); pg.wait_for_timeout(200)
    b.close()
    b, ctx, pg, errs, hits = page_with(p, [(2, 0.5, 1)])
    pg.evaluate("localStorage.setItem('ffmap_lt_alarm_v1', JSON.stringify({ km: 0, sound: true, vib: true }))"); pg.reload(); pg.wait_for_timeout(1800)
    check('"Av": no warning', not pg.is_visible('#ltAlarm'))
    b.close()
    b, ctx, pg, errs, hits = page_with(p, [(15, 5, 1)])
    pg.wait_for_timeout(800)
    check('15 km away: no warning (only within 10 km)', not pg.is_visible('#ltAlarm'))
    b.close()
print('\n%d/%d passed' % (sum(results), len(results)))
