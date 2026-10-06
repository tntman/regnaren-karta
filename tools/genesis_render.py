"""Render a Genesis-based lake for the app: one picture per zoom level and map
style (Genesis' own contour lines + depth numbers for that zoom level, our
colours and relief from the calibrated depth), thumbnails, depth grid, lake.json.

    py -3 tools/genesis_render.py <lake_id>

Needs (see tools/genesis_tiles.py and tools/genesis_depth.py):
    lakes/<lake>/raw/source.json   name, zoom (= the depth data's zoom), levels, bbox or origin+size ...
    raw/<lake>/z<zoom>/depth_m.npy, water.npy   (genesis_depth.py)
    raw/<lake>/z<level>/{a,b,t,v,c}.png         for every level (genesis_tiles.py)
Writes
    docs/lakes/<lake>/map_v<V>_<style>.jpg              the whole lake at the lowest level (zoom 14), lines baked in
    docs/lakes/<lake>/tiles_v<V>/z<z>/<style>/<c>_<r>.webp  higher levels up to the depth data's zoom in 512 px
                                                         pieces (only near water): the BASE -- colours, no lines
    docs/lakes/<lake>/tiles_v<V>/z<z>/lines[_w]/<c>_<r>.webp  Genesis' lines + numbers for that zoom, see-through,
                                                         shared by every style (lines_w = the light ones, Bottenhårdhet).
                                                         Above the depth data's zoom there are only lines: the app
                                                         puts them on the top base, enlarged (tools/PLAN_KARTFORMAT.md)
    docs/lakes/<lake>/thumbs_v<V>/<style>.jpg, depth_v<V>.txt
    lakes/<lake>/lake.json, lakes/<lake>/raw/depth_raw.npz (full-resolution depth for the tests)
(The pictures only live in docs/ -- they're built output, and a copy in lakes/
as well would double the repository.)

Depth lines are never drawn by us: every level shows exactly Genesis' contour
layer for that zoom, so the number of lines grows as you zoom in, like on Genesis.
"""
import sys, os, json, math, shutil, base64
import numpy as np
from PIL import Image
from scipy import ndimage
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import colors as mcolors
Image.MAX_IMAGE_PIXELS = None
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TL = 512
PAD = 8      # neighbour pixels round every detail piece (see pieces())
# Bottenhårdhet (light lines): the white lines thinner (alpha ** LINE_THIN keeps the cores) and see-through
LINE_THIN = float(os.environ.get('FF_LINE_THIN', 2.5))
LINE_OPACITY = float(os.environ.get('FF_LINE_OPACITY', 0.55))
# Bottenhårdhet: Genesis' 4 colours (soft -> hard) and what we draw them as
HARD_SRC = [(255, 255, 204), (254, 194, 93), (252, 134, 67), (250, 74, 41)]
HARD_PALS = {'genesis': HARD_SRC,
             'warm': [(255, 244, 150), (255, 170, 0), (240, 70, 10), (150, 0, 40)],     # pale yellow -> dark red
             'bluered': [(80, 170, 255), (140, 230, 120), (255, 190, 0), (215, 20, 40)]}  # blue (soft) -> red (hard)
HARD_PAL = HARD_PALS[os.environ.get('FF_HARD', 'warm')]      # "warm" chosen (Filip)
# Fixed depth colour scale for every lake: 0-10 m = 2/3 of the scale, 10-50 m the rest, deeper = 50 m
DEPTH_KNOTS_M = [0, 10, 50]
DEPTH_KNOTS_F = [0, 2 / 3, 1]

def hx(s): return np.array([int(s[i:i + 2], 16) for i in (1, 3, 5)], np.float32)

def close_seams(B):
    """Genesis leaves 1-2 px transparent seams between its data blocks: fill them."""
    water = B[..., 3] > 200
    for axis in (0, 1):
        dry = ~water
        s1 = dry & np.roll(water, 1, axis) & np.roll(water, -1, axis)
        s2a = dry & np.roll(dry, -1, axis) & np.roll(water, 1, axis) & np.roll(water, -2, axis)
        for s in (s1, s2a, np.roll(s2a, 1, axis)):
            B[s] = np.roll(B, 1, axis)[s]; water |= s
    return B

