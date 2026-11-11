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
  docs/land/<id>_v<V>.txt   a byte per cell = height above the lake / step (0-250), 255 = lake; runs of 255 packed
                            (251, count lo, count hi), base64 -- the depth file's format, unpacked by the same code
  lakes/<id>/land.json      file, w, h, step, level (the lake's surface, m above the sea), credit, and the map
                            rectangle it was made for ("geo": tools/build.py leaves a stale one out)
A new map rectangle for a lake (the map chat): run this again. New data for a lake that is already out: V + 1.
"""
import os, sys, json, math, base64, site
if sys.flags.isolated: site.addsitedir(site.getusersitepackages())   # (-I leaves out the user's own packages: they are wanted)
import numpy as np
from scipy.ndimage import map_coordinates

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
V = 1          # in the file's name: the service worker keeps a file for good, new data = a new name
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
    f = g.ravel(); out = bytearray()
    edge = np.flatnonzero(np.diff(np.concatenate(([0], (f == 255).view(np.int8), [0]))))    # where the runs of 255 start and end
    i = 0
    for a, b in zip(edge[::2], edge[1::2]):
        out += f[i:a].tobytes()
        while b - a >= 3: k = min(b - a, 65535); out += bytes((251, k & 255, k >> 8)); a += k
        out += bytes([255] * (b - a)); i = b
    out += f[i:].tobytes()
    return base64.b64encode(bytes(out)).decode()

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
    assert (unpack(pack(g), g.size) == g).all()
    print("check ok: sweref() makes Lantmateriet's own box for the square 652_54; pack/unpack give the same grid back")

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
    # the lake: by the depth grid (255 = land there)
    inlake = unpack(open(os.path.join(ROOT, 'docs', 'lakes', lake, dp['file'])).read().strip(), w * h).reshape(h, w) != 255
    level = float(np.nanmedian(hm[inlake]))                                 # the lake's surface in the height data
    up = np.clip(np.nan_to_num(hm, nan=level) - level, 0, None)
    # ponytail: a byte per cell (0,25 m steps on Regnaren) -- no steps seen on flat ground at Höjd x 8; two bytes if they show
    step = next(s for s in (0.1, 0.25, 0.5, 1, 2, 4, 8) if np.percentile(up[~inlake], 99.9) <= 250 * s)
    g = np.clip(np.round(up / step), 0, 250).astype(np.uint8); g[inlake] = 255
    txt = pack(g)
    assert (unpack(txt, w * h) == g.ravel()).all()                          # what the app unpacks is what was made
    os.makedirs(os.path.join(ROOT, 'docs', 'land'), exist_ok=True)
    name = 'land/%s_v%d.txt' % (lake, V)
    open(os.path.join(ROOT, 'docs', name), 'w', newline='\n').write(txt + '\n')
    json.dump({'file': name, 'w': w, 'h': h, 'step': step, 'level': round(level, 1), 'credit': 'Höjddata: Lantmäteriet',
               'geo': [geo[x] for x in ('zoom', 'originX', 'originY', 'fullW', 'imgW', 'imgH')]},
              open(os.path.join(ROOT, 'lakes', lake, 'land.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
    j, i = np.unravel_index(np.argmax(np.where(inlake, 0, up)), up.shape)
    la, lo = latlon(gx[i], gy[j], geo['zoom'])
    print('%s: %d x %d cells of %.1f m from the %d m level, step %.2f m, lake %.1f m above the sea (%.0f %% of its cells within 0,5 m of that), '
          'highest %.0f m above the lake at %.5f, %.5f, %.0f kB' % (lake, w, h, cell, r, step, level,
          100 * float(np.mean(np.abs(hm[inlake] - level) <= 0.5)), up[j, i], la, lo, len(txt) / 1024))

if __name__ == '__main__':
    if len(sys.argv) < 2: sys.exit(__doc__)
    if sys.argv[1] == 'check': check()
    else:
        for lake in sys.argv[1:]: make(lake, os.environ.get('DEM') or os.path.join(os.path.expanduser('~'), 'Downloads'))
