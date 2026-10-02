"""Builds the site into docs/ (what GitHub Pages serves).

    py -3 tools/build.py          (python3 tools/build.py elsewhere)

src/css/*.css     the app's styles     | edit these; each folder is glued together
src/html/*.html   the page's parts     | in name order into ONE page, as before
src/js/*.js       the script           | (see src/README.md)
src/head.html     the <head> (title, icons, manifest, Firebase SDK)
src/sw.js         service worker (offline start)
lakes/<id>/       one folder per lake: lake.json (name, geo-reference, depth
                  scale, map styles, zoom levels ...) -- embedded in the page --
                  and raw/ (source settings + data for tools/genesis_*.py).
                  The pictures are made by tools/genesis_render.py straight
                  into docs/lakes/<id>/.
assets/           icons + manifest (copied as is)
"""
import os, shutil, json
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def rd(*p): return open(os.path.join(ROOT, *p), encoding='utf-8').read()

# ---- lakes: Regnaren first (the default), then by "order" / name
lakes = []
for d in sorted(os.listdir(os.path.join(ROOT, 'lakes'))):
    f = os.path.join(ROOT, 'lakes', d, 'lake.json')
    if os.path.exists(f):
        lk = json.load(open(f, encoding='utf-8'))
        assert lk['id'] == d, 'lake.json id must match its folder: ' + d
        nf = os.path.join(ROOT, 'lakes', d, 'names.json')      # place names from OpenStreetMap (tools/osm_names.py)
        if os.path.exists(nf): lk['names'] = json.load(open(nf, encoding='utf-8'))
        lakes.append(lk)
lakes.sort(key=lambda l: (l.get('order', 0 if l['id'] == 'regnaren' else 100), l['name']))

def parts(sub, ext):
    d = os.path.join(ROOT, 'src', sub)
    return ''.join(rd('src', sub, f) for f in sorted(os.listdir(d)) if f.endswith(ext))
# one page, as before: <style> all css </style>, the html, <script> all js (ONE function scope) </script>
page = ('<style>\n' + parts('css', '.css') + '</style>\n\n' + parts('html', '.html')
        + '<script>\n' + parts('js', '.js') + '</script>\n')
head = rd('src', 'head.html')
i0 = page.index('<style>'); i1 = page.index('</style>') + len('</style>')
style, rest = page[i0:i1], page[i1:]
rest = rest.replace('__LAKES__', json.dumps(lakes, ensure_ascii=False, separators=(',', ':')))
html = head.rstrip('\n') + '\n' + style + '\n</head>\n<body>\n' + rest + '\n</body>\n</html>\n'

out = os.path.join(ROOT, 'docs'); os.makedirs(out, exist_ok=True)
open(os.path.join(out, 'index.html'), 'w', encoding='utf-8').write(html)
shutil.copy(os.path.join(ROOT, 'src', 'sw.js'), out)
for f in os.listdir(os.path.join(ROOT, 'assets')):
    if f.endswith('.svg'): continue
    shutil.copy(os.path.join(ROOT, 'assets', f), out)

# ---- the lakes' pictures (maps, detail tiles, thumbnails, depth grid) are
# written straight into docs/lakes/<id>/ by tools/genesis_render.py -- nothing
# to copy here; just check they're there
for lk in lakes:
    need = os.path.join(out, 'lakes', lk['id'], lk['mapFile'].replace('{style}', lk['styles'][0]['id']))
    if not os.path.exists(need):
        print('WARNING: %s missing -- run tools/genesis_render.py %s' % (need, lk['id']))
n = sum(len(fs) for _, _, fs in os.walk(os.path.join(out, 'lakes')))
print('docs/index.html', len(html) // 1024, 'kB;', len(lakes), 'lakes:', ', '.join(l['id'] for l in lakes), '(%d files)' % n)
