# Kartanalys "Från fångsterna (data)": a species from the competitions' catches in this lake ->
# the parts of the lake most like where it was caught. The data decides how much is lit ("Typiskt":
# how many of 10 catches the lit part holds), on/off for each value (dots = how much it points the
# species out), "Tänt" or "Skala", < 10 catches can't be chosen, not together with the heat map.
from playwright.sync_api import sync_playwright
import fakefb, json, re, calendar
from fakefb import new_page
results = []
def check(name, cond, info=''):
    results.append(bool(cond)); print(('PASS ' if cond else 'FAIL ') + name + ('  -- ' + str(info) if info != '' else ''))
B3 = (58.887269, 15.772629)
def size(pg, root, a, b):   # "Storlek": move the two handles (min, max cm)
    pg.evaluate("""([r, a, b]) => [['cm1', b], ['cm0', a], ['cm1', b]].forEach(([k, v]) => { var e = document.querySelector(r + ' input[data-r=' + k + ']'); e.value = v;
      e.dispatchEvent(new Event('input', { bubbles: true })); e.dispatchEvent(new Event('change', { bubbles: true })); })""", [root, a, b])
def an(pg): return pg.evaluate('window.__ffAnalysis()')
def lit_pct(pg):
    m = re.search(r'Tänt: (<?\d+) %', pg.inner_text('#anResult')); return int(m.group(1).replace('<', '')) if m else None
def pixels(pg, test):
    return pg.evaluate("""(t) => { var c = document.getElementById('anLayer'), d = c.getContext('2d').getImageData(0, 0, c.width, c.height).data, n = 0;
      for (var i = 0; i < d.length; i += 4){ var r = d[i], g = d[i + 1], b = d[i + 2], a = d[i + 3];
        if (t === 'green' ? (g > 120 && g > r + 40 && g > b + 40 && a > 60) : t === 'red' ? (r > 180 && g < 120 && b < 100 && a > 120) : false) n++; } return n; }""", test)

