"""The app's content (Capacitor webDir): app/www/ from docs/ -- run tools/build.py first.

    py -3 tools/build_app.py      (npm run build = build.py + this + npx cap sync android)

Packed into the app: the page, icons, Help, and per lake everything except the detail
tiles (tiles_v*/ come from GitHub Pages, see src/js/11-native.js). No sw.js (no service
worker in the app). Firebase's SDK is packed too (app/vendor/, fetched once from gstatic),
so the app starts without coverage.
"""
import os, re, shutil, urllib.request
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS, OUT, VENDOR = (os.path.join(ROOT, *p) for p in (('docs',), ('app', 'www'), ('app', 'vendor')))

html = open(os.path.join(DOCS, 'index.html'), encoding='utf-8').read()
os.makedirs(VENDOR, exist_ok=True)
def local_sdk(m):
    url = m.group(1); name = url.rsplit('/', 1)[1]
    ver = url.split('/')[-2]
    f = os.path.join(VENDOR, ver + '-' + name)
    if not os.path.exists(f):
        print('hämtar', url)
        urllib.request.urlretrieve(url, f)
    return '<script src="vendor/%s-%s"></script>' % (ver, name)
html, n = re.subn(r'<script src="(https://www\.gstatic\.com/firebasejs/[^"]+)"></script>', local_sdk, html)
assert n == 3, 'Firebase-skripten hittades inte i docs/index.html (%d)' % n
# Capacitor's JS (registerPlugin, CapacitorHttp ...) -- the native bridge alone doesn't have it
shutil.copy(os.path.join(ROOT, 'node_modules', '@capacitor', 'core', 'dist', 'capacitor.js'), os.path.join(VENDOR, 'capacitor.js'))
html = html.replace('<script src="vendor/', '<script src="vendor/capacitor.js"></script>\n<script src="vendor/', 1)

if os.path.exists(OUT): shutil.rmtree(OUT)
os.makedirs(OUT)
open(os.path.join(OUT, 'index.html'), 'w', encoding='utf-8').write(html)
used = set(re.findall(r'vendor/([^"]+)', html))
os.makedirs(os.path.join(OUT, 'vendor'))
for f in used: shutil.copy(os.path.join(VENDOR, f), os.path.join(OUT, 'vendor'))
for f in os.listdir(DOCS):
    if os.path.isfile(os.path.join(DOCS, f)) and f not in ('index.html', 'sw.js'):
        shutil.copy(os.path.join(DOCS, f), OUT)
shutil.copytree(os.path.join(DOCS, 'help'), os.path.join(OUT, 'help'))
shutil.copytree(os.path.join(DOCS, 'lakes'), os.path.join(OUT, 'lakes'),
                ignore=lambda d, names: [x for x in names if re.match(r'tiles_v\d+$', x)])

size = sum(os.path.getsize(os.path.join(d, f)) for d, _, fs in os.walk(OUT) for f in fs)
print('app/www', round(size / 1048576, 1), 'MB')
