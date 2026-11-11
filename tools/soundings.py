"""Our own echo sounder logs where Genesis has no depth -- calibrated against Genesis where both have depth.

    py -3 tools/soundings.py <lake> <log> [<log> ...] [--preview <png>]

<log> = NMEA (GGA or RMC positions + DPT/DBT depth) or CSV (lat, lon, depth_m[, time]).
1. Read: each depth goes with the position just before it; DPT = depth below the transducer + its offset
   (water line), DBT = below the transducer only.
2. Clean: jumps faster than 15 m/s (GPS glitches) and points on land (the lake's depth grid: 255) are dropped.
3. Calibrate (Filip: one global adjustment, no inventing): where Genesis also has depth (grid 0-250), the median
   difference Genesis - log is ONE offset for the whole log (transducer depth, water level). It says how much is
   left after that, and how well the log meets Genesis at the seam -- too much = don't trust the log. Nothing is
   smoothed or reshaped to make it fit.
4. Fill: only grid cells with no Genesis depth (252), only within 25 m of a log point (distance-weighted mean
   of the points around) -- Genesis is never changed, nothing far from the log. The points ->
   lakes/<lake>/soundings.json. --preview: before | after in the map's own depth colours. Never lines or numbers.
"""
import sys, os, json, math, base64, csv
from datetime import datetime
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import genesis_render as R
ROOT = R.ROOT
MAX_SPEED = 15.0          # m/s -- faster than any boat here: a GPS glitch

def nmea_deg(v, hemi):
    if not v: return None
    d = int(float(v) / 100); x = d + (float(v) - d * 100) / 60
    return -x if hemi in 'SW' else x

def nmea_time(v):
    return int(v[0:2]) * 3600 + int(v[2:4]) * 60 + float(v[4:]) if v else None

def read_log(path):
    """[(t or None, lat, lon, depth_m)]"""
    out = []
    if path.lower().endswith('.csv'):
        for r in csv.DictReader(open(path, encoding='utf-8-sig')):
            t = r.get('time')
            try: t = datetime.fromisoformat(t.replace('Z', '+00:00')).timestamp() if t else None
            except ValueError: t = None
            out.append((t, float(r['lat']), float(r['lon']), float(r['depth_m'])))
        return out
    pos = None; day = 0; last_t = None; got = {}           # (got: this fix's DPT / DBT -- DPT wins, whatever the order)
    def flush():
        if pos and got: out.append(pos + (got.get('DPT', got.get('DBT')),))
        got.clear()
    for line in open(path, encoding='ascii', errors='ignore'):
        line = line.strip()
        if not line.startswith('$') or '*' not in line: continue
        body, cs = line[1:].split('*', 1)
        c = 0
        for ch in body: c ^= ord(ch)
        try:
            if c != int(cs[:2], 16): continue                 # (broken line)
        except ValueError: continue
        f = body.split(','); kind = f[0][2:]
        if kind == 'GGA' and f[6] not in ('', '0') and f[2]:
            flush()
            t = nmea_time(f[1])
            if last_t is not None and t is not None and t < last_t - 3600: day += 86400   # (past midnight)
            last_t = t; pos = (t + day if t is not None else None, nmea_deg(f[2], f[3]), nmea_deg(f[4], f[5]))
        elif kind == 'RMC' and f[2] == 'A' and pos is None:
            pos = (nmea_time(f[1]), nmea_deg(f[3], f[4]), nmea_deg(f[5], f[6]))
        elif kind == 'DPT' and pos and f[1]:
            got['DPT'] = float(f[1]) + (float(f[2]) if len(f) > 2 and f[2] and float(f[2]) > 0 else 0)
        elif kind == 'DBT' and pos and len(f) > 3 and f[3]:
            got['DBT'] = float(f[3])                          # (below the transducer -- only if there is no DPT)
    flush()
    return out

def depth_grid(lake):
    """the lake's published depth grid: (vals uint8 [h, w], step m, lake.json)"""
    lk = json.load(open(os.path.join(ROOT, 'lakes', lake, 'lake.json'), encoding='utf-8'))
    raw = base64.b64decode(open(os.path.join(ROOT, 'docs', 'lakes', lake, lk['depth']['file'])).read())
    vals = bytearray(); i = 0
    while i < len(raw):
        b = raw[i]
        if b in (251, 253): vals += bytes([255 if b == 251 else 252]) * (raw[i + 1] | raw[i + 2] << 8); i += 3
        else: vals.append(b); i += 1
    D = lk['depth']
    return np.frombuffer(bytes(vals), np.uint8).reshape(D['h'], D['w']), D['step'], lk

