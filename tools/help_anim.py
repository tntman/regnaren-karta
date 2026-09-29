"""Make the animations on the Hjälp page: docs/help/<name>.webp.

    py -3 tools/help_anim.py            (all)
    py -3 tools/help_anim.py lodet fara (just those)

Records the real app in the test browser (Playwright + Edge, like the tests) with
made-up spots, boats, weather and lightning -- never the real Firebase or FMI (tests/fakefb
blocks them). Everything happens ON THE LAKE (Regnaren's south basin, points checked
against the depth data before recording), never up on land. A white dot shows the finger.
"Installera" is a drawn Safari (tools/help_install_anim.html) -- Safari's own menus
can't be recorded. Writes each animation's size into src/html/40-help.html -- build afterwards.
"""
import sys, os, io, json, time, math, subprocess
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'tests'))
if not os.environ.get('CHROMIUM'):
    for e in (r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe', r'C:\Program Files\Microsoft\Edge\Application\msedge.exe'):
        if os.path.exists(e): os.environ['CHROMIUM'] = e; break
import fakefb                                   # (safety: no real Firebase / FMI, no service worker)
import test_weather
from playwright.sync_api import sync_playwright
from PIL import Image

OUT = os.path.join(ROOT, 'docs', 'help')
PORT = 8896
APP = 'http://localhost:%d/docs/index.html' % PORT
OUT_W = 432                                     # width of the saved animation (px)
FRAME_S = 0.16                                  # at most ~6 frames/s
QUALITY = 42

# places on Regnaren's water (south basin + the bay east of it, north basin); depth in m
P = {'B1': (58.887421, 15.775569), 'B2': (58.88689, 15.780714), 'B3': (58.887269, 15.772629),
     'B4': (58.88651, 15.777774), 'B5': (58.88613, 15.774099), 'E1': (58.884421, 15.780456),
     'T1': (58.895813, 15.774099), 'T2': (58.895624, 15.781449), 'T3': (58.896383, 15.777774)}
ME = P['B3']
def mix(a, b, t): return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)
def metres(a, b):
    return math.hypot((b[0] - a[0]) * 111200, (b[1] - a[1]) * 111320 * math.cos(math.radians(a[0])))

SPOTS = [
    {'lat': P['B4'][0], 'lon': P['B4'][1], 'name': 'Djupa hålet', 'uid': 'filip', 'by': 'Filip', 'type': 'abborre'},
    {'lat': P['B2'][0], 'lon': P['B2'][1], 'name': 'Kalles gäddvik', 'uid': 'kalle', 'by': 'Calle', 'type': 'gadda'},
    {'lat': P['T2'][0], 'lon': P['T2'][1], 'name': 'Gösgropen', 'uid': 'pia', 'by': 'Pia', 'type': 'gos'},
    {'lat': P['T1'][0], 'lon': P['T1'][1], 'name': 'Norra udden', 'uid': 'filip', 'by': 'Filip', 'type': 'mark'},
]
BOATS = [{'uid': 'kalle', 'name': 'Calle', 'lat': P['T3'][0], 'lon': P['T3'][1], 'ageMin': 0},
         {'uid': 'pia', 'name': 'Pia', 'lat': P['T1'][0] + 0.0004, 'lon': P['T1'][1] + 0.002, 'ageMin': 0}]

# the finger: a white dot while "touching"
FINGER_JS = r"""(function(){
  var f = null;
  function mk(){ f = document.createElement('div');
    f.style.cssText = 'position:fixed;left:0;top:0;width:40px;height:40px;margin:-20px 0 0 -20px;border-radius:50%;' +
      'background:rgba(255,255,255,.38);border:2.5px solid rgba(255,255,255,.95);box-shadow:0 0 0 3px rgba(0,0,0,.28),0 3px 10px rgba(0,0,0,.4);' +
      'z-index:2147483647;pointer-events:none;opacity:0;transition:opacity .12s;';
    document.documentElement.appendChild(f); }
  function pos(e){ if (!f) mk(); f.style.transform = 'translate(' + e.clientX + 'px,' + e.clientY + 'px)'; }
  addEventListener('pointerdown', function(e){ pos(e); f.style.opacity = '1'; }, true);
  addEventListener('pointermove', function(e){ if (f && f.style.opacity === '1') pos(e); }, true);
  addEventListener('pointerup', function(){ if (f) f.style.opacity = '0'; }, true);
})();"""

