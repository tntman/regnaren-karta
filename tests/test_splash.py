# The start film (js/35-splash.js, tools/PLAN_SPLASH.md): 3.5 s with the 3D logo every time a name is chosen
# (a new phone, after Logga ut) and from Inställningar -> "Spela" -- black over the app, then the film. Hjälp and
# the location question after it, a tap skips, older phones / no WebGL: the flat logo, three.js failing: only a fade.
# The start picture (head.html, html.boot): the logo on the dark blue from the very first picture, the app fades in.
# (fakefb keeps both away from all the other tests -- here: splash=True.)
from playwright.sync_api import sync_playwright
import fakefb, time
results = []
def check(name, cond, info=''):
    results.append(bool(cond)); print(('PASS ' if cond else 'FAIL ') + name + ('  -- ' + str(info) if info != '' else ''))

# when #app is parsed: the html's background then (the start picture)
FIRST_JS = """new MutationObserver(function(m, o){ if (document.getElementById('app')){ o.disconnect();
  var cs = getComputedStyle(document.documentElement); window.__spBg = cs.backgroundColor; window.__spBgImg = cs.backgroundImage; } })
  .observe(document, { childList: true, subtree: true });"""
NAME = "localStorage.setItem('regnaren_user_name_v1', 'Filip'); "

def fresh(p, extra='', block_three=False, load_ms=10000, help_seen=True):
    b = p.chromium.launch(**fakefb.LAUNCH)
    ctx = b.new_context(viewport={'width': 390, 'height': 844}, has_touch=True, is_mobile=True, splash=True, help_seen=help_seen)
    ctx.add_init_script('window.__fakeCfg = {}; window.__ffSplashLoadMs = %d;' % load_ms)   # (a busy test browser: wait for three.js)
    ctx.add_init_script(FIRST_JS)
    ctx.add_init_script("""window.__geoAt = []; navigator.geolocation.watchPosition = function(){
      window.__geoAt.push(document.documentElement.classList.contains('splash')); return 1; };""")
    if extra: ctx.add_init_script('try { ' + extra + ' } catch(e){}')
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
def help_shown(pg): return pg.evaluate("document.getElementById('helpView').classList.contains('show')")
def theme(pg): return pg.evaluate("document.querySelector('meta[name=theme-color]').content")
def done(pg, ms=8000):
    try: pg.wait_for_function('!window.__ffSplash().running', timeout=ms); return True
    except Exception: return False

