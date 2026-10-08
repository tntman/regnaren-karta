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

def open_app(p, geo=ME, spots=SPOTS, boats=BOATS, wind=(3.2, 225), fmi=None, name='Filip', catches=None, api=None, init=None):
    b = p.chromium.launch(**fakefb.LAUNCH)
    ctx = b.new_context(viewport={'width': 390, 'height': 844}, device_scale_factor=2, has_touch=True, is_mobile=True,
                        geolocation={'latitude': geo[0], 'longitude': geo[1], 'accuracy': 6}, permissions=['geolocation'])
    cfg = {'waypoints': spots, 'positions': boats}
    ctx.add_init_script('window.__fakeCfg = ' + json.dumps(cfg) + ';')
    # the competitions' catches: Fiskfiskarnas API, made up (fakefb)
    ctx.api = fakefb.FakeApi(api or ({'heatmap': [fakefb.api_row(*r) for r in catches]} if catches else {}))   # (api: a competition going on -- Hotzone)
    if init: ctx.add_init_script(init)
    ctx.route('**/fiskfiskarna.se/**', ctx.api.handle)
    # Inställningar as a new user sees it: every section closed (the tests open them all -- fakefb)
    ctx.add_init_script("try { localStorage.setItem('ffmap_settings_open_v1', '[]'); } catch(e){}")
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

# made-up competition catches for Heatmap / Kartanalys "Fångster" -- rows [t, comp, who, sp, cm, lat, lon],
# along stretches of water the scenes already use, a little spread; each checked on the water (water_catches)
def catch_rows():
    import random
    rnd = random.Random(7); rows = []
    t0 = int(time.mktime((2026, 9, 26, 9, 0, 0, 0, 0, -1))) * 1000
    who = ['Calle', 'Pia', 'Olle', 'Filip']
    for sp, n, segs, cm in (('abborre', 22, [(P['B4'], P['B5']), (P['B1'], P['B4'])], (22, 41)),
                            ('gadda', 14, [(P['B1'], P['B2']), (ME, P['B1'])], (55, 92)),
                            ('gos', 11, [(P['E1'], P['B4'])], (40, 68))):
        for i in range(n):
            a, b = segs[i % len(segs)]; ll = mix(a, b, rnd.uniform(0.1, 0.9))
            ll = (ll[0] + rnd.uniform(-0.00012, 0.00012), ll[1] + rnd.uniform(-0.0002, 0.0002))
            rows.append([t0 + rnd.randint(0, 30) * 3600000 + i * 60000, 'regnaren1' if i % 3 else 'regnaren2', who[i % 4], sp, rnd.randint(*cm), round(ll[0], 6), round(ll[1], 6)])
    return rows
def water_catches(p):
    """only the made-up catches that are on the water (>= 1.5 m deep)"""
    b, ctx, pg = open_app(p)
    ok = [r for r in catch_rows() if (pg.evaluate('([a, b]) => __ffGeo.depthAt(a, b)', [r[5], r[6]]) or 0) >= 1.5]
    b.close(); return ok

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
    """tap the map = the lead line (depth, by water, time); the boat moves; tap its box = a marker right there"""
    b, ctx, pg = open_app(p)
    bring(pg, mix(ME, P['E1'], 0.5), (195, 430))
    rec = Rec(pg, Y(120, 844)); rec.hold(700)
    check_water(pg, P['E1'])
    x, y = scr(pg, P['E1']); tap(pg, rec, x, y, after=2600)
    sail(pg, ctx, rec, ME, P['B1'], metres_max=60); rec.hold(1200)
    tap_el(pg, rec, '#probe .pbTag', after=1500)                   # its box: a marker there (the sheet)
    tap_el(pg, rec, '#wpSave', after=1800)
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
    tap_el(pg, rec, '#wpDelete', after=1600)                        # the bin: gone -- "Ångra" for 6 s
    tap_el(pg, rec, '#undoBtn', after=1800)                         # ... and back
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
    tap_el(pg, rec, '#visTypes label:has(input[data-type="abborre"])', after=1300)   # a type: its dot -> grey ring
    tap_el(pg, rec, '#visTypes label:has(input[data-type="abborre"])', after=900)
    tap_el(pg, rec, '#visMoreBtn', after=1200)
    rec.save('filter'); b.close()

