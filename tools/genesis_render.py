"""Render a Genesis-based lake for the app: one picture per zoom level and map
style (Genesis' own contour lines + depth numbers for that zoom level, our
colours and relief from the calibrated depth), thumbnails, depth grid, lake.json.

    py -3 tools/genesis_render.py <lake_id>

Needs (see tools/genesis_tiles.py and tools/genesis_depth.py):
    lakes/<lake>/raw/source.json   name, zoom (= the depth data's zoom), levels, bbox or origin+size ...
    raw/<lake>/z<zoom>/depth_m.npy, water.npy   (genesis_depth.py)
    raw/<lake>/z<level>/{a,b,t,v,c}.png         for every level (genesis_tiles.py)
Writes
    docs/lakes/<lake>/map_v<V>_<style>.jpg              the whole lake at the lowest level (zoom 14)
    docs/lakes/<lake>/tiles_v<V>/z<z>/<style>/<c>_<r>.jpg  higher levels in 512 px pieces (only near water)
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

def relief(dep0, water, dz):
    """Brightness factor (1 = unchanged): light from the north + softer north-west fill,
    steep slopes darker. The same look at zoom 16 and 17 (sizes in metres)."""
    k = 2 ** (dz - 16)
    e = -dep0.copy(); e[water] = ndimage.gaussian_filter(e, 3.0 * k)[water]
    dif = 0.7 * hill(e, 40 * k, 350, 38) + 0.3 * hill(e, 40 * k, 300, 50)
    lo, hi = np.percentile(dif[water], [2, 98]); nm = np.clip((dif - lo) / (hi - lo + 1e-6), 0, 1)
    sh = 1 + (nm - 0.5) * 2 * 0.75
    gy, gx = np.gradient(ndimage.gaussian_filter(-dep0, 2.0 * k)); slope = np.hypot(gx, gy)
    sh *= 1 - 0.35 * np.clip(slope / np.percentile(slope[water], 97), 0, 1)
    return np.clip(sh, 0.35, 1.6).astype(np.float32)

def resize(arr, w, h):
    """float array (H, W[, C]) -> (h, w[, C]); area average when shrinking, bilinear when growing"""
    shrink = w < arr.shape[1]
    f = Image.BOX if shrink else Image.BILINEAR
    if arr.ndim == 2: return np.array(Image.fromarray(arr.astype(np.float32), 'F').resize((w, h), f))
    return np.dstack([np.array(Image.fromarray(arr[..., i].astype(np.float32), 'F').resize((w, h), f)) for i in range(arr.shape[2])])

def main():
    lake = sys.argv[1]
    L = os.path.join(ROOT, 'lakes', lake)
    OUT = os.path.join(ROOT, 'docs', 'lakes', lake)
    src = json.load(open(os.path.join(L, 'raw', 'source.json'), encoding='utf-8'))
    DZ = src['zoom']                                   # the depth data's zoom
    levels = sorted(src['levels']); base, top = levels[0], levels[-1]
    top_styles = src.get('top_styles')                 # styles that get levels above DZ (they're big)
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
    sh = relief(dep0, water, DZ)
    mild = 1 + (sh - 1) * 0.6

    # ---- the water colour of every style, at DZ (uint8 to save memory); None = no own colour
    def ramp(cmap): return cmap(np.clip(dep0 / DMAX, 0, 1))[..., :3].astype(np.float32) * 255
    def u8(a): return np.clip(a, 0, 255).astype(np.uint8)
    def legend_css(cmap, n=7):
        return 'linear-gradient(to right,' + ','.join('%s %d%%' % (mcolors.to_hex(cmap(i / (n - 1))), round(100 * i / (n - 1))) for i in range(n)) + ')'
    c1 = mcolors.LinearSegmentedColormap.from_list('c1', [(0.0, '#d62728'), (0.18, '#ff7f0e'), (0.36, '#ffdd00'), (0.55, '#2ca02c'), (0.72, '#17becf'), (0.87, '#1f4fd6'), (1.0, '#0a1a5c')])
    c2 = plt.get_cmap('turbo_r')
    c4 = mcolors.LinearSegmentedColormap.from_list('n', ['#24475a', '#153a55', '#0c2749', '#061532'])
    c6 = mcolors.LinearSegmentedColormap.from_list('b', ['#cfeefa', '#6fc3e8', '#2a86c9', '#12509a', '#0a2c63'])
    bands = ['#dff3fb', '#c4e7f6', '#a9dbf2', '#8fcdec', '#74bde4', '#5aa9d8', '#4796cb', '#3a84bd', '#2f72ae']
    edges = [round(DMAX * f, 1) for f in (0, 0.05, 0.125, 0.25, 0.375, 0.5, 0.625, 0.75, 0.875)]
    s3 = np.zeros(dep0.shape + (3,), np.float32); s3[:] = hx(bands[0])
    for lo, col in zip(edges[1:], bands[1:]): s3[dep0 >= lo] = hx(col)
    # (id, name, desc, legend, extra, water colour at DZ, how Genesis' lines are drawn)
    STY = [
        ('s1', 'Djupfärger', 'Flygfoto + djupfärger med relief', legend_css(c1), {}, u8(ramp(c1) * sh[..., None]), 'black'),
        ('s2', 'Förenklad', 'Klara djupfärger, utan skuggning', legend_css(c2, 9), {}, u8(ramp(c2)), 'black'),
        ('s3', 'Sjökort', 'Blå djupband som en papperskarta', 'linear-gradient(to right,' + ','.join('%s %d%%' % (c, round(100 * e / DMAX)) for c, e in zip(bands, edges)) + ')', {}, u8(s3), 'black'),
        ('s4', 'Natt', 'Mörkt vatten med ljusa djupkurvor', legend_css(c4, 4), {}, u8(ramp(c4) * mild[..., None]), (143, 233, 244)),
        ('s5', 'Flygfoto + linjer', 'Naturlig bild med vita djupkurvor', None, {}, None, (255, 255, 255)),
        ('s6', 'Blå relief', 'Blå toner med skuggad bottenform', legend_css(c6, 5), {}, u8(ramp(c6) * sh[..., None]), 'black'),
        ('g1', 'C-MAP original', 'Som på Genesis-kartan – med djupsiffror', None, {'note': 'Siffror = djup i m (liten siffra = tiondelar)'}, 'genesis', 'black'),
        ('v1', 'Vegetation', 'Grönt där ekolodet sett växtlighet', 'linear-gradient(to right,#6fc3e8 0%,#6fc3e8 50%,#46dc3c 50%,#46dc3c 100%)', {'ticks': ['Ingen', '', 'Växtlighet']}, u8(ramp(c6) * mild[..., None]), 'black'),
        ('c1', 'Bottenhårdhet', 'Mjuk (ljus) till hård (röd) botten, där det finns mätt', 'linear-gradient(to right,#ffffcc 0%,#fec25d 33%,#fc8643 66%,#fa4a29 100%)', {'ticks': ['Mjuk', '', 'Hård']}, u8(ramp(c6) * 0.55 + 60), 'black'),
    ]
    del s3

    # ---- output folder: only this version's pictures
    os.makedirs(OUT, exist_ok=True)
    for f in os.listdir(OUT):
        p = os.path.join(OUT, f)
        shutil.rmtree(p) if os.path.isdir(p) else os.remove(p)
    os.makedirs(os.path.join(OUT, 'thumbs_v%d' % V))
    level_info = []; ntiles = 0

    for z in levels:
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
        aer = lay('a', 'RGB').astype(np.float32)
        t = lay('t').astype(np.float32)
        wl = resize(water.astype(np.float32), w, h)
        wat = wl >= 0.5
        alpha = np.clip(ndimage.gaussian_filter(wl, 0.6), 0, 1)[..., None]
        near = ndimage.binary_dilation(wat, iterations=max(3, int(14 / f)))[..., None]   # Genesis layers only on our lake
        ta = t[..., 3:4] / 255 * near
        # depth numbers = the light halo round them (lines, even melted together on steep slopes, are black)
        labels = ndimage.binary_dilation((t[..., :3].mean(2) > 170) & (t[..., 3] > 60), iterations=3)[..., None]
        styles_here = [s for s in STY if z <= DZ or not top_styles or s[0] in top_styles]
        for sid, name, desc, leg, extra, colour, lines in styles_here:
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
                    c = c.astype(np.float32); ca = c[..., 3:4] / 255 * 0.9 * alpha
                    img = img * (1 - ca) + c[..., :3] * ca
            # Genesis' contour lines + depth numbers for this zoom (light lines on dark styles; numbers as they are)
            if lines == 'black':
                img = img * (1 - ta) + t[..., :3] * ta
            else:
                col = np.where(labels, t[..., :3], np.asarray(lines, np.float32))
                img = img * (1 - ta) + col * ta
            im = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))
            if z == base:
                im.save(os.path.join(OUT, 'map_v%d_%s.jpg' % (V, sid)), quality=84, optimize=True, progressive=True)
            else:
                cols, rows = -(-w // TL), -(-h // TL)
                nearw = ndimage.binary_dilation(wat, iterations=24)
                have = ''.join('1' if nearw[r * TL:(r + 1) * TL, c * TL:(c + 1) * TL].any() else '0' for r in range(rows) for c in range(cols))
                td = os.path.join(OUT, 'tiles_v%d' % V, 'z%d' % z, sid); os.makedirs(td)
                pad = Image.new('RGB', (cols * TL, rows * TL)); pad.paste(im, (0, 0))
                for r in range(rows):
                    for c in range(cols):
                        if have[r * cols + c] == '1':
                            pad.crop((c * TL, r * TL, (c + 1) * TL, (r + 1) * TL)).save(os.path.join(td, '%d_%d.jpg' % (c, r)), quality=80, optimize=True)
                            ntiles += 1
                if sid == styles_here[0][0]:
                    level_info.append({'z': z, 'cols': cols, 'rows': rows, 'have': have, 'styles': [s[0] for s in styles_here]})
            if z == base + 1:   # thumbnails: a 200x120 look at the middle of the lake at zoom 15
                ys, xs = np.where(wat); my, mx = int(np.median(ys)), int(np.median(xs))
                tw = int(w * 0.3); th = int(tw * 0.6)
                im.crop((mx - tw // 2, my - th // 2, mx + tw // 2, my + th // 2)).resize((200, 120), Image.LANCZOS).save(
                    os.path.join(OUT, 'thumbs_v%d' % V, '%s.jpg' % sid), quality=82)
        print('  zoom %d: %d x %d px, %d styles' % (z, w, h, len(styles_here)))
        del aer, t

    # ---- depth grid for the app (one byte per cell = depth / step; 255 land; runs of land packed)
    gd = src['grid_div']; gw, gh = int(round(W / gd)), int(round(H / gd))
    wf = water.astype(np.float32)
    num = np.array(Image.fromarray(dep0 * wf, 'F').resize((gw, gh), Image.BOX))
    den = np.array(Image.fromarray(wf, 'F').resize((gw, gh), Image.BOX))
    step = src['depth_step']
    vals = np.where(den >= 0.5, np.clip(np.round(num / np.maximum(den, 1e-6) / step), 0, 250), 255).astype(np.uint8).ravel()
    enc = bytearray(); i = 0
    while i < len(vals):
        if vals[i] == 255:
            j = i
            while j < len(vals) and vals[j] == 255 and j - i < 65535: j += 1
            n = j - i
            enc += bytes([251, n & 255, n >> 8]) if n >= 3 else bytes([255] * n)
            i = j
        else:
            enc.append(vals[i]); i += 1
    open(os.path.join(OUT, 'depth_v%d.txt' % V), 'w').write(base64.b64encode(bytes(enc)).decode())

    # full-resolution depth for the tests (the crop at DZ): elevation_m = -depth, water, where it is
    np.savez_compressed(os.path.join(L, 'raw', 'depth_raw.npz'), elevation_m=(-dep0).astype(np.float16), water=water,
                        zoom=DZ, origin=np.array([gx0, gy0]))

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
        'legendTicks': ['0 m', '%d m' % (DMAX // 2), '%d m' % DMAX],
        'contourText': 'Djupkurvor från C-MAP Genesis',
        'mapFile': 'map_v%d_{style}.jpg' % V,
        'thumbFile': 'thumbs_v%d/{style}.jpg' % V,
        'styles': [dict(id=s[0], name=s[1], desc=s[2], legend=s[3], **s[4]) for s in STY],
        'detail': {'file': 'tiles_v%d/z{z}/{style}/{c}_{r}.jpg' % V, 'tile': TL, 'levels': level_info},
    }
    json.dump(lk, open(os.path.join(L, 'lake.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    size = sum(os.path.getsize(os.path.join(dp, f2)) for dp, _, fs in os.walk(OUT) for f2 in fs)
    print('map %d x %d (zoom %d), %d detail tiles, depth grid %d x %d, docs/lakes/%s = %.1f MB' % (
        W // mb, H // mb, base, ntiles, gw, gh, lake, size / 1e6))

if __name__ == '__main__':
    main()