with sync_playwright() as p:
    # 1. a new phone: the start picture, "Vem är du?", then black and the film, then Hjälp and the location question
    b, pg, errs, reqs = fresh(p, help_seen=False)
    check('start: the start picture (the logo on the dark blue, as the iOS launch image) from the very first picture, never white',
          pg.evaluate('window.__spBg') == 'rgb(20, 24, 34)' and (pg.evaluate('window.__spBgImg') or '').startswith('url("data:image/svg'), pg.evaluate('window.__spBgImg'))
    check('...and the browser own empty canvas dark before that (color-scheme), the page itself as before (body: light)',
          pg.evaluate("document.querySelector('meta[name=color-scheme]').content === 'dark' && getComputedStyle(document.body).colorScheme === 'light'"))
    pg.wait_for_timeout(1500)
    check('...then the app fades in over it, the logo gone', pg.evaluate("""!document.documentElement.classList.contains('boot')
          && !document.documentElement.classList.contains('booted') && getComputedStyle(document.body).opacity === '1'"""))
    check('...no film at start, "Vem är du?"', not sp(pg)['shown'] and not html_splash(pg) and names_shown(pg), sp(pg))
    fakefb.login(pg, 'Filip'); pg.wait_for_timeout(100)
    check('a name chosen: the dark (#141822 = the status bar, no edge) fades in over the app, the film',
          html_splash(pg) and sp(pg)['running'] and pg.evaluate("document.getElementById('splash').classList.contains('spIn')")
          and theme(pg) == '#141822' and pg.evaluate("getComputedStyle(document.querySelector('#splash .spBlack')).backgroundColor") == 'rgb(20, 24, 34)', sp(pg))
    pg.wait_for_function("window.__ffSplash().mode === 'film'", timeout=10000)
    check('...the film runs (3D sign); the welcome card and the location question wait', sp(pg)['gl'] and not names_shown(pg) and not pg.is_visible('#welcomeNote')
          and pg.evaluate('window.__geoAt.length') == 0, (sp(pg), pg.evaluate('window.__geoAt')))
    t0 = time.time(); ok = done(pg)
    check('...over after ~3.5 s, nothing left (renderer and canvas gone, html.splash off)',
          ok and time.time() - t0 < 4.5 and not sp(pg)['gl'] and not html_splash(pg) and not pg.is_visible('#splash')
          and pg.evaluate("!document.querySelector('#splash canvas:not(.spBloom)') && document.getElementById('app').style.filter === ''"), (sp(pg), round(time.time() - t0, 2)))
    pg.wait_for_timeout(300)
    check('...then the welcome card (not Hjälp itself) and the location question', pg.is_visible('#welcomeNote') and not help_shown(pg) and pg.evaluate('window.__geoAt') == [False], pg.evaluate('window.__geoAt'))
    pg.click('#welcomeNoteClose')
    # 2. a reload (rotation, another lake, Demo Mode) or a later start: no film
    pg.reload(); pg.wait_for_timeout(1500)
    check('a reload / later start (a name known): no film', not sp(pg)['shown'] and not html_splash(pg) and not names_shown(pg), sp(pg))
    # 3. Logga ut and a name again (the app still open): the film again; a tap skips to the end
    pg.evaluate("document.getElementById('logoutBtn').click()"); pg.wait_for_timeout(300)
    check('Logga ut: "Vem är du?", no film yet', names_shown(pg) and not html_splash(pg))
    fakefb.login(pg, 'Filip')
    pg.wait_for_function("window.__ffSplash().mode === 'film'", timeout=10000)
    check('...a name again: the film again', sp(pg)['running'] and html_splash(pg), sp(pg))
    check('...the welcome card waits for it', not pg.is_visible('#welcomeNote'))
    pg.wait_for_timeout(400)
    pg.mouse.click(195, 420)
    m = sp(pg)['mode']; t0 = time.time(); ok = done(pg, 2000)
    check('a tap: straight to the end (fades in ~0.4 s)', m == 'skip' and ok and time.time() - t0 < 1.2 and not html_splash(pg), (m, round(time.time() - t0, 2)))
    pg.wait_for_timeout(300)
    check('...the tap did nothing else (no view or sheet opened); the welcome card again', not names_shown(pg) and pg.evaluate("!document.querySelector('.sheet.show, #settingsView.show, #helpView.show')") and pg.is_visible('#welcomeNote'))
    pg.click('#welcomeNoteClose')
    # 4. Inställningar -> Avancerat -> Startfilmen "Spela": again, over the map
    pg.click('#menuBtn'); pg.click('#menuItemSettings'); pg.wait_for_timeout(400)
    pg.click('#splashReplayBtn'); pg.wait_for_timeout(100)
    check('Inställningar -> Avancerat -> Startfilmen "Spela": the film again, Inställningar closed (its 3D logo stops)',
          sp(pg)['running'] and html_splash(pg) and not pg.evaluate("document.getElementById('settingsView').classList.contains('show')"), sp(pg))
    check('...over again, back on the map', done(pg, 12000) and not html_splash(pg) and not sp(pg)['gl'], sp(pg))
    check('no errors', not errs, errs)
    b.close()

    # 5. a rotation's reload: no start picture (the app as it was, at once)
    b, pg, errs, reqs = fresh(p, extra=NAME + "sessionStorage.setItem('ffmap_rotation_state_v1', '{}');")
    check("a rotation's reload: no start picture", pg.evaluate('window.__spBgImg') == 'none', pg.evaluate('window.__spBgImg'))
    b.close()

    # 6. no WebGL (the logo has stepped down to 'flat'): the flat logo, no three.js at all
    b, pg, errs, reqs = fresh(p, extra="localStorage.setItem('ffmap_logo3d_v1', 'flat');")
    pg.wait_for_timeout(1200); fakefb.login(pg, 'Filip'); pg.wait_for_timeout(700)
    s = sp(pg)
    check('no WebGL: the flat logo fades in (no spin)', s['mode'] == 'flat' and pg.is_visible('#splash .spFlat'), s)
    ok = done(pg, 4000)
    check('...over after ~2 s, no three.js loaded', ok and not any('three-r170' in u for u in reqs) and not html_splash(pg), [u for u in reqs if 'three' in u])
    b.close()

    # 7. three.js can't be loaded: the black just fades away, the app works
    b, pg, errs, reqs = fresh(p, block_three=True, load_ms=1500)
    pg.wait_for_timeout(1200); fakefb.login(pg, 'Filip')
    t0 = time.time(); ok = done(pg, 4000)
    check('three.js blocked: only the black fades (within ~2 s), the app can be used', ok and time.time() - t0 < 2.5 and not html_splash(pg),
          (round(time.time() - t0, 2), sp(pg)))
    b.close()
print('%d/%d passed' % (sum(results), len(results)))
