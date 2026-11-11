"""Land heights for the 3D map (src/js/73-map3d.js): one file per lake.

    py -3 -I tools/land_height.py <lake> [<lake> ...]        py -3 -I tools/land_height.py check

Source: Lantmäteriet's laser-scanned ground (Markhöjdmodell Nedladdning: 1 m, the ground without the trees, CC BY 4.0
-- "Höjddata: Lantmäteriet" is shown in the view). It comes in 10 km squares, m<N>_<E>.tif of 260 MB each, fetched by
hand with a login (Geotorget; the account needs the permission "Markhöjdmodell Nedladdning", 0 kr): put them in the
folder DEM (the environment variable; else the user's Downloads). Squares that are missing: their links are printed.
A square has ready levels of 1, 2, 4, 8 ... m: only the one just under the output's cell is read, and weighed
bilinearly into the lake's own grid (the depth grid's cells) -- so the app's file is ~1 MB, not 260.
(-I: python's isolated mode, for reading downloaded files. Tried 2026-11-11: the open 30 m data (AWS Terrain Tiles,
EU-DEM/SRTM) -- the tree tops are in it, so the land jumped up in teeth along the shore. Left out.)

Out (nothing of the map chat's is touched -- its tools empty docs/lakes/<id>/ on every render, so the file lies beside):
  docs/land/<id>_v<V>.txt   a byte per cell (0-250): height above the lake = max x (byte / 250)^2 -- fine steps low down,
                            where the shore is (Regnaren: 6 cm at 1 m, 44 cm at the top; linear steps of 1 m showed as
                            stairs on flat ground by a lake with 150 m hills); 255 = lake; 252 = water nobody has charted,
                            beside the charted bottom -- a hole in the 3D map (holes(), below); runs of 255 and of
                            252 packed (251 / 253, count lo, count hi), base64 -- the depth file's packing, unpacked
                            by the same code
  lakes/<id>/land.json      file, w, h, max, level (the lake's surface, m above the sea), credit, and the map
                            rectangle it was made for ("geo": tools/build.py leaves a stale one out)
A new map rectangle for a lake (the map chat): run this again. New data for a lake that is already out: V + 1.
"""
import os, sys, json, math, base64, site
if sys.flags.isolated: site.addsitedir(site.getusersitepackages())   # (-I leaves out the user's own packages: they are wanted)
import numpy as np
from scipy.ndimage import map_coordinates, maximum_filter, minimum_filter, label, binary_opening

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
V = 3          # in the file's name: the service worker keeps a file for good, new data = a new name (1: linear steps; 2: no holes)
WIDE = 30      # m: water nobody has charted is a hole in the 3D map where it is at least this wide ...
SHOAL = 1.0    # m: ...and the charted water beside it is deeper than this (holes())
LM = 'https://dl1.lantmateriet.se/hojd/data/grid/mhm/%d_%d/m%d_%d.tif'

def unpack(b64, n):
    b = base64.b64decode(b64); g = np.empty(n, np.uint8); i = j = 0
    while i < len(b):
        v = b[i]
        if v in (251, 253):
            k = b[i + 1] | b[i + 2] << 8; g[j:j + k] = 255 if v == 251 else 252; j += k; i += 3
        else:
            g[j] = v; j += 1; i += 1
    assert j == n, (j, n)
    return g

def pack(g):
    f = g.ravel(); out = bytearray(); i = 0
    cut = np.concatenate(([0], np.flatnonzero(np.diff(f)) + 1, [f.size]))                   # where the runs of one value start and end
    a0, b0 = cut[:-1], cut[1:]; m = f[a0] >= 252                                             # ...those of 255 (lake) and of 252 (a hole)
    for a, b in zip(a0[m].tolist(), b0[m].tolist()):
        out += f[i:a].tobytes(); v = int(f[a])
        while b - a >= 3: k = min(b - a, 65535); out += bytes((251 if v == 255 else 253, k & 255, k >> 8)); a += k
        out += bytes([v] * (b - a)); i = b
    out += f[i:].tobytes()
    return base64.b64encode(bytes(out)).decode()