def fill(lk, vals, step, lat, lon, cal, R_M=25.0):
    """depth for the grid cells with no Genesis depth (252) within R_M metres of a log point: distance-weighted
    mean of the points around -- far from the log nothing is filled (no guessing)"""
    from scipy.spatial import cKDTree
    h, w = vals.shape; G = lk['geo']; x, y = to_cell(lk, lat, lon)
    px = np.c_[x * w / G['imgW'], y * h / G['imgH']]; cell_m = G['metersPerPx'] * G['imgW'] / w; r = R_M / cell_m
    gy, gx = np.where(vals == 252); q = np.c_[gx + .5, gy + .5]
    tr = cKDTree(px); dist, idx = tr.query(q, k=8, distance_upper_bound=r)
    ok = np.isfinite(dist[:, 0])
    wgt = np.where(np.isfinite(dist), 1 / np.maximum(dist, 0.3) ** 2, 0)
    idx = np.where(np.isfinite(dist), idx, 0)
    dep = (wgt * cal[idx]).sum(1) / np.maximum(wgt.sum(1), 1e-9)
    out = np.full(vals.shape, np.nan, np.float32); out[gy[ok], gx[ok]] = dep[ok]
    return out

def edge_genesis(filled, gen):
    """for the filled cells next to a Genesis cell (4 neighbours): the neighbours' mean Genesis depth, else nan"""
    s = np.zeros_like(gen); c = np.zeros_like(gen)
    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        g = np.roll(np.roll(gen, dy, 0), dx, 1); ok = np.isfinite(g)
        s += np.where(ok, g, 0); c += ok
    e = np.where(np.isfinite(filled) & (c > 0), s / np.maximum(c, 1), np.nan)
    return e

def seam_stats(filled, gen):
    e = edge_genesis(filled, gen); m = np.isfinite(e)
    if not m.any(): return 'no filled cell touches Genesis'
    d = filled[m] - e[m]
    return '%d edge cells, log - Genesis: median %+.2f m, mean |diff| %.2f m, 90 %% within %.2f m, max %.2f m' % (
        m.sum(), np.median(d), np.abs(d).mean(), np.percentile(np.abs(d), 90), np.abs(d).max())

def to_cell(lk, lat, lon):
    G = lk['geo']; n = 256 * 2 ** G['zoom']; k = G['imgW'] / G['fullW']
    x = ((lon + 180) / 360 * n - G['originX']) * k
    y = ((1 - np.log(np.tan(np.radians(lat)) + 1 / np.cos(np.radians(lat))) / math.pi) / 2 * n - G['originY']) * k
    return x, y                                             # (map picture px)