def hill(e, zf, az, alt):
    gx = ndimage.sobel(e, 1) / 8.0; gy = ndimage.sobel(e, 0) / 8.0
    nx, ny, nz = -gx * zf, -gy * zf, np.ones_like(e); n = np.sqrt(nx * nx + ny * ny + nz * nz)
    a, b = np.deg2rad(az), np.deg2rad(alt)
    return np.clip((nx * np.cos(b) * np.sin(a) - ny * np.cos(b) * np.cos(a) + nz * np.sin(b)) / n, 0, 1)

def shift(a, dy, dx):
    """a moved so that out[p] = a[p + (dy, dx)] (edges repeat the original)"""
    out = a.copy(); H, W = a.shape
    out[max(-dy, 0):H + min(-dy, 0), max(-dx, 0):W + min(-dx, 0)] = a[max(dy, 0):H + min(dy, 0), max(dx, 0):W + min(dx, 0)]
    return out

def relief(dep0, water, px, solid=None):
    """Brightness factor (1 = unchanged) -- "T1 x AO" (Filip's choice, see tools/KARTOR.md 8):
    a height map (-depth, smoothed ~1.2 m, heights x12) -> normal map -> diffuse light from
    NW, 45 deg up (T1), times ambient occlusion (holes/gullies darker, ~25 m around).
    All sizes in metres (px = metres per pixel), so it looks the same at every zoom."""
    # solid = where the bottom continues (water + unmapped parts of the lake, filled with
    # the nearest depth) -- so an unmapped hole is no "wall": it doesn't shade its edges
    sol = water if solid is None else solid
    wf = sol.astype(np.float32); s = max(0.5, 1.2 / px)
    h = -np.where(sol, ndimage.gaussian_filter(dep0 * wf, s) / np.maximum(ndimage.gaussian_filter(wf, s), 1e-6), 0).astype(np.float32)
    EX = 12
    gx = ndimage.sobel(h, 1) / (8 * px) * EX; gy = ndimage.sobel(h, 0) / (8 * px) * EX
    n = np.sqrt(gx * gx + gy * gy + 1)
    a, b = math.radians(315), math.radians(45)
    t1 = np.clip((-gx * math.cos(b) * math.sin(a) + gy * math.cos(b) * math.cos(a) + math.sin(b)) / n, 0, 1)
    del gx, gy, n
    he = h * EX; occ = np.zeros_like(h)
    steps = sorted(set(max(1, int(round(1.35 ** i))) for i in range(40) if 1.35 ** i * px <= 25.0)) or [1]
    for i in range(16):
        ang = 2 * math.pi * i / 16; best = np.zeros_like(h)
        for st in steps:
            best = np.maximum(best, (shift(he, int(round(math.sin(ang) * st)), int(round(math.cos(ang) * st))) - he) / (st * px))
        occ += np.sin(np.arctan(best))
    ao = 1 - occ / 16
    def fac(x, strength):
        lo, hi = np.percentile(x[water], [2, 98]); x = np.clip((x - lo) / (hi - lo + 1e-6), 0, 1)
        return 1 + (x - np.median(x[water])) * 2 * strength
    return np.clip(fac(t1, 0.5) * fac(ao, 0.4), 0.3, 1.6).astype(np.float32)

def resize(arr, w, h):
    """float array (H, W[, C]) -> (h, w[, C]); area average when shrinking, bilinear when growing"""
    shrink = w < arr.shape[1]
    f = Image.BOX if shrink else Image.BILINEAR
    if arr.ndim == 2: return np.array(Image.fromarray(arr.astype(np.float32), 'F').resize((w, h), f))
    return np.dstack([np.array(Image.fromarray(arr[..., i].astype(np.float32), 'F').resize((w, h), f)) for i in range(arr.shape[2])])