def s_logg(p):
    """the track: Filter -> Spår's icon = the track menu (colour, how far back); then Logg -> a spot -> there on the map"""
    b, ctx, pg = open_app(p)
    zoom_at(pg, ME, 2, (150, 470))
    a = ME
    for k in range(1, 13):                                         # (not recorded: a bit of today's track behind the boat)
        ll = mix(ME, P['B1'], k / 12.0); check_water(pg, ll)
        ctx.set_geolocation({'latitude': ll[0], 'longitude': ll[1], 'accuracy': 5}); pg.wait_for_timeout(450)
    rec = Rec(pg); rec.hold(600)
    tap_el(pg, rec, '#visMoreBtn', after=700)
    tap_el(pg, rec, '.visSwatch--track', after=1400)                # Spår's icon: the track menu
    tap_el(pg, rec, '#trkColors button[data-c="#FFD23F"]', after=1000)
    tap_el(pg, rec, '#trkDash button[data-d="0"]', after=1000)
    tap_el(pg, rec, '#trkRange button[data-r="7"]', after=1000)
    tap_el(pg, rec, '#trkClose', after=900)
    tap_el(pg, rec, '#menuBtn', after=700)
    tap_el(pg, rec, '#menuItemLog', after=1400)
    tap_el(pg, rec, '#logWhoSeg button[data-who="mine"]', after=1300)   # the filter: Mina, then Andras
    tap_el(pg, rec, '#logWhoSeg button[data-who="others"]', after=1300)
    tap_el(pg, rec, '#logWhoSeg button[data-who="all"]', after=700)
    tap_el(pg, rec, '#logTypes label:has(input[data-type="abborre"])', after=1300)   # a type's dot off and on
    tap_el(pg, rec, '#logTypes label:has(input[data-type="abborre"])', after=800)
    tap_el(pg, rec, '#logSearch', after=300)
    typ(pg, rec, '#logSearch', 'gös'); rec.hold(1200)                    # search
    pg.evaluate("document.activeElement.blur()"); rec.hold(400)
    tap_el(pg, rec, '.logItem:has-text("Gösgropen")', after=2400)
    pg.evaluate("document.getElementById('logSearch').value = ''")
    rec.save('logg'); b.close()

def s_installningar(p):
    b, ctx, pg = open_app(p, name='Calle')         # (as the group sees it: "Filip" also has the Admin row)
    rec = Rec(pg); rec.hold(400)
    tap_el(pg, rec, '#menuBtn', after=600)
    tap_el(pg, rec, '#menuItemSettings', after=1600)               # the sections, closed: a line each of what's chosen
    tap_el(pg, rec, '.setSec[data-sec="map"] summary', after=900)  # Kartan
    tap_el(pg, rec, '#wpSizeSeg button[data-size="1"]', after=900)
    tap_el(pg, rec, '#wpSizeSeg button[data-size="0.7"]', after=700)
    tap_el(pg, rec, '.setSec[data-sec="map"] summary', after=900)  # closed again
    tap_el(pg, rec, '.setSec[data-sec="boat"] summary', after=1400)
    tap_el(pg, rec, 'label:has(#toggleWake) .toggle', after=900)   # Håll skärmen tänd
    tap_el(pg, rec, '.setSec[data-sec="boat"] summary', after=700)
    tap_el(pg, rec, '.setSec[data-sec="warn"] summary', after=2000)
    rec.save('installningar'); b.close()

def s_analys(p):
    """Kartanalys: Djup (drag a handle, the lamp), + Branta kanter (together), another tab takes over (Tumregler:
    Gös, Fångster), back to Kartdata (its choice again), the pill"""
    b, ctx, pg = open_app(p, catches=water_catches(p))
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
    tap_el(pg, rec, '#anLamp', after=1600)                             # 💡 the lit part twice as bright
    tap_el(pg, rec, '#anLamp', after=700)
    tap_el(pg, rec, '#anPanel button[data-m="steep"]', after=1600)     # + Branta kanter: where both are true
    tap_el(pg, rec, '#anCatSeg button[data-cat="rule"]', after=800)    # another tab takes over: Kartdata off
    tap_el(pg, rec, '#anPanel button[data-m="gos"]', after=1800)
    tap_el(pg, rec, '#anCatSeg button[data-cat="data"]', after=600)    # Fångster: where abborre was caught
    tap_el(pg, rec, '#anDataChips button:not([disabled])', after=2000)
    tap_el(pg, rec, '#anScale', after=2200)                            # Skala: coloured by how strongly it matches
    tap_el(pg, rec, '#anCatSeg button[data-cat="now"]', after=2600)    # Fiska nu: five tips with %
    tap_el(pg, rec, '#anScale', after=900)                             # (Skala off again)
    tap_el(pg, rec, '#anCatSeg button[data-cat="map"]', after=1700)    # back: Djup + Branta kanter again
    tap_el(pg, rec, '#anClose', after=1500)                            # the "Kartanalys" pill under the weather
    rec.save('analys'); b.close()

