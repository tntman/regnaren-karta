from playwright.sync_api import sync_playwright
from fakefb import new_page, login

results = []
def check(name, cond, info=''):
    results.append(bool(cond))
    print(('PASS ' if cond else 'FAIL ') + name + ('  -- ' + str(info) if info != '' else ''))

with sync_playwright() as p:
    b, ctx, pg, errs = new_page(p, geo=(58.88951, 15.77759), cfg={}, name='Filip')
    check('menu button shows the profile picture', pg.is_visible('#menuAva') and pg.is_visible('#menuChev'))
    check('hamburger hidden while there is a picture', not pg.is_visible('#menuBtn > svg'))
    check('no user name under the lake title', pg.locator('#headerUser').count() == 0)
    pg.click('#menuBtn')
    check('menu ends with "Logga ut Filip"', pg.inner_text('#menuItemLogout').strip() == 'Logga ut Filip')
    pg.click('#menuItemLogout'); pg.wait_for_timeout(300)
    check('logout opens the name picker', pg.eval_on_selector('#nameModal', 'e=>e.classList.contains("show")'))
    check('logged out: hamburger back, no logout item', pg.is_visible('#menuBtn > svg') and not pg.is_visible('#menuAva'))
    login(pg, 'Calle'); pg.wait_for_timeout(500)
    check('another member -> their own picture', pg.is_visible('#menuAva'))
    check('no page errors', not errs, errs)
    print('\n%d/%d passed' % (sum(results), len(results)), flush=True)
    b.close()