def own_grid(lake, md):
    """an own depth grid (Filip's own logging, already made into a grid: regnaren.md -- Web Mercator, OX/OY at
    zoom 18, PX z18 px per cell, zlib + base64 bytes, 0-250 = byte x STEP m, 255 = land) -> lakes/<lake>/raw/
    own_depth.npz at zoom 17 px (depth m float16, nan = land) for genesis_render.py, which fills the parts of the
    lake Genesis has no depth for with it (Genesis always on top)"""
    import re, zlib
    txt = open(md, encoding='utf-8').read()
    num = lambda k: float(re.search(r'\b%s\s*=\s*([\d.]+)' % k, txt).group(1))
    OX, OY, PX = int(num('OX')), int(num('OY')), int(num('PX'))
    rows, cols = (int(v) for v in re.search(r'reshape\((\d+),\s*(\d+)\)', txt).groups())
    step = float(re.search(r'g\s*\*\s*([\d.]+)', txt).group(1))
    g = np.frombuffer(zlib.decompress(base64.b64decode(''.join(txt.split('```base64', 1)[1].split('```', 1)[0].split()))), np.uint8).reshape(rows, cols)
    f = 2.0 ** (18 - 17) / PX                                # z17 px per cell
    if f != 1: raise SystemExit('expected one cell = one zoom-17 px (PX = 2 at zoom 18), got PX = %d' % PX)
    dep = np.where(g <= 250, g * step, np.nan).astype(np.float16)
    p = os.path.join(ROOT, 'lakes', lake, 'raw', 'own_depth.npz')
    np.savez_compressed(p, dep=dep, zoom=17, origin=np.array([OX // 2, OY // 2]))
    print('own grid %d x %d (%.1f M cells with depth, 0-%.2f m) -> %s' % (cols, rows, np.isfinite(dep).sum() / 1e6, np.nanmax(dep.astype(np.float32)), p))

def main(argv):
    if argv[1:2] == ['--grid']: return own_grid(argv[0], argv[2])
    preview = None
    if '--preview' in argv: i = argv.index('--preview'); preview = argv[i + 1]; argv = argv[:i] + argv[i + 2:]
    lake, logs = argv[0], argv[1:]
    pts = [p for f in logs for p in read_log(f)]
    print('%d depths read from %d file(s)' % (len(pts), len(logs)))
    lat = np.array([p[1] for p in pts]); lon = np.array([p[2] for p in pts]); dep = np.array([p[3] for p in pts])
    # clean: GPS jumps
    mx = 111320 * math.cos(math.radians(float(np.median(lat)))); keep = dep > 0.2
    ts = [p[0] for p in pts]
    if all(isinstance(t, (int, float)) for t in ts):
        t = np.array(ts, float); dt = np.maximum(np.diff(t), 1e-3)
        sp = np.hypot(np.diff(lon) * mx, np.diff(lat) * 110540) / dt
        jump = np.concatenate([[False], (sp > MAX_SPEED) & (dt < 30)]); keep &= ~jump
        print('  %d GPS jumps dropped' % jump.sum())
    vals, step, lk = depth_grid(lake)
    x, y = to_cell(lk, lat, lon); h, w = vals.shape; G = lk['geo']
    cx = (x * w / G['imgW']).astype(int); cy = (y * h / G['imgH']).astype(int)
    inside = (cx >= 0) & (cy >= 0) & (cx < w) & (cy < h); keep &= inside
    v = np.where(inside, vals[np.clip(cy, 0, h - 1), np.clip(cx, 0, w - 1)], 255)
    land = keep & (v == 255); keep &= v != 255
    print('  %d on land dropped (GPS off, or the lake outline)' % land.sum())
    both = keep & (v <= 250)
    if both.sum() < 50: raise SystemExit('only %d points where Genesis has depth too -- too few to calibrate' % both.sum())
    diff = v[both] * step - dep[both]; off = float(np.median(diff)); res = np.abs(diff - off)
    cal = np.maximum(dep + off, 0.1)
    print('calibration on %d points: ONE offset for the whole log %+.2f m (transducer depth, water level); left after it: '
          'mean %.2f m, 90 %% within %.2f m' % (both.sum(), off, res.mean(), np.percentile(res, 90)))
    if np.percentile(res, 90) > 0.5:
        print('  WARNING: the log does not follow Genesis (90 % > 0.5 m) -- check the log before using it')
    nogen = keep & (v == 252)
    cells = {}
    for i in np.where(nogen)[0]:
        cells.setdefault((cy[i], cx[i]), []).append(i)
    out = [[round(float(lat[ix].mean()), 6), round(float(lon[ix].mean()), 6), round(float(cal[ix].mean()), 2)] for ix in (np.array(c) for c in cells.values())]
    p = os.path.join(ROOT, 'lakes', lake, 'soundings.json')
    json.dump({'offset_m': round(off, 2), 'fit_90_m': round(float(np.percentile(res, 90)), 2), 'points': out}, open(p, 'w', encoding='utf-8'))
    print('%d points where Genesis has no depth -> %d cells -> %s' % (nogen.sum(), len(out), p))
    filled = fill(lk, vals, step, lat[keep], lon[keep], cal[keep])
    print('filled %d grid cells without Genesis depth (of %d)' % (np.isfinite(filled).sum(), (vals == 252).sum()))
    gen = np.where(vals <= 250, vals * step, np.nan).astype(np.float32)
    print('seam vs Genesis (not smoothed -- shows how well the log fits): ' + seam_stats(filled, gen))
    e = edge_genesis(filled, gen); m = np.isfinite(e)
    if m.any() and np.percentile(np.abs(filled[m] - e[m]), 90) > 0.5:
        print('  WARNING: the log and Genesis disagree at the seam (90 % > 0.5 m) -- it will show on the map')
    if preview: draw_preview(lk, lake, lat[keep], lon[keep], filled, preview)

def draw_preview(lk, lake, lat, lon, filled, path):
    """before | after: the map (Djupfärger) and the same with the filled cells in the map's own depth colours
    (Genesis untouched -- only cells it has no depth for)"""
    im = Image.open(os.path.join(ROOT, 'docs', 'lakes', lake, lk['mapFile'].replace('{style}', 's1'))).convert('RGB')
    a = np.asarray(im.resize(filled.shape[::-1], Image.LANCZOS), np.float32)
    m = np.isfinite(filled); d = np.where(m, filled, 0)[..., None]
    col = R.make_styles(d[..., 0], np.ones(filled.shape, np.float32), 12)[0][5].astype(np.float32)   # (s1)
    b = a.copy(); b[m] = col[m]
    x, y = to_cell(lk, lat, lon); s = filled.shape[1] / lk['geo']['imgW']; x, y = x * s, y * s
    pad = 30; x0, x1 = int(max(0, x.min() - pad)), int(min(a.shape[1], x.max() + pad))
    y0, y1 = int(max(0, y.min() - pad)), int(min(a.shape[0], y.max() + pad))
    K = max(1, int(560 / max(x1 - x0, y1 - y0)))
    def crop(arr): return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).crop((x0, y0, x1, y1)).resize(((x1 - x0) * K, (y1 - y0) * K), Image.NEAREST)
    A, B = crop(a), crop(b); W, H = A.size
    o = Image.new('RGB', (W * 2 + 12, H + 40), (20, 24, 34)); o.paste(A, (0, 40)); o.paste(B, (W + 12, 40))
    dr = ImageDraw.Draw(o)
    try:
        from PIL import ImageFont; fn = ImageFont.truetype('arialbd.ttf', 22)
    except Exception: fn = None
    dr.text((8, 8), 'Idag (bara Genesis)', fill='white', font=fn); dr.text((W + 20, 8), 'Med ekolodet där Genesis saknas', fill='white', font=fn)
    o.save(path); print('preview', path, o.size)

if __name__ == '__main__':
    main(sys.argv[1:])