def holes(rel, depth, step, cell):
    """-> the cells of water nobody has charted where the 3D map leaves a hole (drawn at the surface they stood as big
    hills beside the charted bottom, Filip 2026-11-12).
    A cell without a depth -- the lake's own (252 in the depth grid: on Regnaren those are islets) or outside the chart
    (255 there: land, or unknown) -- is water by Lantmäteriet's heights when it is planed: the same to the cm as its 8
    neighbours (measured 2026-11-12: 0,000 m on open water in all seven lakes; a low shore, reeds or an islet are not),
    at the lake's level (within 0,5 m: the sea stands differently from one scan to the next) and joined to the lake (a
    pond of its own stays land). Of that water:
    - what is at least WIDE m wide: a narrower strip between the chart and the shore stays as it was (a hole there
      would be a gap along the shore);
    - in pieces with charted water deeper than SHOAL m beside them: a shoal or a reedy bay in shallow water stays as it
      was too, just under the surface -- no hill stands there.
    rel: m above the lake's level; depth: the depth grid (x step = m); cell: m."""
    lake = depth != 255
    water = (depth > 250) & (np.abs(rel) <= 0.5) & (maximum_filter(rel, 3) - minimum_filter(rel, 3) <= 0.02)
    lab, _ = label(water | lake, np.ones((3, 3))); water &= np.isin(lab, np.unique(lab[lake]))
    k = max(3, int(WIDE / cell) | 1)                                                         # (odd: a square with a middle cell)
    lab, n = label(binary_opening(water, np.ones((k, k))), np.ones((3, 3)))                  # the pieces
    near = maximum_filter(lab, 5); at = (depth < 251) & (near > 0); near, d = near[at], depth[at] * step   # the charted cells within 2 cells of a piece
    return np.isin(lab, [p for p in range(1, n + 1) if (near == p).any() and np.percentile(d[near == p], 90) > SHOAL])

def latlon(gx, gy, zoom):            # global px at a zoom (256 px tiles) -> lat, lon (degrees)
    n = 256 * 2 ** zoom
    return np.degrees(np.arctan(np.sinh(math.pi * (1 - 2 * gy / n)))), gx / n * 360 - 180

def sweref(lat, lon):                # degrees -> SWEREF 99 TM (E, N): Krüger's series as Lantmäteriet gives them (GRS 80)
    a, f, k0, lon0 = 6378137.0, 1 / 298.257222101, 0.9996, math.radians(15)
    e2 = f * (2 - f); n = f / (2 - f); ah = a / (1 + n) * (1 + n * n / 4 + n ** 4 / 64)
    A, B, C, D = e2, (5 * e2 ** 2 - e2 ** 3) / 6, (104 * e2 ** 3 - 45 * e2 ** 4) / 120, 1237 * e2 ** 4 / 1260
    beta = (n / 2 - 2 * n * n / 3 + 5 * n ** 3 / 16 + 41 * n ** 4 / 180, 13 * n * n / 48 - 3 * n ** 3 / 5 + 557 * n ** 4 / 1440,
            61 * n ** 3 / 240 - 103 * n ** 4 / 140, 49561 * n ** 4 / 161280)
    phi, dl = np.radians(lat), np.radians(lon) - lon0
    s = np.sin(phi); pc = phi - s * np.cos(phi) * (A + B * s ** 2 + C * s ** 4 + D * s ** 6)        # the conformal latitude
    xi, eta = np.arctan(np.tan(pc) / np.cos(dl)), np.arctanh(np.cos(pc) * np.sin(dl))
    N = k0 * ah * (xi + sum(b * np.sin(2 * i * xi) * np.cosh(2 * i * eta) for i, b in enumerate(beta, 1)))
    E = k0 * ah * (eta + sum(b * np.cos(2 * i * xi) * np.sinh(2 * i * eta) for i, b in enumerate(beta, 1))) + 500000
    return E, N

