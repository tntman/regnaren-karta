# iOS home-screen app: the status bar must be "black", not "black-translucent". With
# translucent, iOS 26 makes the web view a status bar too short -- a dead band at the
# bottom that no CSS can reach (WebKit bug 301108; stretching the app over it only
# clipped the buttons, tried 2026-09-29). And no leftover stretching code.
from playwright.sync_api import sync_playwright
import fakefb
from fakefb import new_page
results = []
def check(name, cond, info=''):
    results.append(bool(cond)); print(('PASS ' if cond else 'FAIL ') + name + ('  -- ' + str(info) if info != '' else ''))
ME = (58.88951, 15.77759)

with sync_playwright() as p:
    b, ctx, pg, errs = new_page(p, geo=ME, cfg={}, name='Filip')
    style = pg.get_attribute('meta[name="apple-mobile-web-app-status-bar-style"]', 'content')
    check('status bar "black" (not "black-translucent")', style == 'black', style)
    check('viewport still viewport-fit=cover (safe areas reported)', 'viewport-fit=cover' in pg.get_attribute('meta[name="viewport"]', 'content'))
    html = pg.content()
    check('no stretching over the dead band (it only clipped the buttons)', 'iosGap' not in html and 'fixIosGap' not in html)
    m = pg.evaluate("() => [document.getElementById('app').getBoundingClientRect().bottom, window.innerHeight]")
    check('the app fills the window exactly', abs(m[0] - m[1]) < 1, m)
    check('no page errors', not errs, errs)
    b.close()
print('\n%d/%d passed' % (sum(results), len(results)))
