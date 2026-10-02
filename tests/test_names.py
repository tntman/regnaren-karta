from playwright.sync_api import sync_playwright
import fakefb
from fakefb import new_page
results = []
def check(name, cond, info=''):
    results.append(bool(cond)); print(('PASS ' if cond else 'FAIL ') + name + ('  -- ' + str(info) if info != '' else ''))

def st(pg): return pg.evaluate("window.__ffNames()")

with sync_playwright() as p:
    b, ctx, pg, errs = new_page(p, name='Filip')
    pg.wait_for_timeout(600)
    s = st(pg)
    check('on at start: layer visible, switch on, names drawn', s['on'] and s['shown'] >= 5 and pg.evaluate("getComputedStyle(document.getElementById('osmNames')).display") == 'block'
          and pg.evaluate("document.getElementById('toggleNames').checked"), s)
    check('Regnaren has its names (islands + places)', s['total'] >= 20, s)
    check('the Filter row is called Namn, under Lager', 'Namn' in pg.inner_text('#toggleNames >> xpath=ancestor::label'))
    lab = pg.evaluate("""() => Array.prototype.filter.call(document.querySelectorAll('.osmN'), e => e.style.display !== 'none').map(e => e.textContent)""")
    check('real names are there (Fårön, Sanda holme), not "bäck"/"flowline"', 'Fårön' in lab and 'Sanda holme' in lab and 'bäck' not in lab and 'flowline' not in lab, lab)
    d = pg.evaluate("""() => { var e = document.querySelector('.osmN'), c = getComputedStyle(e, '::before'); return [c.backgroundColor, getComputedStyle(e).pointerEvents, getComputedStyle(document.getElementById('osmNames')).pointerEvents]; }""")
    check('the dot is white, taps go through', d[0] == 'rgb(255, 255, 255)' and d[2] == 'none', d)
    # no two shown labels overlap
    ov = pg.evaluate("""() => { var r = Array.prototype.filter.call(document.querySelectorAll('.osmN'), e => e.style.display !== 'none').map(e => e.querySelector('span').getBoundingClientRect()), n = 0;
        for (var i = 0; i < r.length; i++) for (var j = i + 1; j < r.length; j++) if (r[i].left < r[j].right - 6 && r[i].right > r[j].left + 6 && r[i].top < r[j].bottom - 2 && r[i].bottom > r[j].top + 2) n++; return n; }""")
    check('no labels on top of each other', ov == 0, ov)
    pg.evaluate("document.getElementById('toggleNames').click()"); pg.wait_for_timeout(100)
    check('switched off: hidden', not st(pg)['on'] and pg.evaluate("getComputedStyle(document.getElementById('osmNames')).display") == 'none')
    # the choice is remembered over a reload (rotation)
    pg.reload(); pg.wait_for_timeout(1500)
    check('off is remembered after a reload', not st(pg)['on'] and not pg.evaluate("document.getElementById('toggleNames').checked"), st(pg))
    pg.evaluate("document.getElementById('toggleNames').click()"); pg.wait_for_timeout(100)
    pg.reload(); pg.wait_for_timeout(1500)
    check('on again and remembered', st(pg)['on'], st(pg))
    # every lake has names, and the page has no errors
    for lake, minimum in (('sibbo', 5), ('sjosjon', 4), ('vagsfjarden', 4)):
        pg.goto('http://localhost:8899/index.html?lake=' + lake); pg.wait_for_timeout(1200)
        s = st(pg); check(lake + ' has names, shown when on', s['total'] >= minimum and s['shown'] >= 1, s)
    check('no page errors', not errs, errs)
    b.close()
print('\n%d/%d passed' % (sum(results), len(results)))
raise SystemExit(0 if all(results) else 1)
