# "Vem är du?" as a full screen: the logo, a picture per member in a grid, "Annat namn" last; a tap = chosen
# (the others dimmed), the button "Fortsätt som X"; Annat namn = the text field, the button follows the text;
# Fortsätt without a choice = the error; lying down: 6 columns.
from playwright.sync_api import sync_playwright
import fakefb
from fakefb import new_page
results = []
def check(name, cond, info=''):
    results.append(bool(cond)); print(('PASS ' if cond else 'FAIL ') + name + ('  -- ' + str(info) if info != '' else ''))
B3 = (58.887269, 15.772629)

with sync_playwright() as p:
    b, ctx, pg, errs = new_page(p, geo=B3, cfg={}, name=None)
    pg.wait_for_timeout(1200)
    check('the name picker is open at start (a full screen)', pg.eval_on_selector('#nameModal', 'e => e.classList.contains("show") && e.getBoundingClientRect().height >= innerHeight - 1'))
    n = pg.evaluate("document.querySelectorAll('#nameList .nameChip[data-name]').length")
    imgs = pg.evaluate("document.querySelectorAll('#nameList .nameChip[data-name] .ava img').length")
    check('a picture per name on the list, "Annat namn" last', n >= 30 and imgs == n and pg.evaluate("document.querySelector('#nameList').lastElementChild.matches('.nameChip--other')") and 'Annat namn' in pg.inner_text('.nameChip--other'), (n, imgs))
    check('the logo is loaded', pg.evaluate("(() => { var i = document.querySelector('.nameLogo img'); return i.complete && i.naturalWidth > 0; })()"))
    # the 3D sign (js/35-name-logo.js): WebGL when there is one, otherwise the flat picture
    pg.wait_for_function("__ffNameLogo().gl || __ffNameLogo().tier == 'flat'", timeout=8000)
    st = pg.evaluate("__ffNameLogo()")
    check('3D logo: a sign (canvas) or the flat picture, running, still', st['running'] and not st['moving'] and (pg.is_visible('.nameLogo3d') if st['gl'] else pg.is_visible('.nameLogo img')), st)
    lb = pg.eval_on_selector('#nameLogo', 'e => { var r = e.getBoundingClientRect(); return [r.x + r.width / 2, r.y + r.height / 2]; }')
    def flick(dx, steps, wait):
        pg.mouse.move(lb[0] - dx * steps / 2, lb[1]); pg.mouse.down()
        for k in range(steps): pg.mouse.move(lb[0] - dx * steps / 2 + dx * (k + 1), lb[1]); pg.wait_for_timeout(wait)
        pg.mouse.up()
    flick(20, 6, 10); pg.wait_for_timeout(60)
    fast = pg.evaluate("__ffNameLogo()")
    check('3D logo: a fast drag spins it (> 45°, moving)', fast['moving'] and abs(fast['ry']) > 45, fast)
    pg.wait_for_function("!__ffNameLogo().moving", timeout=6000)
    check('...and it stops at the start (0°)', pg.evaluate("__ffNameLogo().ry") == 0)
    flick(3, 4, 40); pg.wait_for_timeout(60)
    slow = pg.evaluate("__ffNameLogo()")
    check('a slow short drag: less spin', abs(slow['ry']) < abs(fast['ry']), (slow['ry'], fast['ry']))
    pg.wait_for_function("!__ffNameLogo().moving", timeout=6000)
    if st['gl']:
        pg.evaluate("__ffNameLogo({slow: true})")
        pg.wait_for_function("__ffNameLogo().tier == 'flat'", timeout=15000)
        check('slow frames: full -> lite -> flat, remembered', pg.evaluate("localStorage.getItem('ffmap_logo3d_v1')") == 'flat' and not pg.evaluate("__ffNameLogo().gl") and pg.eval_on_selector('#nameLogo', 'e => e.classList.contains("flat")'))
        flick(20, 6, 10); pg.wait_for_timeout(60)
        fl = pg.evaluate("__ffNameLogo()"); tf = pg.eval_on_selector('.nlSpin', 'e => e.style.transform')
        check('flat: still spins (the picture turns with CSS)', abs(fl['ry']) > 45 and 'rotateY' in tf, (fl, tf))
        pg.wait_for_function("!__ffNameLogo().moving", timeout=6000)
    check('3 columns, the button "Välj dig själv" (grey)', pg.evaluate("getComputedStyle(document.getElementById('nameList')).gridTemplateColumns.split(' ').length") == 3 and pg.inner_text('#nameSave') == 'Välj dig själv' and not pg.eval_on_selector('#nameSave', 'e => e.classList.contains("on")'))
    pg.click('#nameSave'); pg.wait_for_timeout(200)
    check('Fortsätt with nothing chosen: the error', pg.is_visible('#nameError') and pg.eval_on_selector('#nameModal', 'e => e.classList.contains("show")'))
    pg.click('.nameChip[data-name="Calle"]'); pg.wait_for_timeout(300)
    op = pg.evaluate("getComputedStyle(document.querySelector('.nameChip[data-name=\"Filip\"]')).opacity")
    check('tap Calle: chosen (amber), the others dimmed, "Fortsätt som Calle"', pg.eval_on_selector('.nameChip[data-name="Calle"]', 'e => e.classList.contains("selected")') and float(op) < 0.5 and pg.inner_text('#nameSave') == 'Fortsätt som Calle' and pg.eval_on_selector('#nameSave', 'e => e.classList.contains("on")') and not pg.is_visible('#nameError'), op)
    pg.screenshot(path='shot_name_picker.png')
    pg.click('.nameChip--other'); pg.wait_for_timeout(300)
    check('Annat namn: the text field, "Skriv ditt namn", Calle no longer chosen', pg.is_visible('#nameInput') and pg.inner_text('#nameSave') == 'Skriv ditt namn' and not pg.eval_on_selector('.nameChip[data-name="Calle"]', 'e => e.classList.contains("selected")'))
    pg.fill('#nameInput', 'Kalle Anka'); pg.wait_for_timeout(100)
    check('...the button follows the text: "Fortsätt som Kalle Anka"', pg.inner_text('#nameSave') == 'Fortsätt som Kalle Anka' and pg.eval_on_selector('#nameSave', 'e => e.classList.contains("on")'))
    pg.set_viewport_size({'width': 844, 'height': 390}); pg.wait_for_timeout(300)
    check('lying down: 6 columns', pg.evaluate("getComputedStyle(document.getElementById('nameList')).gridTemplateColumns.split(' ').length") == 6)
    pg.set_viewport_size({'width': 390, 'height': 844}); pg.wait_for_timeout(300)
    pg.click('.nameChip[data-name="Filip"]'); pg.click('#nameSave'); pg.wait_for_timeout(600)
    check('Fortsätt: the name is saved, the picker closes', not pg.eval_on_selector('#nameModal', 'e => e.classList.contains("show")') and pg.evaluate("localStorage.getItem('regnaren_user_name_v1')") == 'Filip')
    check('no page errors', not errs, errs)
    b.close()

print('\n%d/%d passed' % (sum(results), len(results)))