with sync_playwright() as p:
    b, ctx, pg, errs = new_page(p, geo=B3, cfg={}, name='Filip')
    pg.wait_for_timeout(2000)
    # made-up catches: 25 gädda where it's 2-3 m deep (a clear pattern), 3 abborre anywhere
    pts = pg.evaluate("""() => { var out = [], deep = [];
      for (var la = 58.884; la < 58.892; la += 0.00018) for (var lo = 15.765; lo < 15.790; lo += 0.00035){
        var d = __ffGeo.depthAt(la, lo); if (d != null && d >= 2.1 && d <= 2.9) out.push([la, lo]); else if (d != null && d > 6) deep.push([la, lo]); }
      return { shallow: out, deep: deep }; }""")
    sh = pts['shallow'][::max(1, len(pts['shallow']) // 25)][:25]
    t0 = calendar.timegm((2026, 9, 26, 8, 0, 0)) * 1000
    rows = [[t0 + i * 60000, 'regnaren1', 'P%d' % i, 'gadda', 60 + i, la, lo] for i, (la, lo) in enumerate(sh)]
    rows += [[t0 + (50 + i) * 60000, 'regnaren1', 'Q%d' % i, 'abborre', 30, la, lo] for i, (la, lo) in enumerate(pts['deep'][:3])]
    ctx.api.heatmap = [fakefb.api_row(*r) for r in rows]
    pg.evaluate("document.getElementById('ctFetch').click()"); pg.wait_for_timeout(600)   # (Inställningar -> Fångstdata -> Hämta nu)
    check('made-up catches: 25 gädda at 2-3 m', len(sh) == 25, len(sh))
    pg.click('#anBtn'); pg.wait_for_timeout(1500)
    pg.click('#anCatSeg button[data-cat="data"]'); pg.wait_for_timeout(300)
    chips = pg.eval_on_selector_all('#anDataChips button', 'e => e.map(x => [x.textContent, x.disabled])')
    check('Kartanalys: "Från fångsterna (data)" -- Abborre 3 (för få, can\'t be chosen), Gädda 25, Gös 0',
          pg.is_visible('#anDataChips') and chips == [['Abborre 3 · för få', True], ['Gädda 25', False], ['Gös 0 · för få', True]], chips)
    pg.click('#anDataChips button[data-m="c_gadda"]'); pg.wait_for_timeout(2500)
    a = an(pg); res = pg.inner_text('#anResult')
    check('Gädda (data): what stands out, incl. the depth (averaged within 25 m: "…–3 m")', a['mode'] == 'c_gadda' and a['ready'] and 'Gädda togs oftast' in res and re.search(r'\d–3 m', res), res)
    size(pg, '#anControls', 70, 130); pg.wait_for_timeout(1500)
    check('Storlek in Från fångsterna: minst 70 cm -> 15 gäddor (the button counts them too; abborre keeps its own range: still 3)', 'Gädda togs oftast' in pg.inner_text('#anResult') and 'Gädda 15' in pg.inner_text('#anDataChips') and 'Abborre 3' in pg.inner_text('#anDataChips'), (pg.inner_text('#anDataChips'), pg.inner_text('#anResult')[:200]))
    size(pg, '#anControls', 80, 130); pg.wait_for_timeout(1500)
    check('...minst 80 cm -> 5: too few', 'För få fångster' in pg.inner_text('#anResult'), pg.inner_text('#anResult')[:200])
    size(pg, '#anControls', 0, 130); pg.wait_for_timeout(2000)
    l7 = lit_pct(pg)
    check('...the data decides how much is lit: "Tänt: x % av sjön – där togs 7 av 10 gäddor" + how clear', l7 is not None and '7 av 10 gäddor' in res and ('mönster' in res), res)
    check('...lit in the species\' colour (green), the catches as dots', pixels(pg, 'green') > 300, pixels(pg, 'green'))
    dots = pg.eval_on_selector_all('#anCF button', 'e => e.map(x => x.textContent)')
    check('each value with dots (how much it alone points gädda out here), at least one ●●●', len(dots) == 6 and all(re.search('[●○]{3}', d) for d in dots) and any('●●●' in d for d in dots), dots)
    pg.screenshot(path='shot_ancatch_area.png')
    def cov(v):
        pg.evaluate("(v) => { var e = document.getElementById('anCCov'); e.value = v; e.dispatchEvent(new Event('input', { bubbles: true })); }", v); pg.wait_for_timeout(1500)
        return lit_pct(pg)
    l5, l9 = cov(5), cov(9)
    pg.click('#anPanel .pnInfoBtn'); pg.wait_for_timeout(300)
    check('"Typiskt" 5 of 10: smaller; 9 of 10: bigger (described behind ⓘ)', l5 <= l7 <= l9 and l5 < l9 and 'udda fångster' in pg.inner_text('#anPanel .pnInfo'), (l5, l7, l9))
    pg.click('#anPanel .pnInfoBtn'); pg.wait_for_timeout(300)
    cov(7)
    for k in ['s', 'h', 'v', 'l', 't']: pg.click('#anCF button[data-cf="%s"]' % k); pg.wait_for_timeout(300)
    pg.wait_for_timeout(1200)
    only_d = lit_pct(pg)
    pg.click('#anCF button[data-cf="d"]'); pg.wait_for_timeout(800)
    check('values off (only Djup left): still works; the last one can\'t be switched off', only_d is not None and pg.eval_on_selector('#anCF button[data-cf="d"]', 'e => e.classList.contains("on")'), only_d)
    for k in ['s', 'h', 'v', 'l', 't']: pg.click('#anCF button[data-cf="%s"]' % k); pg.wait_for_timeout(200)
    pg.click('#anCView button[data-cv="grad"]'); pg.wait_for_timeout(2500)
    res = pg.inner_text('#anResult')
    check('"Skala": the whole lake from unlike to most alike (red), no "Typiskt" slider', 'mest likt fångstplatserna' in res and not pg.query_selector('#anCCov') and pixels(pg, 'red') > 100, (res, pixels(pg, 'red')))
    pg.screenshot(path='shot_ancatch_grad.png')
    pg.click('#anCView button[data-cv="area"]'); pg.wait_for_timeout(1500)
    # not together with the heat map
    pg.click('#anClose'); pg.wait_for_timeout(300)
    bb = pg.locator('#mapTypeBtn').bounding_box(); pg.mouse.move(bb['x'] + 20, bb['y'] + 20); pg.mouse.down(); pg.wait_for_timeout(700); pg.mouse.up(); pg.wait_for_timeout(300)
    pg.click('#mapTypePop .hmOpt'); pg.wait_for_timeout(800)
    check('the heat map on: "Från fångsterna" off', pg.evaluate('window.__ffHeat().on') and an(pg)['mode'] is None)
    pg.click('#hmOff'); pg.wait_for_timeout(300)
    check('no page errors', not errs, errs)
    b.close()
print('\n%d/%d passed' % (sum(results), len(results)))