def check():
    """sweref() against Lantmäteriet's own numbers: their catalogue gives the square 652_54 (E 540000-550000,
    N 6520000-6530000) the lon/lat box below -- its four corners turned back to lat/lon must make that box."""
    box = (15.692587344430855, 58.81701503851668, 15.867958506918225, 58.90786163988046)
    def back(E, N):                  # (the series turned around by stepping)
        lat, lon = N / 111200.0, 15 + (E - 500000) / 60000.0
        for _ in range(12):
            e, n = sweref(lat, lon); lat += (N - n) / 111320.0; lon += (E - e) / (111320.0 * math.cos(math.radians(lat)))
        return lat, lon
    c = [back(E, N) for E in (540000, 550000) for N in (6520000, 6530000)]
    got = (min(p[1] for p in c), min(p[0] for p in c), max(p[1] for p in c), max(p[0] for p in c))
    assert max(abs(a - b) for a, b in zip(got, box)) < 2e-9, (got, box)                 # (2e-9 degrees = 0,2 mm)
    g = np.random.default_rng(1).integers(0, 251, 5000).astype(np.uint8); g[100:104] = 255; g[2000:4000] = 255; g[-1] = 255; g[7] = 255
    g[300:900] = 252; g[4000:4002] = 252                                                # (holes: right after a run of lake, too)
    assert (unpack(pack(g), g.size) == g).all()
    # holes() on a toy map of 10 m cells (a hole = at least 3 cells wide) and depth steps of 0,3 m: rough land, in it a
    # lake that is flat at level 0 and charted, 12 m deep
    d = np.full((60, 90), 255, np.uint8); rel = np.random.default_rng(2).uniform(0.6, 3, d.shape)
    d[10:40, 10:30] = 40; rel[10:40, 10:30] = 0
    d[10:20, 20:30] = 252                               # a wide bay of it nobody has charted                      -> a hole (but for its shore cells)
    d[22:38, 10:12] = 252                               # ...and a strip of two cells along its shore              -> left as it is
    d[29:39, 18:28] = 2; d[31:37, 20:26] = 252          # a patch nobody has charted in 0,6 m of water: a shoal    -> left
    d[24:30, 14:20] = 252; rel[24:30, 14:20] = np.random.default_rng(4).uniform(1, 2, (6, 6))   # an islet the depth grid calls lake -> left
    rel[10:40, 30:50] = 0                               # flat water outside the chart, joined to the lake         -> a hole (but for its shore cells)
    rel[40:42, 10:30] = 0                               # ...a narrow strip of it along the lake                   -> left
    rel[48:56, 60:75] = 0                               # a pond of its own at the lake's level                    -> land
    rel[4:10, 10:20] = -2                               # flat water 2 m lower, next to the lake                   -> land
    rel[22:38, 4:10] = np.random.default_rng(3).uniform(0, 0.3, (16, 6))                # a low, rough shore        -> land
    want = np.zeros(d.shape, bool); want[11:20, 20:30] = True; want[11:39, 30:49] = True
    got = holes(rel, d, 0.3, 10.0)
    assert (got == want).all(), np.argwhere(got != want)[:8]
    print("check ok: sweref() makes Lantmateriet's own box for the square 652_54; pack/unpack give the same grid back; holes() "
          "finds wide water without depth, and nothing else")