def make_styles(depc, sh, LMAX):
    """the map styles: (id, name, desc, legend, extra, water colour at DZ, how Genesis' lines are drawn).
    depc = depth (unmapped parts filled), sh = relief brightness, LMAX = the legend's end (m)"""
    # ---- the water colour of every style, at DZ (uint8 to save memory); None = no own colour
    # FIXED depth -> colour, the same in every lake (Filip): most colour change 0-10 m
    # (where you fish) = 2/3 of the scale, then 10-50 m blue -> dark blue, deeper = as 50 m
    def fpos(d): return np.interp(d, DEPTH_KNOTS_M, DEPTH_KNOTS_F)
    def ramp(cmap): return cmap(fpos(depc))[..., :3].astype(np.float32) * 255
    def u8(a): return np.clip(a, 0, 255).astype(np.uint8)
    def legend_css(cmap, n=25):
        # evenly spaced in metres 0..LMAX, each the colour the map uses at that depth
        return 'linear-gradient(to right,' + ','.join('%s %g%%' % (mcolors.to_hex(cmap(float(fpos(LMAX * i / (n - 1))))), round(100 * i / (n - 1), 1)) for i in range(n)) + ')'
    def bands_css(cols, edges):
        # Sjökort: hard bands, where each starts in metres (0..LMAX)
        st = []
        for k, (c, e) in enumerate(zip(cols, edges)):
            if e >= LMAX: break
            nxt = min(LMAX, edges[k + 1]) if k + 1 < len(edges) else LMAX
            st.append('%s %g%%,%s %g%%' % (c, round(100 * e / LMAX, 1), c, round(100 * nxt / LMAX, 1)))
        return 'linear-gradient(to right,' + ','.join(st) + ')'
    # Djupfärger: red 0 m, orange 1,5, yellow 3, green 5, turquoise 7,5, blue 10, dark blue 50 m
    c1 = mcolors.LinearSegmentedColormap.from_list('c1', [(float(fpos(d)), c) for d, c in
        ((0, '#d62728'), (1.5, '#ff7f0e'), (3, '#ffdd00'), (5, '#2ca02c'), (7.5, '#17becf'), (10, '#1f4fd6'), (25, '#0f2c8a'), (50, '#03081f'))])
    c6 = mcolors.LinearSegmentedColormap.from_list('b', ['#cfeefa', '#6fc3e8', '#2a86c9', '#12509a', '#0a2c63'])
    bands = ['#dff3fb', '#c4e7f6', '#a9dbf2', '#8fcdec', '#74bde4', '#5aa9d8', '#4796cb', '#3a84bd', '#2f72ae']
    edges = [0, 1, 2, 3, 5, 7.5, 10, 20, 30]           # Sjökort: fixed depths (m) where a new band starts
    s3 = np.zeros(depc.shape + (3,), np.float32); s3[:] = hx(bands[0])
    for lo, col in zip(edges[1:], bands[1:]): s3[depc >= lo] = hx(col)
    # (id, name, desc, legend, extra, water colour at DZ, how Genesis' lines are drawn)
    STY = [
        ('s1', 'Djupfärger', 'Flygfoto + djupfärger med relief', legend_css(c1), {}, u8(ramp(c1) * sh[..., None]), 'black'),
        ('s2', 'Förenklad', 'Samma djupfärger, utan skuggning', legend_css(c1), {}, u8(ramp(c1)), 'black'),
        ('s3', 'Sjökort', 'Blå djupband som en papperskarta', bands_css(bands, edges), {}, u8(s3), 'black'),
        # (no "Natt" (s4) and no "Flygfoto + linjer" (s5) -- dropped, Filip's decisions; see tools/KARTOR.md)
        ('s6', 'Blå relief', 'Blå toner med skuggad bottenform', legend_css(c6), {}, u8(ramp(c6) * sh[..., None]), 'black'),
        ('g1', 'C-MAP original', 'Som på Genesis-kartan – med djupsiffror', None, {'note': 'Siffror = djup i m (liten siffra = tiondelar)'}, 'genesis', 'black'),
        ('v1', 'Vegetation', 'Grönt där ekolodet sett växtlighet', 'linear-gradient(to right,#6fc3e8 0%,#6fc3e8 50%,#46dc3c 50%,#46dc3c 100%)', {'ticks': ['Ingen', '', 'Växtlighet']}, u8(ramp(c6)), 'black'),
        ('c1', 'Bottenhårdhet', 'Mjuk (ljus) till hård (röd) botten, där det finns mätt', 'linear-gradient(to right,' + ','.join('%s %d%%' % (mcolors.to_hex(np.array(c) / 255), p) for c, p in zip(HARD_PAL, (0, 33, 66, 100))) + ')', {'ticks': ['Mjuk', '', 'Hård']}, None, (255, 255, 255)),
        # (Bottenhårdhet: no water colour -- the aerial photo where nothing is measured, the
        #  hardness colours where it is, thin light depth lines on top)
    ]
    return STY

