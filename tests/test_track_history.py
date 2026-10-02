from playwright.sync_api import sync_playwright
import fakefb, json, datetime
from fakefb import new_page
# Spår för evigt (ingen Börja om; en annan person väljs i en rullgardin): historik, Spår-menyn, andras spår, uppladdning, Demo Mode (tillfälligt spår), stopp som ringar, Fog of war
results = []
def check(name, cond, info=''):
    results.append(bool(cond)); print(('PASS ' if cond else 'FAIL ') + name + ('  -- ' + str(info) if info != '' else ''))

ME = (58.88951, 15.77759)
def b36(n):
    if n == 0: return '0'
    sg = '-' if n < 0 else ''; n = abs(n); d = '0123456789abcdefghijklmnopqrstuvwxyz'; out = ''
    while n: out = d[n % 36] + out; n //= 36
    return sg + out
def pack(segs):    # same format as packSegs() in js/46-gps-track.js (points: [lat, lon, ms])
    res = []
    for seg in segs:
        pl = po = pt = 0; pts = []
        for la, lo, t in seg:
            la = round(la * 1e6); lo = round(lo * 1e6); t = round(t / 1000)
            pts.append('%s,%s,%s' % (b36(la - pl), b36(lo - po), b36(t - pt))); pl, po, pt = la, lo, t
        res.append(';'.join(pts))
    return '|'.join(res)
def day_n(n):   # a "track day" (06:00 - 06:00), n days ago, as YYYY-MM-DD
    return (datetime.datetime.now() - datetime.timedelta(hours=6) - datetime.timedelta(days=n)).strftime('%Y-%m-%d')
def ms_ago(days): return int((datetime.datetime.now() - datetime.timedelta(days=days)).timestamp() * 1000)
def seg(k, n=20, t0=None):   # a little line near the lake, shifted per k so the days differ
    t0 = t0 or ms_ago(k)
    return [[ME[0] + k * 0.0004 + i * 0.0001, ME[1] + i * 0.0001, t0 + i * 8000] for i in range(n)]
def rec(k, stops=None):
    return {'p': pack([seg(k)]), 's': stops or [], 'n': 20, 'u': 1}
def M(pg, sel): return (pg.get_attribute(sel, 'd') or '').count('M')
def seed(ctx, pg, items):   # items: {key: value|None}; applied once, at the start of the next load (pagehide of the old page can't undo it)
    ctx.add_init_script("if (!sessionStorage.getItem('__seed')) { sessionStorage.setItem('__seed', '1'); var it = %s; for (var k in it) { if (it[k] === null) localStorage.removeItem(k); else localStorage.setItem(k, typeof it[k] === 'string' ? it[k] : JSON.stringify(it[k])); } }" % json.dumps(items))
    pg.evaluate("sessionStorage.removeItem('__seed')")
def open_panel(pg):
    pg.click('#visMoreBtn'); pg.wait_for_timeout(120); pg.click('.visSwatch--track'); pg.wait_for_timeout(350)

other = {'lake': 'regnaren', 'uid': 'calle', 'name': 'Calle', 'day': day_n(2), 'pts': pack([seg(2)]), 'st': '', 'n': 20, 'lakeDay': 'regnaren_' + day_n(2), 'ownKey': 'regnaren_calle_' + day_n(2)}
mine_remote = {'lake': 'regnaren', 'uid': 'filip', 'name': 'Filip', 'day': day_n(9), 'pts': pack([seg(9)]), 'st': '%f,%f,13' % (ME[0] + 0.0002, ME[1] + 0.0001), 'n': 20, 'lakeDay': 'regnaren_' + day_n(9), 'ownKey': 'regnaren_filip_' + day_n(9)}
cfg = {'tracks': {'regnaren_calle_' + day_n(2): other, 'regnaren_filip_' + day_n(9): mine_remote}}