def make(lake, dem):
    import tifffile
    lk = json.load(open(os.path.join(ROOT, 'lakes', lake, 'lake.json'), encoding='utf-8'))
    geo, dp = lk['geo'], lk['depth']
    fw = geo['fullW']; fh = geo['imgH'] * fw / geo['imgW']                 # the map picture in its own zoom's px
    w, h = dp['w'], dp['h']; cell = geo['metersPerPx'] * fw / w            # the depth grid's own cells
    gx = geo['originX'] + (np.arange(w) + 0.5) * fw / w; gy = geo['originY'] + (np.arange(h) + 0.5) * fh / h   # their middles, global px
    lat, lon = latlon(*np.meshgrid(gx, gy), geo['zoom']); E, N = sweref(lat, lon)
    sq = (N // 10000).astype(int) * 1000 + (E // 10000).astype(int)        # (a square is named by its south-west corner / 10 km)
    need = [divmod(int(s), 1000) for s in np.unique(sq)]
    missing = [(n, e) for n, e in need if not os.path.exists(os.path.join(dem, 'm%d_%d.tif' % (n, e)))]
    if missing:
        print('%s: %d of its %d squares are not in %s -- nothing made. Fetch (a login is asked for):' % (lake, len(missing), len(need), dem))
        for n, e in missing: print('   ' + LM % (n // 10, e // 10, n, e))
        return
    hm = np.full(E.shape, np.nan)
    for n, e in need:
        m = sq == n * 1000 + e
        with tifffile.TiffFile(os.path.join(dem, 'm%d_%d.tif' % (n, e))) as t:
            lv = [l for l in t.series[0].levels if 10000 / l.shape[0] <= cell][-1]      # the level just under the cell: 1, 2, 4, 8 m ...
            r = 10000 / lv.shape[0]; a = lv.asarray().astype(np.float64)
            tp = t.pages[0].tags['ModelTiepointTag'].value                               # (.., E of its left edge, N of its top edge, ..)
        a[a < -9000] = np.nan                                                            # (no data, e.g. open sea)
        hm[m] = map_coordinates(a, [(tp[4] - N[m]) / r - 0.5, (E[m] - tp[3]) / r - 0.5], order=1, mode='nearest')
    # the lake: by the depth grid (255 = land there, or unknown)
    depth = unpack(open(os.path.join(ROOT, 'docs', 'lakes', lake, dp['file'])).read().strip(), w * h).reshape(h, w); inlake = depth != 255
    level = float(np.nanmedian(hm[inlake]))                                 # the lake's surface in the height data
    rel = np.nan_to_num(hm, nan=level) - level; hole = holes(rel, depth, dp['step'], cell)
    up = np.clip(rel, 0, None)
    mx = math.ceil(float(up[~inlake].max()))                                # ponytail: a byte per cell, square-root steps; two bytes if stairs still show
    g = np.clip(np.round(250 * np.sqrt(up / mx)), 0, 250).astype(np.uint8); g[inlake] = 255; g[hole] = 252
    txt = pack(g)
    assert (unpack(txt, w * h) == g.ravel()).all()                          # what the app unpacks is what was made
    os.makedirs(os.path.join(ROOT, 'docs', 'land'), exist_ok=True)
    for old in range(1, V): old = os.path.join(ROOT, 'docs', 'land', '%s_v%d.txt' % (lake, old)); os.path.exists(old) and os.remove(old)
    name = 'land/%s_v%d.txt' % (lake, V)
    open(os.path.join(ROOT, 'docs', name), 'w', newline='\n').write(txt + '\n')
    json.dump({'file': name, 'w': w, 'h': h, 'max': mx, 'level': round(level, 1), 'credit': 'Höjddata: Lantmäteriet',
               'geo': [geo[x] for x in ('zoom', 'originX', 'originY', 'fullW', 'imgW', 'imgH')]},
              open(os.path.join(ROOT, 'lakes', lake, 'land.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
    j, i = np.unravel_index(np.argmax(np.where(inlake, 0, up)), up.shape)
    la, lo = latlon(gx[i], gy[j], geo['zoom'])
    print('%s: %d x %d cells of %.1f m from the %d m level, steps of %.2f m at 1 m and %.2f m at the top, lake %.1f m above the sea (%.0f %% of its '
          'cells within 0,5 m of that), highest %.0f m above the lake at %.5f, %.5f, %.0f kB' % (lake, w, h, cell, r, 2 * math.sqrt(mx) / 250, 2 * mx / 250,
          level, 100 * float(np.mean(np.abs(hm[inlake] - level) <= 0.5)), up[j, i], la, lo, len(txt) / 1024))
    print('   holes (water nobody has charted, %d m wide or more, beside charted water deeper than %g m): %.1f %% of what the depth grid calls land -- water outside the chart -- and %.0f %% of '
          "the lake's own cells without a depth (which are %.1f %% of the lake)" % (WIDE, SHOAL, 100 * float(hole[~inlake].mean()),
          100 * float(hole[depth == 252].mean()) if (depth == 252).any() else 0, 100 * float((depth == 252).sum()) / inlake.sum()))

if __name__ == '__main__':
    if len(sys.argv) < 2: sys.exit(__doc__)
    if sys.argv[1] == 'check': check()
    else:
        for lake in sys.argv[1:]: make(lake, os.environ.get('DEM') or os.path.join(os.path.expanduser('~'), 'Downloads'))
