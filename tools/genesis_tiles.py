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
    for attempt in range(3):
        try:
            r = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30)
            data = r.read()
            os.makedirs(os.path.dirname(path), exist_ok=True)
            open(path, 'wb').write(data)
            return True
        except urllib.error.HTTPError as e:
            if e.code in (403, 404):
                return False  # no data there
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
    for L in layers:
        mode = 'RGB' if L == 'a' else 'RGBA'
        canvas = Image.new(mode, (nx * 256, ny * 256))
        got = 0
        for j in range(ny):
            for i in range(nx):
                qk = quadkey(tx0 + i, ty0 + j, z)
                p = os.path.join(out, L, qk + ('.jpg' if L == 'a' else '.png'))
                if fetch(SRC[L].format(qk=qk, s=(i + j) % 4), p):
                    try:
                        canvas.paste(Image.open(p).convert(mode), (i * 256, j * 256)); got += 1
                    except Exception as e:
                        print('  bad tile', p, e)
            print('  %s row %d/%d' % (L, j + 1, ny), end='\r')
        canvas.save(os.path.join(out, L + '.png'))
        print('  %s: %d/%d tiles -> %s.png' % (L, got, nx * ny, L))

def _mk(d, f):
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, f)

if __name__ == '__main__':
    main()
