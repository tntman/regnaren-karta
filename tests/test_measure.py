from playwright.sync_api import sync_playwright
from fakefb import new_page
import math

results = []
def check(name, cond, info=''):
    results.append(bool(cond))
    print(('PASS ' if cond else 'FAIL ') + name + ('  -- ' + str(info) if info != '' else ''))

ME = (58.88951, 15.77759)
cfg = {'waypoints': [{'lat': 58.8880, 'lon': 15.7800, 'name': 'Målet', 'uid': 'kalle', 'by': 'Calle'}]}

with sync_playwright() as p:
    b, ctx, pg, errs = new_page(p, geo=ME, cfg=cfg, name='Filip')
    pg.wait_for_timeout(500)

    # ---- knot meter with real (emulated) GPS moving north at ~2 kn ----
    check('knot meter visible on the lake', pg.is_visible('#speedPill'), pg.inner_text('#speedPill'))
    w = pg.evaluate("[document.getElementById('speedPill').getBoundingClientRect().width, document.getElementById('legend').getBoundingClientRect().width, document.getElementById('speedPill').scrollWidth - document.getElementById('speedPill').clientWidth]")
    check('knot/depth box as wide as the depth scale, text fits', abs(w[0] - w[1]) < 1 and w[2] <= 0, w)
    lat = ME[0]
    for i in range(12):
        lat += 1.03 / 111320.0            # 1.03 m per second = 2.0 kn
        ctx.set_geolocation({'latitude': lat, 'longitude': ME[1], 'accuracy': 5})
        pg.wait_for_timeout(1000)
    moving = pg.inner_text('#speedVal')
    check('knot meter ~2 kn while moving', 1.6 <= float(moving.replace(',', '.')) <= 2.4, moving + ' kn')
    pg.wait_for_timeout(9500)
    check('knot meter drops to 0,0 when fixes stop', pg.inner_text('#speedVal') == '0,0', pg.inner_text('#speedVal'))

    # ---- cruise speed setting ----
    pg.click('#menuBtn'); pg.click('#menuItemSettings'); pg.wait_for_timeout(200)
    check('cruise default 2,0', pg.input_value('#cruiseInput') == '2,0')
    check('settings say cruise is used (no average yet)', 'marschfarten 2,0 kn' in pg.inner_text('#speedUsedNote'), pg.inner_text('#speedUsedNote'))
    print('   avg field:', pg.inner_text('#avgSpeedVal'), '|', pg.inner_text('#avgSpeedSub'))
    pg.fill('#cruiseInput', 'abc'); pg.press('#cruiseInput', 'Enter'); pg.wait_for_timeout(100)
    check('invalid cruise rejected', pg.eval_on_selector('#cruiseInput', 'e=>e.classList.contains("invalid")'))
    pg.fill('#cruiseInput', '4'); pg.press('#cruiseInput', 'Enter'); pg.wait_for_timeout(100)
    check('cruise 4 kn saved', pg.input_value('#cruiseInput') == '4,0' and pg.evaluate("localStorage.getItem('ffmap_cruise_kn_v1')") == '4')
    pg.screenshot(path='./shot_speed_settings.png')
    pg.click('#settingsBackBtn'); pg.wait_for_timeout(300)

    # ---- measuring tool ----
    w = pg.eval_on_selector('#scaleLine', 'e=>e.getBoundingClientRect().width'); lab = pg.inner_text('#scaleLabel')
    mpp = float(lab.split()[0]) * (1000 if 'km' in lab else 1) / w
    pg.click('#measureBtn'); pg.wait_for_timeout(200)
    check('measuring panel opens', pg.is_visible('#measurePanel') and pg.eval_on_selector('#measureBtn', 'e=>e.classList.contains("active")'))
    n_wp = pg.evaluate("document.querySelectorAll('#waypoints .wpPin').length")
    pts = [(80, 300), (80, 500), (280, 500)]   # 200 px down, 200 px right
    for x, y in pts:
        pg.mouse.click(x, y); pg.wait_for_timeout(120)
    expect_m = 400 * mpp
    main = pg.inner_text('#mpMain'); sub = pg.inner_text('#mpSub')
    print('   panel:', main, '|', sub, '| expected ~%d m' % expect_m)
    shown = main.split(' · ')[0]
    shown_m = float(shown.replace(' km', '').replace(',', '.')) * 1000 if 'km' in shown else float(shown.replace(' m', ''))
    check('distance matches the taps (±3 %)', abs(shown_m - expect_m) / expect_m < 0.03, '%s vs %.0f m' % (shown, expect_m))
    exp_min = round(shown_m / (4 / 1.943844) / 60)
    check('time uses cruise 4 kn', ('ca %d min' % exp_min) in main and 'marschfart' in sub, main)
    check('3 point markers drawn', pg.evaluate("document.querySelectorAll('#measureLayer .mlPt').length") == 3)
    check('double tap did not zoom / long-press no new spot', pg.evaluate("document.querySelectorAll('#waypoints .wpPin').length") == n_wp)
    pg.screenshot(path='./shot_measure.png')
    # tap a fishing spot -> point snaps onto it, no sheet opens
    pg.click('#waypoints .wpPin'); pg.wait_for_timeout(200)
    check('tapping a spot adds a point (no sheet)', pg.evaluate("document.querySelectorAll('#measureLayer .mlPt').length") == 4
          and not pg.eval_on_selector('#wpSheet', 'e=>e.classList.contains("show")'))
    pg.click('#mpUndo'); pg.wait_for_timeout(100)
    check('Ångra removes last point', pg.evaluate("document.querySelectorAll('#measureLayer .mlPt').length") == 3)
    # map still pans in measuring mode (drag != tap)
    pg.mouse.move(200, 400); pg.mouse.down(); pg.mouse.move(150, 350, steps=6); pg.mouse.up(); pg.wait_for_timeout(150)
    check('dragging pans instead of adding a point', pg.evaluate("document.querySelectorAll('#measureLayer .mlPt').length") == 3)
    pg.click('#mpClear'); pg.wait_for_timeout(100)
    check('Rensa clears all', pg.evaluate("document.querySelectorAll('#measureLayer .mlPt').length") == 0 and 'Tryck på kartan' in pg.inner_text('#mpMain'))
    pg.mouse.click(100, 300); pg.wait_for_timeout(100)
    pg.click('#mpClose'); pg.wait_for_timeout(150)
    check('✕ closes and clears', not pg.is_visible('#measurePanel') and pg.evaluate("document.querySelectorAll('#measureLayer .mlPt').length") == 0)
    # normal behaviour back: tapping a spot opens its sheet again
    pg.click('#waypoints .wpPin'); pg.wait_for_timeout(400)
    check('after closing, spots open normally again', pg.eval_on_selector('#wpSheet', 'e=>e.classList.contains("show")'))
    pg.click('#wpCancel'); pg.wait_for_timeout(300)

    # layout check in landscape
    pg.click('#measureBtn'); pg.mouse.click(100, 300); pg.mouse.click(250, 350); pg.wait_for_timeout(100)
    pg.set_viewport_size({'width': 844, 'height': 390}); pg.wait_for_timeout(500)
    pg.screenshot(path='./shot_measure_landscape.png')
    check('no page errors', not errs, errs)
    b.close()

print('\n%d/%d passed' % (sum(results), len(results)))