def save_lines(arr, path):
    """a see-through lines piece: 32 colours, lossless WebP (8 made the numbers' halos ragged)"""
    a = np.clip(arr, 0, 255).astype(np.uint8); a[a[..., 3] == 0, :3] = 0
    Image.fromarray(a, 'RGBA').quantize(32, method=Image.FASTOCTREE).convert('RGBA').save(path, 'WEBP', lossless=True, method=6)

def line_layer(kind, t, ta, labels):
    """Genesis' contour lines + depth numbers for a zoom as colour + alpha: black lines as they are, or
    light lines (Bottenhårdhet): thinner (only the line cores -- the soft edges fade out) and see-through;
    the depth numbers as they are"""
    if kind == 'lines': return np.concatenate([t[..., :3], ta * 255], axis=2)
    thin = np.where(labels, ta, (ta ** LINE_THIN) * LINE_OPACITY)
    col = np.where(labels, t[..., :3], np.float32(255))
    return np.concatenate([col, thin * 255], axis=2)

def bake(img, ll):
    """lines (line_layer) drawn onto a picture"""
    a = ll[..., 3:4] / 255
    return img * (1 - a) + ll[..., :3] * a

def style_image(sty, aer, alpha, near, lay, w, h):
    """a style's picture at one level, without lines (lay(name) = that Genesis layer over the same area)"""
    sid, colour = sty[0], sty[5]
    if isinstance(colour, np.ndarray):
        img = aer * (1 - alpha) + resize(colour.astype(np.float32), w, h) * alpha
    elif colour == 'genesis':
        b = lay('b'); b = close_seams(b).astype(np.float32); ba = b[..., 3:4] / 255 * near
        img = aer * (1 - ba) + b[..., :3] * ba
    else:
        img = aer * np.array([0.9, 0.97, 1.05], np.float32)
    if sid == 'v1':
        v = lay('v'); va = (v[..., 3:4].astype(np.float32) / 255) * 0.72 * alpha if v is not None else 0
        img = img * (1 - va) + np.array([70, 220, 60], np.float32) * va
    if sid == 'c1':
        c = lay('c')
        if c is not None:
            # Genesis' 4 hardness levels (soft -> hard), recoloured with more contrast
            c = c.astype(np.float32); ca = c[..., 3:4] / 255 * alpha
            src4 = np.array(HARD_SRC, np.float32); dst4 = np.array(HARD_PAL, np.float32)
            k = np.argmin(((c[..., None, :3] - src4) ** 2).sum(-1), axis=-1)
            img = img * (1 - ca) + dst4[k] * ca
    return img

def pack_depth(vals):
    """depth grid bytes: runs packed -- 251 n_lo n_hi = n land cells, 253 n_lo n_hi = n "lake, unknown depth" cells"""
    enc = bytearray(); i = 0
    while i < len(vals):
        if vals[i] in (255, 252):
            v = vals[i]; j = i
            while j < len(vals) and vals[j] == v and j - i < 65535: j += 1
            n = j - i
            enc += bytes([251 if v == 255 else 253, n & 255, n >> 8]) if n >= 3 else bytes([v] * n)
            i = j
        else:
            enc.append(vals[i]); i += 1
    return bytes(enc)

def pack_bottom(bv):
    """bottom grid bytes: runs of 0 packed -- 250 n_lo n_hi"""
    enc = bytearray(); i = 0
    while i < len(bv):
        if bv[i] == 0:
            j = i
            while j < len(bv) and bv[j] == 0 and j - i < 65535: j += 1
            n = j - i; enc += bytes([250, n & 255, n >> 8]) if n >= 3 else bytes(n); i = j
        else:
            enc.append(bv[i]); i += 1
    return bytes(enc)

