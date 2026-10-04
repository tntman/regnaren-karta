# Profiler (Fiskfiskarnas API, dashboard.php: anglers, anglerStats with å/ä/ö keys, dashboard, results, records):
# the panel from a boat, from Profil in the menu (yourself), from Vem in a catch; "Fångster" = the heat map with only
# their catches; a v2 copy (no profiles) is fetched again; a rotation keeps it open.
# Your latest catch as a quick message: first in the choices while a competition is on (counted, not annulled,
# only yours), the edge in the species' colour, its photo in the message panel -- only Cloudinary photos.
from playwright.sync_api import sync_playwright
import fakefb, json, datetime
from fakefb import new_page
results = []
def check(name, cond, info=''):
    results.append(bool(cond)); print(('PASS ' if cond else 'FAIL ') + name + ('  -- ' + str(info) if info != '' else ''))

B3 = (58.887269, 15.772629); B1 = (58.887421, 15.775569); B4 = (58.88651, 15.777774)
TODAY = datetime.date.today().isoformat()
def ms_ago(minutes): return int((datetime.datetime.now() - datetime.timedelta(minutes=minutes)).timestamp() * 1000)
PHOTO = 'https://res.cloudinary.com/demo/image/upload/w_2000,q_auto,f_auto/v1/fisk.jpg'
PROF = {
    'anglers': [{'angler_id': 'ANG001', 'name': 'Filip', 'nickname': 'Hajen', 'joined_year': 2020, 'home_water': 'Valdemarsvik', 'bio_short': 'Född i en vass.'},
                {'angler_id': 'ANG034', 'name': 'Calle', 'nickname': '', 'joined_year': 2022, 'home_water': '', 'bio_short': ''}],
    'anglerStats': [{'angler_id': 'ANG001', 'WIN%': '43%', 'WIN(A)': 15, 'TÄVLING(Antal)': 35, 'TOPGädda': 112.0, 'TOPAbborre': 42.0, 'TOPGös': 88.0, '100+Gäddor': 2}],
    'dashboard': [{'competition_id': 'total', 'angler_id': 'ANG001', 'season': 2026, 'rank': 2, 'elo_out': 2606.0},
                  {'competition_id': 'regnaren_26_01', 'angler_id': 'ANG001', 'rank': 9, 'elo_out': 1.0}],
    'results': [{'angler_id': 'ANG001', 'competition_name': 'Tävling %d' % i, 'competition_date': '2025-0%d-01' % (i + 1), 'rank': i + 1, 'totl': 100.0 + i} for i in range(7)],
    'records': [{'angler_id': 'ANG001', 'RECORD_ART': 'Pike', 'RECORD_CM': 112.0, 'RECORD_ACTIVE': 'TRUE'}, {'angler_id': 'ANG001', 'RECORD_ART': 'Perch', 'RECORD_CM': 38.0, 'RECORD_ACTIVE': 'FALSE'}],
}
HIST = [fakefb.api_row(ms_ago(60 * 24 * 7 + i), 'regnaren1', 'Filip' if i < 3 else 'Calle', 'gadda', 60 + i, B4[0] + i * 0.0001, B4[1]) for i in range(5)]
def api(**kw): return dict(PROF, heatmap=HIST, competitions=[{'competition_id': 'reg2', 'competition_name': 'Regnaren 2', 'date': TODAY, 'status': 'done', 'water': 'Regnaren'}], **kw)
POS = [{'uid': 'kalle', 'name': 'Calle', 'lat': B1[0], 'lon': B1[1], 'ageMin': 0},
       {'uid': 'pia', 'name': 'Pia', 'lat': B1[0] + 0.004, 'lon': B1[1], 'ageMin': 0}]
PNG = __import__('base64').b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==')
def photos(ctx): ctx.route('**/res.cloudinary.com/**', lambda r: r.fulfill(status=200, content_type='image/png', body=PNG))   # (the tests never reach the net)
def shown(pg, id): return pg.evaluate("id => document.getElementById(id).classList.contains('show')", id)   # (the panels slide away, still "visible")
def pf(pg): return shown(pg, 'pfCard')
def boat(pg, name): pg.evaluate("n => Array.from(document.querySelectorAll('.boatPip')).filter(e => e.textContent.indexOf(n) >= 0)[0].click()", name); pg.wait_for_timeout(400)

