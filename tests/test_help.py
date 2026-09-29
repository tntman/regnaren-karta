# Hjälp: opens by itself (with a welcome) after the name is chosen the first time; menu ->
# Hjälp; contents jump to the section; "Nytt i appen" (5 + "Visa äldre") with a dot on the
# menu until read; install steps for the phone/browser (or "✓" in the home-screen app);
# the animations are there and load; stays open (and scrolled) after a rotation reload.
from playwright.sync_api import sync_playwright
import fakefb, os, re, json
from fakefb import new_page
results = []
def check(name, cond, info=''):
    results.append(bool(cond)); print(('PASS ' if cond else 'FAIL ') + name + ('  -- ' + str(info) if info != '' else ''))
ME = (58.88951, 15.77759)
HELP = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'docs', 'help')
UA = {'ios': 'Mozilla/5.0 (iPhone; CPU iPhone OS 18_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.5 Mobile/15E148 Safari/604.1',
      'ioschrome': 'Mozilla/5.0 (iPhone; CPU iPhone OS 18_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/129.0 Mobile/15E148 Safari/604.1',
      'android': 'Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0 Mobile Safari/537.36'}

def fresh(p, ua=None, standalone=False, seen=None):
    """a phone that has never chosen a name (Hjälp not read), optionally another browser"""
    b = p.chromium.launch(**fakefb.LAUNCH)
    kw = dict(viewport={'width': 390, 'height': 844}, has_touch=True, is_mobile=True, help_seen=False,
              geolocation={'latitude': ME[0], 'longitude': ME[1], 'accuracy': 8}, permissions=['geolocation'])
    if ua: kw['user_agent'] = ua
    ctx = b.new_context(**kw)
    ctx.add_init_script('window.__fakeCfg = {};')
    if standalone: ctx.add_init_script("Object.defineProperty(navigator, 'standalone', { value: true, configurable: true });")
    if seen is not None: ctx.add_init_script("if (!localStorage.getItem('ffmap_help_seen_v1')) localStorage.setItem('ffmap_help_seen_v1', '%d');" % seen)
    ctx.add_init_script(fakefb.FAKE_FIREBASE_JS)
    pg = ctx.new_page(); errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.goto('http://localhost:8899/index.html'); pg.wait_for_timeout(500)
    fakefb.login(pg, 'Filip'); pg.wait_for_timeout(900)
    return b, pg, errs

def os_tab(pg):
    return pg.eval_on_selector('#helpInstallSeg button.on', 'e => e.getAttribute("data-os")')