def Y(y0, y1): return {'x': 0, 'y': y0, 'width': 390, 'height': y1 - y0}   # a band of the screen (css px)

class Rec:
    """the browser's own screen recording (CDP screencast): smooth, with real timing.
    clip = part of the screen to keep (css px)."""
    def __init__(self, pg, clip=None):
        import base64
        self.pg, self.clip, self.fr, self.b64, self.acks = pg, clip, [], base64, []
        self.cdp = pg.context.new_cdp_session(pg)
        self.cdp.on('Page.screencastFrame', self._frame)
        self.cdp.send('Page.startScreencast', {'format': 'jpeg', 'quality': 88, 'maxWidth': 780, 'maxHeight': 1688, 'everyNthFrame': 1})
    def _frame(self, e):                  # (acknowledged from the waiting loop -- not from inside the event)
        self.fr.append((e['data'], e['metadata']['timestamp'])); self.acks.append(e['sessionId'])
    def _ack(self):
        while self.acks:
            sid = self.acks.pop(0)
            try: self.cdp.send('Page.screencastFrameAck', {'sessionId': sid})
            except Exception: pass
    def snap(self): self.hold(35)
    def hold(self, ms):
        end = time.time() + ms / 1000.0
        while True:
            self._ack()
            left = end - time.time()
            if left <= 0: break
            self.pg.wait_for_timeout(min(25, max(1, int(left * 1000))))
    def save(self, name, last=1600):
        self.pg.wait_for_timeout(150)
        try: self.cdp.send('Page.stopScreencast')
        except Exception: pass
        os.makedirs(OUT, exist_ok=True)
        # ~8 frames/s is plenty for these (and keeps the file small)
        kept = []
        for i, (data, t) in enumerate(self.fr):
            if not kept or t - kept[-1][1] >= FRAME_S or i == len(self.fr) - 1: kept.append((data, t))
        ims, durs = [], []
        for i, (data, t) in enumerate(kept):
            im = Image.open(io.BytesIO(self.b64.b64decode(data))).convert('RGB')
            if self.clip:
                k = im.width / 390.0; c = self.clip
                im = im.crop((int(c['x'] * k), int(c['y'] * k), int((c['x'] + c['width']) * k), int((c['y'] + c['height']) * k)))
            ims.append(im.resize((OUT_W, int(round(im.height * OUT_W / im.width))), Image.LANCZOS))
            durs.append(max(40, int(round((kept[i + 1][1] - t) * 1000))) if i + 1 < len(kept) else last)
        durs[-1] = max(durs[-1], last)
        path = os.path.join(OUT, name + '.webp')
        ims[0].save(path, 'WEBP', save_all=True, append_images=ims[1:], duration=durs, loop=0, quality=QUALITY, method=6)
        print('  %s: %d frames, %.1f s, %d kB' % (name, len(ims), sum(durs) / 1000.0, os.path.getsize(path) // 1024))
        set_size_in_page(name, ims[0].width, ims[0].height)

def set_size_in_page(name, w, h):
    """the Hjälp page reserves each animation's space (no jumping while they load):
    write the new size into src/html/40-help.html (then build)"""
    import re
    p = os.path.join(ROOT, 'src', 'html', '40-help.html'); s = open(p, encoding='utf-8').read()
    s2 = re.sub(r'<img loading="lazy"( width="\d+" height="\d+")? src="help/%s\.webp"' % name,
                '<img loading="lazy" width="%d" height="%d" src="help/%s.webp"' % (w, h, name), s)
    if s2 != s:
        with open(p, 'w', encoding='utf-8') as f: f.write(s2)   # (text mode: keeps the file's CRLF on Windows)

def open_app(p, geo=ME, spots=SPOTS, boats=BOATS, wind=(3.2, 225), fmi=None, name='Filip'):
    b = p.chromium.launch(**fakefb.LAUNCH)
    ctx = b.new_context(viewport={'width': 390, 'height': 844}, device_scale_factor=2, has_touch=True, is_mobile=True,
                        geolocation={'latitude': geo[0], 'longitude': geo[1], 'accuracy': 6}, permissions=['geolocation'])
    ctx.add_init_script('window.__fakeCfg = ' + json.dumps({'waypoints': spots, 'positions': boats}) + ';')
    ctx.add_init_script(FINGER_JS)
    ctx.add_init_script(fakefb.FAKE_FIREBASE_JS)
    wx = test_weather.wx_json(); wx['current']['wind_speed_10m'], wx['current']['wind_direction_10m'] = wind
    wx['current']['wind_gusts_10m'] = round(wind[0] * 1.6, 1)
    ctx.route('**/api.open-meteo.com/**', lambda r: r.fulfill(status=200, content_type='application/json', body=json.dumps(wx), headers={'Access-Control-Allow-Origin': '*'}))
    if fmi: ctx.route('**/opendata.fmi.fi/**', fmi)
    pg = ctx.new_page(); errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.goto(APP); pg.wait_for_timeout(700)
    fakefb.login(pg, name); pg.wait_for_timeout(2600)
    assert not errs, errs
    return b, ctx, pg

def scr(pg, ll):
    return pg.evaluate('([a, b]) => __ffGeo.screenOf(a, b)', list(ll))
def check_water(pg, ll, min_d=1.0):
    d = pg.evaluate('([a, b]) => __ffGeo.depthAt(a, b)', list(ll))
    assert d is not None and d >= min_d, ('not on the water', ll, d)
def bring(pg, ll, to=(195, 430)):
    """drag the map (not recorded) so that a place is at a screen point"""
    x, y = scr(pg, ll)
    pg.mouse.move(200, 500); pg.mouse.down(); pg.mouse.move(200 + to[0] - x, 500 + to[1] - y, steps=10); pg.mouse.up(); pg.wait_for_timeout(900)
def tap(pg, rec, x, y, hold=160, after=900):
    pg.mouse.move(x, y); pg.mouse.down(); rec.hold(hold); pg.mouse.up(); rec.hold(after)
def tap_el(pg, rec, sel, **kw):
    bb = pg.locator(sel).first.bounding_box()
    tap(pg, rec, bb['x'] + bb['width'] / 2, bb['y'] + bb['height'] / 2, **kw)
def press(pg, rec, x, y, ms=900, after=900):
    pg.mouse.move(x, y); pg.mouse.down(); rec.hold(ms); pg.mouse.up(); rec.hold(after)
def drag(pg, rec, a, b, steps=14):
    pg.mouse.move(*a); pg.mouse.down(); rec.snap()
    for i in range(1, steps + 1):
        pg.mouse.move(a[0] + (b[0] - a[0]) * i / steps, a[1] + (b[1] - a[1]) * i / steps); rec.snap()
    pg.mouse.up()
def sail(pg, ctx, rec, a, b, metres_max=None, speed=8.0, dt=0.5):
    """GPS fixes from a towards b at a boat's speed (m/s), one every dt s -- only on the water"""
    L = metres(a, b); L = min(L, metres_max) if metres_max else L
    n = max(1, int(L / (speed * dt)))
    for k in range(1, n + 1):
        ll = mix(a, b, k * speed * dt / metres(a, b)); check_water(pg, ll)
        ctx.set_geolocation({'latitude': ll[0], 'longitude': ll[1], 'accuracy': 5}); rec.hold(int(dt * 1000))
    return ll
def zoom_at(pg, ll, clicks, to=None):
    x, y = scr(pg, ll); pg.mouse.move(x, y)
    for i in range(abs(clicks)): pg.mouse.wheel(0, -300 if clicks > 0 else 300); pg.wait_for_timeout(80)
    pg.wait_for_timeout(1000)
    if to: bring(pg, ll, to)
def typ(pg, rec, sel, text):
    pg.fill(sel, '')
    for ch in text: pg.type(sel, ch); rec.snap()

# ---------------------------------------------------------------- the scenes
def s_kartan(p):
    b, ctx, pg = open_app(p)
    bring(pg, P['B1'], (195, 520))
    rec = Rec(pg, Y(200, 844)); rec.hold(700)
    drag(pg, rec, (120, 520), (260, 500)); rec.hold(500)        # along the lake
    drag(pg, rec, (260, 500), (150, 540)); rec.hold(500)
    for i in range(2):                                          # double tap = zoom in (on the water)
        x, y = scr(pg, P['B1'])
        pg.mouse.move(x, y); pg.mouse.down(); rec.snap(); pg.mouse.up(); pg.mouse.down(); rec.snap(); pg.mouse.up(); rec.hold(1500)
    x, y = scr(pg, P['B1']); drag(pg, rec, (x, y), (x - 90, y + 20)); rec.hold(1300)
    rec.save('kartan'); b.close()

def s_kartlagen(p):
    b, ctx, pg = open_app(p)
    rec = Rec(pg, Y(0, 560)); rec.hold(600)
    for i in range(4): tap_el(pg, rec, '#mapTypeBtn', after=1500)
    bb = pg.locator('#mapTypeBtn').bounding_box()
    press(pg, rec, bb['x'] + 20, bb['y'] + 20, ms=900, after=1600)
    tap_el(pg, rec, '#mapTypePop .styleOpt[data-style="s3"]', after=1700)
    rec.save('kartlagen'); b.close()

def s_position(p):
    b, ctx, pg = open_app(p)
    zoom_at(pg, ME, 4, (110, 470))
    rec = Rec(pg, Y(250, 844)); rec.hold(800)
    ll = sail(pg, ctx, rec, ME, P['B1'], metres_max=40, speed=4.5)
    sail(pg, ctx, rec, ll, P['B4'], metres_max=25, speed=4.5); rec.hold(900)
    drag(pg, rec, (200, 380), (300, 250)); rec.hold(600)
    tap_el(pg, rec, '#locateBtn', after=1800)
    rec.save('position'); b.close()

def s_lodet(p):
    b, ctx, pg = open_app(p)
    bring(pg, mix(ME, P['E1'], 0.5), (195, 470))
    rec = Rec(pg, Y(120, 720)); rec.hold(700)
    check_water(pg, P['E1'])
    x, y = scr(pg, P['E1']); tap(pg, rec, x, y, after=2600)
    sail(pg, ctx, rec, ME, P['B1'], metres_max=60); rec.hold(1200)
    x, y = scr(pg, P['E1']); tap(pg, rec, x, y, after=1200)
    rec.save('lodet'); b.close()

def s_platser(p):
    """add: hold a finger on the water (Markering), then ＋ = a spot where the boat is (Gädda)"""
    b, ctx, pg = open_app(p)
    bring(pg, P['B1'], (190, 330))
    rec = Rec(pg); rec.hold(600)
    spot = mix(P['B1'], P['B5'], 0.5); check_water(pg, spot)
    x, y = scr(pg, spot); press(pg, rec, x, y, ms=900, after=600)
    tap_el(pg, rec, '#wpTypeSeg button[data-type="mark"]', after=400)
    typ(pg, rec, '#wpName', 'Kanten'); rec.hold(300)
    tap_el(pg, rec, '#wpSave', after=1200)
    tap_el(pg, rec, '#addHereBtn', after=1300)                 # ＋: where you are (the boat is on the water)
    tap_el(pg, rec, '#wpTypeSeg button[data-type="gadda"]', after=400)
    typ(pg, rec, '#wpName', 'Gäddhugget'); rec.hold(300)
    tap_el(pg, rec, '#wpSave', after=1800)
    rec.save('platser'); b.close()

def s_andra(p):
    """change and delete: tap your own spot -> other type + name -> save; tap again -> Ta bort"""
    b, ctx, pg = open_app(p)
    bring(pg, P['B4'], (195, 330))
    rec = Rec(pg); rec.hold(700)
    x, y = scr(pg, P['B4']); tap(pg, rec, x, y - 8, after=1000)     # "Djupa hålet" (yours, Abborre)
    tap_el(pg, rec, '#wpTypeSeg button[data-type="gos"]', after=500)
    typ(pg, rec, '#wpName', 'Gösgropen'); rec.hold(300)
    tap_el(pg, rec, '#wpSave', after=1500)
    x, y = scr(pg, P['B4']); tap(pg, rec, x, y - 8, after=1100)
    tap_el(pg, rec, '#wpDelete', after=1800)
    rec.save('andra'); b.close()

def s_fara(p):
    b, ctx, pg = open_app(p)
    bring(pg, P['B1'], (195, 330))
    rec = Rec(pg); rec.hold(600)
    a = mix(P['B5'], P['B3'], 0.4); check_water(pg, a)
    x, y = scr(pg, a); press(pg, rec, x, y, ms=900, after=600)
    tap_el(pg, rec, '#wpTypeSeg button[data-type="fara"]', after=400)
    typ(pg, rec, '#wpName', 'Sten'); tap_el(pg, rec, '#wpSave', after=1300)
    m = mix(P['B1'], P['B4'], 0.5); check_water(pg, m)
    x, y = scr(pg, m); press(pg, rec, x, y, ms=900, after=600)
    tap_el(pg, rec, '#wpTypeSeg button[data-type="meet"]', after=400)
    typ(pg, rec, '#wpName', 'Lunch'); tap_el(pg, rec, '#wpSave', after=3200)
    rec.save('fara'); b.close()

def s_batar(p):
    boats = [{'uid': 'kalle', 'name': 'Calle', 'lat': P['E1'][0], 'lon': P['E1'][1], 'ageMin': 0},
             {'uid': 'pia', 'name': 'Pia', 'lat': P['B1'][0], 'lon': P['B1'][1], 'ageMin': 0},
             {'uid': 'olle', 'name': 'Olle', 'lat': P['B5'][0], 'lon': P['B5'][1], 'ageMin': 25}]
    b, ctx, pg = open_app(p, boats=boats)
    bring(pg, mix(P['B1'], P['E1'], 0.5), (195, 430))
    rec = Rec(pg, Y(150, 750)); rec.hold(600)
    for k in range(1, 7):
        c = mix(P['E1'], P['B4'], k / 7.0); q = mix(P['B1'], P['B2'], k / 7.0)
        check_water(pg, c); check_water(pg, q)
        pg.evaluate('(a) => { __addPos(a[0]); __addPos(a[1]); }', [{'uid': 'kalle', 'name': 'Calle', 'lat': c[0], 'lon': c[1]}, {'uid': 'pia', 'name': 'Pia', 'lat': q[0], 'lon': q[1]}])
        rec.hold(650)
    x, y = scr(pg, mix(P['E1'], P['B4'], 6 / 7.0)); tap(pg, rec, x, y, after=2400)
    if pg.is_visible('#boatInfoClose'): tap_el(pg, rec, '#boatInfoClose', after=800)
    rec.save('batar'); b.close()

def s_mat(p):
    b, ctx, pg = open_app(p)
    bring(pg, P['B1'], (195, 400))
    rec = Rec(pg); rec.hold(500)
    tap_el(pg, rec, '#measureBtn', after=700)
    for ll in (P['B3'], P['B1'], P['B4'], P['E1']):
        check_water(pg, ll); x, y = scr(pg, ll); tap(pg, rec, x, y, after=900)
    tap_el(pg, rec, '#mpUndo', after=1100)
    tap_el(pg, rec, '#mpClose', after=900)
    rec.save('mat'); b.close()

def s_vader(p):
    b, ctx, pg = open_app(p, wind=(6.0, 250))
    bring(pg, P['B1'], (195, 470))
    rec = Rec(pg, Y(0, 650)); rec.hold(500)
    tap_el(pg, rec, '#wxChip', after=2600)
    tap_el(pg, rec, '#wxClose', after=500)
    tap_el(pg, rec, '#visMoreBtn', after=500)
    tap_el(pg, rec, 'label:has(#toggleWind) .toggle', after=500)
    tap_el(pg, rec, '#visMoreBtn', after=4200)
    rec.save('vader'); b.close()

def s_blixtar(p):
    km_lat, km_lon = 1 / 111.2, 1 / (111.32 * math.cos(math.radians(ME[0])))
    strikes = [(1.3, 0.9, 1.5), (1.7, 1.4, 3), (0.6, 1.6, 6), (2.0, 0.3, 9), (0.9, 2.1, 14), (1.5, -0.9, 20), (2.2, 1.9, 26), (0.2, 1.2, 11), (1.1, 1.5, 4), (8, 9, 5), (11, 7, 12)]
    def xml():
        els = []
        for i, (e, n, ago) in enumerate(strikes):
            t = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(time.time() - ago * 60))
            els.append('<wfs:member><BsWfs:BsWfsElement><BsWfs:Location><gml:Point><gml:pos>%.5f %.5f </gml:pos></gml:Point></BsWfs:Location>'
                       '<BsWfs:Time>%s</BsWfs:Time><BsWfs:ParameterName>peak_current</BsWfs:ParameterName><BsWfs:ParameterValue>-9</BsWfs:ParameterValue></BsWfs:BsWfsElement></wfs:member>'
                       % (ME[0] + n * km_lat, ME[1] + e * km_lon, t))
        return '<wfs:FeatureCollection xmlns:wfs="x" xmlns:gml="y" xmlns:BsWfs="z">' + ''.join(els) + '</wfs:FeatureCollection>'
    fmi = lambda r: r.fulfill(status=200, content_type='text/xml', body=xml(), headers={'Access-Control-Allow-Origin': '*'})
    b, ctx, pg = open_app(p, fmi=fmi)
    bring(pg, ME, (110, 560))                          # (the strikes are north-east of the boat)
    rec = Rec(pg, Y(0, 620)); rec.hold(2200)
    if pg.is_visible('#ltAlarm'): tap_el(pg, rec, '#ltAlarmOk', after=700)       # the alarm (strike < 10 km): OK
    x, y = scr(pg, ME)
    for i in range(4):                                 # zoom out a bit: the strikes on the map
        pg.mouse.move(x + 60, y - 60); pg.mouse.wheel(0, 380); rec.hold(260)
    rec.hold(1500)
    strikes.append((0.8, 0.7, 0))                      # a new one, close: it flashes
    pg.evaluate('__ffLightningFetch()'); rec.hold(2600)                         # flashes + warns again
    if pg.is_visible('#ltAlarm'): tap_el(pg, rec, '#ltAlarmOk', after=1400)
    rec.save('blixtar'); b.close()

def s_filter(p):
    c, q = mix(P['B2'], P['E1'], 0.35), mix(P['B3'], P['B1'], 0.55)
    b, ctx, pg = open_app(p, boats=[{'uid': 'kalle', 'name': 'Calle', 'lat': c[0], 'lon': c[1], 'ageMin': 0},
                                    {'uid': 'pia', 'name': 'Pia', 'lat': q[0], 'lon': q[1], 'ageMin': 0}])
    check_water(pg, c); check_water(pg, q)
    bring(pg, mix(P['B1'], P['B2'], 0.5), (195, 470))
    rec = Rec(pg, Y(0, 700)); rec.hold(500)
    tap_el(pg, rec, '#visMoreBtn', after=700)
    tap_el(pg, rec, 'label:has(#toggleOthers) .toggle', after=1100)
    tap_el(pg, rec, 'label:has(#toggleBoats) .toggle', after=1100)
    tap_el(pg, rec, 'label:has(#toggleOthers) .toggle', after=700)
    tap_el(pg, rec, 'label:has(#toggleBoats) .toggle', after=900)
    tap_el(pg, rec, '#visMoreBtn', after=1200)
    rec.save('filter'); b.close()

def s_logg(p):
    b, ctx, pg = open_app(p)
    rec = Rec(pg); rec.hold(500)
    tap_el(pg, rec, '#menuBtn', after=700)
    tap_el(pg, rec, '#menuItemLog', after=1400)
    tap_el(pg, rec, '.logItem:has-text("Gösgropen")', after=2600)
    rec.save('logg'); b.close()

def s_installningar(p):
    b, ctx, pg = open_app(p)
    rec = Rec(pg); rec.hold(400)
    tap_el(pg, rec, '#menuBtn', after=600)
    tap_el(pg, rec, '#menuItemSettings', after=1000)
    tap_el(pg, rec, '#wpSizeSeg button[data-size="1"]', after=900)
    tap_el(pg, rec, '#wpSizeSeg button[data-size="0.7"]', after=700)
    goal = pg.evaluate("(() => { var b = document.getElementById('settingsBody'), r = document.getElementById('othersOpacitySeg'); return r.getBoundingClientRect().top - b.getBoundingClientRect().top + b.scrollTop - 330; })()")
    for i in range(1, 19):                                          # past the offline download to Andras / Djup
        pg.evaluate("t => document.getElementById('settingsBody').scrollTop = t", goal * i / 18); rec.snap()
    rec.hold(900)
    tap_el(pg, rec, '#othersOpacitySeg button[data-op="0.5"]', after=900)
    tap_el(pg, rec, '#othersOpacitySeg button[data-op="1"]', after=1600)
    rec.save('installningar'); b.close()

def s_analys(p):
    """Kartanalys: depth range (drag), tops & holes (tap a label -> lead line), a preset"""
    b, ctx, pg = open_app(p)
    bring(pg, P['B1'], (195, 300))
    rec = Rec(pg); rec.hold(500)
    tap_el(pg, rec, '#anBtn', after=700)
    tap_el(pg, rec, '#anPanel button[data-m="depth"]', after=900)
    r = pg.eval_on_selector('#anControls .anDual', 'e => { var r = e.getBoundingClientRect(); return [r.left, r.width]; }')
    dmax = float(pg.inner_text('#anControls .anTicks span:last-child').replace(' m', '').replace(',', '.'))
    k = pg.eval_on_selector_all('#anControls .anKnob', 'e => e.map(x => { var r = x.getBoundingClientRect(); return [r.left + r.width / 2, r.top + r.height / 2]; })')[1]
    pg.mouse.move(k[0], k[1]); pg.mouse.down(); rec.hold(150)                     # drag the right handle to 9 m
    for i in range(1, 9):
        pg.mouse.move(k[0] + (r[0] + r[1] * 9 / dmax - k[0]) * i / 8, k[1]); rec.hold(110)
    pg.mouse.up(); rec.hold(900)
    tap_el(pg, rec, '#anPanel button[data-m="tops"]', after=1400)
    lbl = pg.evaluate("""() => { var best = null; document.querySelectorAll('.anLbl').forEach(function(l){ var r = l.getBoundingClientRect();
        if (r.top > 110 && r.bottom < 480 && r.left > 10 && r.right < 380 && !best) best = [r.left + r.width / 2, r.top + r.height / 2]; }); return best; }""")
    if lbl: tap(pg, rec, lbl[0], lbl[1], after=1500)
    tap_el(pg, rec, '#anBtn', after=600)
    tap_el(pg, rec, '#anPanel button[data-m="gos"]', after=1800)
    tap_el(pg, rec, '#anClose', after=1500)
    rec.save('analys'); b.close()

def s_akhit(p):
    """tap a spot -> Åk hit -> the card; the boat moves, the distance/time follow"""
    b, ctx, pg = open_app(p)
    bring(pg, mix(ME, P['B4'], 0.5), (195, 470))
    rec = Rec(pg, Y(0, 720)); rec.hold(600)
    x, y = scr(pg, P['B4']); tap(pg, rec, x, y - 8, after=900)
    tap_el(pg, rec, '#wpGo', after=1500)
    sail(pg, ctx, rec, ME, P['B1'], metres_max=45, speed=5.0); rec.hold(1800)
    rec.save('akhit'); b.close()

def s_meddelanden(p):
    """the message button -> Fisk!!! -> a bubble at your boat; Calle and Pia (same boat) answer = one
    bubble with a row each; tap Calle's row -> the panel -> Åk hit"""
    c = mix(P['B1'], P['B4'], 0.5)
    b, ctx, pg = open_app(p, boats=[{'uid': 'kalle', 'name': 'Calle', 'lat': c[0], 'lon': c[1], 'ageMin': 0},
                                    {'uid': 'pia', 'name': 'Pia', 'lat': c[0] + 0.00005, 'lon': c[1], 'ageMin': 0, 'msg': 'Kommer 🚤', 'msgAgeMin': 8}])
    check_water(pg, c)
    bring(pg, mix(ME, c, 0.5), (195, 470))
    rec = Rec(pg); rec.hold(600)
    tap_el(pg, rec, '#msgBtn', after=900)
    tap_el(pg, rec, '#msgPop button:has-text("Fisk")', after=1600)
    pg.evaluate("c => __addPos({ uid: 'kalle', name: 'Calle', lat: c[0], lon: c[1], msg: 'Mat? 🍔', msgAgeMin: 6 })", list(c)); rec.hold(2000)
    tap_el(pg, rec, '.mLine:has-text("Calle")', after=2000)          # Calle's row: when, how long left, Åk hit
    tap_el(pg, rec, '#msgCardGo', after=2000)
    rec.save('meddelanden'); b.close()

def s_installera(p):
    b = p.chromium.launch(**fakefb.LAUNCH)
    ctx = b.new_context(viewport={'width': 390, 'height': 844}, device_scale_factor=2)
    pg = ctx.new_page()
    pg.goto('http://localhost:%d/tools/help_install_anim.html' % PORT); pg.wait_for_timeout(800)
    rec = Rec(pg); pg.evaluate('play()')
    while not pg.evaluate('!!window.done'): rec.snap()
    rec.save('installera', last=2400); b.close()

SCENES = [('installera', s_installera), ('kartan', s_kartan), ('kartlagen', s_kartlagen), ('position', s_position),
          ('lodet', s_lodet), ('platser', s_platser), ('andra', s_andra), ('fara', s_fara), ('batar', s_batar), ('mat', s_mat),
          ('vader', s_vader), ('blixtar', s_blixtar), ('filter', s_filter), ('logg', s_logg), ('installningar', s_installningar),
          ('analys', s_analys), ('akhit', s_akhit), ('meddelanden', s_meddelanden)]

if __name__ == '__main__':
    want = sys.argv[1:] or [n for n, f in SCENES]
    srv = subprocess.Popen([sys.executable, '-m', 'http.server', str(PORT), '--directory', ROOT], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(1.2)
    try:
        with sync_playwright() as p:
            for n, f in SCENES:
                if n in want:
                    print(n); f(p)
    finally:
        srv.terminate()
