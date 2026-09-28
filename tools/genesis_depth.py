"""Turn downloaded Genesis Social Map layers into a real depth field (metres).

    py -3 tools/genesis_depth.py <lake_id> sheet   -> raw/<lake>/z<zoom>/labels_sheet.png
    (read the numbers on the sheet, write them into lakes/<lake>/raw/depth_labels.json)
    py -3 tools/genesis_depth.py <lake_id>         -> raw/<lake>/z<zoom>/depth_m.npy
(zoom from lakes/<lake>/raw/source.json: 17 where Genesis has it, else 16)

Input  raw/<lake>/z<zoom>/b.png  depth colours: flat colours, light = shallow, but
                             NOT evenly spaced in metres
       raw/<lake>/z<zoom>/t.png  contour lines (0.5 m at z17, 1 m at z16) + depth labels
       lakes/<lake>/raw/depth_labels.json  label readings (value in metres,
                             subscript 5 = .5) at label positions

How: every colour is ranked (lightest = 0). Genesis' own depth labels sit on
the contour lines; the colour right around each label + its value give
colour -> metres pairs, fitted as a rising curve (isotonic). That table is
applied to every pixel and gently smoothed so the steps don't show. The
deepest spots, which Genesis leaves uncoloured, are holes in the colour layer
ringed by the deepest colour -> "a little deeper than the deepest colour".
(Why not simply count contour lines from the shore? Where the bottom is
steep, the lines melt together and can't be counted -- tried, it came out
far too shallow.)
"""
import sys, os, json
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage
Image.MAX_IMAGE_PIXELS = None
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def zoom_of(lake):
    f = os.path.join(ROOT, 'lakes', lake, 'raw', 'source.json')
    return json.load(open(f, encoding='utf-8')).get('zoom', 17) if os.path.exists(f) else 17

def load(lake):
    Z = zoom_of(lake)
    D = os.path.join(ROOT, 'raw', lake, 'z%d' % Z)
    B = np.array(Image.open(os.path.join(D, 'b.png')))
    T = np.array(Image.open(os.path.join(D, 't.png')))
    water = B[..., 3] > 200
    # Genesis leaves a 1-2 px transparent seam between its data blocks (every
    # 4096 px here) -- close it with the neighbour's colour, or the lake falls
    # apart into pieces
    for axis in (0, 1):
        dry = ~water
        s1 = dry & np.roll(water, 1, axis) & np.roll(water, -1, axis)                       # 1 px
        s2a = dry & np.roll(dry, -1, axis) & np.roll(water, 1, axis) & np.roll(water, -2, axis)  # 2 px, first
        for s in (s1, s2a, np.roll(s2a, 1, axis)):       # (second px of a 2-px seam copies the first)
            B[s] = np.roll(B, 1, axis)[s]
            water |= s
    lab, n = ndimage.label(water)                     # our lake = the biggest water body
    sizes = ndimage.sum(water, lab, range(1, n + 1))
    water = lab == (np.argmax(sizes) + 1)
    c = B[..., :3].astype(np.int32)
    key = (c[..., 0] << 16) | (c[..., 1] << 8) | c[..., 2]
    u, inv = np.unique(key[water], return_inverse=True)
    order = np.lexsort((-(u >> 16), -((u >> 8) & 255)))   # G desc, then R desc = shallow first
    rank = np.empty(len(u), np.int32); rank[order] = np.arange(len(u))
    idx = np.full(key.shape, -1, np.int32); idx[water] = rank[inv]
    return D, B, T, water, idx, len(u)
    # (B comes back with the seams closed)

def label_blobs(T):
    blobs = ndimage.binary_opening(T[..., 3] > 100, structure=np.ones((4, 4)))
    bl, nb = ndimage.label(blobs)
    return bl, ndimage.find_objects(bl)

def ring_colour(idx, bl, i, sl):
    y0, y1 = max(0, sl[0].start - 8), sl[0].stop + 8; x0, x1 = max(0, sl[1].start - 8), sl[1].stop + 8
    m = bl[y0:y1, x0:x1] == i
    ring = ndimage.binary_dilation(m, iterations=6) & ~ndimage.binary_dilation(m, iterations=2)
    v = idx[y0:y1, x0:x1][ring]; v = v[v >= 0]
    return v