def main():
    lake = sys.argv[1]
    L = os.path.join(ROOT, 'lakes', lake)
    OUT = os.path.join(ROOT, 'docs', 'lakes', lake)
    src = json.load(open(os.path.join(L, 'raw', 'source.json'), encoding='utf-8'))
    DZ = src['zoom']                                   # the depth data's zoom
    levels = sorted(src['levels']); base, top = levels[0], levels[-1]
    V = src.get('version', 1)                          # new version = new file names (phones re-download)

    # ---- the crop at DZ, aligned so it's whole pixels at every level
    def gpx(lat, lon, z):
        n = 256 * 2 ** z
        return ((lon + 180) / 360 * n,
                (1 - math.log(math.tan(math.radians(lat)) + 1 / math.cos(math.radians(lat))) / math.pi) / 2 * n)
    la0, la1, lo0, lo1 = src['bbox']
    if 'origin' in src: (x0, y0), (W, H) = src['origin'], src['size']
    else:
        x0, y0 = gpx(la1, lo0, DZ); x1, y1 = gpx(la0, lo1, DZ); W, H = x1 - x0, y1 - y0
    m = 2 ** (DZ - base)
    gx0, gy0 = int(math.floor(x0 / m)) * m, int(math.floor(y0 / m)) * m
    W = int(math.ceil((x0 + W - gx0) / m)) * m; H = int(math.ceil((y0 + H - gy0) / m)) * m
    print('crop %d x %d px at z%d (depth data); levels %s' % (W, H, DZ, levels))

    D = os.path.join(ROOT, 'raw', lake, 'z%d' % DZ); g = json.load(open(os.path.join(D, 'grid.json')))
    cx0, cy0 = gx0 - g['tile_x0'] * 256, gy0 - g['tile_y0'] * 256
    def cropdz(a, fill):
        out = np.full((H, W) + a.shape[2:], fill, a.dtype)
        y1, x1 = min(a.shape[0], cy0 + H), min(a.shape[1], cx0 + W)
        out[:y1 - cy0, :x1 - cx0] = a[cy0:y1, cx0:x1]
        return out
    dep = cropdz(np.load(os.path.join(D, 'depth_m.npy')), np.nan)
    water = cropdz(np.load(os.path.join(D, 'water.npy')), False)
    dep0 = np.where(water, dep, 0).astype(np.float32)
    maxd = float(np.nanmax(dep)); sc = 2 if maxd <= 20 else 5
    DMAX = sc * math.ceil(maxd / sc)
    print('max depth %.1f m -> colour scale 0-%d m' % (maxd, DMAX))
    # The legend runs from 0 to the lake's own max depth (Filip: "0-50 m" looked like the
    # lake went that deep): whole metres up to 20 m, else 5 m steps; ticks evenly spaced
    # in metres (4 if they come out whole, else 3). Its colours = the fixed scale for those depths.
    LMAX = math.ceil(maxd) if maxd <= 20 else 5 * math.ceil(maxd / 5)
    nt = 4 if LMAX % 3 == 0 else 3
    TICKS = ['%s m' % ('%g' % (LMAX * i / (nt - 1))).replace('.', ',') for i in range(nt)]
    PXD = 156543.03392 * math.cos(math.radians((la0 + la1) / 2)) / 2 ** DZ   # metres per px at DZ
    # Parts of the lake Genesis has no data for (inside the OpenStreetMap outline): a hard
    # cut-out -- the aerial photo shows there. For the relief and the colours at their
    # edges they're filled with the nearest known depth, so they don't act as a wall
    # (shade) or bleed "0 m" colour into the lake around them.
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import osm_water
    osm0 = osm_water.mask(lake, DZ, gx0, gy0, W, H)
    unm = (osm0 & ~water) if osm0 is not None else np.zeros_like(water)
    depc = dep0
    if unm.any():
        iy, ix = ndimage.distance_transform_edt(~water, return_distances=False, return_indices=True)
        depc = dep0.copy(); depc[unm] = dep0[iy[unm], ix[unm]]; del iy, ix
    sh = relief(depc, water, PXD, solid=water | unm)   # only Djupfärger (s1) and Blå relief (s6) are shaded

    STY = make_styles(depc, sh, LMAX)

    # "grid": only the depth grid + lake.json (pictures unchanged -- much faster)
    grid_only = len(sys.argv) > 2 and sys.argv[2] == 'grid'
    # "preview <levels> <folder>": whole pictures of those levels, all styles, into a folder
    # of your choice -- nothing in docs/ or lakes/ is touched (for looking before building)
    preview = len(sys.argv) > 4 and sys.argv[2] == 'preview'
    if preview:
        levels = [int(x) for x in sys.argv[3].split(',')]; PREV = sys.argv[4]; os.makedirs(PREV, exist_ok=True)
    ntiles = 0
    if preview:
        level_info = []
    elif grid_only:
        level_info = json.load(open(os.path.join(L, 'lake.json'), encoding='utf-8'))['detail']['levels']
    else:
        # ---- output folder: only this version's pictures
        os.makedirs(OUT, exist_ok=True)
        for f in os.listdir(OUT):
            p = os.path.join(OUT, f)
            shutil.rmtree(p) if os.path.isdir(p) else os.remove(p)
        os.makedirs(os.path.join(OUT, 'thumbs_v%d' % V))
        level_info = []

    LDIRS = sorted({'lines' if s[6] == 'black' else 'lines_w' for s in STY})
    for z in ([] if grid_only else levels):
        f = 2 ** (DZ - z)                                   # DZ px per level px (< 1 above DZ)
        w, h = int(round(W / f)), int(round(H / f)); ox, oy = int(round(gx0 / f)), int(round(gy0 / f))
        Dz = os.path.join(ROOT, 'raw', lake, 'z%d' % z); gz = json.load(open(os.path.join(Dz, 'grid.json')))
        lx, ly = ox - gz['tile_x0'] * 256, oy - gz['tile_y0'] * 256
        def lay(n, mode='RGBA'):
            p = os.path.join(Dz, n + '.png')
            if not os.path.exists(p): return None
            a = np.array(Image.open(p).convert(mode)); out = np.zeros((h, w) + a.shape[2:], a.dtype)
            y1, x1 = min(a.shape[0], ly + h), min(a.shape[1], lx + w)
            out[:y1 - ly, :x1 - lx] = a[ly:y1, lx:x1]
            return out
        t = lay('t').astype(np.float32)
        wl = resize(water.astype(np.float32), w, h)
        wat = wl >= 0.5
        alpha = np.clip(ndimage.gaussian_filter(wl, 0.6), 0, 1)[..., None]
        near = ndimage.binary_dilation(wat, iterations=max(3, int(14 / f)))[..., None]   # Genesis layers only on our lake
        ta = t[..., 3:4] / 255 * near
        # depth numbers = the light halo round them (lines, even melted together on steep slopes, are black)
        labels = ndimage.binary_dilation((t[..., :3].mean(2) > 170) & (t[..., 3] > 60), iterations=3)[..., None]
        LL = lambda kind: line_layer(kind, t, ta, labels)
        if z > base:
            cols, rows = -(-w // TL), -(-h // TL)
            nearw = ndimage.binary_dilation(wat, iterations=24)
            have = ''.join('1' if nearw[r * TL:(r + 1) * TL, c * TL:(c + 1) * TL].any() else '0' for r in range(rows) for c in range(cols))
            level_info.append({'z': z, 'cols': cols, 'rows': rows, 'have': have, 'base': z <= DZ})
            def pieces(im, td, save):
                # every piece carries PAD px of its neighbours all round (the app shows only the inside): the
                # browser enlarges each piece on its own, and without real neighbour pixels at the edge the
                # lines kinked and the colours jumped where two pieces met
                os.makedirs(td)
                pad = Image.new(im.mode, (cols * TL + 2 * PAD, rows * TL + 2 * PAD)); pad.paste(im, (PAD, PAD))
                n = 0
                for r in range(rows):
                    for c in range(cols):
                        if have[r * cols + c] == '1':
                            save(pad.crop((c * TL, r * TL, (c + 1) * TL + 2 * PAD, (r + 1) * TL + 2 * PAD)), os.path.join(td, '%d_%d.webp' % (c, r))); n += 1
                return n
            if not preview:
                for kind in LDIRS:
                    ll = LL(kind).clip(0, 255).astype(np.uint8)
                    ntiles += pieces(Image.fromarray(ll, 'RGBA'), os.path.join(OUT, 'tiles_v%d' % V, 'z%d' % z, kind),
                                     lambda im, pth: save_lines(np.array(im), pth))
                    del ll
        if z > DZ:                                          # above the depth data: only the lines (bases = DZ enlarged)
            if preview:
                for kind in LDIRS: Image.fromarray(LL(kind).clip(0, 255).astype(np.uint8), 'RGBA').save(os.path.join(PREV, '%s_z%d_%s.png' % (lake, z, kind)))
            print('  zoom %d: %d x %d px, lines only' % (z, w, h))
            del t; continue
        aer = lay('a', 'RGB').astype(np.float32)
        styles_here = STY
        if preview and os.environ.get('FF_PREVIEW_STYLES'):     # (a preview of just some styles)
            styles_here = [s for s in styles_here if s[0] in os.environ['FF_PREVIEW_STYLES'].split(',')]
        for sty in styles_here:
            sid, lines = sty[0], sty[6]
            img = style_image(sty, aer, alpha, near, lay, w, h)
            kind = 'lines' if lines == 'black' else 'lines_w'
            u8i = lambda a: Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
            if preview:
                u8i(bake(img, LL(kind))).save(os.path.join(PREV, '%s_z%d_%s.jpg' % (lake, z, sid)), quality=88); continue
            if z == base:                                   # the map picture: lines baked in, as before
                u8i(bake(img, LL(kind))).save(os.path.join(OUT, 'map_v%d_%s.jpg' % (V, sid)), quality=84, optimize=True, progressive=True)
            else:                                           # the base: colours only, WebP 35 (soft colours take it)
                ntiles += pieces(u8i(img), os.path.join(OUT, 'tiles_v%d' % V, 'z%d' % z, sid),
                                 lambda im, pth: im.save(pth, 'WEBP', quality=35, method=6))
            if z == base + 1:   # thumbnails: a 200x120 look at the middle of the lake at zoom 15
                ys, xs = np.where(wat); my, mx = int(np.median(ys)), int(np.median(xs))
                tw = int(w * 0.3); th = int(tw * 0.6)
                u8i(bake(img, LL(kind))).crop((mx - tw // 2, my - th // 2, mx + tw // 2, my + th // 2)).resize((200, 120), Image.LANCZOS).save(
                    os.path.join(OUT, 'thumbs_v%d' % V, '%s.jpg' % sid), quality=82)
        print('  zoom %d: %d x %d px, %d styles' % (z, w, h, len(styles_here)))
        del aer, t
    if preview:
        print('preview pictures in', PREV); return

    # ---- depth grid for the app: one byte per cell = depth / step (0-250); 252 = lake but no
    # depth data (inside the OpenStreetMap outline, not logged in Genesis); 255 = land.
    # Runs are packed: 251 n_lo n_hi = n land cells, 253 n_lo n_hi = n "lake, unknown depth" cells.
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import osm_water
    osm = osm_water.mask(lake, DZ, gx0, gy0, W, H)
    if osm is None: print('  (no OpenStreetMap outline -- run tools/osm_water.py %s)' % lake); osm = np.zeros_like(water)
    gd = src['grid_div']; gw, gh = int(round(W / gd)), int(round(H / gd))
    wf = water.astype(np.float32)
    num = np.array(Image.fromarray(dep0 * wf, 'F').resize((gw, gh), Image.BOX))
    den = np.array(Image.fromarray(wf, 'F').resize((gw, gh), Image.BOX))
    lakef = np.array(Image.fromarray((osm | water).astype(np.float32), 'F').resize((gw, gh), Image.BOX))
    step = src['depth_step']
    vals = np.where(den >= 0.5, np.clip(np.round(num / np.maximum(den, 1e-6) / step), 0, 250),
                    np.where(lakef >= 0.5, 252, 255)).astype(np.uint8).ravel()
    print('  depth grid: %d cells with depth, %d lake cells without depth data' % ((vals <= 250).sum(), (vals == 252).sum()))
    open(os.path.join(OUT, 'depth_v%d.txt' % V), 'w').write(base64.b64encode(pack_depth(vals)).decode())

    # ---- bottom grid for Kartanalys (same cells as the depth grid): bits 0-2 = Genesis hardness
    # 1..4 (soft -> hard; 0 = not measured), bit 3 = vegetation. Runs of 0 packed: 250 n_lo n_hi.
    def lay_dz(n):
        pth = os.path.join(D, n + '.png')
        return cropdz(np.array(Image.open(pth).convert('RGBA')), 0) if os.path.exists(pth) else None
    bot = np.zeros((gh, gw), np.uint8)
    v = lay_dz('v')
    if v is not None:
        vf = np.array(Image.fromarray(((v[..., 3] > 100) & water).astype(np.float32), 'F').resize((gw, gh), Image.BOX))
        bot |= ((vf >= 0.3) * 8).astype(np.uint8); del v
    c = lay_dz('c')
    if c is not None:
        cm = (c[..., 3] > 100) & water
        ck = np.argmin(((c[..., None, :3].astype(np.int32) - np.array(HARD_SRC, np.int32)) ** 2).sum(-1), axis=-1) + 1
        del c
        mf = np.array(Image.fromarray(cm.astype(np.float32), 'F').resize((gw, gh), Image.BOX))
        kf = np.array(Image.fromarray((ck * cm).astype(np.float32), 'F').resize((gw, gh), Image.BOX))
        lvl = np.where(mf >= 0.3, np.clip(np.round(kf / np.maximum(mf, 1e-6)), 1, 4), 0).astype(np.uint8)
        bot |= lvl; del ck, cm
    open(os.path.join(OUT, 'bottom_v%d.txt' % V), 'w').write(base64.b64encode(pack_bottom(bot.ravel())).decode())
    print('  bottom grid: %d cells with vegetation, %d with hardness' % (((bot & 8) > 0).sum(), ((bot & 7) > 0).sum()))

    # full-resolution depth for the tests (the crop at DZ): elevation_m = -depth, water, where it is
    rawp = os.path.join(L, 'raw', 'depth_raw.npz'); el = (-dep0).astype(np.float16); lk_ = osm | water
    old = np.load(rawp) if os.path.exists(rawp) else None
    if old is None or not (np.array_equal(old['elevation_m'], el, equal_nan=True) and np.array_equal(old['water'], water)
                           and np.array_equal(old['lake'], lk_) and list(old['origin']) == [gx0, gy0]):   # (unchanged: no new file for git)
        np.savez_compressed(rawp, elevation_m=el, water=water, lake=lk_, zoom=DZ, origin=np.array([gx0, gy0]))

    # ---- lake.json (the map picture = the lowest level)
    latc = (la0 + la1) / 2; mb = 2 ** (DZ - base)
    lk = {
        'id': src['id'], 'name': src['name'],
        'center': src.get('center') or [round(latc, 5), round((lo0 + lo1) / 2, 5)],
        'source': src.get('source', ''),
        'geo': {'zoom': base, 'originX': gx0 // mb, 'originY': gy0 // mb, 'fullW': W // mb,
                'metersPerPx': 156543.03392 * math.cos(math.radians(latc)) / 2 ** base,
                'imgW': W // mb, 'imgH': H // mb},
        'depth': {'file': 'depth_v%d.txt' % V, 'w': gw, 'h': gh, 'step': step, 'max': DMAX, 'capped': False},
        'bottom': {'file': 'bottom_v%d.txt' % V},              # (vegetation + hardness per depth-grid cell)
        'legendTicks': TICKS,                                  # (0 .. the lake's max depth)
        'contourText': 'Djupkurvor från C-MAP Genesis',
        'mapFile': 'map_v%d_{style}.jpg' % V,
        'thumbFile': 'thumbs_v%d/{style}.jpg' % V,
        # (a style with light lines names its lines folder: "lines": "lines_w")
        'styles': [dict(id=s[0], name=s[1], desc=s[2], legend=s[3], **s[4], **({} if s[6] == 'black' else {'lines': 'lines_w'})) for s in STY],
        # base pieces up to baseMax (= the depth data's zoom); every level has its own lines; above baseMax the app
        # enlarges the baseMax base under that level's lines
        'detail': {'file': 'tiles_v%d/z{z}/{style}/{c}_{r}.webp' % V, 'lines': 'tiles_v%d/z{z}/{lines}/{c}_{r}.webp' % V,
                   'baseMax': DZ, 'tile': TL, 'pad': PAD, 'levels': level_info},
    }
    json.dump(lk, open(os.path.join(L, 'lake.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    size = sum(os.path.getsize(os.path.join(dp, f2)) for dp, _, fs in os.walk(OUT) for f2 in fs)
    print('map %d x %d (zoom %d), %d detail tiles, depth grid %d x %d, docs/lakes/%s = %.1f MB' % (
        W // mb, H // mb, base, ntiles, gw, gh, lake, size / 1e6))

if __name__ == '__main__':
    main()
