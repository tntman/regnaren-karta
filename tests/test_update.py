# A new version (sw.js): the start uses the saved copy at once (no wait for the network, no white), the newest is
# fetched alongside it -- changed: saved for the next start and "Ny version – tryck för att ladda om" (#updNote).
# (An older saved copy is made here by putting a marked copy of the page in the cache -- docs/ isn't touched.)
from playwright.sync_api import sync_playwright
import fakefb
from fakefb import new_page
results = []
def check(name, cond, info=''):
    results.append(bool(cond)); print(('PASS ' if cond else 'FAIL ') + name + ('  -- ' + str(info) if info != '' else ''))
REG = (58.88951, 15.77759)
def note(pg): return pg.evaluate("document.getElementById('updNote').classList.contains('show')")
def marked(pg): return pg.evaluate("document.documentElement.outerHTML.indexOf('OLD-COPY') >= 0")

with sync_playwright() as p:
    b, ctx, pg, errs = new_page(p, geo=REG, cfg={}, name='Filip', sw=True)
    pg.wait_for_function("navigator.serviceWorker.controller || navigator.serviceWorker.ready.then(function(){ return true; })", timeout=10000)
    pg.reload(); pg.wait_for_function('!!navigator.serviceWorker.controller', timeout=10000); pg.wait_for_timeout(1500)
    check('controlled by sw.js, the page saved, nothing new: no notice', not note(pg) and pg.evaluate("caches.keys().then(function(k){ return k.length > 0; })"))
    # an older copy saved on the phone
    pg.evaluate("""async () => { var t = await (await fetch('./', { cache: 'no-store' })).text();
      var keys = await caches.keys(); var c = await caches.open(keys.filter(function(k){ return k.indexOf('ffmap-v') === 0; })[0]);
      await c.put('./', new Response(t.replace('</body>', '<!-- OLD-COPY --></body>'), { headers: { 'Content-Type': 'text/html' } })); }""")
    pg.reload(); pg.wait_for_timeout(300)
    check('next start: the saved copy at once (the older one)', marked(pg))
    try: pg.wait_for_function("document.getElementById('updNote').classList.contains('show')", timeout=8000); ok = True
    except Exception: ok = False
    check('...the newer one found alongside: "Ny version – Tryck för att ladda om"', ok and pg.is_visible('#updNote') and 'Ny version' in pg.inner_text('#updNote'), pg.inner_text('#updNote'))
    pg.click('#updNoteGo'); pg.wait_for_load_state(); pg.wait_for_timeout(2000)
    check('a tap: reloaded into the new version, no notice', not marked(pg) and not note(pg))
    pg.reload(); pg.wait_for_timeout(2000)
    check('...and the next start: no notice either', not marked(pg) and not note(pg))
    pg.evaluate("document.getElementById('updNote').classList.add('show')"); pg.click('#updNoteClose')
    check('✕ closes it', not note(pg))
    check('no errors', not errs, errs)
    b.close()
print('%d/%d passed' % (sum(results), len(results)))
