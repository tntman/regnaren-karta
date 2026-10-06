"""Download C-MAP Genesis Social Map tiles (+ aerial photo) for a lake and
stitch them into one canvas per layer.

    py -3 tools/genesis_tiles.py <lake_id> <zoom> <lat_min> <lat_max> <lon_min> <lon_max> [layers]

Layers (Bing quadkey tiles, 256 px, Web Mercator -- same as Genesis' web map):
    b  depth colours          (socialmap.genesismaps.com/img/b_<qk>.png)
    t  contour lines + labels (.../t_<qk>.png)
    v  vegetation             (.../v_<qk>.png)
    c  bottom hardness        (.../c_<qk>.png)
    a  aerial photo (Bing)    (ecn.tX.tiles.virtualearth.net/tiles/a<qk>.jpeg)
Genesis serves zoom 12..18 (19+ -> 403).

Tiles are cached in raw/<lake>/z<zoom>/<layer>/ (not in git, can be large);
the stitched canvases go to raw/<lake>/z<zoom>/<layer>.png plus a
raw/<lake>/z<zoom>/grid.json with the tile origin (for geo-referencing).
Polite: one request at a time, cached, never fetched twice.
"""
import sys, os, math, json, time, urllib.request
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UA = {'User-Agent': 'Mozilla/5.0 (FF Map lake chart builder)', 'Referer': 'https://www.genesismaps.com/'}
SRC = {
    'b': 'https://socialmap.genesismaps.com/img/b_{qk}.png',
    't': 'https://socialmap.genesismaps.com/img/t_{qk}.png',
    'v': 'https://socialmap.genesismaps.com/img/v_{qk}.png',
    'c': 'https://socialmap.genesismaps.com/img/c_{qk}.png',
    'a': 'https://ecn.t{s}.tiles.virtualearth.net/tiles/a{qk}.jpeg?g=14000',
}

def quadkey(x, y, z):
    s = ''
    for i in range(z, 0, -1):
        m = 1 << (i - 1)
        s += str((1 if x & m else 0) + (2 if y & m else 0))
    return s

def ll2px(lat, lon, z):
    n = 256 * 2 ** z
    x = (lon + 180) / 360 * n
    y = (1 - math.log(math.tan(math.radians(lat)) + 1 / math.cos(math.radians(lat))) / math.pi) / 2 * n
    return x, y

def fetch(url, path):
    if os.path.exists(path):
        return True
    if os.path.exists(path + '.none'):   # known to be missing (403 earlier) -- don't ask again
        return False
    for attempt in range(3):
        try:
            r = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30)
            data = r.read()
            os.makedirs(os.path.dirname(path), exist_ok=True)
            open(path, 'wb').write(data)
            return True
        except urllib.error.HTTPError as e:
            if e.code in (403, 404):     # no data there -- remember it
                os.makedirs(os.path.dirname(path), exist_ok=True)
                open(path + '.none', 'w').close()
                return False
            time.sleep(1 + attempt)
        except Exception:
            time.sleep(1 + attempt)
    return False

def main():
    lake, z = sys.argv[1], int(sys.argv[2])
    la0, la1, lo0, lo1 = map(float, sys.argv[3:7])
    layers = sys.argv[7] if len(sys.argv) > 7 else 'btvca'
    x0, y1 = ll2px(la0, lo0, z); x1, y0 = ll2px(la1, lo1, z)
    tx0, ty0, tx1, ty1 = int(x0 // 256), int(y0 // 256), int(x1 // 256), int(y1 // 256)
    nx, ny = tx1 - tx0 + 1, ty1 - ty0 + 1
    out = os.path.join(ROOT, 'raw', lake, 'z%d' % z)
    print('zoom %d: %d x %d tiles = %d per layer' % (z, nx, ny, nx * ny))
    json.dump({'zoom': z, 'tile_x0': tx0, 'tile_y0': ty0, 'nx': nx, 'ny': ny}, open(os.path.join(out, 'grid.json') if os.path.isdir(out) else _mk(out, 'grid.json'), 'w'))
    # FF_SHARD=k/n: only fetch every n-th row (starting at k), no stitching -- run several
    # of these side by side to download faster, then once without FF_SHARD to stitch
    # (everything is cached by then, so that run is quick)
    shard = os.environ.get('FF_SHARD')
    sk, sn = (int(v) for v in shard.split('/')) if shard else (0, 1)
    # FF_CLIP=<polygon json> ("polygon_latlon": [[lat, lon], ...], e.g. tools/malaren_polygon.json): only tiles
    # inside the polygon (+ 2 tiles round it) -- for a big lake where only a part is wanted
    clip = None
    if os.environ.get('FF_CLIP'):
        from PIL import ImageDraw
        import numpy as np
        poly = json.load(open(os.environ['FF_CLIP'], encoding='utf-8'))['polygon_latlon']
        m = Image.new('L', (nx, ny), 0)
        ImageDraw.Draw(m).polygon([(ll2px(a, b, z)[0] / 256 - tx0, ll2px(a, b, z)[1] / 256 - ty0) for a, b in poly], fill=1, outline=1)
        clip = np.array(m, bool)
        for _ in range(2):
            c2 = clip.copy(); c2[1:] |= clip[:-1]; c2[:-1] |= clip[1:]; c2[:, 1:] |= clip[:, :-1]; c2[:, :-1] |= clip[:, 1:]; clip = c2
        print('  FF_CLIP: %d of %d tiles per layer' % (clip.sum(), nx * ny))
    for L in layers:
        mode = 'RGB' if L == 'a' else 'RGBA'
        canvas = None if shard else Image.new(mode, (nx * 256, ny * 256))
        got = 0
        for j in range(ny):
            if j % sn != sk: continue
            for i in range(nx):
                if clip is not None and not clip[j, i]: continue
                qk = quadkey(tx0 + i, ty0 + j, z)
                p = os.path.join(out, L, qk + ('.jpg' if L == 'a' else '.png'))
                if fetch(SRC[L].format(qk=qk, s=(i + j) % 4), p):
                    got += 1
                    if canvas is None: continue
                    try:
                        canvas.paste(Image.open(p).convert(mode), (i * 256, j * 256))
                    except Exception as e:
                        print('  bad tile', p, e)
            print('  %s row %d/%d' % (L, j + 1, ny), end='\r')
        if canvas is None:
            print('  %s: shard %d/%d fetched (%d tiles)' % (L, sk, sn, got)); continue
        canvas.save(os.path.join(out, L + '.png'))
        print('  %s: %d/%d tiles -> %s.png' % (L, got, nx * ny, L))

def _mk(d, f):
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, f)

if __name__ == '__main__':
    main()