with sync_playwright() as p:
    # ---- the data: å/ä/ö keys, this season, the latest 5, records ----
    b, ctx, pg, errs = new_page(p, geo=B3, cfg={'api': api(), 'positions': POS}, name='Filip')
    pg.wait_for_timeout(1500)
    f = pg.evaluate("window.__ffProfile('filip')")
    check('profile from the API: å/ä/ö keys read (TOPGädda, TÄVLING(Antal), WIN(A))', f and f['top']['gadda'] == 112 and f['top']['gos'] == 88 and f['comps'] == 35 and f['win'] == 15, f)
    check('...this season (total): rank 2, ELO 2606; the latest 5 competitions, newest first', f['rank'] == 2 and f['elo'] == 2606 and [r['c'] for r in f['res']] == ['Tävling 6', 'Tävling 5', 'Tävling 4', 'Tävling 3', 'Tävling 2'], f['res'])
    check('an unknown name: no profile', pg.evaluate("window.__ffProfile('Pia')") is None)
    # ---- Profil in the menu ----
    pg.click('#menuBtn'); pg.wait_for_timeout(200)
    check('Profil in the menu (there is a profile for your name)', pg.is_visible('#menuItemProfile'))
    pg.click('#menuItemProfile'); pg.wait_for_timeout(500)
    t = pg.inner_text('#pfCard')
    check('...opens your profile: picture, name, nickname, since, home, bio', pf(pg) and pg.is_visible('#pfAva img') and 'Filip' in t and '”Hajen”' in t and 'sedan 2020' in t and 'Valdemarsvik' in t and 'Född i en vass.' in t, t[:200])
    check('...rank, ELO, wins, competitions; biggest fish, the pike a club record (★)', '2:a' in t and '2606' in t and '15 · 43 %' in t and '35' in t and '112 cm' in t and '★ Klubbrekord' in t and '42 cm' in t and t.count('Klubbrekord') == 1, t)
    check('..."Visa på kartan" (you are on the map) and "Fångster i Regnaren (3)"', pg.is_visible('#pfMap') and pg.inner_text('#pfCatches') == 'Fångster i Regnaren (3)')
    pg.screenshot(path='shot_profile.png')
    # "Fångster": the heat map with only Filip's catches; ✕ = everyone's again
    pg.click('#pfCatches'); pg.wait_for_timeout(700)
    h = pg.evaluate('window.__ffHeat()')
    check('"Fångster": the heat map on, only his 3 catches, "Bara Filip ✕"', not pf(pg) and h['on'] and h['n'] == 3 and pg.is_visible('.hmWho') and 'Bara Filip' in pg.inner_text('.hmWho'), h)
    pg.click('.hmWho'); pg.wait_for_timeout(400)
    check('...✕: everyone\'s catches again', pg.evaluate('window.__ffHeat()')['n'] == 5)
    # Vem in a catch -> the profile
    check('..."Fångster" shows them as dots', h['style'] == 'dots')
    pg.evaluate("document.getElementById('hmPanel').classList.remove('show')"); pg.wait_for_timeout(300)
    sx = pg.evaluate("window.__ffHeatScreen(window.__ffCatches().filter(c => c.who === 'Filip')[0].id)")
    pg.mouse.click(sx[0], sx[1]); pg.wait_for_timeout(600)
    check('a catch: Vem can be tapped (his profile)', pg.is_visible('#hmCard') and pg.is_visible('#hmCardData .pfLink'), pg.inner_text('#hmCardData') if pg.is_visible('#hmCard') else 'no card')
    if pg.is_visible('#hmCardData .pfLink'):
        pg.click('#hmCardData .pfLink'); pg.wait_for_timeout(500)
        check('...opens it (the catch panel closes)', pf(pg) and not shown(pg, 'hmCard') and pg.inner_text('#pfName') == 'Filip', [shown(pg, 'hmCard'), pg.inner_text('#pfName')])
    pg.click('#pfClose'); pg.wait_for_timeout(300)
    # a boat: one person with a profile -> the profile; without -> the old box
    boat(pg, 'Calle')
    t = pg.inner_text('#pfCard')
    check("tap Calle's boat: his profile (no stats: – / Inga ännu), Båten på kartan · uppdaterad …, Visa på kartan", pf(pg) and pg.inner_text('#pfName') == 'Calle' and 'Båten på kartan' in t and pg.is_visible('#pfMap') and 'Inga ännu' in t and '–' in pg.inner_text('#pfData'), t[:200])
    check('...his 2 catches here: "Fångster i Regnaren (2)"', pg.inner_text('#pfCatches') == 'Fångster i Regnaren (2)', pg.inner_text('#pfCatches'))
    check("Calle's profile has \"Åk hit\" (his boat is on the map)", pg.is_visible('#pfGo'))
    check('...and his 2 catches listed (newest first)', pg.evaluate("document.querySelectorAll('#pfList .pfRow').length") == 2, pg.inner_text('#pfList'))
    pg.click('#pfClose'); pg.wait_for_timeout(300)
    boat(pg, 'Pia')
    check('tap Pia\'s boat (no profile): the old box', not pf(pg) and pg.is_visible('#boatInfoModal') and pg.inner_text('#boatInfoName') == 'Pia')
    check('the box has "Åk hit"; it closes and the lead line goes to the boat', pg.is_visible('#boatInfoGo'))
    pg.click('#boatInfoGo'); pg.wait_for_timeout(700)
    check('...the lead line is on', pg.eval_on_selector('#probe', 'e => e.classList.contains("show")') and not pg.eval_on_selector('#boatInfoModal', 'e => e.classList.contains("show")'))
    check('no page errors', not errs, errs)
    b.close()

    # ---- an old copy (v2, no profiles) is fetched again; Profil hidden for an unknown name ----
    b, ctx, pg, errs = new_page(p, geo=B3, cfg={'api': api()}, name='Testare')
    pg.wait_for_timeout(1500)
    pg.evaluate("(() => { var c = JSON.parse(localStorage.getItem('ffmap_catches_v1')); c.v = 2; delete c.prof; localStorage.setItem('ffmap_catches_v1', JSON.stringify(c)); })()")
    n0 = ctx.api.n('dashboard'); pg.reload(); pg.wait_for_timeout(2200)
    check('a v2 copy (no profiles): fetched again at start', ctx.api.n('dashboard') == n0 + 1 and pg.evaluate("window.__ffProfile('Filip')") is not None, ctx.api.hits)
    pg.click('#menuBtn'); pg.wait_for_timeout(200)
    check('an unknown name: no Profil in the menu', not pg.is_visible('#menuItemProfile'))
    check('no page errors', not errs, errs)
    b.close()

    # ---- your latest catch as a quick message ----
    live = [dict(fakefb.api_row(ms_ago(30), 'regnaren2', 'Filip', 'gadda', 78, B3[0], B3[1]), approved=True, imageUrl=PHOTO),
            dict(fakefb.api_row(ms_ago(10), 'regnaren2', 'Filip', 'abborre', 22, B3[0], B3[1]), approved=False, imageUrl=''),     # not counted (under 25 cm)
            dict(fakefb.api_row(ms_ago(5), 'regnaren2', 'Calle', 'gos', 55, B1[0], B1[1]), approved=True)]                          # someone else's
    comps = [{'competition_id': 'reg2', 'competition_name': 'Regnaren 2', 'date': TODAY, 'status': 'active', 'water': 'Regnaren'}]
    b, ctx, pg, errs = new_page(p, geo=B3, cfg={'api': dict(api(), competitions=comps, live={'reg2': live}),
        'positions': [{'uid': 'kalle', 'name': 'Calle', 'lat': B1[0], 'lon': B1[1], 'ageMin': 0, 'msg': 'Gös 55 🐟', 'msgAgeMin': 1, 'msgSp': 'gos', 'msgImg': PHOTO},
                      {'uid': 'olle', 'name': 'Olle', 'lat': B1[0] - 0.004, 'lon': B1[1], 'ageMin': 0, 'msg': 'Gädda 40 🐟', 'msgAgeMin': 4, 'msgSp': 'gadda'},   # (over 3 min: faded, plain black)
                      {'uid': 'pia', 'name': 'Pia', 'lat': B1[0] + 0.004, 'lon': B1[1], 'ageMin': 0, 'msg': 'Kolla', 'msgAgeMin': 1, 'msgSp': 'gadda', 'msgImg': 'https://example.com/spy.gif'}]}, name='Filip')
    photos(ctx)
    pg.wait_for_timeout(2500)
    pg.click('#msgBtn'); pg.wait_for_timeout(300)
    opts = pg.eval_on_selector_all('#msgPop button', 'e => e.map(x => x.textContent)')
    hm = pg.evaluate("(() => { var d = new Date(Date.now() - 30 * 60000); return ('0' + d.getHours()).slice(-2) + ':' + ('0' + d.getMinutes()).slice(-2); })()")
    check('competition on: your latest counted catch first ("Gädda 78 🐟 · hh:mm"), not the 22 cm perch, not Calle\'s', opts[0] == 'Gädda 78 🐟 · ' + hm and opts[1] == 'Fisk!!! 🎣' and not any('Gös' in o or 'Abborre' in o for o in opts), opts)
    check("...a plain edge like the others, no dot; the pike's green sweeping through the text", pg.evaluate("(() => { var b = document.getElementById('msgFishBtn'), o = document.querySelector('#msgPop button:not(.msgFish)'), t = b.querySelector('.mT.sp'); return !b.querySelector('.hmSpDot') && !!t && b.style.getPropertyValue('--sp') === '#35D24A' && getComputedStyle(b).borderTopColor === getComputedStyle(o).borderTopColor && getComputedStyle(b, '::before').content === 'none'; })()"))
    pg.click('#msgFishBtn'); pg.wait_for_timeout(500)
    w = [x for x in pg.evaluate('window.__posWrites') if x.get('msg')]
    check('sent by hand: "Gädda 78 🐟", the species and the photo (600 px wide) with it', w and w[-1]['msg'] == 'Gädda 78 🐟' and w[-1]['msgSp'] == 'gadda' and w[-1]['msgImg'] == PHOTO.replace('w_2000', 'w_600'), w[-1:] if w else w)
    check('...your bubble: the species colour sweeping through the text, as for everyone', pg.evaluate("(() => { var t = document.querySelector('.msgBub.mine .mT.sp'); return !!t && t.style.getPropertyValue('--sp') === '#35D24A'; })()"))
    pg.click('#msgBtn'); pg.wait_for_timeout(300)
    check('the same fish can be sent again (no lock)', pg.is_visible('#msgFishBtn'))
    pg.click('#msgBtn'); pg.wait_for_timeout(200)
    # Calle's catch message: green? no -- the zander's blue; his photo in the panel; his name -> his profile
    check("Olle's catch (4 min old): faded, the colour is gone -- plain black", pg.evaluate("(() => { var l = Array.from(document.querySelectorAll('.mLine')).filter(x => x.textContent.indexOf('Gädda 40') >= 0)[0]; return !!l && !l.querySelector('.mT.sp') && !l.querySelector('.rbText'); })()"))
    check("Calle's catch bubble: the zander's blue in the text", pg.evaluate("(() => { var l = Array.from(document.querySelectorAll('.mLine')).filter(x => x.textContent.indexOf('Gös 55') >= 0)[0]; var t = l && l.querySelector('.mT.sp'); return !!t && t.style.getPropertyValue('--sp') === '#3A86FF'; })()"))
    pg.evaluate("Array.from(document.querySelectorAll('.mLine')).filter(x => x.textContent.indexOf('Gös 55') >= 0)[0].click()"); pg.wait_for_timeout(400)
    check('...his panel shows the photo (only loaded now)', pg.is_visible('#msgCard') and pg.get_attribute('#msgCardImg', 'src') == PHOTO and not pg.eval_on_selector('#msgCardImg', 'e => e.hidden'))
    pg.click('#msgCardWho'); pg.wait_for_timeout(400)
    check('...tap his name: his profile', pf(pg) and pg.inner_text('#pfName') == 'Calle' and not shown(pg, 'msgCard'))
    pg.click('#pfClose'); pg.wait_for_timeout(300)
    pg.evaluate("Array.from(document.querySelectorAll('.mLine')).filter(x => x.textContent.indexOf('Kolla') >= 0)[0].click()"); pg.wait_for_timeout(400)
    check('a photo address that is not Cloudinary is never shown', pg.is_visible('#msgCard') and pg.eval_on_selector('#msgCardImg', 'e => e.hidden && !e.getAttribute("src")'))
    pg.click('#msgCardClose'); pg.wait_for_timeout(300)
    check('no page errors', not errs, errs)
    b.close()

    # ---- no competition going on: no catch choice ----
    b, ctx, pg, errs = new_page(p, geo=B3, cfg={'api': api(live={'reg2': live})}, name='Filip')
    pg.wait_for_timeout(2000)
    pg.click('#msgBtn'); pg.wait_for_timeout(300)
    check('no competition on: no catch in the choices', not pg.is_visible('#msgFishBtn') and pg.eval_on_selector_all('#msgPop button', 'e => e[0].textContent') == 'Fisk!!! 🎣')
    b.close()

    # ---- rotation: the profile stays open ----
    b, ctx, pg, errs = new_page(p, geo=B3, cfg={'api': api()}, name='Filip')
    ctx.add_init_script("Object.defineProperty(navigator, 'standalone', { value: true, configurable: true });")
    pg.reload(); pg.wait_for_timeout(1500)
    pg.click('#menuBtn'); pg.wait_for_timeout(200); pg.click('#menuItemProfile'); pg.wait_for_timeout(400)
    pg.set_viewport_size({'width': 844, 'height': 390})
    pg.evaluate("window.dispatchEvent(new Event('orientationchange')); if (screen.orientation) screen.orientation.dispatchEvent(new Event('change'));")
    pg.wait_for_load_state('load'); pg.wait_for_timeout(1800)
    check('after a rotation: the profile still open', pg.evaluate("performance.getEntriesByType('navigation')[0].type") == 'reload' and pf(pg) and pg.inner_text('#pfName') == 'Filip')
    check('no page errors', not errs, errs)
    b.close()

print('\n%d/%d passed' % (sum(results), len(results)))
