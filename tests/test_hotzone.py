# Hotzone (Filter, Lager; on by default): while a competition is on, 4 fish within 200 m in the last hour = a hot spot
# (a red ring with 🔥 n); a new spot gives a note at the top -- at most one per 45 min; a spot dies an hour after its last fish.
from playwright.sync_api import sync_playwright
import fakefb, json, datetime
from fakefb import new_page
results = []
def check(name, cond, info=''):
    results.append(bool(cond)); print(('PASS ' if cond else 'FAIL ') + name + ('  -- ' + str(info) if info != '' else ''))

B3 = (58.887269, 15.772629)
Z0 = (58.887421, 15.775569); Z1 = (58.8858, 15.7835); Z2 = (58.8893, 15.7630)   # (on the water, 500-700 m apart)
TODAY = datetime.date.today().isoformat()
def ms_ago(minutes): return int((datetime.datetime.now() - datetime.timedelta(minutes=minutes)).timestamp() * 1000)
def fish(mins, at, k, who='Calle', sp='abborre'): return dict(fakefb.api_row(ms_ago(mins), 'reg2', who, sp, 30 + k, at[0] + 0.0002 * (k % 3 - 1), at[1] + 0.0003 * (k % 2)), approved=True)
comps = [{'competition_id': 'reg2', 'competition_name': 'Regnaren 2', 'date': TODAY, 'status': 'active', 'water': 'Regnaren'}]
def hz(pg): return pg.evaluate('window.__ffHotzone()')
def refetch(ctx, pg, live):
    ctx.api.live = {'reg2': live}; pg.evaluate("document.getElementById('ctFetch').click()"); pg.wait_for_timeout(1200)

with sync_playwright() as p:
    live = [fish(40, Z0, 0), fish(30, Z0, 1, 'Olle'), fish(20, Z0, 2)]
    b, ctx, pg, errs = new_page(p, geo=B3, name='Filip', cfg={'api': {'heatmap': [], 'competitions': comps, 'live': {'reg2': live}}})
    pg.wait_for_timeout(2500)
    s = hz(pg)
    check('on by default; 3 fish: no hot spot, no note', s['on'] and s['zones'] == [] and s['note'] is None and pg.is_checked('#toggleHotzone'), s)
    live.append(fish(10, Z0, 3, 'Pia')); refetch(ctx, pg, live); s = hz(pg)
    check('the 4th within 200 m: a hot spot with 4', len(s['zones']) == 1 and s['zones'][0]['n'] == 4, s)
    check('...the note: "Hotzone: 4 abborrar senaste timmen", a place name and how far',
          s['note'] and s['note'].startswith('Hotzone: 4 abborrar senaste timmen | vid ') and ' m bort · tryck för att åka dit' in s['note'], s['note'])
    pg.screenshot(path='shot_hotzone_live.png')
    ring = pg.evaluate("(() => { const e = document.querySelector('#hzLayer .hzZ'); const r = e.getBoundingClientRect(); return [r.width, e.textContent]; })()")
    m400 = pg.evaluate("(() => { const g = window.__ffGeo, a = g.screenOf(%f, %f), b = g.screenOf(%f, %f); return Math.abs(a[1] - b[1]); })()" % (Z0[0], Z0[1], Z0[0] + 400 / 111320, Z0[1]))
    check('...a ring 400 m across with 🔥 4', abs(ring[0] - m400) < 3 and ring[1] == '\U0001F525 4', (ring, m400))
    pg.click('#hzNoteGo'); pg.wait_for_timeout(800)
    c = pg.evaluate("(() => { const e = document.querySelector('#hzLayer .hzZ').getBoundingClientRect(); return [e.left + e.width / 2, e.top + e.height / 2, innerWidth, innerHeight]; })()")
    check('tap on the note: closed, the map goes to the spot', hz(pg)['note'] is None and abs(c[0] - c[2] / 2) < 20 and abs(c[1] - c[3] / 2) < 60, c)
    live.append(fish(5, Z0, 4)); refetch(ctx, pg, live); s = hz(pg)
    check('a 5th in the same spot: the count grows, no new note', len(s['zones']) == 1 and s['zones'][0]['n'] == 5 and s['note'] is None, s)
    live += [fish(9, Z1, 0), fish(8, Z1, 1), fish(7, Z1, 2), fish(6, Z1, 3, sp='gadda')]; refetch(ctx, pg, live); s = hz(pg)
    check('another spot within 45 min: only its ring (mixed species)', len(s['zones']) == 2 and s['note'] is None, s)
    # 46 minutes later (the last note moved back): the next new spot gets its note
    pg.evaluate("(() => { const k = 'ffmap_hotzone_note_v1', o = JSON.parse(localStorage.getItem(k)); o.at -= 46 * 60e3; localStorage.setItem(k, JSON.stringify(o)); })()")
    pg.reload(); pg.wait_for_timeout(2500)
    check('after a reload: the spots known, no note again', len(hz(pg)['zones']) == 2 and hz(pg)['note'] is None, hz(pg))
    live += [fish(4, Z2, 0), fish(3, Z2, 1), fish(2, Z2, 2, sp='gadda'), fish(1, Z2, 3, sp='gadda')]; refetch(ctx, pg, live); s = hz(pg)
    check('45 min after the last note: a new spot gets its note ("fiskar" when mixed)', len(s['zones']) == 3 and s['note'] and s['note'].startswith('Hotzone: 4 fiskar'), s)
    t = pg.evaluate("document.getElementById('menuItemSettings').click(), document.querySelector('.setSec[data-sec=catch]').textContent")
    check('Fångstdata: live every 2 min while Hotzone is on', 'var 2:a min (Hotzone är på)' in t, t[:300])
    pg.evaluate("document.getElementById('toggleHotzone').click()"); pg.wait_for_timeout(300); s = hz(pg)
    check('Filter off: no rings, no note', not s['on'] and s['zones'] == [] and s['note'] is None and pg.evaluate("document.getElementById('hzLayer').children.length") == 0, s)
    check('no page errors', not errs, errs)
    b.close()

    old = [fish(90 - k * 5, Z0, k) for k in range(5)]   # (the last fish 70 min ago)
    b, ctx, pg, errs = new_page(p, geo=B3, cfg={'api': {'heatmap': [], 'competitions': comps, 'live': {'reg2': old}}})
    pg.wait_for_timeout(2500)
    check('the last fish over an hour ago: the spot is gone', hz(pg)['zones'] == [], hz(pg))
    b.close()

    planned = [dict(comps[0], status='planned')]
    b, ctx, pg, errs = new_page(p, geo=B3, cfg={'api': {'heatmap': [], 'competitions': planned, 'live': {'reg2': live}}})
    pg.wait_for_timeout(2500)
    check('no competition going on: nothing', hz(pg)['zones'] == [] and hz(pg)['note'] is None, hz(pg))
    b.close()
print('\n%d/%d passed' % (sum(results), len(results)))
