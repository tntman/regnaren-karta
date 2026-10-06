# The start film (js/35-splash.js, tools/PLAN_SPLASH.md): 3.5 s with the 3D logo on a first start and when the
# app hasn't been in use for > 24 h (ffmap_last_active_v1). All black from the very first picture (head.html),
# the name picker after it, a tap skips, older phones / no WebGL: the flat logo, three.js failing: only a fade.
# (fakefb keeps it away from all the other tests -- here: splash=True.)
from playwright.sync_api import sync_playwright
import fakefb, time
results = []
def check(name, cond, info=''):
    results.append(bool(cond)); print(('PASS ' if cond else 'FAIL ') + name + ('  -- ' + str(info) if info != '' else ''))

# when #app is parsed: is it already black (html.splash, and #splash before it)?
FIRST_JS = """new MutationObserver(function(m, o){ var f = document.querySelector('script[src*=gstatic]');
  if (f && !window.__spBg) window.__spBg = getComputedStyle(document.documentElement).backgroundColor;
  if (document.getElementById('app')){ o.disconnect();
  window.__spFirst = { cls: document.documentElement.classList.contains('splash'), el: !!document.getElementById('splash') }; } })
  .observe(document, { childList: true, subtree: true });"""

def fresh(p, extra=None, block_three=False, load_ms=10000):
    b = p.chromium.launch(**fakefb.LAUNCH)
    ctx = b.new_context(viewport={'width': 390, 'height': 844}, has_touch=True, is_mobile=True, splash=True)
    ctx.add_init_script('window.__fakeCfg = {}; window.__ffSplashLoadMs = %d;' % load_ms)   # (a busy test browser: wait for three.js)
    ctx.add_init_script(FIRST_JS)
    if extra: ctx.add_init_script(extra)
    ctx.add_init_script(fakefb.FAKE_FIREBASE_JS)
    if block_three: ctx.route('**/three-r170*', lambda r: r.abort())
    pg = ctx.new_page(); errs = []; reqs = []
    pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.on('request', lambda r: reqs.append(r.url))
    pg.goto('http://localhost:8899/index.html')
    return b, pg, errs, reqs
def sp(pg): return pg.evaluate('window.__ffSplash()')
def html_splash(pg): return pg.evaluate("document.documentElement.classList.contains('splash')")
def names_shown(pg): return pg.evaluate("document.getElementById('nameModal').classList.contains('show')")
def theme(pg): return pg.evaluate("document.querySelector('meta[name=theme-color]').content")
def done(pg, ms=8000):
    try: pg.wait_for_function('!window.__ffSplash().running', timeout=ms); return True
    except Exception: return False
def ago(pg, h): pg.evaluate("(h) => localStorage.setItem('ffmap_last_active_v1', String(Date.now() - h * 3600000))", h)
def reload_ago(pg, h):   # (a reload hides the old page first, and hidden = "in use until now": keep the old page from writing it)
    ago(pg, h)
    pg.evaluate("""() => { var s = Storage.prototype.setItem;
      Storage.prototype.setItem = function(k, v){ if (k !== 'ffmap_last_active_v1') return s.call(this, k, v); }; }""")
    pg.reload()

