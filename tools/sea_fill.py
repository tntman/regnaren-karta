"""The sea where Genesis has no data (Gryts Skärgård): water from OpenStreetMap's coastline, a rough depth
from EMODnet Bathymetry (open data, ~115 m grid) -- tools/KARTOR.md "Hav utan Genesis".

    py -3 tools/sea_fill.py <lake>      (source.json "fill": "emodnet"; run before genesis_big.py relief/render)

Writes raw/<lake>/z<DZ>/sea_z15.npz: sea (bool) + dep (m, float16) at zoom 15 over the lake's crop.
The coastline is drawn as a wall and the sea flood-filled from EMODnet's deep cells (land, islands and
inland lakes stay out). The depth: EMODnet (holes filled from the nearest cell), at most
0.4 m + 6 cm per metre from the shore so it shoals toward land. genesis_big.block_depth uses it where
Genesis has nothing -- colours, relief, the depth grid (lead line, Kartanalys). Never lines or numbers.
Map data (c) OpenStreetMap contributors (ODbL); EMODnet Bathymetry Consortium (CC BY 4.0).
"""
import sys, os, io, json, math, time, urllib.request, urllib.parse
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import genesis_big as B
Z = 15

def gpx(lat, lon, z):
    n = 256 * 2 ** z
    return ((lon + 180) / 360 * n, (1 - math.log(math.tan(math.radians(lat)) + 1 / math.cos(math.radians(lat))) / math.pi) / 2 * n)

def get(url, data=None):
    req = urllib.request.Request(url, data=data, headers={'User-Agent': 'FF Map lake builder (private fishing app)'})
    for attempt in range(5):
        try: return urllib.request.urlopen(req, timeout=180).read()
        except Exception as e: print('  busy (%s), trying again ...' % e); time.sleep(10 * (attempt + 1))
    raise SystemExit('no answer from ' + url.split('/')[2])

def main(lake):
    lk = B.Lake(lake); la0, la1, lo0, lo1 = lk.src['bbox']; M = 0.02
    f = 2 ** (lk.DZ - Z); ox, oy = lk.gx0 / f, lk.gy0 / f; W, H = lk.W // f, lk.H // f
    # EMODnet: elevation (negative = depth), 1/16 arc minute
    D = 1 / 960; e0, e1, n0, n1 = lo0 - M, lo1 + M, la0 - M, la1 + M
    tif = get('https://ows.emodnet-bathymetry.eu/wcs?service=WCS&version=1.0.0&request=GetCoverage&coverage=emodnet:mean'
              '&crs=EPSG:4326&BBOX=%f,%f,%f,%f&format=image/tiff&resx=%.10f&resy=%.10f' % (e0, n0, e1, n1, D, D))
    import tifffile
    el = tifffile.imread(io.BytesIO(tif)).astype(np.float32)
    rx, ry = (e1 - e0) / el.shape[1], (n1 - n0) / el.shape[0]
    # coastline (OSM): every coastline way in the box, as a wall
    q = '[out:json][timeout:120];way[natural=coastline](%f,%f,%f,%f);out geom;' % (n0, e0, n1, e1)
    ways = json.loads(get('https://overpass-api.de/api/interpreter', urllib.parse.urlencode({'data': q}).encode()))['elements']
    print('  EMODnet %d x %d, %d coastline ways' % (el.shape[1], el.shape[0], len(ways)))
    wall = Image.new('1', (W, H), 0); dr = ImageDraw.Draw(wall)
    for w in ways:
        pts = [(gpx(p['lat'], p['lon'], Z)[0] - ox, gpx(p['lat'], p['lon'], Z)[1] - oy) for p in w['geometry']]
        dr.line(pts, fill=1, width=3)
    wall = np.array(wall, bool)
    # EMODnet over our px (centres), holes (land) filled from the nearest sea cell
    n = 256 * 2 ** Z
    lon = (ox + np.arange(W) + .5) / n * 360 - 180
    lat = np.degrees(np.arctan(np.sinh(math.pi * (1 - 2 * (oy + np.arange(H) + .5) / n))))
    dep_e = -el; sea_e = dep_e > 0
    iy, ix = ndimage.distance_transform_edt(~sea_e, return_distances=False, return_indices=True)
    filled = ndimage.gaussian_filter(dep_e[iy, ix], 1.0)         # (soft: the ~115 m cells would show as squares)
    ci = (lon - e0) / rx - 0.5; ri = (n1 - lat) / ry - 0.5
    R, C = np.meshgrid(ri, ci, indexing='ij')
    de = ndimage.map_coordinates(filled, [R, C], order=1, mode='nearest').astype(np.float32); del R, C
    wet = ndimage.map_coordinates(dep_e, [np.repeat(ri[:, None], W, 1), np.repeat(ci[None, :], H, 0)], order=0, mode='nearest') > 0.5
    # the sea = the parts between the walls that EMODnet mostly calls water (EMODnet also has a few
    # wet patches on land -- one of them must not make the whole mainland sea)
    lab, k = ndimage.label(~wall)
    frac = ndimage.mean(wet, lab, np.arange(1, k + 1))
    sea = np.concatenate([[False], frac > 0.5])[lab]; del lab
    sea |= wall & ndimage.binary_dilation(sea, iterations=2)      # (the wall itself: water up to the shore)
    mpp = 156543.03392 * math.cos(math.radians(lk.latc)) / 2 ** Z
    dist = ndimage.distance_transform_edt(sea) * mpp
    sea &= lk.clip_mask(Z, 0, 0, W, H)      # only inside the drawn area (EMODnet stops at its edge; after the distance: no false shore)
    dep = np.where(sea, np.clip(np.minimum(de, 0.4 + 0.06 * dist), 0.3, None), 0).astype(np.float16)
    np.savez_compressed(os.path.join(lk.D, 'sea_z15.npz'), sea=sea, dep=dep)
    print('  sea %.0f %% of the crop, depth up to %.1f m -> %s' % (sea.mean() * 100, float(dep.max()), os.path.join(lk.D, 'sea_z15.npz')))
    Image.fromarray((np.clip(dep.astype(np.float32) / 40, 0, 1) * 255).astype(np.uint8)).resize((W // 4, H // 4)).save(os.path.join(lk.D, 'sea_preview.png'))

if __name__ == '__main__':
    main(sys.argv[1])