with sync_playwright() as p:
    # ================= history, the panel, Andras =================
    b, ctx, pg, errs = new_page(p, geo=ME, cfg=cfg, name='Filip')
    pg.wait_for_timeout(800)
    # seed: an unfinished track from a day ago (old unpadded day format) -> must become history, not vanish
    yd = datetime.datetime.now() - datetime.timedelta(hours=6) - datetime.timedelta(days=1)
    old_day = '%d-%d-%d' % (yd.year, yd.month, yd.day)
    hist = {day_n(20): rec(20), day_n(45): rec(45), day_n(1): rec(1, [[ME[0] + 0.0004, ME[1], 13]])}
    del hist[day_n(1)]   # (yesterday comes from the unfinished track below)
    seed(ctx, pg, {'ffmap_trackhist_v1': hist, 'ffmap_track_v1': {'day': old_day, 'segs': [seg(1, 30)]}, 'ffmap_tracksync_v1': None})
    pg.reload(); pg.wait_for_timeout(1800)
    h = pg.evaluate("JSON.parse(localStorage.getItem('ffmap_trackhist_v1'))")
    check('an old unfinished day moves to the history (padded day key)', day_n(1) in h and h[day_n(1)]['n'] == 30, sorted(h))
    check('...and is uploaded to Firestore `tracks`', any(s['id'] == 'regnaren_filip_' + day_n(1) and s['lakeDay'] == 'regnaren_' + day_n(1) and s['ownKey'] == 'regnaren_filip_' + day_n(1) and s['lake'] == 'regnaren' for s in pg.evaluate('window.__trackSets')), [s['id'] for s in pg.evaluate('window.__trackSets')])
    check('a new phone gets its own days back from Firestore (once)', day_n(9) in pg.evaluate("JSON.parse(localStorage.getItem('ffmap_trackhist_v1'))"))
    gets = pg.evaluate('window.__trackGets')
    check('...asking only for its own days', len(gets) == 1 and gets[0].startswith('ownKey >= regnaren_filip_'), gets)
    check('default: only today (just its first point so far, no line)', 'L' not in (pg.get_attribute('#trackLayer .trkLine', 'd') or ''), pg.get_attribute('#trackLayer .trkLine', 'd'))
    pg.evaluate("1")
    # a track today (drive a little)
    la, lo = ME
    for i in range(10):
        la += 10 / 111320.0; ctx.set_geolocation({'latitude': la, 'longitude': lo, 'accuracy': 5}); pg.wait_for_timeout(700)
    check('today is drawn', M(pg, '#trackLayer .trkLine') == 1, M(pg, '#trackLayer .trkLine'))
    open_panel(pg)
    check('tap the Spår icon in Filter -> the Spår panel opens', pg.is_visible('#trkPanel') and pg.eval_on_selector('#trkPanel', 'e=>e.classList.contains("show")'))
    check('...without switching the Spår toggle', pg.is_checked('#toggleTrack'))
    check('Filter closes when the panel opens', not pg.is_visible('#visMore'))
    pg.screenshot(path='shot_trk_panel.png')
    check('the info line says how many days are saved', 'dagar' in pg.inner_text('#trkInfo'), pg.inner_text('#trkInfo'))
    for r, n in [('7', 2), ('30', 4), ('all', 5), ('today', 1)]:
        pg.click('#trkRange button[data-r="%s"]' % r); pg.wait_for_timeout(200)
        check('range %s -> %d days drawn' % (r, n), M(pg, '#trackLayer .trkLine') == n, M(pg, '#trackLayer .trkLine'))
    # (7 d = today + yesterday; 30 d = + 20 d ago + 9 d ago; all = + 45 d ago)
    pg.click('#trkRange button[data-r="30"]')
    pg.click('#trkDash button[data-d="0"]'); pg.wait_for_timeout(150)
    check('Hel -> solid line', pg.eval_on_selector('#trackLayer', 'e=>e.classList.contains("solid")') and pg.eval_on_selector('#trackLayer .trkLine', 'e=>getComputedStyle(e).strokeDasharray') == 'none')
    pg.click('#trkColors button[data-c="#FFFFFF"]'); pg.wait_for_timeout(150)
    check('colour -> the line is white', pg.eval_on_selector('#trackLayer .trkLine', 'e=>getComputedStyle(e).stroke') == 'rgb(255, 255, 255)', pg.eval_on_selector('#trackLayer .trkLine', 'e=>getComputedStyle(e).stroke'))
    check('nobody else is fetched before you pick someone', len(pg.evaluate('window.__trackGets')) == 1)
    check('...and nobody else line drawn', M(pg, '#trackLayer .trkOther') == 0)
    opts = pg.eval_on_selector_all('#trkWhoSel option', 'a=>a.map(e=>e.textContent)')
    check('the drop-down lists the member list (not yourself), "Ingen" first', opts[0] == 'Ingen' and 'Calle' in opts and 'Filip' not in opts, opts[:5])
    pg.select_option('#trkWhoSel', 'calle'); pg.wait_for_timeout(500)
    gets = pg.evaluate('window.__trackGets')
    check('pick Calle -> only HIS days are fetched (by his key + day range)', len(gets) == 2 and gets[1].startswith('ownKey >= regnaren_calle_' + day_n(29)) and gets[1].endswith('ownKey <= regnaren_calle_~'), gets[-1])
    check('...his line is drawn', M(pg, '#trackLayer .trkOther') == 1, M(pg, '#trackLayer .trkOther'))
    check('...and the info line names him', 'Calle' in pg.inner_text('#trkInfo'), pg.inner_text('#trkInfo'))
    pg.select_option('#trkWhoSel', ''); pg.wait_for_timeout(200)
    check('Ingen -> his line is hidden again', M(pg, '#trackLayer .trkOther') == 0)
    pg.select_option('#trkWhoSel', 'calle'); pg.wait_for_timeout(300)
    check('...picking him again does not read the database twice', len(pg.evaluate('window.__trackGets')) == 2)
    pg.click('#trkWho button[data-w="mine"]'); pg.wait_for_timeout(150)
    check('Mina off -> my lines hidden', M(pg, '#trackLayer .trkLine') == 0 and M(pg, '#trackLayer .trkOther') == 1)
    pg.click('#trkWho button[data-w="mine"]'); pg.wait_for_timeout(150)
    # ---- stops as rings ----
    check('stops off by default', pg.eval_on_selector_all('#trackLayer .trkStops circle', 'a=>a.length') == 0)
    pg.click('label[for="trkStopsToggle"] .toggle'); pg.wait_for_timeout(200)
    txt = pg.eval_on_selector_all('#trackLayer .trkStops text', 'a=>a.map(e=>e.textContent)')
    check('stops on -> a ring with "13 min" (from the day 9 d ago)', '13 min' in txt, txt)
    check('...with a slider for the shortest stop that counts', pg.is_visible('#trkStopMin'))
    pg.evaluate("(() => { const e = document.getElementById('trkStopMin'); e.value = '20'; e.dispatchEvent(new Event('input', {bubbles: true})); })()"); pg.wait_for_timeout(200)
    txt = pg.eval_on_selector_all('#trackLayer .trkStops text', 'a=>a.map(e=>e.textContent)')
    check('minimum 20 min -> the 13 min stop is hidden', '13 min' not in txt and pg.inner_text('#trkStopMinVal') == '20 min', txt)
    pg.evaluate("(() => { const e = document.getElementById('trkStopMin'); e.value = '5'; e.dispatchEvent(new Event('input', {bubbles: true})); })()"); pg.wait_for_timeout(200)
    pg.screenshot(path='shot_trk_stops.png')
    # ---- settings survive a reload ----
    pg.evaluate("document.dispatchEvent(new Event('visibilitychange'))"); pg.reload(); pg.wait_for_timeout(1800)
    cfgs = pg.evaluate("JSON.parse(localStorage.getItem('ffmap_track_cfg_v1'))")
    check('panel choices are remembered', cfgs['range'] == '30' and cfgs['dash'] is False and cfgs['color'] == '#FFFFFF' and cfgs['stops'] is True and cfgs['who'] == 'calle' and cfgs['stopMin'] == 5, cfgs)
    check('...his days are fetched again at start (he was picked)', any(g.startswith('ownKey >= regnaren_calle_') for g in pg.evaluate('window.__trackGets')))
    # ---- upload of today ----
    sets0 = len(pg.evaluate('window.__trackSets'))
    ctx.set_geolocation({'latitude': la + 0.0002, 'longitude': lo, 'accuracy': 5}); pg.wait_for_timeout(900)
    pg.evaluate("Object.defineProperty(document, 'visibilityState', {value: 'hidden', configurable: true}); document.dispatchEvent(new Event('visibilitychange'))"); pg.wait_for_timeout(300)
    ts = [s for s in pg.evaluate('window.__trackSets') if s['id'] == 'regnaren_filip_' + day_n(0)]
    check('today is uploaded when the app goes to the background', len(ts) >= 1 and ts[-1]['n'] >= 8 and ts[-1]['pts'], len(ts))
    n1 = len(pg.evaluate('window.__trackSets'))
    pg.evaluate("document.dispatchEvent(new Event('visibilitychange'))"); pg.wait_for_timeout(200)
    check('...but not again when nothing new was recorded', len(pg.evaluate('window.__trackSets')) == n1)
    pg.evaluate("Object.defineProperty(document, 'visibilityState', {value: 'visible', configurable: true})")
    open_panel(pg) if not pg.eval_on_selector('#trkPanel', 'e=>e.classList.contains("show")') else None
    check('there is no "Börja om" (the track cannot be wiped)', pg.evaluate("!document.getElementById('trackClearBtn')"))
    pg.click('#trkClose'); pg.wait_for_timeout(350)
    check('✕ closes the panel', not pg.eval_on_selector('#trkPanel', 'e=>e.classList.contains("show")'))
    pg.click('#menuBtn'); pg.click('#menuItemSettings'); pg.wait_for_timeout(300)
    check('Inställningar: a pointer to the panel instead of the old track rows', pg.is_visible('#trkOpenBtn') and not pg.eval_on_selector('#settingsBody', 'e=>!!e.querySelector("#trackOpSlider")'))
    pg.click('#trkOpenBtn'); pg.wait_for_timeout(500)
    check('...Öppna takes you to the panel', pg.eval_on_selector('#trkPanel', 'e=>e.classList.contains("show")') and not pg.eval_on_selector('#settingsView', 'e=>e.classList.contains("show")'))
    check('no page errors', not errs, errs[:3])
    b.close()

    # ================= stops from a real dwell (today's own track) =================
    b, ctx, pg, errs = new_page(p, geo=ME, cfg={}, name='Filip')
    now = int(datetime.datetime.now().timestamp() * 1000)
    t0 = now - 20 * 60000
    today_seg = [[ME[0], ME[1], t0], [ME[0] + 0.00007, ME[1], t0 + 5 * 60000], [ME[0] + 0.002, ME[1], t0 + 6 * 60000], [ME[0] + 0.0021, ME[1], t0 + 6 * 60000 + 5000]]
    seed(ctx, pg, {'ffmap_track_v1': {'day': day_n(0), 'segs': [today_seg]}, 'ffmap_track_cfg_v1': {'stops': True}})
    pg.reload(); pg.wait_for_timeout(1800)
    txt = pg.eval_on_selector_all('#trackLayer .trkStops text', 'a=>a.map(e=>e.textContent)')
    check('a 5 min dwell in today\'s track becomes a "5 min" ring', '5 min' in txt, txt)
    b.close()

    # ================= Demo Mode: a temporary track, never saved =================
    b, ctx, pg, errs = new_page(p, geo=ME, cfg={}, name='Filip')
    seed(ctx, pg, {'ffmap_track_v1': None, 'regnaren_demo_mode_v1': '1', 'regnaren_demo_since_v1': '9999999999999', 'regnaren_demo_move_v1': '1'})
    pg.reload(); pg.wait_for_timeout(1500)
    la, lo = ME
    for i in range(8):
        la += 12 / 111320.0; ctx.set_geolocation({'latitude': la, 'longitude': lo, 'accuracy': 5}); pg.wait_for_timeout(900)
    check('Demo Mode is on', pg.evaluate("document.getElementById('demoModeToggle').checked"))
    pg.wait_for_timeout(5000)
    d = pg.get_attribute('#trackLayer .trkLine', 'd') or ''
    check('Demo Mode shows a track on the screen (to try the Spår out)', d.count('L') >= 1, d[:60])
    saved = pg.evaluate("localStorage.getItem('ffmap_track_v1')")
    n = 0
    try: n = sum(len(s) for s in json.loads(saved)['segs'])
    except Exception: pass
    check('...but it is NOT saved on the phone (own track)', n == 0, (saved or '')[:80])
    check('...only temporarily (sessionStorage, survives a rotation)', pg.evaluate("!!sessionStorage.getItem('ffmap_demotrack_v1')"))
    pg.evaluate("document.dispatchEvent(new Event('visibilitychange'))"); pg.wait_for_timeout(200)
    check('...and never uploaded to Firestore', not pg.evaluate('window.__trackSets'), pg.evaluate('window.__trackSets'))
    check('...nor added to the history', not pg.evaluate("localStorage.getItem('ffmap_trackhist_v1')") or pg.evaluate("localStorage.getItem('ffmap_trackhist_v1')") == '{}')
    open_panel(pg)
    check('the panel says the demo track is not saved', 'Demo Mode' in pg.inner_text('#trkInfo'), pg.inner_text('#trkInfo'))
    pg.click('#trkClose'); pg.wait_for_timeout(300)
    pg.click('#menuBtn'); pg.click('#menuItemSettings'); pg.wait_for_timeout(300); pg.click('#demoModeToggle'); pg.wait_for_timeout(600)
    check('Demo Mode off -> the demo track is gone', 'L' not in (pg.get_attribute('#trackLayer .trkLine', 'd') or '') and not pg.evaluate("sessionStorage.getItem('ffmap_demotrack_v1')"), pg.get_attribute('#trackLayer .trkLine', 'd'))
    b.close()

    # ================= Fog of war =================
    b, ctx, pg, errs = new_page(p, geo=ME, cfg={}, name='Filip')
    la, lo = ME
    for i in range(12):
        la += 10 / 111320.0; ctx.set_geolocation({'latitude': la, 'longitude': lo, 'accuracy': 5}); pg.wait_for_timeout(650)
    pg.evaluate("document.getElementById('locateBtn').click()"); pg.wait_for_timeout(1500)
    check('Fog of war is off by default', not pg.is_visible('#fogLayer'))
    pg.click('#visMoreBtn'); pg.wait_for_timeout(150)
    check('Fog of war is in the Lager list', pg.is_visible('label:has(#toggleFog)'))
    pg.click('label:has(#toggleFog) .toggle'); pg.wait_for_timeout(500)
    check('...on -> the fog layer shows', pg.is_visible('#fogLayer'))
    pg.click('#visMoreBtn'); pg.wait_for_timeout(200)
    st = pg.evaluate('window.__ffFog()')
    check('cells are marked along the track', st['on'] and st['cells'] >= 8, st)
    box = pg.evaluate("(() => { const r = document.getElementById('dot').getBoundingClientRect(); return [r.left + r.width / 2, r.top + r.height / 2]; })()")
    al = pg.evaluate("""([x, y]) => { const c = document.getElementById('fogLayer'), g = c.getContext('2d'), d = c.width / c.clientWidth, out = [];
        for (let dx = 0; dx <= 90; dx += 2){ out.push(g.getImageData(Math.round((x + dx) * d), Math.round(y * d), 1, 1).data[3]); } return out; }""", box)
    check('dark far away, clear where you are', al[0] < 40 and al[-1] > 200, (al[0], al[-1]))
    check('...and a soft fade in between (never a hard edge)', all(al[i] <= al[i + 1] + 6 for i in range(len(al) - 1)) and len([a for a in al if 60 < a < 190]) >= 2, al)
    z = pg.evaluate("[getComputedStyle(document.getElementById('fogLayer')).zIndex, getComputedStyle(document.getElementById('osmNames')).zIndex, getComputedStyle(document.getElementById('trackLayer')).zIndex]")
    check('z-order: fog 12, names 11, track 13', z == ['12', '11', '13'], z)
    pg.screenshot(path='shot_fog.png')
    pg.reload(); pg.wait_for_timeout(1800)
    check('Fog of war stays on after a reload (rebuilt from the saved track)', pg.is_visible('#fogLayer') and pg.evaluate('window.__ffFog().cells') >= 8, pg.evaluate('window.__ffFog()'))
    check('no page errors', not errs, errs[:3])
    b.close()

    # ================= the panel survives a rotation =================
    b, ctx, pg, errs = new_page(p, geo=ME, cfg={}, name='Filip')
    ctx.add_init_script("Object.defineProperty(navigator, 'standalone', { value: true, configurable: true });")
    pg.reload(); pg.wait_for_timeout(1200)
    open_panel(pg)
    pg.set_viewport_size({'width': 844, 'height': 390})
    pg.evaluate("window.dispatchEvent(new Event('orientationchange')); if (screen.orientation) screen.orientation.dispatchEvent(new Event('change'));")
    pg.wait_for_load_state('load'); pg.wait_for_timeout(1800)
    check('the Spår panel is still open after a rotation', pg.eval_on_selector('#trkPanel', 'e=>e.classList.contains("show")'))
    pg.screenshot(path='shot_trk_panel_land.png')
    b.close()

print('%d/%d passed' % (sum(results), len(results)))
