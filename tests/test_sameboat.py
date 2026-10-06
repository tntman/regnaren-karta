# "The same boat" (sameBoatM, js/14-spots.js): closer than 40 m + how far the boat gets between the two positions' times.
from playwright.sync_api import sync_playwright
from fakefb import new_page
results = []
def check(name, cond, info=''):
    results.append(bool(cond)); print(('PASS ' if cond else 'FAIL ') + name + ('  -- ' + str(info) if info != '' else ''))

ME = (58.887269, 15.772629); P = (58.88651, 15.777774)
SET = """([cLat, cLon, cAgo, oLat, oLon, oAgo]) => { const t = ms => ({ toMillis: () => ms }), now = Date.now(), d = window.__posDocs;
  d.calle = { uid: 'calle', name: 'Calle', lake: 'regnaren', lat: cLat, lon: cLon, updatedAt: t(now - cAgo * 1000) };
  d.olle = { uid: 'olle', name: 'Olle', lake: 'regnaren', lat: oLat, lon: oLon, updatedAt: t(now - oAgo * 1000) };
  window.__firePos(); return Array.from(document.querySelectorAll('.boatName')).map(e => e.textContent).sort(); }"""
N = 1 / 111320; E = 1 / 57540   # degrees per metre north / east here
with sync_playwright() as p:
    b, ctx, pg, errs = new_page(p, geo=ME)
    pg.wait_for_timeout(2000)
    r = pg.evaluate(SET, [P[0], P[1], 40, P[0] + 30 * N, P[1], 20])
    check('still, 30 m apart: the same boat', r == ['CalleOlle'], r)
    r = pg.evaluate(SET, [P[0], P[1], 40, P[0] + 50 * N, P[1], 20])
    check('still, 50 m apart: two boats', r == ['Calle', 'Olle'], r)
    r = pg.evaluate(SET, [P[0], P[1] + 40 * E, 20, P[0] + 50 * N, P[1] + 40 * E, 0])
    check('both moving 2 m/s, 50 m apart, 20 s between the positions (40 + 40 m): the same boat', r == ['CalleOlle'], r)
    r = pg.evaluate(SET, [P[0], P[1] + 40 * E, 20, P[0] + 300 * N, P[1] + 40 * E, 0])
    check('...but 300 m apart: two boats', r == ['Calle', 'Olle'], r)
    check('no page errors', not errs, errs)
    b.close()
print('%d/%d passed' % (sum(results), len(results)))