with sync_playwright() as p:
    # ---- first time on an iPhone in Safari
    b, pg, errs = fresh(p, UA['ios'])
    check('first time: Hjälp opens by itself after the name, with a welcome', pg.is_visible('#helpView') and pg.is_visible('#helpWelcome') and 'Välkommen, Filip!' in pg.inner_text('#helpWelcome'), pg.inner_text('#helpWelcome') if pg.is_visible('#helpWelcome') else '')
    toc = pg.eval_on_selector_all('#helpToc a', 'e => e.map(x => x.textContent.trim())')
    check('contents: 20 sections', len(toc) == 20 and 'Blixtar' in ''.join(toc) and 'Installera appen' in ''.join(toc), toc)
    check('iPhone Safari: the Safari steps are shown, not "✓ installed"', os_tab(pg) == 'ios' and pg.is_visible('.helpSteps[data-os="ios"]') and not pg.is_visible('#helpInstalled'), os_tab(pg))
    news = pg.eval_on_selector_all('#helpNewsList .helpNewsItem', 'e => e.filter(x => x.offsetParent).length')
    check('Nytt i appen: 5 shown, the rest behind "Visa äldre"', news == 5 and pg.is_visible('#helpNewsMore'), news)
    pg.click('#helpNewsMore'); pg.wait_for_timeout(200)
    n_all = pg.eval_on_selector_all('#helpNewsList .helpNewsItem', 'e => e.filter(x => x.offsetParent).length')
    tags = pg.eval_on_selector_all('#helpNewsList .helpTag', 'e => Array.from(new Set(e.map(x => x.textContent)))')
    check('...then all of them, tagged NYTT / BÄTTRE / FIXAT', n_all > 5 and set(tags) <= {'NYTT', 'BÄTTRE', 'FIXAT'} and 'NYTT' in tags, (n_all, tags))
    pg.screenshot(path='shot_help_top.png')
    # contents -> the section
    pg.click('#helpToc a[href="#help-blixtar"]'); pg.wait_for_timeout(400)
    top = pg.evaluate("document.getElementById('help-blixtar').getBoundingClientRect().top - document.getElementById('helpBody').getBoundingClientRect().top")
    check('tapping "Blixtar" in the contents scrolls to that section', -5 <= top <= 30, top)
    pg.wait_for_timeout(1500)
    ok = pg.evaluate("(() => { var i = document.querySelector('#help-blixtar .helpAnim img'); return i.complete && i.naturalWidth > 0; })()")
    check('its animation loads', ok)
    pg.screenshot(path='shot_help_blixtar.png')
    pg.click('#helpBackBtn'); pg.wait_for_timeout(300)
    check('back -> the map; no "new" dot (all read)', not pg.is_visible('#helpView') and not pg.is_visible('#menuBtn .newDot'))
    pg.reload(); pg.wait_for_timeout(1500)
    check('opening the app again: Hjälp does not pop up again', not pg.is_visible('#helpView'))
    pg.click('#menuBtn'); pg.wait_for_timeout(200)
    check('Hjälp is in the menu (last)', pg.is_visible('#menuItemHelp') and pg.evaluate("document.querySelector('#menuPanel').lastElementChild.id") == 'menuItemHelp')
    pg.click('#menuItemHelp'); pg.wait_for_timeout(400)
    check('menu -> Hjälp opens it (no welcome this time), at the top', pg.is_visible('#helpView') and not pg.is_visible('#helpWelcome') and pg.evaluate("document.getElementById('helpBody').scrollTop") == 0)
    check('no page errors', not errs, errs)
    b.close()

    # ---- other browsers / the home-screen app
    for os_, want in (('ioschrome', 'ioschrome'), ('android', 'android')):
        b, pg, errs = fresh(p, UA[os_])
        check('%s: its own steps preselected' % os_, os_tab(pg) == want and pg.is_visible('.helpSteps[data-os="%s"]' % want), os_tab(pg))
        b.close()
    b, pg, errs = fresh(p, UA['ios'], standalone=True)
    check('in the home-screen app: "✓ Du använder redan hemskärmsappen", no steps', pg.is_visible('#helpInstalled') and not pg.is_visible('#helpInstallSeg'))
    # rotating the phone reloads the home-screen app: Hjälp stays open, about the same place
    pg.click('#helpToc a[href="#help-fara"]'); pg.wait_for_timeout(400)
    y0 = pg.evaluate("document.getElementById('helpBody').scrollTop")
    pg.evaluate("window.__rc = 1")
    pg.set_viewport_size({'width': 844, 'height': 390})
    pg.evaluate("window.dispatchEvent(new Event('orientationchange')); if (screen.orientation) screen.orientation.dispatchEvent(new Event('change'));")
    pg.wait_for_load_state('load'); pg.wait_for_timeout(3200)
    top = pg.evaluate("document.getElementById('help-fara').getBoundingClientRect().top - document.getElementById('helpBody').getBoundingClientRect().top")
    check('after a rotation (reload): Hjälp still open, at the same section', pg.evaluate('window.__rc') is None and pg.is_visible('#helpView') and -40 <= top <= 40, top)
    check('no page errors', not errs, errs)
    b.close()

    # ---- someone who has read older news: the dot, until Hjälp is opened
    b, pg, errs = fresh(p, seen=3)
    check('had read Hjälp before: it does not open by itself', not pg.is_visible('#helpView'))
    check('...but new things since then: a dot on the menu button and on Hjälp', pg.is_visible('#menuBtn .newDot'))
    pg.click('#menuBtn'); pg.wait_for_timeout(200)
    check('...the Hjälp item has the dot too', pg.is_visible('#menuItemHelp .newDot'))
    pg.click('#menuItemHelp'); pg.wait_for_timeout(300); pg.click('#helpBackBtn'); pg.wait_for_timeout(200)
    check('...read -> the dot is gone', not pg.is_visible('#menuBtn .newDot'))
    check('no page errors', not errs, errs)
    b.close()

# every animation the page asks for exists (tools/help_anim.py makes them)
html = open(os.path.join(os.path.dirname(HELP), 'index.html'), encoding='utf-8').read()
want = re.findall(r'src="help/([a-z]+)\.webp"', html)
missing = [w for w in want if not os.path.exists(os.path.join(HELP, w + '.webp'))]
check('all %d animations exist in docs/help/' % len(want), len(want) == 18 and not missing, missing)
from PIL import Image
wrong = [w for w in want if w not in missing and ('width="%d" height="%d" src="help/%s.webp"' % (Image.open(os.path.join(HELP, w + '.webp')).size + (w,))) not in html]
check('the page has the size of each animation (no jumping while they load; tools/help_anim.py writes them)', not wrong, wrong)
sizes = {w: os.path.getsize(os.path.join(HELP, w + '.webp')) // 1024 for w in want if w not in missing}
check('each animation under 1,2 MB', all(v < 1200 for v in sizes.values()), sizes)
print('\n%d/%d passed' % (sum(results), len(results)))
