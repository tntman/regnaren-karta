from playwright.sync_api import sync_playwright
from fakefb import new_page, login

LAKE = (58.88951, 15.77759)
results = []
def check(name, cond, info=''):
    results.append((name, bool(cond)))
    print(('PASS ' if cond else 'FAIL ') + name + ('  -- ' + str(info) if info != '' else ''))

with sync_playwright() as p:
    # ---- #2: far from the lake -> nothing is shared ----
    b, ctx, pg, errs = new_page(p, geo=(59.30, 18.05), name='Hemma')
    pg.wait_for_timeout(9500)
    w = pg.evaluate('window.__posWrites')
    check('#2 no position shared when far from the lake', len(w) == 0, w)
    check('#2 far-away pill still shows distance', 'km' in pg.inner_text('#farAway'), pg.inner_text('#farAway'))
    check('no page errors (far)', not errs, errs); b.close()

    # ---- #4: GPS permission denied -> visible message ----
    b, ctx, pg, errs = new_page(p, geo=None, perms=False, name='Nekad')
    pg.wait_for_timeout(1500)
    fa_vis = pg.eval_on_selector('#farAway', 'e => getComputedStyle(e).display')
    txt = pg.inner_text('#farAway')
    check('#4 GPS problem message visible', fa_vis == 'flex' and ('nekad' in txt.lower() or 'söker' in txt.lower()), txt)

    # ---- #3: demo on then off with no real GPS -> no ghost broadcast ----
    pg.click('#menuBtn'); pg.click('#menuItemSettings'); pg.wait_for_timeout(200)
    check('#6 demo coordinate inputs are 16px (no iOS zoom)',
          pg.eval_on_selector('#demoLatInput', 'e => getComputedStyle(e).fontSize') == '16px')
    pg.click('#demoModeToggle'); pg.wait_for_timeout(300)
    n_on = len(pg.evaluate('window.__posWrites'))
    pg.click('#demoModeToggle'); pg.wait_for_timeout(200)
    pg.evaluate('window.__posWrites.length = 0')
    pg.wait_for_timeout(9000)
    check('#3 demo position was shared while demo was on', n_on >= 1, n_on)
    check('#3 nothing shared after demo off without GPS', len(pg.evaluate('window.__posWrites')) == 0, pg.evaluate('window.__posWrites'))
    check('#3 own marker hidden after demo off without GPS', pg.eval_on_selector('#marker', 'e => getComputedStyle(e).display') == 'none')
    check('no page errors (denied/demo)', not errs, errs); b.close()

    # ---- #5 + numbering: long-press opens sheet at once even if the server never answers ----
    cfg = {'waypoints': [{'lat':58.889,'lon':15.776,'name':'Annans plats','uid':'kalle'},
                         {'lat':58.8895,'lon':15.7765,'name':'Annans plats 2','uid':'kalle'},
                         {'lat':58.8897,'lon':15.7769,'name':'Fiskeplats 3','uid':'lisa'}]}
    b, ctx, pg, errs = new_page(p, geo=LAKE, cfg=cfg, name='Filip')
    pg.click('#addHereBtn'); pg.wait_for_timeout(900)  # map pans to you first, then the sheet opens
    check('#5 sheet opens immediately (server never confirms)', pg.eval_on_selector('#wpSheet', 'e => e.classList.contains("show")'))
    check('#5 uses a local id, not add()', pg.evaluate('window.__wpAdds') == 0 and len(pg.evaluate('window.__wpSets')) == 1)
    check('numbering counts only your own spots', pg.input_value('#wpName') == 'Markering 1', pg.input_value('#wpName'))
    meta = pg.inner_text('#wpMeta')
    check('distance shown in sheet (own spot at your position)', 'Du är här' in meta, meta)
    pg.click('#wpSave'); pg.wait_for_timeout(300)
    # open someone else's spot -> distance in metres
    pg.click('#menuBtn'); pg.click('#menuItemLog'); pg.wait_for_timeout(300)
    pg.click('.logItem:has-text("Annans plats 2")'); pg.wait_for_timeout(700)
    pins = pg.query_selector_all('.wpPin--other')
    # tap the pin for "Annans plats 2" via the log -> map centred on it; click the centre pin
    pg.evaluate("""() => { var els = document.querySelectorAll('.wpPin--other'); var best=null, bd=1e9;
       els.forEach(e => { var r=e.getBoundingClientRect(); var d=Math.hypot(r.left+r.width/2-195, r.top+r.height/2-422); if(d<bd){bd=d;best=e;} }); best.click(); }""")
    pg.wait_for_timeout(400)
    meta2 = pg.inner_text('#wpMeta')
    check("distance shown for someone else's spot", ' m bort' in meta2 and 'Sparad av' in meta2, meta2)
    pg.click('#wpCancel'); pg.wait_for_timeout(300)
    check('no page errors (waypoints)', not errs, errs); b.close()

    # ---- #8 + clash + #7 + banner + offline badge + wake lock ----
    cfg = {'positions': [
        {'uid':'nisse','name':'Nisse','lat':58.8960,'lon':15.7820,'ageMin':0},     # live
        {'uid':'gamle','name':'Gamle','lat':58.89601,'lon':15.78203,'ageMin':40},  # stale, 3 m away
        {'uid':'filip','name':'Filip','lat':58.8800,'lon':15.7600,'ageMin':0.2,'device':'other-phone'}  # my name, other device, ~1.5 km away
    ]}
    b, ctx, pg, errs = new_page(p, geo=LAKE, cfg=cfg, name='Filip')
    pg.wait_for_timeout(500)
    labels = pg.eval_on_selector_all('.boatName', 'els => els.map(e => e.innerText.replace(/\\n/g,"+"))')
    check('#8 live and stale positions are not merged', sorted(labels) == ['Gamle', 'Nisse'], labels)
    stale = pg.eval_on_selector_all('.boatPip', 'els => els.map(e => e.innerText + ":" + e.classList.contains("boatPip--stale"))')
    check('#8 stale one is grey, live one white', sorted(stale) == ['Gamle:true', 'Nisse:false'], stale)

    # offline badge
    pg.evaluate('window.__setFromCache(true)'); pg.wait_for_timeout(1000)
    early = pg.eval_on_selector('#netBadge', 'e => e.classList.contains("show")')
    pg.wait_for_timeout(2600)
    check('offline badge waits ~3 s, then shows', (not early) and pg.eval_on_selector('#netBadge', 'e => e.classList.contains("show")'), pg.inner_text('#netBadge'))
    pg.screenshot(path='./shot_review_offline.png')
    pg.evaluate('window.__setFromCache(false)'); pg.wait_for_timeout(200)
    check('offline badge hides when back online', not pg.eval_on_selector('#netBadge', 'e => e.classList.contains("show")'))

    # demo banner no longer covers the legend
    pg.click('#menuBtn'); pg.click('#menuItemSettings'); pg.wait_for_timeout(200)
    pg.click('#demoModeToggle'); pg.wait_for_timeout(200); pg.click('#settingsBackBtn'); pg.wait_for_timeout(300)
    ov = pg.evaluate("""() => { var a=document.getElementById('demoBanner').getBoundingClientRect(), b=document.getElementById('legend').getBoundingClientRect(), c=document.getElementById('refreshBtn').getBoundingClientRect();
        function hit(x,y){ return !(x.right<y.left||x.left>y.right||x.bottom<y.top||x.top>y.bottom); } return hit(a,b)||hit(a,c); }""")
    check('demo banner does not cover legend/refresh', not ov)
    pg.screenshot(path='./shot_review_banner.png')
    pg.click('#menuBtn'); pg.click('#menuItemSettings'); pg.wait_for_timeout(200)
    pg.click('#demoModeToggle'); pg.wait_for_timeout(200)

    # #7 logout expires your shared position
    pg.evaluate('window.__posWrites.length = 0')
    pg.click('#logoutBtn'); pg.wait_for_timeout(300)
    w = pg.evaluate('window.__posWrites') + (pg.evaluate('window.__posUpdates') or [])
    check('#7 logout marks position as expired', any(x['id'] == 'filip' and x['updatedAtMs'] == 0 for x in w), w)
    login(pg, 'Filip2'); pg.wait_for_timeout(9000)
    labels = pg.eval_on_selector_all('.boatName', 'els => els.map(e => e.innerText)')
    check('#7 no ghost pip for the old name', 'Filip' not in labels, labels)
    check('#7 new name is shared', any(x['id'] == 'filip2' for x in pg.evaluate('window.__posWrites')))
    check('no page errors (boats/etc)', not errs, errs)

    heads = pg.evaluate("""() => [!!document.querySelector('link[rel=apple-touch-icon]'), !!document.querySelector('link[rel=manifest]'), !!document.querySelector('link[rel=icon]')]""")
    check('icon/manifest links present', all(heads), heads)
    b.close()

print('\n%d/%d passed' % (sum(1 for _, ok in results if ok), len(results)))
