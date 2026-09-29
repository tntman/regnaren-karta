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
    pg.wait_for_timeout(1200)
    tiles = pg.eval_on_selector_all('#wpData .wpTile i', 'e => e.map(x => x.textContent)')
    vals = pg.eval_on_selector_all('#wpData .wpTile b', 'e => e.map(x => x.textContent)')
    check('the sheet shows what is under the spot: depth, slope, bottom, plants (just heading + value)', tiles == ['Djup', 'Lutning', 'Botten', 'Växter'] and vals[0].endswith(' m') and vals[1].endswith('%') and vals[2] != '–' and not pg.query_selector('#wpData small') and not pg.query_selector('#wpData .wpTerrain'), (tiles, vals, pg.inner_text('#wpData')))
    check('"Sparad av" + the name in bold', pg.inner_text('#wpMeta b.who') == 'dig')
    cdp = ctx.new_cdp_session(pg)
    def touch(x, y0, y1, steps, ms):
        cdp.send('Input.dispatchTouchEvent', {'type': 'touchStart', 'touchPoints': [{'x': x, 'y': y0}]})
        for k in range(1, steps + 1):
            cdp.send('Input.dispatchTouchEvent', {'type': 'touchMove', 'touchPoints': [{'x': x, 'y': y0 + (y1 - y0) * k / steps}]}); pg.wait_for_timeout(ms)
        cdp.send('Input.dispatchTouchEvent', {'type': 'touchEnd', 'touchPoints': []}); pg.wait_for_timeout(500)
    sh = lambda: pg.eval_on_selector('#wpSheet', 'e => [e.getBoundingClientRect().height, e.classList.contains("show")]')
    g = pg.eval_on_selector('#wpSheet .sheetGrab', 'e => { var r = e.getBoundingClientRect(); return [r.left + r.width / 2, r.top + r.height / 2, r.height]; }')
    h0 = sh()[0]; touch(g[0], g[1], g[1] + 90, 15, 30)
    check('spot sheet: drag its grip strip down (finger) = smaller, still open', g[2] >= 26 and sh()[1] and sh()[0] < h0 - 60, (g, h0, sh()))
    g = pg.eval_on_selector('#wpSheet .sheetGrab', 'e => { var r = e.getBoundingClientRect(); return [r.left + r.width / 2, r.top + r.height / 2]; }')
    touch(g[0], g[1], g[1] - 200, 12, 30)
    check('...up again: full size', abs(sh()[0] - h0) < 3, (h0, sh()))
    pg.click('#wpGo'); pg.wait_for_timeout(900)
    info = pg.inner_text('#probeDistTxt')
    route = pg.eval_on_selector('#routeLayer .rtLine', 'e => e.getAttribute("points")')
    check('"Åk hit": the lead line on the spot, distance by water + the route (no extra card)', pg.eval_on_selector('#probe', 'e => e.classList.contains("show")') and info.endswith('m') and route and pg.query_selector('#navCard') is None, (info, bool(route)))
    pg.screenshot(path='shot_nav.png')
    ctx.set_geolocation({'latitude': B1[0], 'longitude': B1[1], 'accuracy': 5}); pg.wait_for_timeout(1500)
    info2 = pg.inner_text('#probeDistTxt')
    check('moving: distance updated', info2 != info, (info, info2))
    # ---- Håll skärmen tänd
    pg.click('#visMoreBtn'); pg.wait_for_timeout(200)
    check('"Håll skärmen tänd" in Filter, off by default, nothing requested', not pg.is_checked('#toggleWake') and pg.evaluate('window.__wakeReqs') == 0)
    pg.click('label:has(#toggleWake) .toggle'); pg.wait_for_timeout(300)
    check('on: the screen is kept on', pg.evaluate('window.__wakeReqs') == 1 and pg.evaluate('window.__ffWake()')['held'])
    pg.click('#visMoreBtn'); pg.wait_for_timeout(300)
    check('...and a yellow sun by your name', pg.is_visible('#wakeBadge'))
    pg.click('#wakeBadge'); pg.wait_for_timeout(300)
    check('tap the sun: off, and a note saying what it was and where to turn it on', not pg.evaluate('window.__ffWake()')['held'] and not pg.is_visible('#wakeBadge') and pg.is_visible('#wakeNote') and 'Filter' in pg.inner_text('#wakeNote'))
    pg.click('#visMoreBtn'); pg.wait_for_timeout(200)
    check('...Filter shows it off', not pg.is_checked('#toggleWake'))
    pg.click('#visMoreBtn'); pg.wait_for_timeout(200)
    pg.click('#wakeNoteClose'); pg.wait_for_timeout(300)
    check('the note closes with ✕', not pg.is_visible('#wakeNote'))
    # ---- quick messages
    msgs = pg.evaluate('window.__ffMsgs()')
    check("Calle's message (2 min old) shows at his boat; Pia's (20 min) is too old", any('Hugg!' in m['t'] and 'Calle' in m['t'] for m in msgs) and not any('Pia' in m['t'] for m in msgs), msgs)
    check('the message button is a small button at the bottom', pg.is_visible('#msgBtn') and not pg.is_visible('#msgPop'))
    pg.click('#msgBtn'); pg.wait_for_timeout(200)
    opts = pg.eval_on_selector_all('#msgPop button', 'e => e.map(x => x.textContent)')
    check('tap it: the choices', pg.is_visible('#msgPop') and opts == ['Fisk!!! 🎣', 'Kommer 🚤', 'Åker in 🏠', 'Mat? 🍔', 'Bajs 💩', 'Egen text'], opts)
    pg.evaluate('window.__posWrites.length = 0')
    pg.click('#msgPop button:has-text("Åker in")'); pg.wait_for_timeout(400)
    w = [x for x in pg.evaluate('window.__posWrites') if x.get('msg')]
    check('sent with your position (for everyone)', w and w[-1]['msg'] == 'Åker in 🏠' and w[-1]['lat'] and not pg.is_visible('#msgPop'), w)
    check('your bubble at your boat', any(m['k'] == 'me' and 'Åker in' in m['t'] for m in pg.evaluate('window.__ffMsgs()')))
    pg.screenshot(path='shot_msgs.png')
    check('a new message: the rainbow edge (first 5 min), round the tail too', pg.evaluate("(() => { var bb = document.querySelector('.mLine.mine').closest('.msgBub'), r = bb.querySelector('.msgRb'); return !!r && r.offsetHeight > bb.offsetHeight + 5; })()"))
    op = [[m['k'], m['o']] for m in pg.evaluate('window.__ffMsgs()')]
    check("they fade with age: Calle's (2 min) less than yours (new)", dict(op).get('me', 0) > [v for k, v in op if k != 'me'][0], op)
    check("Calle's (2 min old) also has the rainbow edge", pg.evaluate("!!document.querySelector('.mLine:not(.mine)').closest('.msgBub').querySelector('.msgRb')"))
    pg.evaluate("document.querySelector('.mLine:not(.mine)').click()"); pg.wait_for_timeout(500)
    card = pg.inner_text('#msgCard')
    check("tap Calle's: a panel with when it was written and when it goes", pg.eval_on_selector('#msgCard', 'e => e.classList.contains("show")') and 'CALLE' in card and 'Hugg!' in card and 'Skrivet' in card and '2 min sedan' in card and 'Försvinner om 13 min' in card, card)
    pg.click('#msgCardGo'); pg.wait_for_timeout(700)
    check('"Åk hit": the lead line on Calle\'s boat', pg.eval_on_selector('#probe', 'e => e.classList.contains("show")') and not pg.eval_on_selector('#msgCard', 'e => e.classList.contains("show")'))
    pg.evaluate("document.querySelector('.mLine:not(.mine)').click()"); pg.wait_for_timeout(700)
    pg.click('#msgCardDrop'); pg.wait_for_timeout(300)
    check("...\"Dölj för mig\": hidden for you", not any(m['k'] != 'me' for m in pg.evaluate('window.__ffMsgs()')))
    pg.evaluate('window.__posWrites.length = 0')
    pg.evaluate("document.querySelector('.mLine.mine').click()"); pg.wait_for_timeout(400)
    check('your own: the panel says "Ta bort (för alla)"', pg.inner_text('#msgCardDrop') == 'Ta bort (för alla)' and not pg.is_visible('#msgCardGo'))
    pg.click('#msgCardDrop'); pg.wait_for_timeout(300)
    w = pg.evaluate('window.__posWrites')
    check('...taken back for everyone', not pg.evaluate('window.__ffMsgs()') and w and w[-1]['msg'] is None, w)
    check('no page errors', not errs, errs)
    b.close()
    # your own message comes back from the database (e.g. after a reload / on another phone)
    b, ctx, pg, errs = new_page(p, geo=B3, cfg={'positions': [{'uid': 'filip', 'name': 'Filip', 'lat': B3[0], 'lon': B3[1], 'ageMin': 0, 'msg': 'Fika? ☕', 'msgAgeMin': 1}]}, name='Filip')
    pg.wait_for_timeout(1500)
    check('your message from the database shows at your boat', any(m['k'] == 'me' and 'Fika' in m['t'] for m in pg.evaluate('window.__ffMsgs()')), pg.evaluate('window.__ffMsgs()'))
    b.close()
    # "Egen text": a small box, typing straight away, at most 15 characters (an emoji = 1)
    b, ctx, pg, errs = new_page(p, geo=B3, cfg={}, name='Filip')
    pg.wait_for_timeout(1500)
    pg.click('#msgBtn'); pg.wait_for_timeout(200)
    check('"Egen text": the rainbow words with the pen after them', pg.eval_on_selector('#msgOwnBtn', 'e => e.firstElementChild.className === "rbText" && e.lastElementChild.tagName.toLowerCase() === "svg"'))
    pg.click('#msgOwnBtn'); pg.wait_for_timeout(300)
    check('...tap it: the small box, ready to type (focused), the choices gone', pg.is_visible('#msgOwn') and pg.evaluate("document.activeElement.id") == 'msgOwnIn' and not pg.is_visible('#msgPop') and pg.inner_text('#msgOwnN') == '0/15')
    pg.keyboard.type('Vart är ni?? 😅!!!!'); pg.wait_for_timeout(200)
    v = pg.input_value('#msgOwnIn')
    check('...at most 15 characters (an emoji counts as one); the counter red when full', len(list(v)) == 15 and v == 'Vart är ni?? 😅!' and pg.inner_text('#msgOwnN') == '15/15' and pg.eval_on_selector('#msgOwnN', 'e => e.classList.contains("full")'), v)
    pg.evaluate('window.__posWrites.length = 0')
    pg.keyboard.press('Enter'); pg.wait_for_timeout(400)
    w = [x for x in pg.evaluate('window.__posWrites') if x.get('msg')]
    check('...Enter sends it (for everyone) and shows it at your boat', w and w[-1]['msg'] == 'Vart är ni?? 😅!' and not pg.is_visible('#msgOwn') and any(m['k'] == 'me' and 'Vart är ni' in m['t'] for m in pg.evaluate('window.__ffMsgs()')), w)
    pg.click('#msgBtn'); pg.click('#msgOwnBtn'); pg.wait_for_timeout(200); pg.keyboard.type('Nej'); pg.mouse.click(200, 300); pg.wait_for_timeout(300)
    check('...tap outside: closed, nothing sent', not pg.is_visible('#msgOwn') and not [x for x in pg.evaluate('window.__posWrites') if x.get('msg') == 'Nej'])
    check('no page errors', not errs, errs)
    b.close()
    # not at the lake: no message is sent
    b, ctx, pg, errs = new_page(p, geo=(59.33, 18.06), cfg={}, name='Filip')
    pg.wait_for_timeout(1200); pg.evaluate('window.__posWrites.length = 0')
    pg.click('#msgBtn'); pg.click('#msgPop button:has-text("Fisk")'); pg.wait_for_timeout(300)
    check('away from the lake: nothing sent, a note instead', not [x for x in pg.evaluate('window.__posWrites') if x.get('msg')] and pg.is_visible('#msgToast'))
    b.close()

    # several messages from the same boat: ONE bubble, a row per person, newest first
    cfg3 = {'waypoints': cfg['waypoints'], 'positions': [
        {'uid': 'kalle', 'name': 'Calle', 'lat': B1[0], 'lon': B1[1], 'ageMin': 0, 'msg': 'Kommer 🚤', 'msgAgeMin': 9},
        {'uid': 'pia', 'name': 'Pia', 'lat': B1[0] + 0.00005, 'lon': B1[1], 'ageMin': 0, 'msg': 'Fisk!!! 🎣', 'msgAgeMin': 1},
        {'uid': 'olle', 'name': 'Olle', 'lat': B1[0], 'lon': B1[1] + 0.00008, 'ageMin': 0, 'msg': 'Mat? 🍔', 'msgAgeMin': 4}]}
    b, ctx, pg, errs = new_page(p, geo=B3, cfg=cfg3, name='Filip')
    pg.wait_for_timeout(1500)
    ms = pg.evaluate('window.__ffMsgs()')
    check('three in the same boat: one shared bubble', pg.evaluate("document.querySelectorAll('.msgBub').length") == 1 and len(ms) == 3 and len(set(m['bubble'] for m in ms)) == 1, ms)
    check('...one row per person, newest first (Pia, Olle, Calle)', [m['t'].split('🎣')[0] for m in ms][0].startswith('Fisk') and 'Pia' in ms[0]['t'] and 'Olle' in ms[1]['t'] and 'Calle' in ms[2]['t'], ms)
    check('...older rows fainter', ms[0]['o'] > ms[1]['o'] > ms[2]['o'], [m['o'] for m in ms])
    check('...the rainbow edge round the whole bubble (one is new)', pg.evaluate("!!document.querySelector('.msgBub.multi .msgRb')"))
    pg.screenshot(path='shot_msgs_group.png')
    pg.evaluate("[].filter.call(document.querySelectorAll('.mLine'), e => e.textContent.indexOf('Olle') >= 0)[0].click()"); pg.wait_for_timeout(500)
    card = pg.inner_text('#msgCard')
    check("tap Olle's row: his message's panel", 'OLLE' in card and 'Mat?' in card, card)
    pg.click('#msgCardClose'); pg.wait_for_timeout(400)
    # a finger that starts on a spot still pans the map; a plain tap opens it
    s0 = pg.evaluate('window.__ffGeo.screenOf(%f, %f)' % B4)
    pg.mouse.move(s0[0], s0[1] - 12); pg.mouse.down()
    for k in range(1, 9): pg.mouse.move(s0[0] - 10 * k, s0[1] - 12 + 6 * k); pg.wait_for_timeout(16)
    pg.mouse.up(); pg.wait_for_timeout(500)
    s1 = pg.evaluate('window.__ffGeo.screenOf(%f, %f)' % B4)
    check('drag that starts on a spot: the map pans, the spot is not opened', abs(s1[0] - s0[0] + 80) < 6 and abs(s1[1] - s0[1] - 48) < 6 and not pg.eval_on_selector('#wpSheet', 'e => e.classList.contains("show")'), (s0, s1))
    pg.mouse.click(s1[0], s1[1] - 12); pg.wait_for_timeout(500)
    check('...a tap on it opens it', pg.eval_on_selector('#wpSheet', 'e => e.classList.contains("show")') and pg.input_value('#wpName') == 'Djupa hålet')
    check('no page errors', not errs, errs)
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
