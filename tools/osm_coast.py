"""The sea as water for a lake on the coast (Gryts Skärgård): OpenStreetMap's coastline, no depth.

    py -3 tools/osm_coast.py <lake>      (before genesis_big.py render; like osm_water.py for an inland lake)

Writes raw/<lake>/z<DZ>/sea_z15.npz (sea: bool, zoom 15 over the lake's crop). The coastline ways
(natural=coastline, Overpass) are drawn as walls; OSM draws them with the land on the left, so a point just
right of each piece is sea and one just left is land -- each area between the walls is sea when most of its
points say so. genesis_big.block_depth treats it like osm_water: water with unknown depth in the depth grid
(the white shoreline, the lead line's "water"), the map picture stays the aerial photo. Never depth.
Map data (c) OpenStreetMap contributors (ODbL).
"""
import sys, os, json, math, time, urllib.request, urllib.parse
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import genesis_big as B
Z = 15

def main(lake):
    lk = B.Lake(lake); la0, la1, lo0, lo1 = lk.src['bbox']; M = 0.02
    f = 2 ** (lk.DZ - Z); ox, oy = lk.gx0 / f, lk.gy0 / f; W, H = lk.W // f, lk.H // f
    q = '[out:json][timeout:120];way[natural=coastline](%f,%f,%f,%f);out geom;' % (la0 - M, lo0 - M, la1 + M, lo1 + M)
    req = urllib.request.Request('https://overpass-api.de/api/interpreter', data=urllib.parse.urlencode({'data': q}).encode(),
                                 headers={'User-Agent': 'FF Map lake builder (private fishing app)'})
    for attempt in range(5):          # the public Overpass server is often busy: try again
        try: ways = json.loads(urllib.request.urlopen(req, timeout=180).read())['elements']; break
        except Exception as e: print('  busy (%s), trying again ...' % e); time.sleep(10 * (attempt + 1))
    else: raise SystemExit('OpenStreetMap did not answer -- try again later')
    wall = Image.new('1', (W, H), 0); dr = ImageDraw.Draw(wall); right, left = [], []
    for w in ways:
        pts = [(B.gpx(p['lat'], p['lon'], Z)[0] - ox, B.gpx(p['lat'], p['lon'], Z)[1] - oy) for p in w['geometry']]
        dr.line(pts, fill=1, width=3)
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            L = math.hypot(x1 - x0, y1 - y0)
            if L < 8: continue
            mx, my, nx, ny = (x0 + x1) / 2, (y0 + y1) / 2, -(y1 - y0) / L * 4, (x1 - x0) / L * 4    # (n: 4 px to the right, y down)
            right.append((mx + nx, my + ny)); left.append((mx - nx, my - ny))
    wall = np.array(wall, bool)
    lab, k = ndimage.label(~wall)
    def votes(pts):
        v = np.zeros(k + 1, np.int64)
        for x, y in pts:
            xi, yi = int(x), int(y)
            if 0 <= xi < W and 0 <= yi < H: v[lab[yi, xi]] += 1
        return v
    r, l = votes(right), votes(left)
    is_sea = r > l; is_sea[0] = False
    sea = is_sea[lab]; del lab
    sea |= wall & ndimage.binary_dilation(sea, iterations=2)      # (the wall itself: water up to the shore)
    sea &= lk.clip_mask(Z, 0, 0, W, H)
    np.savez_compressed(os.path.join(lk.D, 'sea_z15.npz'), sea=sea)
    print('  %d coastline ways, sea %.0f %% of the crop -> %s' % (len(ways), sea.mean() * 100, os.path.join(lk.D, 'sea_z15.npz')))
    Image.fromarray((sea * 255).astype(np.uint8)).resize((W // 4, H // 4)).save(os.path.join(lk.D, 'sea_preview.png'))

if __name__ == '__main__':
    main(sys.argv[1])
