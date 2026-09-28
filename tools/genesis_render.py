"""Render a Genesis-based lake for the app: map styles, detail tiles,
thumbnails, depth grid and lake.json.

    py -3 tools/genesis_render.py <lake_id>

Needs (see tools/genesis_tiles.py and tools/genesis_depth.py):
    lakes/<lake>/raw/source.json      name, zoom, bbox (lat_min, lat_max, lon_min, lon_max), sizes
    raw/<lake>/z<zoom>/{a,b,t,v,c}.png, depth_m.npy, water.npy, grid.json
Writes lakes/<lake>/:
    map_v1_<style>.jpg                the whole map, downscaled (base_div) -- shown first
    tiles_v1/<style>/<c>_<r>.jpg      full-resolution pieces (tile px), only where there is water
    thumbs/<style>.jpg                200x120 previews for the style picker
    depth_v1.txt                      depth grid (see app: depthAtImgPx)
    lake.json                         everything the app needs to know about the lake
"""
import sys, os, json, math, shutil
import numpy as np
from PIL import Image
from scipy import ndimage
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import colors as mcolors
Image.MAX_IMAGE_PIXELS = None
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def hx(s): return np.array([int(s[i:i + 2], 16) for i in (1, 3, 5)], np.float32)

def main():
    lake = sys.argv[1]
    L = os.path.join(ROOT, 'lakes', lake)
    src = json.load(open(os.path.join(L, 'raw', 'source.json'), encoding='utf-8'))
    z = src['zoom']; D = os.path.join(ROOT, 'raw', lake, 'z%d' % z)
    g = json.load(open(os.path.join(D, 'grid.json')))

    # ---- crop = the bbox, in global pixels at this zoom
    def gpx(lat, lon):
        n = 256 * 2 ** z
        return ((lon + 180) / 360 * n,
                (1 - math.log(math.tan(math.radians(lat)) + 1 / math.cos(math.radians(lat))) / math.pi) / 2 * n)
    la0, la1, lo0, lo1 = src['bbox']
    if 'origin' in src:        # an exact crop (e.g. to keep an existing lake's geo-reference)
        (gx0, gy0), (W, H) = src['origin'], src['size']
    else:
        gx0, gy0 = gpx(la1, lo0); gx1, gy1 = gpx(la0, lo1)
        gx0, gy0 = int(round(gx0)), int(round(gy0))
        W, H = int(round(gx1)) - gx0, int(round(gy1)) - gy0
    V = src.get('version', 1)  # file version: a new version = new file names, so phones don't keep old copies
    cx0, cy0 = gx0 - g['tile_x0'] * 256, gy0 - g['tile_y0'] * 256    # inside the canvases
    TL = src['tile']; cols, rows = -(-W // TL), -(-H // TL)
    PW, PH = cols * TL, rows * TL                                       # padded for whole tiles
    print('crop %d x %d px at z%d, %d x %d detail tiles' % (W, H, z, cols, rows))

    def crop(arr, fill=0):
        out = np.full((PH, PW) + arr.shape[2:], fill, arr.dtype)
        y1, x1 = min(arr.shape[0], cy0 + PH), min(arr.shape[1], cx0 + PW)
        out[:y1 - cy0, :x1 - cx0] = arr[cy0:y1, cx0:x1]
        return out
    def layer(name, mode='RGBA'):
        if name == 'b' and os.path.exists(os.path.join(D, 'b_fixed.png')): name = 'b_fixed'  # seams closed
        return crop(np.array(Image.open(os.path.join(D, name + '.png')).convert(mode)))
    aer = layer('a', 'RGB').astype(np.float32)
    dep = crop(np.load(os.path.join(D, 'depth_m.npy')), np.nan)
    water = crop(np.load(os.path.join(D, 'water.npy')), False)
    dep0 = np.where(water, dep, 0).astype(np.float32)
    maxd = float(np.nanmax(dep))
    sc = 2 if maxd <= 20 else 5
    DMAX = sc * math.ceil(maxd / sc)                   # colour scale 0..DMAX (Vågsfjärden 40, Regnaren 12)
    print('max depth %.1f m -> scale 0-%d m' % (maxd, DMAX))

    # soft shoreline + shading
    alpha = ndimage.gaussian_filter(water.astype(np.float32), 1.0)
    dsm = ndimage.gaussian_filter(dep0, 2.0)
    def hillshade(zf, az=315, alt=40, sig=6):
        zz = ndimage.gaussian_filter(dep0, sig)
        gx = ndimage.sobel(zz, 1) / 8.0; gy = ndimage.sobel(zz, 0) / 8.0
        nx, ny, nz = gx * zf, gy * zf, np.ones_like(zz)
        n = np.sqrt(nx * nx + ny * ny + nz * nz); a, b = np.deg2rad(az), np.deg2rad(alt)
        return np.clip((nx * np.cos(b) * np.sin(a) - ny * np.cos(b) * np.cos(a) + nz * np.sin(b)) / n, 0, 1)
    hs = hillshade(1.6)
    # depth contours, anti-aliased: each pixel's distance (px) to the nearest
    # level line = depth difference / slope; the line fades out over its edge,
    # so it stays smooth however far you zoom in
    gy, gx = np.gradient(dsm); slope = np.hypot(gx, gy) + 1e-4
    def dist(step):
        f = np.mod(dsm, step); return np.minimum(f, step - f) / slope
    def line_alpha(d, width, min_depth):
        a = np.clip(width / 2 + 0.5 - d, 0, 1)
        return (a * (water & (dsm > min_depth))).astype(np.float32)
    # lines: every metre down to 10 m, then every 2 m; strong every 5 m
    minor = line_alpha(np.where(dsm <= 10.5, dist(1.0), dist(2.0)), 1.6, 0.5)
    major = line_alpha(dist(5.0), 2.6, 2.5)
    del gx, gy
    shore = (water & ~ndimage.binary_erosion(water, iterations=4)).astype(np.float32)
    def mix(base, a, color, k):
        a = (a * k)[..., None]
        base *= (1 - a); base += np.asarray(color, np.float32) * a
    def ramp(cmap):
        return cmap(np.clip(dep0 / DMAX, 0, 1))[..., :3].astype(np.float32) * 255
    def legend_css(cmap, n=7):
        return 'linear-gradient(to right,' + ','.join(
            '%s %d%%' % (mcolors.to_hex(cmap(i / (n - 1))), round(100 * i / (n - 1))) for i in range(n)) + ')'
    def finish(w):
        return aer * (1 - alpha[..., None]) + np.clip(w, 0, 255) * alpha[..., None]
    def over(base, name):   # a Genesis layer (RGBA) laid over an image
        lay = layer(name).astype(np.float32); a = lay[..., 3:4] / 255
        return base * (1 - a) + lay[..., :3] * a

    styles = []
    out = {}
    # s1: depth colours with relief (the same colours as Regnaren's first style)
    c1 = mcolors.LinearSegmentedColormap.from_list('c1', [(0.0, '#d62728'), (0.18, '#ff7f0e'), (0.36, '#ffdd00'), (0.55, '#2ca02c'), (0.72, '#17becf'), (0.87, '#1f4fd6'), (1.0, '#0a1a5c')])
    w = ramp(c1) * (0.62 + 0.55 * hs[..., None]); mix(w, minor, (0, 0, 0), 0.28); mix(w, major, (0, 0, 0), 0.5); mix(w, shore, (20, 20, 20), 0.6)
    out['s1'] = finish(w); styles.append(dict(id='s1', name='Djupfärger', desc='Flygfoto + djupfärger med relief', legend=legend_css(c1)))
    # s2: simplified
    c2 = plt.get_cmap('turbo_r')
    w = ramp(c2); mix(w, minor, (0, 0, 0), 0.4); mix(w, major, (0, 0, 0), 0.65); mix(w, shore, (20, 20, 20), 0.85)
    out['s2'] = finish(w); styles.append(dict(id='s2', name='Förenklad', desc='Klara djupfärger och tydliga djupkurvor', legend=legend_css(c2, 9)))
    # s3: sea chart, blue bands (at 40 m: 2, 5, 10, 15 ... 35 m -- scaled to the lake)
    bands = ['#dff3fb', '#c4e7f6', '#a9dbf2', '#8fcdec', '#74bde4', '#5aa9d8', '#4796cb', '#3a84bd', '#2f72ae']
    w = np.zeros(dep0.shape + (3,), np.float32); w[:] = hx(bands[0])
    edges = [round(DMAX * f, 1) for f in (0, 0.05, 0.125, 0.25, 0.375, 0.5, 0.625, 0.75, 0.875)]
    for lo, col in zip(edges[1:], bands[1:]): w[dsm >= lo] = hx(col)
    mix(w, minor, hx('#3a78a8'), 0.45); mix(w, major, hx('#1f5a8a'), 0.7); mix(w, shore, hx('#5b4b2a'), 0.85)
    out['s3'] = finish(w)
    stops = ','.join('%s %d%%' % (c, round(100 * e / DMAX)) for c, e in zip(bands, edges))
    styles.append(dict(id='s3', name='Sjökort', desc='Blå djupband som en papperskarta', legend='linear-gradient(to right,' + stops + ')'))
    # s4: night
    c4 = mcolors.LinearSegmentedColormap.from_list('n', ['#24475a', '#153a55', '#0c2749', '#061532'])
    w = ramp(c4) * (0.75 + 0.4 * hs[..., None]); mix(w, minor, hx('#39c5d6'), 0.4); mix(w, major, hx('#8fe9f4'), 0.6); mix(w, shore, hx('#8fd3dc'), 0.8)
    out['s4'] = finish(w); styles.append(dict(id='s4', name='Natt', desc='Mörkt vatten med ljusa djupkurvor', legend=legend_css(c4, 4)))
    # s5: aerial + lines
    w = aer * np.array([0.9, 0.97, 1.05], np.float32); mix(w, minor, (255, 255, 255), 0.4); mix(w, major, (255, 255, 255), 0.75); mix(w, shore, (255, 236, 160), 0.85)
    out['s5'] = finish(w); styles.append(dict(id='s5', name='Flygfoto + linjer', desc='Naturlig bild med vita djupkurvor', legend=None))
    # s6: blue relief
    c6 = mcolors.LinearSegmentedColormap.from_list('b', ['#cfeefa', '#6fc3e8', '#2a86c9', '#12509a', '#0a2c63'])
    w = ramp(c6) * (0.55 + 0.6 * hs[..., None]); mix(w, major, (10, 30, 60), 0.3); mix(w, shore, (245, 250, 252), 0.7)
    out['s6'] = finish(w); styles.append(dict(id='s6', name='Blå relief', desc='Blå toner med skuggad bottenform', legend=legend_css(c6, 5)))
    # g1: the original C-MAP Genesis look, with its depth numbers
    base = over(over(aer.copy(), 'b'), 't')
    out['g1'] = base; styles.append(dict(id='g1', name='C-MAP original', desc='Som på Genesis-kartan – med djupsiffror', legend=None, note='Siffror = djup i m (liten siffra = tiondelar)'))
    # v1: vegetation over a calm blue depth picture
    w = ramp(c6) * (0.7 + 0.35 * hs[..., None]); mix(w, major, (10, 30, 60), 0.35); mix(w, shore, (245, 250, 252), 0.6)
    w = finish(w)
    veg = layer('v').astype(np.float32); va = (veg[..., 3:4] / 255) * 0.72 * alpha[..., None]   # (only on our lake)
    w = w * (1 - va) + np.array([70, 220, 60], np.float32) * va
    out['v1'] = w; styles.append(dict(id='v1', name='Vegetation', desc='Grönt där ekolodet sett växtlighet', legend='linear-gradient(to right,#6fc3e8 0%,#6fc3e8 50%,#46dc3c 50%,#46dc3c 100%)', ticks=['Ingen', '', 'Växtlighet']))
    # c1: bottom hardness (only where boats have logged sonar)
    w = ramp(c6) * 0.55 + 60; mix(w, major, (10, 30, 60), 0.35); mix(w, shore, (245, 250, 252), 0.6)
    w = finish(w)
    hard = layer('c').astype(np.float32); ha = hard[..., 3:4] / 255 * 0.9 * alpha[..., None]
    w = w * (1 - ha) + hard[..., :3] * ha
    out['c1'] = w; styles.append(dict(id='c1', name='Bottenhårdhet', desc='Mjuk (ljus) till hård (röd) botten, där det finns mätt', legend='linear-gradient(to right,#ffffcc 0%,#fec25d 33%,#fc8643 66%,#fa4a29 100%)', ticks=['Mjuk', '', 'Hård']))

    # ---- write pictures
    imgW = src['img_w'] if 'img_w' in src else int(round(W / src['base_div']))
    S = imgW / W; imgH = int(round(H * S))
    # clear out the lake's pictures (any version) -- only this version is kept
    for f in os.listdir(L):
        p = os.path.join(L, f)
        if f.startswith(('thumbs', 'tiles_v')) and os.path.isdir(p): shutil.rmtree(p)
        elif (f.startswith('map_v') and f.endswith('.jpg')) or (f.startswith('depth_v') and f.endswith('.txt')): os.remove(p)
    os.makedirs(os.path.join(L, 'thumbs_v%d' % V))
    near_water = ndimage.binary_dilation(water, iterations=40)
    have = ''.join('1' if near_water[r * TL:(r + 1) * TL, c * TL:(c + 1) * TL].any() else '0'
                   for r in range(rows) for c in range(cols))
    ntiles = 0
    for sid, arr in out.items():
        im = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
        im.crop((0, 0, W, H)).resize((imgW, imgH), Image.LANCZOS).save(
            os.path.join(L, 'map_v%d_%s.jpg' % (V, sid)), quality=84, optimize=True, progressive=True)
        td = os.path.join(L, 'tiles_v%d' % V, sid); os.makedirs(td)
        for r in range(rows):
            for c in range(cols):
                if have[r * cols + c] != '1': continue
                im.crop((c * TL, r * TL, (c + 1) * TL, (r + 1) * TL)).save(
                    os.path.join(td, '%d_%d.jpg' % (c, r)), quality=78, optimize=True)
                ntiles += 1
        # thumbnail: a 200x120 look at the middle of the lake
        tw, th = int(W * 0.34), int(W * 0.34 * 0.6)
        ys, xs = np.where(water[:H, :W]); my, mx = int(np.median(ys)), int(np.median(xs))
        im.crop((mx - tw // 2, my - th // 2, mx + tw // 2, my + th // 2)).resize((200, 120), Image.LANCZOS).save(
            os.path.join(L, 'thumbs_v%d' % V, '%s.jpg' % sid), quality=82)
        print('  %s done' % sid)

    # ---- depth grid for the app (one byte per cell = depth / step; 255 land; runs of land packed)
    gd = src['grid_div']; gw, gh = int(round(W / gd)), int(round(H / gd))
    wf = water[:H, :W].astype(np.float32)
    num = np.array(Image.fromarray(dep0[:H, :W] * wf, 'F').resize((gw, gh), Image.BOX))
    den = np.array(Image.fromarray(wf, 'F').resize((gw, gh), Image.BOX))
    step = src['depth_step']
    vals = np.where(den >= 0.5, np.clip(np.round(num / np.maximum(den, 1e-6) / step), 0, 250), 255).astype(np.uint8).ravel()
    enc = bytearray(); i = 0
    while i < len(vals):
        if vals[i] == 255:
            j = i
            while j < len(vals) and vals[j] == 255 and j - i < 65535: j += 1
            n = j - i
            if n >= 3: enc += bytes([251, n & 255, n >> 8])
            else: enc += bytes([255] * n)
            i = j
        else:
            enc.append(vals[i]); i += 1
    import base64
    open(os.path.join(L, 'depth_v%d.txt' % V), 'w').write(base64.b64encode(bytes(enc)).decode())

    # full-resolution depth for the tests (same crop as the map): elevation_m = -depth, water
    np.savez_compressed(os.path.join(L, 'raw', 'depth_raw.npz'),
                        elevation_m=(-dep0[:H, :W]).astype(np.float16), water=water[:H, :W])

    # ---- lake.json
    latc = (la0 + la1) / 2
    lk = {
        'id': src['id'], 'name': src['name'],
        'center': src.get('center') or [round(latc, 5), round((lo0 + lo1) / 2, 5)],
        'source': src.get('source', ''),
        'geo': {'zoom': z, 'originX': gx0, 'originY': gy0, 'fullW': W,
                'metersPerPx': 156543.03392 * math.cos(math.radians(latc)) / 2 ** z,
                'imgW': imgW, 'imgH': imgH},
        'depth': {'file': 'depth_v%d.txt' % V, 'w': gw, 'h': gh, 'step': step, 'max': DMAX, 'capped': False},
        'legendTicks': ['0 m', '%d m' % (DMAX // 2), '%d m' % DMAX],
        'contourText': 'Djupkurvor var 1 m' if maxd <= 10.5 else 'Djupkurvor var 1 m (2 m under 10 m)',
        'mapFile': 'map_v%d_{style}.jpg' % V,
        'thumbFile': 'thumbs_v%d/{style}.jpg' % V,
        'styles': styles,
        'detail': {'file': 'tiles_v%d/{style}/{c}_{r}.jpg' % V, 'tile': TL, 'cols': cols, 'rows': rows,
                   'have': have, 'styles': [s['id'] for s in styles]},
    }
    json.dump(lk, open(os.path.join(L, 'lake.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    size = sum(os.path.getsize(os.path.join(dp, f)) for dp, _, fs in os.walk(L) for f in fs if 'raw' not in dp)
    print('image %d x %d, %d detail tiles, depth grid %d x %d (%d kB), lake folder %.1f MB' % (
        imgW, imgH, ntiles, gw, gh, len(enc) * 4 // 3 // 1024, size / 1e6))

if __name__ == '__main__':
    main()
