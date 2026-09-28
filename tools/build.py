"""Builds the site into docs/ (what GitHub Pages serves).

    python3 tools/build.py

src/app.html      the app (CSS + HTML + JS) -- edit this
src/head.html     the <head> (title, icons, manifest, Firebase SDK)
src/sw.js         service worker (offline start)
data/             depth grid + map-style thumbnails, injected at build
assets/           icons, manifest, the six map pictures (copied as is)
"""
import os, shutil
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def rd(*p): return open(os.path.join(ROOT, *p), encoding='utf-8').read()
page = rd('src', 'app.html'); head = rd('src', 'head.html')
i0 = page.index('<style>'); i1 = page.index('</style>') + len('</style>')
style, rest = page[i0:i1], page[i1:]
rest = rest.replace('__MAP_THUMBS__', rd('data', 'map_thumbs.js').strip())
rest = rest.replace('__DEPTH_GRID_B64__', rd('data', 'depth_grid_b64.txt').strip())
html = head.rstrip('\n') + '\n' + style + '\n</head>\n<body>\n' + rest + '\n</body>\n</html>\n'
out = os.path.join(ROOT, 'docs'); os.makedirs(out, exist_ok=True)
open(os.path.join(out, 'index.html'), 'w', encoding='utf-8').write(html)
shutil.copy(os.path.join(ROOT, 'src', 'sw.js'), out)
for f in os.listdir(os.path.join(ROOT, 'assets')):
    if f.endswith('.svg'): continue
    shutil.copy(os.path.join(ROOT, 'assets', f), out)
print('docs/index.html', len(html) // 1024, 'kB')
