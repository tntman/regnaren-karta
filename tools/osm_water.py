"""Fetch a lake's outline from OpenStreetMap (in Sweden: Lantmäteriet's map).

    py -3 tools/osm_water.py <lake_id>

Reads "osm": {"type": "relation"|"way", "id": ...} from lakes/<lake>/raw/source.json
and saves the outline to lakes/<lake>/raw/osm_water.json. genesis_render.py then
treats everything inside it as water -- also where Genesis has no depth data
(the map picture stays the aerial photo there; the depth grid says "water,
unknown depth", so routes by water and the lead line know it's lake).
Map data (c) OpenStreetMap contributors, ODbL.
"""
import sys, os, json, math, urllib.request, urllib.parse
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def fetch(lake):
    src = json.load(open(os.path.join(ROOT, 'lakes', lake, 'raw', 'source.json'), encoding='utf-8'))
    o = src['osm']
    q = '[out:json][timeout:60];%s(%d);out geom;' % (o['type'], o['id'])
    req = urllib.request.Request('https://overpass-api.de/api/interpreter', data=urllib.parse.urlencode({'data': q}).encode(),
                                 headers={'User-Agent': 'FF Map lake builder (private fishing app)'})
    import time
    for attempt in range(5):          # the public Overpass server is often busy: try again
        try:
            d = json.loads(urllib.request.urlopen(req, timeout=90).read()); break
        except Exception as e:
            print('  busy (%s), trying again ...' % e); time.sleep(10 * (attempt + 1))
    else:
        raise SystemExit('OpenStreetMap did not answer -- try again later')
    out = os.path.join(ROOT, 'lakes', lake, 'raw', 'osm_water.json')
    json.dump(d, open(out, 'w', encoding='utf-8'))
    print('saved', out, '-', len(d['elements']), 'element(s)')

def rings(el):
    """closed rings [(role, [(lat, lon), ...])] of a way or a multipolygon relation"""
    if el['type'] == 'way':
        return [('outer', [(p['lat'], p['lon']) for p in el['geometry']])]
    out = []
    for role in ('outer', 'inner'):
        segs = [[(p['lat'], p['lon']) for p in m['geometry']] for m in el['members']
                if m['type'] == 'way' and (m.get('role') or 'outer') == role and 'geometry' in m]
        while segs:
            ring = segs.pop(0)
            while ring[0] != ring[-1]:
                for i, s in enumerate(segs):
                    if s[0] == ring[-1]: ring += s[1:]; segs.pop(i); break
                    if s[-1] == ring[-1]: ring += s[::-1][1:]; segs.pop(i); break
                else: break
            out.append((role, ring))
    return out

def mask(lake, zoom, ox, oy, W, H):
    """the OSM lake as a bool array over the crop (global px at `zoom`, top-left ox, oy); None if not fetched"""
    import numpy as np
    from PIL import Image, ImageDraw
    p = os.path.join(ROOT, 'lakes', lake, 'raw', 'osm_water.json')
    if not os.path.exists(p): return None
    el = json.load(open(p, encoding='utf-8'))['elements'][0]
    n = 256 * 2 ** zoom
    def px(lat, lon):
        return ((lon + 180) / 360 * n - ox,
                (1 - math.log(math.tan(math.radians(lat)) + 1 / math.cos(math.radians(lat))) / math.pi) / 2 * n - oy)
    im = Image.new('L', (W, H), 0); d = ImageDraw.Draw(im)
    for role, r in sorted(rings(el), key=lambda t: t[0] != 'outer'):   # outer first, islands cut out after
        d.polygon([px(*q) for q in r], fill=255 if role == 'outer' else 0)
    return np.array(im) > 127

if __name__ == '__main__':
    fetch(sys.argv[1])
