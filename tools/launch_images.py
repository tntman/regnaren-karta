"""iOS's launch images (apple-touch-startup-image): what a home-screen app shows while it starts, instead of black.
The same picture as the page's own start picture (src/head.html, html.boot: the logo on black, the status bar's dark blue fading into it), so it
fades straight into the app. Made from the built page's rule, in Edge, at each iPhone's size:

    py -3 tools/build.py; py -3 tools/launch_images.py; py -3 tools/build.py     (-> assets/launch-*.png)

The page sits below the status bar (status-bar-style default) and the launch image covers the whole screen: the
logo is moved down by half the status bar so it doesn't jump. A new iPhone size: add it here (no image = black).
Only upright -- started on its side, iOS shows black as before. Changed images: add the app to the home screen again.
"""
import os, re
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# (CSS width, height, pixel ratio, status bar height (pt, roughly))
LAUNCH = [
    (440, 956, 3, 62),   # 16 Pro Max, 17 Pro Max
    (402, 874, 3, 62),   # 16 Pro, 17, 17 Pro
    (420, 912, 3, 62),   # Air
    (430, 932, 3, 59),   # 14 Pro Max, 15 Plus, 15 Pro Max, 16 Plus
    (393, 852, 3, 59),   # 14 Pro, 15, 15 Pro, 16
    (428, 926, 3, 47),   # 12 Pro Max, 13 Pro Max, 14 Plus
    (390, 844, 3, 47),   # 12, 12 Pro, 13, 13 Pro, 14, 16e
    (375, 812, 3, 44),   # X, XS, 11 Pro, 12 mini, 13 mini
    (414, 896, 3, 44),   # XS Max, 11 Pro Max
    (414, 896, 2, 48),   # XR, 11
    (414, 736, 3, 20),   # 6/7/8 Plus
    (375, 667, 2, 20),   # 6/7/8, SE 2nd/3rd
    (320, 568, 2, 20),   # SE 1st
]

if __name__ == '__main__':
    from playwright.sync_api import sync_playwright
    page = open(os.path.join(ROOT, 'docs', 'index.html'), encoding='utf-8').read()
    style = re.search(r'<style>html\{background:#141822;--ffLogo.*?</style>', page, re.S).group(0)
    exe = os.environ.get('CHROMIUM', 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe')
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path=exe)
        for w, h, r, sb in LAUNCH:
            pg = b.new_page(viewport={'width': w, 'height': h}, device_scale_factor=r)
            pg.set_content('<html class="boot"><head>%s<style>html.boot{background-position:50%% calc(50%% + %dpx),0 %dpx}html.boot body{opacity:1}</style></head>'
                           '<body><div style="position:fixed;left:0;right:0;top:0;height:%dpx;background:#141822"></div></body></html>'
                           % (style, sb // 2, sb, sb))
            pg.wait_for_timeout(200)
            f = os.path.join(ROOT, 'assets', 'launch-%dx%d.png' % (w * r, h * r))
            pg.screenshot(path=f)
            pg.close()
            print(f, os.path.getsize(f) // 1024, 'kB')
        b.close()