def sheet(lake):
    D, B, T, water, idx, ncol = load(lake)
    bl, objs = label_blobs(T)
    comp = Image.fromarray(B).convert('RGBA'); comp.alpha_composite(Image.fromarray(T)); comp = comp.convert('RGB')
    cands = []
    for i, sl in enumerate(objs, 1):
        h, w = sl[0].stop - sl[0].start, sl[1].stop - sl[1].start
        if not (10 <= h <= 40 and 10 <= w <= 40): continue
        v = ring_colour(idx, bl, i, sl)
        if v.size < 20 or v.max() - v.min() > 2: continue
        cands.append((int(np.median(v)), (sl[0].start + sl[0].stop) // 2, (sl[1].start + sl[1].stop) // 2))
    rng = np.random.RandomState(0); pick = []
    for lo in range(0, ncol, 3):
        g = [c for c in cands if lo <= c[0] < lo + 3]; rng.shuffle(g); pick += g[:4]
    cell, cols = 96, 10; rows = (len(pick) + cols - 1) // cols
    im = Image.new('RGB', (cols * cell, rows * (cell + 14)), 'white'); dr = ImageDraw.Draw(im)
    for k, (ci, cy, cx) in enumerate(pick):
        X, Y = (k % cols) * cell, (k // cols) * (cell + 14)
        im.paste(comp.crop((cx - 24, cy - 24, cx + 24, cy + 24)).resize((cell, cell), Image.LANCZOS), (X, Y + 14))
        dr.text((X + 2, Y + 1), '#%d' % k, fill=(200, 0, 0))
    im.save(os.path.join(D, 'labels_sheet.png'))
    out = os.path.join(ROOT, 'lakes', lake, 'raw', 'depth_labels.json')
    if not os.path.exists(out):
        os.makedirs(os.path.dirname(out), exist_ok=True)
        json.dump({'zoom': zoom_of(lake), 'labels': [{'id': k, 'x': cx, 'y': cy, 'colour_index': ci, 'depth_m': None}
                                         for k, (ci, cy, cx) in enumerate(pick)]}, open(out, 'w'), indent=1)
    print('%d labels on the sheet -> %s; fill in depth_m in %s' % (len(pick), os.path.join(D, 'labels_sheet.png'), out))

def land_of(water_all):
    return ~water_all

def isotonic(y, w):
    out = []
    for v, ww in zip(y, w):
        out.append([v, ww, 1])
        while len(out) > 1 and out[-2][0] > out[-1][0]:
            v2, w2, n2 = out.pop(); v1, w1, n1 = out.pop()
            out.append([(v1 * w1 + v2 * w2) / (w1 + w2), w1 + w2, n1 + n2])
    return np.concatenate([[v] * n for v, _, n in out])

def build(lake):
    D, B, T, water, idx, ncol = load(lake)
    Image.fromarray(B).save(os.path.join(D, 'b_fixed.png'))   # seams closed (used by genesis_render)
    labels = json.load(open(os.path.join(ROOT, 'lakes', lake, 'raw', 'depth_labels.json')))['labels']
    # colour right around each label (looked up from its position: colour
    # numbers change when the colour set does)
    bl, objs = label_blobs(T)
    pts = []
    for l in labels:
        if l['depth_m'] is None: continue
        win = bl[l['y'] - 3:l['y'] + 4, l['x'] - 3:l['x'] + 4]; ids = win[win > 0]
        if not ids.size: continue
        i = int(np.bincount(ids).argmax())
        v = ring_colour(idx, bl, i, objs[i - 1])
        if v.size >= 20: pts.append((int(np.median(v)), l['depth_m']))
    # colour -> metres: median per colour, rising, interpolated between colours
    xs = np.arange(ncol)
    ci = np.array([p[0] for p in pts]); dm = np.array([p[1] for p in pts], float)
    have = sorted(set(ci.tolist()))
    med = np.array([np.median(dm[ci == k]) for k in have]); wt = np.array([(ci == k).sum() for k in have], float)
    med = isotonic(med, wt)
    table = np.interp(xs, have, med)
    # beyond the last reading: keep the average slope of the last part
    if have[-1] < ncol - 1:
        slope = (med[-1] - med[max(0, len(med) - 6)]) / max(1, have[-1] - have[max(0, len(have) - 6)])
        # (at most 1 m deeper than the deepest reading: the last colours are
        # often rare edge colours, not a big unknown depth)
        table[have[-1]:] = np.minimum(med[-1] + slope * (xs[have[-1]:] - have[-1]), med[-1] + 1.0)
    if have[0] > 0:
        table[:have[0]] = np.maximum(0.25, med[0] - (have[0] - xs[:have[0]]) * 0.5)
    with open(os.path.join(D, 'depth_calib.txt'), 'w') as f:
        for i in range(ncol): f.write('%2d %6.2f m\n' % (i, table[i]))
    print('colour table: %d colours, %.2f .. %.2f m (%d label readings)' % (ncol, table[0], table[-1], len(pts)))

    # holes in the water: islands (ringed by shallow colours) or the uncoloured deepest spots
    # Holes in the colour layer (inside the lake) are islands OR areas Genesis has no
    # data for (unmapped) -- either way NO depth: they're left out (not coloured; the
    # map shows the aerial photo there, OpenStreetMap says whether it's lake).
    # (Earlier we took holes ringed by deep colours for "extra deep" -- wrong: they
    # were unmapped strips, see tools/KARTOR.md.)
    holes = ndimage.binary_fill_holes(water) & ~water
    print('holes in the colour layer (islands / unmapped): %d' % ndimage.label(holes)[1])
    water_all = water
    # Inside each colour band the depth runs smoothly from the band's shallow
    # edge to its deep edge (by distance to the shallower / deeper colours),
    # instead of one flat value per band -- otherwise flat bottoms become
    # terraces. (Done at half resolution; plenty for bands tens of px wide.)
    # A hole is neither shallower nor deeper (we don't know) -- only real land
    # (outside the lake) counts as "shallower".
    ih = idx[::2, ::2]; land_h = land_of(water | holes)[::2, ::2]
    edges = np.concatenate([[0.0], (table[:-1] + table[1:]) / 2, [table[-1] + 0.75]])  # edges[i]..edges[i+1] = band i
    dh = np.zeros(ih.shape, np.float32)
    M = 150
    for i in range(ncol + 1):
        m = ih == i
        if not m.any(): continue
        ys, xs = np.where(m)
        y0, y1 = max(0, ys.min() - M), min(ih.shape[0], ys.max() + M + 1)
        x0, x1 = max(0, xs.min() - M), min(ih.shape[1], xs.max() + M + 1)
        sub = ih[y0:y1, x0:x1]
        up = ((sub >= 0) & (sub < i)) | land_h[y0:y1, x0:x1]
        dn = sub > i
        du = ndimage.distance_transform_edt(~up) if up.any() else np.full(sub.shape, 1e4)
        dd = ndimage.distance_transform_edt(~dn) if dn.any() else np.full(sub.shape, 1e4)
        lo, hi = edges[i], (edges[i + 1] if i < ncol else table[-1] + 1.5)
        t = du / (du + dd + 1e-6)
        mm = m[y0:y1, x0:x1]
        dh[y0:y1, x0:x1][mm] = (lo + (hi - lo) * t)[mm]
    # before scaling up: cells without depth (land, holes) take the nearest known depth,
    # or the bilinear scaling blends "0 m" into the edge pixels (the edge of an unmapped
    # hole became ~7 m too shallow and got a dark relief rim)
    known = ih >= 0
    iy, ix = ndimage.distance_transform_edt(~known, return_distances=False, return_indices=True)
    dh = dh[iy, ix]; del iy, ix
    dep = np.array(Image.fromarray(dh, 'F').resize((water.shape[1], water.shape[0]), Image.BILINEAR))
    wf = water_all.astype(np.float32)
    num = ndimage.gaussian_filter(dep * wf, 2.0); den = ndimage.gaussian_filter(wf, 2.0)
    sm = np.where(water_all, num / np.maximum(den, 1e-6), np.nan).astype(np.float32)
    np.save(os.path.join(D, 'depth_m.npy'), sm)
    np.save(os.path.join(D, 'water.npy'), water_all)
    # check against every reading: depth at the label position
    err = []
    for l in labels:
        if l['depth_m'] is None: continue
        v = sm[l['y'] - 12:l['y'] + 13, l['x'] - 12:l['x'] + 13]
        err.append(np.nanmedian(v) - l['depth_m'])
    err = np.array(err)
    print('vs labels: median error %+.2f m, 90 %% within %.2f m' % (np.median(err), np.percentile(np.abs(err), 90)))
    print('saved depth_m.npy: max %.1f m' % np.nanmax(sm))

if __name__ == '__main__':
    lake = sys.argv[1]
    if len(sys.argv) > 2 and sys.argv[2] == 'sheet': sheet(lake)
    else: build(lake)