with sync_playwright() as p:
    # 1. the first start
    b, pg, errs, reqs = fresh(p)
    first = pg.evaluate('window.__spFirst')
    check('first start: black from before the Firebase scripts too', pg.evaluate('window.__spBg') == 'rgb(0, 0, 0)', pg.evaluate('window.__spBg'))
    check('first start: black from the very first picture (html.splash and #splash before the map is parsed), status bar black (no top fade)',
          first == {'cls': True, 'el': True} and theme(pg) == '#000' and not pg.is_visible('#splash .spTop'), (first, theme(pg)))
    pg.wait_for_function("window.__ffSplash().mode === 'film'", timeout=10000)
    check('...the film runs (3D sign), the name picker waits', sp(pg)['gl'] and pg.is_visible('#splash') and not names_shown(pg), sp(pg))
    t0 = time.time(); ok = done(pg)
    check('...over after ~3.5 s, nothing left (renderer and canvas gone, html.splash off, status bar back)',
          ok and time.time() - t0 < 4.5 and not sp(pg)['gl'] and not html_splash(pg) and not pg.is_visible('#splash') and theme(pg) == '#141822'
          and pg.evaluate("!document.querySelector('#splash canvas:not(.spBloom)') && document.getElementById('app').style.filter === ''"), (sp(pg), round(time.time() - t0, 2)))
    pg.wait_for_timeout(300)
    check('...then "Vem är du?" (a new phone)', names_shown(pg))
    # 2. a reload within 24 h (rotation, another lake, Demo Mode): no film
    pg.evaluate('window.__spBg = null'); pg.reload(); pg.wait_for_timeout(800)
    check('a start without the film: the dark blue at once (before the Firebase scripts hold up the page own css), never white',
          pg.evaluate('window.__spBg') == 'rgb(20, 24, 34)', pg.evaluate('window.__spBg'))
    check('reload within 24 h: no film', not sp(pg)['shown'] and not html_splash(pg) and names_shown(pg), sp(pg))
    # 3. + 5. last in use 25 h ago: the film; a tap skips to the end
    reload_ago(pg, 25)
    pg.wait_for_function("window.__ffSplash().mode === 'film'", timeout=10000)
    check('last in use 25 h ago: the film again', sp(pg)['running'] and html_splash(pg), sp(pg))
    pg.wait_for_timeout(400)
    pg.mouse.click(195, 420)
    m = sp(pg)['mode']; t0 = time.time(); ok = done(pg, 2000)
    check('a tap: straight to the end (fades in ~0.4 s)', m == 'skip' and ok and time.time() - t0 < 1.2 and not html_splash(pg), (m, round(time.time() - t0, 2)))
    pg.wait_for_timeout(300)
    check('...the tap did nothing else (the name picker is there, nothing chosen)', names_shown(pg) and not pg.query_selector('.nameChip.selected'))
    # 5b. back from the background after > 24 h, without a reload
    pg.evaluate("""() => { window.__vis = 'hidden'; Object.defineProperty(document, 'visibilityState', { get: () => window.__vis, configurable: true });
      document.dispatchEvent(new Event('visibilitychange')); }""")
    check('hidden: in use until now (the key is written)', pg.evaluate("Date.now() - +localStorage.getItem('ffmap_last_active_v1') < 2000"))
    ago(pg, 25)
    pg.evaluate("() => { window.__vis = 'visible'; document.dispatchEvent(new Event('visibilitychange')); }")
    s = sp(pg)
    check('back after 25 h without a reload: the film (black at once)', s['running'] and html_splash(pg) and pg.is_visible('#splash'), s)
    check('...and over again, nothing left', done(pg, 12000) and not sp(pg)['gl'] and not html_splash(pg), sp(pg))
    # Inställningar -> Avancerat -> Startfilmen "Spela": again, over the map
    fakefb.login(pg, 'Filip'); pg.wait_for_timeout(600)
    pg.click('#menuBtn'); pg.click('#menuItemSettings'); pg.wait_for_timeout(400)
    pg.click('#splashReplayBtn'); pg.wait_for_timeout(100)
    check('Inställningar -> Avancerat -> Startfilmen "Spela": the film again, Inställningar closed (its 3D logo stops)',
          sp(pg)['running'] and html_splash(pg) and not pg.evaluate("document.getElementById('settingsView').classList.contains('show')"), sp(pg))
    check('...without a reload the status bar stays #141822 (iOS keeps it): the top fades from it instead', theme(pg) == '#141822' and pg.is_visible('#splash .spTop'), theme(pg))
    check('...over again, back on the map', done(pg, 12000) and not html_splash(pg) and not sp(pg)['gl'], sp(pg))
    # Logga ut, then the app closed and opened again: the film (a reload in the same session, e.g. a rotation: not)
    pg.wait_for_timeout(300)
    pg.click('#menuBtn'); pg.click('#menuItemLogout'); pg.wait_for_timeout(300)
    pg.reload(); pg.wait_for_timeout(800)
    check('Logga ut, then a reload in the same session (rotation): no film', not sp(pg)['shown'] and not html_splash(pg), sp(pg))
    st = pg.context.storage_state()
    check('no errors', not errs, errs)
    b.close()
    b = p.chromium.launch(**fakefb.LAUNCH)
    ctx = b.new_context(viewport={'width': 390, 'height': 844}, storage_state=st, splash=True)
    ctx.add_init_script('window.__fakeCfg = {};'); ctx.add_init_script(fakefb.FAKE_FIREBASE_JS)
    pg = ctx.new_page(); pg.goto('http://localhost:8899/index.html'); pg.wait_for_timeout(300)
    check('...closed and opened again: the film (once)', html_splash(pg) and sp(pg)['shown'], sp(pg))
    done(pg, 12000); pg.reload(); pg.wait_for_timeout(800)
    check('...and not on the next start', not sp(pg)['shown'] and not html_splash(pg), sp(pg))
    b.close()

    # a known name, last in use 25 h ago: the location question (watchPosition) only after the film
    b, pg, errs, reqs = fresh(p, extra="""try { localStorage.setItem('regnaren_user_name_v1', 'Filip');
      localStorage.setItem('ffmap_last_active_v1', String(Date.now() - 25 * 3600000)); } catch(e){}
      window.__geoAt = []; navigator.geolocation.watchPosition = function(){ window.__geoAt.push(document.documentElement.classList.contains('splash')); return 1; };""")
    pg.wait_for_function("window.__ffSplash().mode === 'film'", timeout=10000)
    g1 = pg.evaluate('window.__geoAt.length'); done(pg, 12000); pg.wait_for_timeout(200)
    check('the location question waits for the film (not over it), then comes', g1 == 0 and pg.evaluate('window.__geoAt') == [False], (g1, pg.evaluate('window.__geoAt')))
    b.close()

    # 6. no WebGL (the logo has stepped down to 'flat'): the flat logo, no three.js at all
    b, pg, errs, reqs = fresh(p, extra="try { localStorage.setItem('ffmap_logo3d_v1', 'flat'); } catch(e){}")
    pg.wait_for_timeout(700)
    s = sp(pg)
    check('no WebGL: the flat logo fades in (no spin)', s['mode'] == 'flat' and pg.is_visible('#splash .spFlat'), s)
    ok = done(pg, 4000)
    check('...over after ~2 s, no three.js loaded, then the name picker', ok and not any('three-r170' in u for u in reqs) and not html_splash(pg) and names_shown(pg),
          [u for u in reqs if 'three' in u])
    b.close()

    # 7. three.js can't be loaded: the black just fades away, the app works
    b, pg, errs, reqs = fresh(p, block_three=True, load_ms=1500)
    t0 = time.time(); ok = done(pg, 4000)
    pg.wait_for_timeout(300)
    check('three.js blocked: only the black fades (within ~2 s), the app can be used', ok and time.time() - t0 < 2.5 and not html_splash(pg) and names_shown(pg),
          (round(time.time() - t0, 2), sp(pg)))
    b.close()
print('%d/%d passed' % (sum(results), len(results)))
