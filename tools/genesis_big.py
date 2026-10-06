"""Big lakes (Mälaren): the same maps as genesis_depth.py + genesis_render.py, but worked out in blocks
(4096 x 4096 px at the depth data's zoom) so memory stays small, and only inside the lake's polygon
("clip" in source.json). Reads the Genesis tiles straight from raw/<lake>/z<z>/<layer>/ (never stitched --
too big). tools/PLAN_KARTFORMAT.md.

    py -3 tools/genesis_big.py <lake> colours     every Genesis depth colour in the polygon, ranked shallow -> deep
    py -3 tools/genesis_big.py <lake> sheet       labels_sheet.png + lakes/<lake>/raw/depth_labels.json to fill in
    py -3 tools/genesis_big.py <lake> depth       depth per block (raw/<lake>/z<DZ>/depth/<bx>_<by>.npz)
    py -3 tools/genesis_big.py <lake> relief      relief (T1, AO) per block + the lake-wide brightness scale
    py -3 tools/genesis_big.py <lake> render [k/n] pictures, pieces, depth/bottom grid, lake.json (k/n: every
                                                  n-th block from k -- several side by side, then once without)
"""
import sys, os, json, math, base64, shutil
from functools import lru_cache
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import genesis_render as R
import genesis_depth as GD
import genesis_tiles as GT
import osm_water
Image.MAX_IMAGE_PIXELS = None
ROOT = R.ROOT; TL = R.TL; PAD = R.PAD

def gpx(lat, lon, z):
    n = 256 * 2 ** z
    return ((lon + 180) / 360 * n, (1 - math.log(math.tan(math.radians(lat)) + 1 / math.cos(math.radians(lat))) / math.pi) / 2 * n)

