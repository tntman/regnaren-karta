# Säkerhetskopia (Admin, js/36-admin.js): the whole database to a file (spots on all lakes, config, Spår,
# trackusers; Timestamps as {__ts}) and back -- everything in the file is written back, what's new is left
# alone, and a copy only goes back into the project it came from.
import json, os, tempfile
from playwright.sync_api import sync_playwright
import fakefb
from fakefb import new_page
results = []
def check(name, cond, info=''):
    results.append(bool(cond)); print(('PASS ' if cond else 'FAIL ') + name + ('  -- ' + str(info) if info != '' else ''))
TRK = 'regnaren_kalle_2026-10-01'
cfg = {
  'waypoints': [{'lat': 58.8898, 'lon': 15.7784, 'name': 'Stenen', 'uid': 'kalle', 'by': 'Calle', 'type': 'gadda'},
                {'lat': 60.2900, 'lon': 25.3900, 'name': 'Annan sjö', 'uid': 'pia', 'by': 'Pia', 'lake': 'sibbo'}],
  'config': {'posIntervalS': 30},
  'tracks': {TRK: {'lake': 'regnaren', 'uid': 'kalle', 'name': 'Calle', 'day': '2026-10-01', 'pts': 'abc', 'n': 3}},
  'trackusers': {'regnaren': {'users': {'kalle': {'u': 'kalle', 'n': 'Calle'}}}}}
msgs = []
with sync_playwright() as p:
    b, ctx, pg, errs = new_page(p, cfg=cfg, name='Filip')
    pg.on('dialog', lambda d: (msgs.append(d.message), d.accept()))
    pg.evaluate("window.__trackDocs[%s].savedAt = { toMillis: function(){ return 1700000000000; } }" % json.dumps(TRK))   # (a Timestamp)
    pg.click('#menuBtn'); pg.click('#menuItemSettings'); pg.wait_for_timeout(300)
    pg.click('#adminOpenBtn'); pg.wait_for_timeout(300)
    pg.fill('#pinInput', fakefb.TEST_PIN); pg.press('#pinInput', 'Enter'); pg.wait_for_timeout(500)
    check('Admin: the card, no copy yet', pg.is_visible('#adminBackupMake') and 'Ingen kopia' in pg.inner_text('#adminBackupStatus'), pg.inner_text('#adminBackupStatus'))
    pg.click('#adminBackupMake')
    pg.wait_for_function("document.getElementById('adminBackupStatus').textContent.indexOf('Klar') === 0", timeout=5000)
    st = pg.inner_text('#adminBackupStatus')
    check('Gör en kopia: fetched, the counts, then "Spara filen"', '2 fiskeplatser, 1 spårdagar, 1 inställningar' in st and pg.inner_text('#adminBackupMake') == 'Spara filen', st)
    pg.evaluate("Object.defineProperty(navigator, 'canShare', { value: undefined, configurable: true })")   # (the download path, as in test_admin)
    with pg.expect_download() as dl:
        pg.click('#adminBackupMake')
    path = dl.value.path(); data = json.load(open(path, encoding='utf-8'))
    wps = data['cols']['waypoints']
    check('the file: the project, the spots on all lakes, Spår, trackusers, config', data['project'] == 'regnaren-b8b6a' and sorted(w['name'] for w in wps.values()) == ['Annan sjö', 'Stenen']
          and data['cols']['tracks'][TRK]['pts'] == 'abc' and 'kalle' in data['cols']['trackusers']['regnaren']['users'] and data['cols']['config']['regnaren']['posIntervalS'] == 30,
          dl.value.suggested_filename)
    check('...Timestamps as {__ts: ms}', wps['w0']['createdAt'].get('__ts') and data['cols']['tracks'][TRK]['savedAt'] == {'__ts': 1700000000000}, wps['w0'])
    check('...and "Senaste kopia: … (idag)", the button back', 'Senaste kopia' in pg.inner_text('#adminBackupStatus') and '(idag)' in pg.inner_text('#adminBackupStatus')
          and pg.inner_text('#adminBackupMake') == 'Gör en kopia', pg.inner_text('#adminBackupStatus'))
    # a copy from another project (e.g. the test database) never goes in here (first: a restore that waits for coverage blocks the buttons)
    d2 = dict(data, project='ffmap-test')
    other = os.path.join(tempfile.mkdtemp(), 'annan.json'); json.dump(d2, open(other, 'w', encoding='utf-8'))
    pg.evaluate("window.__wpSets.length = 0")
    with pg.expect_file_chooser() as fc:
        pg.click('#adminBackupRestore')
    fc.value.set_files(other); pg.wait_for_timeout(600)
    check('a copy from another database: refused, nothing written', 'annan databas' in msgs[-1] and pg.evaluate('window.__wpSets.length') == 0, msgs[-1:])
    # someone wrecks it: every spot gone, junk in, the track emptied
    pg.evaluate("""Object.keys(__wpDocs).forEach(k => delete __wpDocs[k]);
      __wpDocs.junk = { lat: 58.89, lon: 15.78, name: 'SKRÄP', uid: 'x', lake: 'regnaren' }; __fireWp();
      __trackDocs[%s].pts = ''; __trackDocs[%s].savedAt = null""" % (json.dumps(TRK), json.dumps(TRK)))
    with pg.expect_file_chooser() as fc:
        pg.click('#adminBackupRestore')
    fc.value.set_files(path); pg.wait_for_timeout(800)
    names = sorted(d.get('name') for d in pg.evaluate('Object.values(window.__wpDocs)'))
    trk = pg.evaluate('window.__trackDocs[%s]' % json.dumps(TRK))
    check('Återställ: asked first, the spots back (both lakes), the junk left alone', msgs and 'Lägga tillbaka kopian' in msgs[-1] and names == ['Annan sjö', 'SKRÄP', 'Stenen'], (names, msgs[-1:]))
    check('...the track back, with its Timestamp', trk['pts'] == 'abc' and trk['savedAt'] == {'__epoch': True, 'ms': 1700000000000}, trk)
    check('...status: writing them back', 'Lägger tillbaka 5' in pg.inner_text('#adminBackupStatus'), pg.inner_text('#adminBackupStatus'))
    check('no page errors', not errs, errs)
    b.close()
print('\n%d/%d passed' % (sum(results), len(results)))