def s_heatmap(p):
    """Heatmap: its button at the top; the four styles; När (tap the best hour, then again = all); tap a catch -> its card"""
    rows = water_catches(p)
    b, ctx, pg = open_app(p, catches=rows)
    bring(pg, P['B1'], (195, 330))
    rec = Rec(pg); rec.hold(500)
    tap_el(pg, rec, '#hmBtn', after=2200)                              # Värme
    for s in ('species', 'hex', 'dots'):
        tap_el(pg, rec, '#hmStyleSeg button[data-s="%s"]' % s, after=1700)
    tap_el(pg, rec, '#hmStyleSeg button[data-s="heat"]', after=900)
    pg.evaluate("document.querySelector('#hmTime').scrollIntoView({ block: 'end' })"); rec.hold(500)
    best = pg.evaluate("""() => { var b = null; document.querySelectorAll('#hmTime .hmBars i').forEach(function(i){
        if (!b || i.offsetHeight > b.offsetHeight) b = i; }); var r = b.getBoundingClientRect(); return [r.left + r.width / 2, r.bottom - 6]; }""")
    tap(pg, rec, best[0], best[1], after=1900)                          # När: only the catches in that hour
    tap(pg, rec, best[0], best[1], after=1000)                          # the same again: all
    tap_el(pg, rec, '#hmClose', after=700)
    big = max((r for r in rows if r[3] == 'gadda'), key=lambda r: r[4])
    xy = pg.evaluate('(id) => window.__ffHeatScreen(id)', '%d|%s|%s|%s' % (big[0], big[2], big[3], big[4]))
    if xy and 120 < xy[1] < 700 and 10 < xy[0] < 380: tap(pg, rec, xy[0], xy[1], after=2600)
    if pg.is_visible('#hmCard'): tap_el(pg, rec, '#hmCardClose', after=900)
    rec.save('heatmap'); b.close()

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

def s_hotzone(p):
    """Hotzone (Tävlingarna): a competition going on; one hot spot already breathing (its note long gone); 4 fish
    near B1 -> a new ring + the note at the top; tap it -> the map goes there"""
    def ms(minutes): return int((time.time() - minutes * 60) * 1000)
    def row(m, at, k, who, sp='abborre'):
        return dict(fakefb.api_row(ms(m), 'reg9', who, sp, 30 + k, round(at[0] + 0.00018 * (k % 3 - 1), 6), round(at[1] + 0.0003 * (k % 2), 6)), approved=True)
    old = [row(50 - 6 * k, P['E1'], k, ['Calle', 'Pia', 'Olle'][k % 3]) for k in range(5)]
    new = [row(30 - 7 * k, P['B1'], k, ['Olle', 'Calle', 'Pia', 'Calle'][k], 'gadda' if k == 1 else 'abborre') for k in range(4)]
    comps = [{'competition_id': 'reg9', 'competition_name': 'Regnaren 9', 'date': time.strftime('%Y-%m-%d'), 'status': 'active', 'water': 'Regnaren'}]
    zid = '|'.join([str(fakefb_ms(old[3]['timestamp'])), old[3]['name'], 'abborre', '33'])   # (the spot by E1 = its 4th fish: already told)
    init = "try { localStorage.setItem('ffmap_hotzone_note_v1', JSON.stringify({ at: Date.now() - 50 * 60e3, ids: { '%s': Date.now() } })); } catch(e){}" % zid
    b, ctx, pg = open_app(p, api={'heatmap': [], 'competitions': comps, 'live': {'reg9': old + new[:3]}}, init=init)
    for r in old + new: check_water(pg, (r['lat'], r['lng']))
    m = mix(P['E1'], P['B1'], 0.5); bring(pg, m, (195, 430)); zoom_at(pg, m, -1); bring(pg, m, (195, 400))   # (zoom, then one real drag -- a drag of 0 px is a tap: the lead)
    rec = Rec(pg); rec.hold(2600)                                      # the spot by E1: a red ring that breathes, 🔥 5
    ctx.api.live = {'reg9': old + new}; pg.evaluate("document.getElementById('ctFetch').click()"); rec.hold(3200)   # the 4th fish by B1: a new ring + the note
    tap_el(pg, rec, '#hzNoteGo', after=3000)                           # tap the note: the map goes there
    rec.save('hotzone'); b.close()

def fakefb_ms(iso):   # the API's timestamp -> ms (as the app's Date.parse)
    import datetime
    return int(datetime.datetime.strptime(iso, '%Y-%m-%dT%H:%M:%S.%fZ').replace(tzinfo=datetime.timezone.utc).timestamp() * 1000)

SCENES = [('installera', s_installera), ('kartan', s_kartan), ('kartlagen', s_kartlagen), ('position', s_position),
          ('lodet', s_lodet), ('platser', s_platser), ('andra', s_andra), ('fara', s_fara), ('batar', s_batar), ('mat', s_mat),
          ('vader', s_vader), ('blixtar', s_blixtar), ('filter', s_filter), ('logg', s_logg), ('installningar', s_installningar),
          ('analys', s_analys), ('heatmap', s_heatmap), ('akhit', s_akhit), ('meddelanden', s_meddelanden), ('hotzone', s_hotzone)]

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
