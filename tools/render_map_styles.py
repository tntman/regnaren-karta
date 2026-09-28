import numpy as np, base64, io
from PIL import Image
from scipy.ndimage import gaussian_filter, sobel, binary_dilation, binary_erosion
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import colors as mcolors
Image.MAX_IMAGE_PIXELS = None
x0, x1, y0, y1 = 1853, 8360, 4026, 7203
OW, OH = 3600, 1758          # the app's map size
SS = 2                        # supersample for smooth lines
W, H = OW * SS, OH * SS
e = np.load('elevation_m_soft_full.npy').astype('float32')
o = np.load('opaque_full_crop.npy').astype('float32')
aer = np.ascontiguousarray(np.load('aerial_canvas.npy', mmap_mode='r')[y0:y1, x0:x1])
aer_big = np.array(Image.fromarray(aer).resize((W, H), Image.LANCZOS)).astype('float32'); del aer
dep = np.array(Image.fromarray(np.clip(-e, 0, 10), 'F').resize((W, H), Image.BILINEAR)); del e
alpha = np.clip(np.array(Image.fromarray(o, 'F').resize((W, H), Image.BILINEAR)), 0, 1)  # soft shoreline
water = alpha >= 0.5
dsm = gaussian_filter(dep, 3.0)
def hillshade(z, az=315, alt=40, zf=5):
    gx = sobel(z, 1) / 8.0; gy = sobel(z, 0) / 8.0
    nx, ny, nz = gx * zf, gy * zf, np.ones_like(z)
    n = np.sqrt(nx*nx + ny*ny + nz*nz)
    a, b = np.deg2rad(az), np.deg2rad(alt)
    return np.clip((nx*np.cos(b)*np.sin(a) - ny*np.cos(b)*np.cos(a) + nz*np.sin(b)) / n, 0, 1)
hs = hillshade(gaussian_filter(dep, 7))
def contour(levels, width):
    m = np.zeros(dep.shape, bool)
    for L in levels:
        a = dsm >= L
        m |= (a ^ np.roll(a, 1, 0)) | (a ^ np.roll(a, 1, 1))
    m &= water
    if width > 1: m = binary_dilation(m, iterations=width - 1)
    return m
c1 = contour(np.arange(1, 10, 1.0), 2)       # every metre
c2 = contour([2, 4, 6, 8], 3)                # every 2 m, stronger
shore = water & ~binary_erosion(water, iterations=3)   # a thin line just inside the shoreline
def mix(base, mask, color, a):
    base[mask] = base[mask] * (1 - a) + np.array(color, 'float32') * a
def hx(s): return tuple(int(s[i:i+2], 16) for i in (1, 3, 5))
def finish(water_rgb, name):
    out = aer_big * (1 - alpha[..., None]) + water_rgb * alpha[..., None]
    im = Image.fromarray(np.clip(out, 0, 255).astype('uint8')).resize((OW, OH), Image.LANCZOS)
    im.save('styles/map_v1_%s.jpg' % name, quality=84, optimize=True, progressive=True)
    return im
res = {}
# 2 simplified
w = plt.get_cmap('turbo_r')(np.clip(dep / 10, 0, 1))[..., :3].astype('float32') * 255
mix(w, c1, (0, 0, 0), 0.45); mix(w, shore, (20, 20, 20), 0.85)
res['s2'] = finish(w, 's2')
# 3 sea chart
w = np.zeros((H, W, 3), 'float32'); w[:] = hx('#dff3fb')
for lo, c in [(1, '#c4e7f6'), (2, '#a9dbf2'), (3, '#8fcdec'), (5, '#74bde4'), (7, '#5aa9d8'), (9, '#4796cb')]:
    w[dsm >= lo] = hx(c)
mix(w, c1, hx('#3a78a8'), 0.5); mix(w, c2, hx('#1f5a8a'), 0.65); mix(w, shore, hx('#5b4b2a'), 0.85)
res['s3'] = finish(w, 's3')
# 4 night
cm = mcolors.LinearSegmentedColormap.from_list('n', ['#24475a', '#153a55', '#0c2749', '#061532'])
w = cm(np.clip(dep / 10, 0, 1))[..., :3].astype('float32') * 255 * (0.75 + 0.4 * hs[..., None])
mix(w, c1, hx('#39c5d6'), 0.45); mix(w, c2, hx('#8fe9f4'), 0.6); mix(w, shore, hx('#8fd3dc'), 0.8)
res['s4'] = finish(w, 's4')
# 5 aerial + lines
w = aer_big * np.array([0.9, 0.97, 1.05], 'float32')
mix(w, c1, (255, 255, 255), 0.45); mix(w, c2, (255, 255, 255), 0.75); mix(w, shore, (255, 236, 160), 0.85)
res['s5'] = finish(w, 's5')
# 6 blue relief
cm = mcolors.LinearSegmentedColormap.from_list('b', ['#cfeefa', '#6fc3e8', '#2a86c9', '#12509a', '#0a2c63'])
w = np.clip(cm(np.clip(dep / 10, 0, 1))[..., :3].astype('float32') * 255 * (0.55 + 0.6 * hs[..., None]), 0, 255)
mix(w, c2, (10, 30, 60), 0.3); mix(w, shore, (245, 250, 252), 0.7)
res['s6'] = finish(w, 's6')
# 1 = the current map, as a separate file
open('styles/map_v1_s1.jpg', 'wb').write(base64.b64decode(open('img_b64.txt').read()))  # the current map, unchanged
import os
for k in ['s1','s2','s3','s4','s5','s6']:
    print(k, os.path.getsize('styles/map_v1_%s.jpg' % k) // 1024, 'kB')
