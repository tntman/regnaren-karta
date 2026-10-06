"""The app icon (tools/PLAN_LOGGA.md): exported from tools/logo_ny.html, in Edge, square (iOS and Android round the
corners themselves) and without transparency. Also the page's favicon (64 px, embedded in src/head.html).

    py -3 tools/app_icon.py; py -3 tools/build.py        (-> assets/apple-touch-icon.png, icon-192.png, icon-512.png)
    py -3 tools/app_icon.py <size> <file>                 (one more, e.g. 1024 for the iPhone app's AppIcon)

Changed icon: raise CACHE in src/sw.js (same file names), and the app must be added to the home screen again.
"""
import base64, os, re, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ICONS = [(180, 'apple-touch-icon.png'), (192, 'icon-192.png'), (512, 'icon-512.png')]

def render(pg, size, path=None):
    pg.evaluate("""s => { document.body.innerHTML = '<svg id="ic" width="' + s + '" height="' + s + '" viewBox="0 0 512 512">'
      + LOGO.replace('<g clip-path="url(#rr)">', '<g>') + '</svg>';
      document.body.style.cssText = 'margin:0;padding:0;background:#000'; }""", size)
    pg.wait_for_function("[...document.querySelectorAll('#ic image')].every(i => i.getBBox().width > 0)")
    pg.wait_for_timeout(300)   # (the fish's svg drawn)
    return pg.screenshot(path=path, clip={'x': 0, 'y': 0, 'width': size, 'height': size})

if __name__ == '__main__':
    from playwright.sync_api import sync_playwright
    exe = os.environ.get('CHROMIUM', 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe')
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path=exe)
        pg = b.new_page(viewport={'width': 1100, 'height': 1100})
        pg.goto('file:///' + os.path.join(ROOT, 'tools', 'logo_ny.html').replace('\\', '/'))
        if len(sys.argv) == 3:
            render(pg, int(sys.argv[1]), sys.argv[2]); print(sys.argv[2])
        else:
            for size, name in ICONS:
                f = os.path.join(ROOT, 'assets', name); render(pg, size, f); print(f, os.path.getsize(f) // 1024, 'kB')
            fav = base64.b64encode(render(pg, 64)).decode()
            h = os.path.join(ROOT, 'src', 'head.html'); s = open(h, encoding='utf-8').read()
            s, n = re.subn(r'(<link rel="icon" type="image/png" href="data:image/png;base64,)[^"]*', lambda m: m.group(1) + fav, s)
            assert n == 1; open(h, 'w', encoding='utf-8', newline='').write(s); print(h, 'favicon 64 px')
        b.close()
