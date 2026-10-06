"""Fetch the real place names around a lake from OpenStreetMap (islands, points, bays, farms, hamlets).

    py -3 tools/osm_names.py            (all lakes)
    py -3 tools/osm_names.py <lake_id>  (one lake)

Reads the map's extent from lakes/<lake>/lake.json and saves lakes/<lake>/names.json:
[[lat, lon, name, kind], ...] with kind "w" (in or at the water: islet, point, bay) or "p" (on land: farm,
hamlet). build.py embeds it in the page ("Namn" in Filter -> Lager). Unnamed things are skipped.
Map data (c) OpenStreetMap contributors, ODbL.
"""
import sys, os, json, math, time, urllib.request, urllib.parse
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WATER = {'island', 'islet'}
WATER_NAT = {'bay', 'cape', 'peninsula', 'strait'}
LAND = {'isolated_dwelling', 'hamlet', 'farm', 'locality', 'village', 'neighbourhood'}

def corners(g):
    """lat/lon of the map picture's corners (the picture is a crop of the Web-Mercator canvas at g.zoom)"""
    n = 256 * 2 ** g['zoom']
    S = g['imgW'] / g['fullW']
    def ll(x, y):
        gx, gy = g['originX'] + x / S, g['originY'] + y / S
        return (math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * gy / n)))), gx / n * 360 - 180)
    (n_, w), (s, e) = ll(0, 0), ll(g['imgW'], g['imgH'])
    return s, w, n_, e

def query(q):
    req = urllib.request.Request('https://overpass-api.de/api/interpreter', data=urllib.parse.urlencode({'data': q}).encode(),
                                 headers={'User-Agent': 'FF Map lake builder (private fishing app)'})
    for attempt in range(5):          # the public Overpass server is often busy: try again
        try:
            return json.loads(urllib.request.urlopen(req, timeout=90).read())
        except Exception as e:
            print('  busy (%s), trying again ...' % e); time.sleep(10 * (attempt + 1))
    raise SystemExit('OpenStreetMap did not answer -- try again later')

def fetch(lake):
    lk = json.load(open(os.path.join(ROOT, 'lakes', lake, 'lake.json'), encoding='utf-8'))
    s, w, n, e = corners(lk['geo'])
    b = '(%.5f,%.5f,%.5f,%.5f)' % (s, w, n, e)
    q = ('[out:json][timeout:60];(nwr[place~"^(%s)$"][name]%s;nwr[natural~"^(%s)$"][name]%s;);out tags center;'
         % ('|'.join(sorted(WATER | LAND)), b, '|'.join(sorted(WATER_NAT)), b))
    out, seen = [], set()
    for el in query(q)['elements']:
        t = el.get('tags', {})
        c = el.get('center') or el
        if 'lat' not in c: continue
        kind = 'w' if t.get('place') in WATER or t.get('natural') in WATER_NAT else 'p'
        key = (t['name'], kind)
        if key in seen: continue          # one label per name (e.g. an island group)
        seen.add(key)
        out.append([round(c['lat'], 5), round(c['lon'], 5), t['name'], kind])
    out.sort(key=lambda r: (r[3], r[2]))
    p = os.path.join(ROOT, 'lakes', lake, 'names.json')
    json.dump(out, open(p, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    print(lake, ':', len(out), 'names (%d water, %d land)' % (sum(r[3] == 'w' for r in out), sum(r[3] == 'p' for r in out)))

if __name__ == '__main__':
    for lake in sys.argv[1:] or sorted(d for d in os.listdir(os.path.join(ROOT, 'lakes')) if os.path.exists(os.path.join(ROOT, 'lakes', d, 'lake.json'))):
        fetch(lake)