class Lake:
    def __init__(self, lake):
        self.id = lake
        self.L = os.path.join(ROOT, 'lakes', lake)
        src = self.src = json.load(open(os.path.join(self.L, 'raw', 'source.json'), encoding='utf-8'))
        self.DZ = src['zoom']; self.levels = sorted(src['levels']); self.base = self.levels[0]
        self.BS = src.get('blocks', 4096); self.V = src.get('version', 1)
        la0, la1, lo0, lo1 = src['bbox']
        x0, y0 = gpx(la1, lo0, self.DZ); x1, y1 = gpx(la0, lo1, self.DZ)
        m = 2 ** (self.DZ - self.base)
        self.gx0, self.gy0 = int(x0 // m) * m, int(y0 // m) * m          # (whole px at every level)
        self.nbx = int(math.ceil((x1 - self.gx0) / self.BS)); self.nby = int(math.ceil((y1 - self.gy0) / self.BS))
        self.W, self.H = self.nbx * self.BS, self.nby * self.BS
        self.D = os.path.join(ROOT, 'raw', lake, 'z%d' % self.DZ)
        self.poly = json.load(open(os.path.join(ROOT, src['clip']), encoding='utf-8'))['polygon_latlon']
        self.latc = (la0 + la1) / 2
        self.PXD = 156543.03392 * math.cos(math.radians(self.latc)) / 2 ** self.DZ
        # blocks that touch the polygon (+ 1 block round it, for the margins)
        cm = self.clip_mask(self.DZ, 0, 0, self.W, self.H, step=self.BS // 64)
        bm = cm.reshape(self.nby, 64, self.nbx, 64).any(axis=(1, 3))
        self.blocks = [(bx, by) for by in range(self.nby) for bx in range(self.nbx) if bm[by, bx]]
        print('%s: %d x %d px at z%d, %d of %d blocks in the polygon' % (lake, self.W, self.H, self.DZ, len(self.blocks), self.nbx * self.nby))

    def clip_mask(self, z, X0, Y0, w, h, step=1):
        """polygon as bool array over a rect (level-z px, relative to the crop origin), every `step` px"""
        f = 2 ** (self.DZ - z)
        ox, oy = self.gx0 / f + X0, self.gy0 / f + Y0
        im = Image.new('L', (int(math.ceil(w / step)), int(math.ceil(h / step))), 0)
        ImageDraw.Draw(im).polygon([((gpx(a, b, z)[0] - ox) / step, (gpx(a, b, z)[1] - oy) / step) for a, b in self.poly], fill=1, outline=1)
        return np.array(im, bool)

@lru_cache(maxsize=1200)
def _tile(path, mode):
    try: return np.array(Image.open(path).convert(mode))
    except Exception: return None

def read(lake, z, layer, X, Y, w, h):
    """level-z pixels [X, X+w) x [Y, Y+h) (global px) of a Genesis layer from the cached tiles; missing = 0"""
    mode = 'RGB' if layer == 'a' else 'RGBA'
    out = np.zeros((h, w, len(mode)), np.uint8)
    d = os.path.join(ROOT, 'raw', lake, 'z%d' % z, layer); ext = '.jpg' if layer == 'a' else '.png'
    for ty in range(Y // 256, (Y + h - 1) // 256 + 1):
        for tx in range(X // 256, (X + w - 1) // 256 + 1):
            t = _tile(os.path.join(d, GT.quadkey(tx, ty, z) + ext), mode)
            if t is None: continue
            sx0, sy0 = max(X, tx * 256), max(Y, ty * 256); sx1, sy1 = min(X + w, tx * 256 + 256), min(Y + h, ty * 256 + 256)
            out[sy0 - Y:sy1 - Y, sx0 - X:sx1 - X] = t[sy0 - ty * 256:sy1 - ty * 256, sx0 - tx * 256:sx1 - tx * 256]
    return out

def close_seams(B):
    """Genesis' 1-2 px transparent seams between its data blocks, closed with the neighbour's colour"""
    water = B[..., 3] > 200
    for axis in (0, 1):
        dry = ~water
        s1 = dry & np.roll(water, 1, axis) & np.roll(water, -1, axis)
        s2a = dry & np.roll(dry, -1, axis) & np.roll(water, 1, axis) & np.roll(water, -2, axis)
        for s in (s1, s2a, np.roll(s2a, 1, axis)):
            B[s] = np.roll(B, 1, axis)[s]; water |= s
    return B, water

def keys_of(B): c = B[..., :3].astype(np.int32); return (c[..., 0] << 16) | (c[..., 1] << 8) | c[..., 2]

# ---------------------------------------------------------------- colours
def colours(lk):
    """every depth colour in the polygon's b tiles at DZ, ranked like genesis_depth.load (G desc, then R desc)"""
    d = os.path.join(lk.D, 'b'); cnt = {}
    for f in os.listdir(d):
        if not f.endswith('.png'): continue
        a = _tile(os.path.join(d, f), 'RGBA')
        if a is None: continue
        k = keys_of(a)[a[..., 3] > 200]
        u, n = np.unique(k, return_counts=True)
        for kk, nn in zip(u.tolist(), n.tolist()): cnt[kk] = cnt.get(kk, 0) + nn
    u = np.array(sorted(cnt), np.int64)
    order = np.lexsort((-(u >> 16), -((u >> 8) & 255)))
    ranked = u[order].tolist()
    json.dump({'keys': ranked, 'counts': [cnt[k] for k in ranked]}, open(os.path.join(lk.D, 'colours.json'), 'w'))
    print('%d colours (%d with >= 1000 px)' % (len(ranked), sum(1 for k in ranked if cnt[k] >= 1000)))

def rank_lookup(lk):
    c = json.load(open(os.path.join(lk.D, 'colours.json')))
    keys = np.array(c['keys'], np.int64); srt = np.argsort(keys)
    def idx_of(B, water):
        k = keys_of(B).astype(np.int64); pos = np.clip(np.searchsorted(keys[srt], k), 0, len(keys) - 1)
        ok = water & (keys[srt][pos] == k)
        out = np.full(k.shape, -1, np.int32); out[ok] = srt[pos[ok]]
        return out
    return idx_of, len(keys)

def block_rect(lk, bx, by, margin):
    """global DZ px of a block + margin"""
    return lk.gx0 + bx * lk.BS - margin, lk.gy0 + by * lk.BS - margin, lk.BS + 2 * margin, lk.BS + 2 * margin

# ---------------------------------------------------------------- the sheet of depth labels to read
def sheet(lk):
    idx_of, ncol = rank_lookup(lk)
    cands = []
    for bx, by in lk.blocks:
        X, Y, w, h = block_rect(lk, bx, by, 16)
        B, water = close_seams(read(lk.id, lk.DZ, 'b', X, Y, w, h)); T = read(lk.id, lk.DZ, 't', X, Y, w, h)
        if not water.any(): continue
        idx = idx_of(B, water); bl, objs = GD.label_blobs(T)
        for i, sl in enumerate(objs, 1):
            if sl is None: continue
            hh, ww = sl[0].stop - sl[0].start, sl[1].stop - sl[1].start
            cy, cx = (sl[0].start + sl[0].stop) // 2, (sl[1].start + sl[1].stop) // 2
            if not (10 <= hh <= 40 and 10 <= ww <= 40) or not (16 <= cx < 16 + lk.BS and 16 <= cy < 16 + lk.BS): continue
            v = GD.ring_colour(idx, bl, i, sl)
            if v.size < 20 or v.max() - v.min() > 2: continue
            cands.append((int(np.median(v)), Y + cy, X + cx))
        print('  block %d,%d: %d candidates so far' % (bx, by, len(cands)), end='\r')
    rng = np.random.RandomState(0); pick = []
    for lo in range(0, ncol, 3):
        g = [c for c in cands if lo <= c[0] < lo + 3]; rng.shuffle(g); pick += g[:int(os.environ.get('FF_PER', 4))]
    cell, cols = 96, 10; rows = (len(pick) + cols - 1) // cols
    im = Image.new('RGB', (cols * cell, rows * (cell + 14)), 'white'); dr = ImageDraw.Draw(im)
    for k, (ci, gy, gx) in enumerate(pick):
        b = Image.fromarray(read(lk.id, lk.DZ, 'b', gx - 24, gy - 24, 48, 48)); b.alpha_composite(Image.fromarray(read(lk.id, lk.DZ, 't', gx - 24, gy - 24, 48, 48)))
        X, Y = (k % cols) * cell, (k // cols) * (cell + 14)
        im.paste(b.convert('RGB').resize((cell, cell), Image.LANCZOS), (X, Y + 14)); dr.text((X + 2, Y + 1), '#%d' % k, fill=(200, 0, 0))
    im.save(os.path.join(lk.D, 'labels_sheet.png'))
    out = os.path.join(lk.L, 'raw', 'depth_labels.json')
    if not os.path.exists(out):
        json.dump({'zoom': lk.DZ, 'global': True, 'labels': [{'id': k, 'gx': gx, 'gy': gy, 'colour_index': ci, 'depth_m': None}
                                                             for k, (ci, gy, gx) in enumerate(pick)]}, open(out, 'w'), indent=1)
    print('\n%d candidates, %d on the sheet -> %s; fill in depth_m in %s' % (len(cands), len(pick), os.path.join(lk.D, 'labels_sheet.png'), out))

# ---------------------------------------------------------------- depth (genesis_depth.build, per block)
def colour_table(lk, idx_of, ncol):
    labels = json.load(open(os.path.join(lk.L, 'raw', 'depth_labels.json')))['labels']
    pts = []
    for l in labels:
        if l['depth_m'] is None: continue
        X, Y = l['gx'] - 64, l['gy'] - 64
        B, water = close_seams(read(lk.id, lk.DZ, 'b', X, Y, 128, 128)); T = read(lk.id, lk.DZ, 't', X, Y, 128, 128)
        idx = idx_of(B, water); bl, objs = GD.label_blobs(T)
        win = bl[61:68, 61:68]; ids = win[win > 0]
        if not ids.size: continue
        i = int(np.bincount(ids).argmax()); v = GD.ring_colour(idx, bl, i, objs[i - 1])
        if v.size >= 20: pts.append((int(np.median(v)), l['depth_m']))
    xs = np.arange(ncol)
    ci = np.array([p[0] for p in pts]); dm = np.array([p[1] for p in pts], float)
    have = sorted(set(ci.tolist()))
    med = np.array([np.median(dm[ci == k]) for k in have]); wt = np.array([(ci == k).sum() for k in have], float)
    med = GD.isotonic(med, wt)
    table = np.interp(xs, have, med)
    if have[-1] < ncol - 1:
        slope = (med[-1] - med[max(0, len(med) - 6)]) / max(1, have[-1] - have[max(0, len(have) - 6)])
        table[have[-1]:] = np.minimum(med[-1] + slope * (xs[have[-1]:] - have[-1]), med[-1] + 1.0)
    if have[0] > 0:
        table[:have[0]] = np.maximum(0.25, med[0] - (have[0] - xs[:have[0]]) * 0.5)
    with open(os.path.join(lk.D, 'depth_calib.txt'), 'w') as f:
        for i in range(ncol): f.write('%2d %6.2f m\n' % (i, table[i]))
    print('colour table: %d colours, %.2f .. %.2f m (%d label readings)' % (ncol, table[0], table[-1], len(pts)))
    return table, labels

def depth(lk, shard=None):
    sk, sn = shard or (0, 1)
    idx_of, ncol = rank_lookup(lk)
    table, labels = colour_table(lk, idx_of, ncol)
    edges = np.concatenate([[0.0], (table[:-1] + table[1:]) / 2, [table[-1] + 0.75]])
    out = os.path.join(lk.D, 'depth'); os.makedirs(out, exist_ok=True)
    MG = 640
    for n, (bx, by) in enumerate(lk.blocks):
        if n % sn != sk or os.path.exists(os.path.join(out, '%d_%d.npz' % (bx, by))): continue   # (done in an earlier run)
        X, Y, w, h = block_rect(lk, bx, by, MG)
        B, water = close_seams(read(lk.id, lk.DZ, 'b', X, Y, w, h))
        if not water[MG:-MG, MG:-MG].any():
            np.savez_compressed(os.path.join(out, '%d_%d.npz' % (bx, by)), dep=np.zeros((lk.BS, lk.BS), np.float16), water=np.zeros((lk.BS, lk.BS), bool)); continue
        idx = idx_of(B, water); water = idx >= 0; del B
        holes = ndimage.binary_fill_holes(water) & ~water
        ih = idx[::2, ::2]; land_h = (~(water | holes))[::2, ::2]
        dh = np.zeros(ih.shape, np.float32); M = 150
        for i in np.unique(ih[ih >= 0]).tolist():
            m = ih == i
            ys, xs = np.where(m)
            y0, y1 = max(0, ys.min() - M), min(ih.shape[0], ys.max() + M + 1); x0, x1 = max(0, xs.min() - M), min(ih.shape[1], xs.max() + M + 1)
            sub = ih[y0:y1, x0:x1]
            up = ((sub >= 0) & (sub < i)) | land_h[y0:y1, x0:x1]; dn = sub > i
            du = ndimage.distance_transform_edt(~up) if up.any() else np.full(sub.shape, 1e4)
            dd = ndimage.distance_transform_edt(~dn) if dn.any() else np.full(sub.shape, 1e4)
            lo, hi = edges[i], (edges[i + 1] if i < ncol else table[-1] + 1.5)
            t = du / (du + dd + 1e-6); mm = m[y0:y1, x0:x1]
            dh[y0:y1, x0:x1][mm] = (lo + (hi - lo) * t)[mm]
        known = ih >= 0
        iy, ix = ndimage.distance_transform_edt(~known, return_distances=False, return_indices=True)
        dh = dh[iy, ix]; del iy, ix
        dep = np.array(Image.fromarray(dh, 'F').resize((w, h), Image.BILINEAR))
        wf = water.astype(np.float32)
        num = ndimage.gaussian_filter(dep * wf, 2.0); den = ndimage.gaussian_filter(wf, 2.0)
        sm = np.where(water, num / np.maximum(den, 1e-6), np.nan).astype(np.float32)[MG:-MG, MG:-MG]
        np.savez_compressed(os.path.join(out, '%d_%d.npz' % (bx, by)) + '.tmp.npz', dep=sm.astype(np.float16), water=water[MG:-MG, MG:-MG])
        os.replace(os.path.join(out, '%d_%d.npz' % (bx, by)) + '.tmp.npz', os.path.join(out, '%d_%d.npz' % (bx, by)))
        print('  depth block %d/%d (%d,%d)' % (n + 1, len(lk.blocks), bx, by), flush=True)
    if shard: return
    maxd = 0
    for bx, by in lk.blocks:
        t = _dblock(os.path.join(out, '%d_%d.npz' % (bx, by)))
        if t is None: raise SystemExit('depth block %d,%d missing' % (bx, by))
        if np.isfinite(t[0]).any(): maxd = max(maxd, float(np.nanmax(t[0])))
    json.dump({'max': maxd}, open(os.path.join(out, 'stats.json'), 'w'))
    err = []
    for l in labels:
        if l['depth_m'] is None: continue
        d0, _ = load_depth(lk, l['gx'] - lk.gx0 - 12, l['gy'] - lk.gy0 - 12, 25, 25)
        if np.isfinite(d0).any(): err.append(np.nanmedian(d0) - l['depth_m'])
    err = np.array(err)
    print('\nvs labels: median error %+.2f m, 90 %% within %.2f m; max depth %.1f m' % (np.median(err), np.percentile(np.abs(err), 90), maxd))

@lru_cache(maxsize=12)
def _dblock(path):
    if not os.path.exists(path): return None
    z = np.load(path); return z['dep'].astype(np.float32), z['water']

def load_depth(lk, X, Y, w, h):
    """depth (nan off the water) + water over crop px [X, X+w) x [Y, Y+h), from the depth blocks"""
    dep = np.full((h, w), np.nan, np.float32); wat = np.zeros((h, w), bool); BS = lk.BS
    for by in range(max(0, Y // BS), min(lk.nby, (Y + h - 1) // BS + 1)):
        for bx in range(max(0, X // BS), min(lk.nbx, (X + w - 1) // BS + 1)):
            t = _dblock(os.path.join(lk.D, 'depth', '%d_%d.npz' % (bx, by)))
            if t is None: continue
            sx0, sy0 = max(X, bx * BS), max(Y, by * BS); sx1, sy1 = min(X + w, bx * BS + BS), min(Y + h, by * BS + BS)
            dep[sy0 - Y:sy1 - Y, sx0 - X:sx1 - X] = t[0][sy0 - by * BS:sy1 - by * BS, sx0 - bx * BS:sx1 - bx * BS]
            wat[sy0 - Y:sy1 - Y, sx0 - X:sx1 - X] = t[1][sy0 - by * BS:sy1 - by * BS, sx0 - bx * BS:sx1 - bx * BS]
    return dep, wat

# ---------------------------------------------------------------- relief: per block, one brightness scale for the lake
RMG = 128      # margin (DZ px) round a block for relief, colours, the pieces' PAD and "near water"

def block_depth(lk, bx, by):
    """depth with the unmapped parts of the OSM lake filled (genesis_render: depc), water, osm -- block + RMG"""
    X, Y = bx * lk.BS - RMG, by * lk.BS - RMG; w = h = lk.BS + 2 * RMG
    dep, water = load_depth(lk, X, Y, w, h)
    dep0 = np.where(water, dep, 0).astype(np.float32)
    osm = osm_water.mask(lk.id, lk.DZ, lk.gx0 + X, lk.gy0 + Y, w, h)
    if osm is None: osm = np.zeros_like(water)
    unm = osm & ~water; depc = dep0
    if unm.any() and water.any():
        iy, ix = ndimage.distance_transform_edt(~water, return_distances=False, return_indices=True)
        depc = dep0.copy(); depc[unm] = dep0[iy[unm], ix[unm]]; del iy, ix
    return dep0, depc, water, osm, unm

def relief_parts(depc, water, px, solid):
    """genesis_render.relief without the last step (the brightness scale): T1 and AO"""
    sol = solid; wf = sol.astype(np.float32); s = max(0.5, 1.2 / px)
    hgt = -np.where(sol, ndimage.gaussian_filter(depc * wf, s) / np.maximum(ndimage.gaussian_filter(wf, s), 1e-6), 0).astype(np.float32)
    EX = 12
    gx = ndimage.sobel(hgt, 1) / (8 * px) * EX; gy = ndimage.sobel(hgt, 0) / (8 * px) * EX
    n = np.sqrt(gx * gx + gy * gy + 1); a, b = math.radians(315), math.radians(45)
    t1 = np.clip((-gx * math.cos(b) * math.sin(a) + gy * math.cos(b) * math.cos(a) + math.sin(b)) / n, 0, 1); del gx, gy, n
    he = hgt * EX; occ = np.zeros_like(hgt)
    steps = sorted(set(max(1, int(round(1.35 ** i))) for i in range(40) if 1.35 ** i * px <= 25.0)) or [1]
    for i in range(16):
        ang = 2 * math.pi * i / 16; best = np.zeros_like(hgt)
        for st in steps:
            best = np.maximum(best, (R.shift(he, int(round(math.sin(ang) * st)), int(round(math.cos(ang) * st))) - he) / (st * px))
        occ += np.sin(np.arctan(best))
    return t1.astype(np.float32), (1 - occ / 16).astype(np.float32)

def relief(lk, shard=None):
    sk, sn = shard or (0, 1)
    out = os.path.join(lk.D, 'relief'); os.makedirs(out, exist_ok=True)
    rng = np.random.RandomState(1)
    for n, (bx, by) in enumerate(lk.blocks):
        p = os.path.join(out, '%d_%d.npz' % (bx, by))
        if n % sn != sk or os.path.exists(p): continue
        dep0, depc, water, osm, unm = block_depth(lk, bx, by)
        if not water.any():
            np.savez_compressed(p + '.tmp.npz', none=np.zeros(1)); os.replace(p + '.tmp.npz', p); continue
        t1, ao = relief_parts(depc, water, lk.PXD, water | unm)
        core = water[RMG:-RMG, RMG:-RMG]; ii = np.flatnonzero(core)
        pick = rng.choice(ii, min(20000, ii.size), replace=False) if ii.size else np.zeros(0, int)
        np.savez_compressed(p + '.tmp.npz', t1=t1.astype(np.float16), ao=ao.astype(np.float16),
                            st=t1[RMG:-RMG, RMG:-RMG].ravel()[pick], sa=ao[RMG:-RMG, RMG:-RMG].ravel()[pick])
        os.replace(p + '.tmp.npz', p)
        print('  relief block %d/%d' % (n + 1, len(lk.blocks)), flush=True)
    if shard: return
    samp_t, samp_a = [], []
    for bx, by in lk.blocks:
        z = np.load(os.path.join(out, '%d_%d.npz' % (bx, by)))
        if 'st' in z: samp_t.append(z['st']); samp_a.append(z['sa'])
    st = {}
    for k, s in (('t1', np.concatenate(samp_t)), ('ao', np.concatenate(samp_a))):
        lo, hi = np.percentile(s, [2, 98]); x = np.clip((s - lo) / (hi - lo + 1e-6), 0, 1)
        st[k] = [float(lo), float(hi), float(np.median(x))]
    json.dump(st, open(os.path.join(out, 'stats.json'), 'w'))
    print('\nrelief scale', st)

def shade(lk, bx, by):
    p = os.path.join(lk.D, 'relief', '%d_%d.npz' % (bx, by))
    if not os.path.exists(p): return None
    z = np.load(p); st = json.load(open(os.path.join(lk.D, 'relief', 'stats.json')))
    if 't1' not in z: return None
    def fac(x, k, strength):
        lo, hi, med = st[k]; x = np.clip((x.astype(np.float32) - lo) / (hi - lo + 1e-6), 0, 1)
        return 1 + (x - med) * 2 * strength
    return np.clip(fac(z['t1'], 't1', 0.5) * fac(z['ao'], 'ao', 0.4), 0.3, 1.6).astype(np.float32)

# ---------------------------------------------------------------- render
def legend_scale(lk):
    maxd = json.load(open(os.path.join(lk.D, 'depth', 'stats.json')))['max']
    sc = 2 if maxd <= 20 else 5; DMAX = sc * math.ceil(maxd / sc)
    LMAX = math.ceil(maxd) if maxd <= 20 else 5 * math.ceil(maxd / 5)
    nt = 4 if LMAX % 3 == 0 else 3
    TICKS = ['%s m' % ('%g' % (LMAX * i / (nt - 1))).replace('.', ',') for i in range(nt)]
    return maxd, DMAX, LMAX, TICKS

def render(lk, shard=None):
    sk, sn = shard or (0, 1)
    OUT = os.path.join(ROOT, 'docs', 'lakes', lk.id); TD = os.path.join(OUT, 'tiles_v%d' % lk.V)
    PART = os.path.join(lk.D, 'render_parts'); os.makedirs(PART, exist_ok=True)
    maxd, DMAX, LMAX, TICKS = legend_scale(lk)
    STY = None
    ldirs = None
    for n, (bx, by) in enumerate(lk.blocks):
        if n % sn != sk: continue
        if os.path.exists(os.path.join(PART, '%d_%d.npz' % (bx, by))): continue    # (done in an earlier run)
        dep0, depc, water, osm, unm = block_depth(lk, bx, by)
        sh = shade(lk, bx, by)
        if sh is None: sh = np.ones(water.shape, np.float32)
        STY = R.make_styles(depc, sh, LMAX)
        ldirs = sorted({'lines' if s[6] == 'black' else 'lines_w' for s in STY})
        part = {}
        for z in lk.levels:
            f = 2 ** (lk.DZ - z); core = int(lk.BS / f); mg = int(RMG / f); w = h = core + 2 * mg
            X0, Y0 = int((lk.gx0 + bx * lk.BS) / f) - mg, int((lk.gy0 + by * lk.BS) / f) - mg      # level px, global
            lay = lambda n, mode='RGBA': read(lk.id, z, n, X0, Y0, w, h) if os.path.isdir(os.path.join(ROOT, 'raw', lk.id, 'z%d' % z, n)) else None
            t = lay('t').astype(np.float32)
            wl = R.resize(water.astype(np.float32), w, h); wat = wl >= 0.5
            alpha = np.clip(ndimage.gaussian_filter(wl, 0.6), 0, 1)[..., None]
            near = ndimage.binary_dilation(wat, iterations=max(3, int(14 / f)))[..., None]
            ta = t[..., 3:4] / 255 * near
            labels = ndimage.binary_dilation((t[..., :3].mean(2) > 170) & (t[..., 3] > 60), iterations=3)[..., None]
            if z > lk.base:
                n_c = core // TL                                   # pieces per block side at this level
                c0, r0 = (bx * lk.BS) // f // TL, (by * lk.BS) // f // TL
                nearw = ndimage.binary_dilation(wat, iterations=24)
                inside = lk.clip_mask(z, (bx * lk.BS) / f, (by * lk.BS) / f, core, core, step=TL // 8).reshape(n_c, 8, n_c, 8).any(axis=(1, 3))
                have = np.zeros((n_c, n_c), bool)
                for j in range(n_c):
                    for i in range(n_c):
                        have[j, i] = inside[j, i] and nearw[mg + j * TL:mg + (j + 1) * TL, mg + i * TL:mg + (i + 1) * TL].any()
                part['have%d' % z] = have
                def pieces(arr, folder, save):
                    d = os.path.join(TD, 'z%d' % z, folder); os.makedirs(d, exist_ok=True)
                    for j in range(n_c):
                        for i in range(n_c):
                            if have[j, i]:
                                y = mg + j * TL; x = mg + i * TL
                                save(arr[y - PAD:y + TL + PAD, x - PAD:x + TL + PAD], os.path.join(d, '%d_%d.webp' % (c0 + i, r0 + j)))
                for kind in ldirs:
                    ll = R.line_layer(kind, t, ta, labels)
                    pieces(ll, kind, R.save_lines); del ll
            if z > lk.DZ: del t; continue
            aer = lay('a', 'RGB').astype(np.float32)
            for sty in STY:
                sid, lines = sty[0], sty[6]
                img = R.style_image(sty, aer, alpha, near, lay, w, h)
                kind = 'lines' if lines == 'black' else 'lines_w'
                if z == lk.base:
                    part['map_' + sid] = np.clip(R.bake(img, R.line_layer(kind, t, ta, labels)), 0, 255).astype(np.uint8)[mg:mg + core, mg:mg + core]
                else:
                    u8 = np.clip(img, 0, 255).astype(np.uint8)
                    pieces(u8, sid, lambda a, pth: Image.fromarray(a).save(pth, 'WEBP', quality=35, method=6))
                    if z == lk.base + 1:
                        part['th_' + sid] = np.clip(R.bake(img, R.line_layer(kind, t, ta, labels)), 0, 255).astype(np.uint8)[mg:mg + core, mg:mg + core][::2, ::2]
            del aer, t
        # depth grid + bottom grid cells of this block (genesis_render, same encoding)
        gd = lk.src['grid_div']; cw = lk.BS // gd; core = slice(RMG, RMG + lk.BS)
        wf = water[core, core].astype(np.float32)
        part['num'] = np.array(Image.fromarray(dep0[core, core] * wf, 'F').resize((cw, cw), Image.BOX))
        part['den'] = np.array(Image.fromarray(wf, 'F').resize((cw, cw), Image.BOX))
        part['lakef'] = np.array(Image.fromarray((osm | water)[core, core].astype(np.float32), 'F').resize((cw, cw), Image.BOX))
        X, Y = lk.gx0 + bx * lk.BS, lk.gy0 + by * lk.BS
        v = read(lk.id, lk.DZ, 'v', X, Y, lk.BS, lk.BS); bot = np.zeros((cw, cw), np.uint8)
        vf = np.array(Image.fromarray(((v[..., 3] > 100) & water[core, core]).astype(np.float32), 'F').resize((cw, cw), Image.BOX))
        bot |= ((vf >= 0.3) * 8).astype(np.uint8); del v
        c = read(lk.id, lk.DZ, 'c', X, Y, lk.BS, lk.BS); cm = (c[..., 3] > 100) & water[core, core]
        ck = np.argmin(((c[..., None, :3].astype(np.int32) - np.array(R.HARD_SRC, np.int32)) ** 2).sum(-1), axis=-1) + 1; del c
        mf = np.array(Image.fromarray(cm.astype(np.float32), 'F').resize((cw, cw), Image.BOX))
        kf = np.array(Image.fromarray((ck * cm).astype(np.float32), 'F').resize((cw, cw), Image.BOX))
        bot |= np.where(mf >= 0.3, np.clip(np.round(kf / np.maximum(mf, 1e-6)), 1, 4), 0).astype(np.uint8)
        part['bot'] = bot; part['nwater'] = int(water[core, core].sum())
        np.savez_compressed(os.path.join(PART, '%d_%d.npz' % (bx, by)), **part)
        print('  render block %d/%d (%d,%d)' % (n + 1, len(lk.blocks), bx, by), flush=True)
    if shard: return
    finish(lk, maxd, DMAX, LMAX, TICKS)

def finish(lk, maxd, DMAX, LMAX, TICKS):
    """put the blocks together: map pictures (zoom 14), thumbnails, have-lists, depth + bottom grid, lake.json"""
    OUT = os.path.join(ROOT, 'docs', 'lakes', lk.id); PART = os.path.join(lk.D, 'render_parts')
    os.makedirs(os.path.join(OUT, 'thumbs_v%d' % lk.V), exist_ok=True)
    f14 = 2 ** (lk.DZ - lk.base); mw, mh = lk.W // f14, lk.H // f14; bw = lk.BS // f14
    # the map picture: the aerial photo everywhere (zoom 14 tiles), the blocks' pictures on top
    aer = read(lk.id, lk.base, 'a', lk.gx0 // f14, lk.gy0 // f14, mw, mh)
    dummy = np.zeros((8, 8), np.float32)
    STY = R.make_styles(dummy, np.ones_like(dummy), LMAX)
    maps = {s[0]: aer.copy() for s in STY}
    gd = lk.src['grid_div']; cw = lk.BS // gd; gw, gh = lk.nbx * cw, lk.nby * cw
    num = np.zeros((gh, gw), np.float32); den = np.zeros((gh, gw), np.float32); lakef = np.zeros((gh, gw), np.float32)
    bot = np.zeros((gh, gw), np.uint8)
    have = {z: np.zeros((int(lk.H * 2.0 ** (z - lk.DZ)) // TL, int(lk.W * 2.0 ** (z - lk.DZ)) // TL), bool) for z in lk.levels if z > lk.base}
    best = None
    for bx, by in lk.blocks:
        p = os.path.join(PART, '%d_%d.npz' % (bx, by))
        if not os.path.exists(p): raise SystemExit('block %d,%d not rendered yet' % (bx, by))
        q = np.load(p)
        for s in STY:
            if 'map_' + s[0] in q: maps[s[0]][by * bw:(by + 1) * bw, bx * bw:(bx + 1) * bw] = q['map_' + s[0]]
        for z in have:
            if 'have%d' % z in q:
                n_c = q['have%d' % z].shape[0]; have[z][by * n_c:(by + 1) * n_c, bx * n_c:(bx + 1) * n_c] = q['have%d' % z]
        sl = (slice(by * cw, (by + 1) * cw), slice(bx * cw, (bx + 1) * cw))
        num[sl] = q['num']; den[sl] = q['den']; lakef[sl] = q['lakef']; bot[sl] = q['bot']
        if best is None or q['nwater'] > best[0]: best = (int(q['nwater']), bx, by)
    for sid, m in maps.items():
        Image.fromarray(m).save(os.path.join(OUT, 'map_v%d_%s.jpg' % (lk.V, sid)), quality=84, optimize=True, progressive=True)
    q = np.load(os.path.join(PART, '%d_%d.npz' % best[1:]))
    for s in STY:
        th = q['th_' + s[0]]; hh, ww = th.shape[:2]; tw = int(ww * 0.6); tht = int(tw * 0.6)
        Image.fromarray(th).crop(((ww - tw) // 2, (hh - tht) // 2, (ww + tw) // 2, (hh + tht) // 2)).resize((200, 120), Image.LANCZOS).save(
            os.path.join(OUT, 'thumbs_v%d' % lk.V, '%s.jpg' % s[0]), quality=82)
    step = lk.src['depth_step']
    vals = np.where(den >= 0.5, np.clip(np.round(num / np.maximum(den, 1e-6) / step), 0, 250), np.where(lakef >= 0.5, 252, 255)).astype(np.uint8).ravel()
    open(os.path.join(OUT, 'depth_v%d.txt' % lk.V), 'w').write(base64.b64encode(R.pack_depth(vals)).decode())
    open(os.path.join(OUT, 'bottom_v%d.txt' % lk.V), 'w').write(base64.b64encode(R.pack_bottom(bot.ravel())).decode())
    print('  depth grid %d x %d: %d cells with depth, %d lake without' % (gw, gh, (vals <= 250).sum(), (vals == 252).sum()))
    level_info = []
    for z in sorted(have):
        hv = have[z]; rows, cols = hv.shape
        level_info.append({'z': z, 'cols': cols, 'rows': rows, 'have': ''.join('1' if x else '0' for x in hv.ravel()), 'base': z <= lk.DZ})
    mb = f14
    lake = {
        'id': lk.src['id'], 'name': lk.src['name'],
        'center': lk.src.get('center') or [round(lk.latc, 5), round(sum(p[1] for p in lk.poly) / len(lk.poly), 5)],
        'source': lk.src.get('source', ''),
        'geo': {'zoom': lk.base, 'originX': lk.gx0 // mb, 'originY': lk.gy0 // mb, 'fullW': lk.W // mb,
                'metersPerPx': 156543.03392 * math.cos(math.radians(lk.latc)) / 2 ** lk.base, 'imgW': mw, 'imgH': mh},
        'depth': {'file': 'depth_v%d.txt' % lk.V, 'w': gw, 'h': gh, 'step': step, 'max': DMAX, 'capped': False},
        'bottom': {'file': 'bottom_v%d.txt' % lk.V},
        'legendTicks': TICKS,
        'contourText': 'Djupkurvor från C-MAP Genesis',
        'mapFile': 'map_v%d_{style}.jpg' % lk.V,
        'thumbFile': 'thumbs_v%d/{style}.jpg' % lk.V,
        'styles': [dict(id=s[0], name=s[1], desc=s[2], legend=s[3], **s[4], **({} if s[6] == 'black' else {'lines': 'lines_w'})) for s in STY],
        'detail': {'file': 'tiles_v%d/z{z}/{style}/{c}_{r}.webp' % lk.V, 'lines': 'tiles_v%d/z{z}/{lines}/{c}_{r}.webp' % lk.V,
                   'baseMax': lk.DZ, 'tile': TL, 'pad': PAD, 'levels': level_info},
    }
    json.dump(lake, open(os.path.join(lk.L, 'lake.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    size = sum(os.path.getsize(os.path.join(dp, f2)) for dp, _, fs in os.walk(OUT) for f2 in fs)
    print('map %d x %d (zoom %d), depth grid %d x %d, max %.1f m, docs/lakes/%s = %.1f MB' % (mw, mh, lk.base, gw, gh, maxd, lk.id, size / 1e6))

if __name__ == '__main__':
    lk = Lake(sys.argv[1]); step = sys.argv[2]
    if step == 'colours': colours(lk)
    elif step == 'sheet': sheet(lk)
    elif step == 'depth': depth(lk, tuple(int(v) for v in sys.argv[3].split('/')) if len(sys.argv) > 3 else None)
    elif step == 'relief': relief(lk, tuple(int(v) for v in sys.argv[3].split('/')) if len(sys.argv) > 3 else None)
    elif step == 'render':
        sh = tuple(int(v) for v in sys.argv[3].split('/')) if len(sys.argv) > 3 else None
        render(lk, sh)
    elif step == 'finish': finish(lk, *legend_scale(lk))
    else: raise SystemExit(__doc__)
