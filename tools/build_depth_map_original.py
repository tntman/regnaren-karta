import gc
import numpy as np
from PIL import Image
from scipy import ndimage
from scipy.ndimage import gaussian_filter, sobel
import matplotlib.colors as mcolors
import math

Image.MAX_IMAGE_PIXELS = None

print('loading canvases...')
depth_canvas = np.load('/tmp/fulllake/depth_full_canvas.npy')
H, W = depth_canvas.shape[:2]

alpha_all = depth_canvas[:, :, 3]
opaque_all = alpha_all > 10
del alpha_all

labeled, num = ndimage.label(opaque_all)
sizes = ndimage.sum(opaque_all, labeled, range(1, num + 1))
main_id = np.argmax(sizes) + 1
opaque_full = labeled == main_id
del labeled, opaque_all
gc.collect()

ys, xs = np.where(opaque_full)
pad = 80
x0, x1 = max(0, xs.min() - pad), min(W, xs.max() + pad)
y0, y1 = max(0, ys.min() - pad), min(H, ys.max() + pad)
print('crop box', x0, x1, y0, y1, ' -> size', x1 - x0, y1 - y0)

arr_b = depth_canvas[y0:y1, x0:x1].copy()
opaque = opaque_full[y0:y1, x0:x1].copy()
del depth_canvas, opaque_full
gc.collect()

contour_canvas = np.load('/tmp/fulllake/contour_full_canvas.npy')
t_arr = contour_canvas[y0:y1, x0:x1].copy()
del contour_canvas
gc.collect()

aerial_canvas = np.load('/tmp/fulllake/aerial_canvas.npy')
aerial_crop = aerial_canvas[y0:y1, x0:x1].copy()
del aerial_canvas
gc.collect()

h, w = opaque.shape

# ---- SEGMENTED base color, ranked by the ORIGINAL color's own intrinsic
# depth signal instead of "distance from shore". The C-MAP source ramp turns
# out to be (in this data) a near-white -> saturated blue ramp where the
# GREEN channel decreases almost perfectly monotonically with true depth
# (verified directly against the raw tile colors) -- unlike shore-distance,
# this is correct regardless of the lake's shape/basin layout, so a deep spot
# near a narrow shore no longer gets mis-ranked as "shallow".
rgb = arr_b[:, :, :3].reshape(-1, 3)
opaque_flat = opaque.reshape(-1)
opaque_colors = rgb[opaque_flat]
uniq, inverse, counts = np.unique(opaque_colors, axis=0, return_inverse=True, return_counts=True)

g_vals = uniq[:, 1].astype(np.float64)
# Rank by AREA-WEIGHTED percentile of the intrinsic G channel (green channel
# decreases monotonically with true depth in this source's ramp). Neither a
# raw linear normalize of G (compresses most of the real depth range into a
# narrow band because the deep end packs many close-together RGB codes) nor
# an unweighted rank-by-order (the deep end also has ~30 near-duplicate,
# extremely rare anti-aliasing colors that would then hog half the rank
# space despite covering a negligible sliver of actual lake area) gives the
# right answer. Weighting each unique color's rank position by how many
# pixels actually use it fixes both problems at once.
order = np.argsort(-g_vals)  # descending G first = shallowest color first
sorted_counts = counts[order].astype(np.float64)
cum_before = np.concatenate([[0.0], np.cumsum(sorted_counts)[:-1]])
cum_mid = cum_before + sorted_counts / 2.0
rank_sorted = cum_mid / counts.sum()
rank = np.empty(len(uniq))
rank[order] = rank_sorted

rank_raster = np.zeros(h * w)
rank_raster[opaque_flat] = rank[inverse]
rank_raster = rank_raster.reshape(h, w)

custom_stops = [(0.0, '#d62728'), (0.18, '#ff7f0e'), (0.36, '#ffdd00'), (0.55, '#2ca02c'),
                (0.72, '#17becf'), (0.87, '#1f4fd6'), (1.0, '#0a1a5c')]
cmap = mcolors.LinearSegmentedColormap.from_list('c', [c for _, c in custom_stops], N=256)
newc = (cmap(rank)[:, :3] * 255).astype(np.uint8)[inverse]
out = np.zeros((h * w, 4), dtype=np.uint8)
out[:, :3][opaque_flat] = newc
out[:, 3] = (opaque.reshape(-1) * 255).astype(np.uint8)
recolored = Image.fromarray(out.reshape(h, w, 4), 'RGBA')

# ---- shading: derive relief from the ACTUAL DEPTH field (rank_raster, now
# correctly calibrated above) rather than distance-from-shore. Distance-from-
# shore looks smooth and avoids terracing, but it isn't real bathymetry -- a
# wide bay far from any shore reads as "high ground" even if it's flat, so
# the shading didn't track the lake's real underwater shape. Real depth is
# the correct elevation source; it's just naturally a ~63-step staircase (one
# flat step per original contour-fill color), which is why it needs smoothing
# before computing normals (bare steps -> hard terracing rings at every
# boundary). The smoothing is fine here specifically because shading is
# applied as a MULTIPLY on brightness only (below), never touching hue, so a
# generously smoothed elevation field gives natural-looking relief without
# ever bleeding one flat color into its neighbor the way the old
# overlay-blend version did.
MAX_DEPTH_M = 10.0
elevation_true = np.where(opaque, -rank_raster * MAX_DEPTH_M, 0.0)

smooth_sigma = 4.5
elevation_for_normal = elevation_true.copy()
elevation_for_normal[opaque] = gaussian_filter(elevation_true, sigma=smooth_sigma)[opaque]


def compute_normal(elev_field, z_factor):
    gx = sobel(elev_field, axis=1) / 8.0
    gy = sobel(elev_field, axis=0) / 8.0
    nx = -gx * z_factor
    ny = -gy * z_factor
    nz = np.ones_like(elev_field)
    norm = np.sqrt(nx ** 2 + ny ** 2 + nz ** 2)
    return nx / norm, ny / norm, nz / norm


def light_shade(nx, ny, nz, azimuth_deg, altitude_deg):
    az = np.deg2rad(azimuth_deg)
    alt = np.deg2rad(altitude_deg)
    lx = np.cos(alt) * np.sin(az)
    ly = -np.cos(alt) * np.cos(az)
    lz = np.sin(alt)
    return np.clip(nx * lx + ny * ly + nz * lz, 0, 1)


zf = 30
nx, ny, nz = compute_normal(elevation_for_normal, zf)
diffuse = light_shade(nx, ny, nz, 350, 40)
lo, hi = np.percentile(diffuse[opaque], [2, 98])
normed = np.clip((diffuse - lo) / (hi - lo + 1e-6), 0, 1)  # 0..1, 0.5-ish = neutral

# gentle, smooth multiplicative brightness factor -- centered at 1.0, mild range
STRENGTH = 0.55
shade_mult = 1.0 + (normed - 0.5) * 2 * STRENGTH  # roughly [1-STRENGTH, 1+STRENGTH]
shade_mult = np.clip(shade_mult, 0.55, 1.45)

rc = np.array(recolored).astype(float)
rc[:, :, :3] = np.clip(rc[:, :, :3] * shade_mult[..., None], 0, 255)
relief = Image.fromarray(rc.astype(np.uint8), 'RGBA')

t_arr[:, :, 3] = np.where(opaque, t_arr[:, :, 3], 0)
t_masked = Image.fromarray(t_arr, 'RGBA')

aerial_rgba = Image.fromarray(aerial_crop, 'RGB').convert('RGBA')
base = aerial_rgba.copy()
base.alpha_composite(relief)
base.alpha_composite(t_masked)
composite_rgb = np.array(base.convert('RGB'))

print('final composite size:', composite_rgb.shape)
Image.fromarray(composite_rgb).save('/tmp/fulllake/regnaren_FULLLAKE_depthmap_v8_full.png')
im = Image.open('/tmp/fulllake/regnaren_FULLLAKE_depthmap_v8_full.png')
im.save('/mnt/user-data/outputs/regnaren_FULLLAKE_depthmap_v8.jpg', quality=95)
print('saved v8')
