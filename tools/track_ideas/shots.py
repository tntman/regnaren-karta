import sys, os, math, json, random
sys.path.insert(0, r'E:\github\regnaren-karta\tests')
os.chdir(r'E:\github\regnaren-karta\tests')
from playwright.sync_api import sync_playwright
from fakefb import new_page
import numpy as np
OUT = os.path.dirname(os.path.abspath(__file__))
raw = np.load('../lakes/regnaren/raw/depth_raw.npz')
Z = int(raw['zoom']); OX, OY = [int(v) for v in raw['origin']]; W = raw['water']
def ll(c, r):
    xg = c + OX; yg = r + OY; n = 2 ** Z * 256
    return math.degrees(math.atan(math.sinh(math.pi - 2 * math.pi * yg / n))), xg / n * 360 - 180
def wet(c, r, m=12):
    c, r = int(c), int(r)
    return W[r-m:r+m+1:6, c-m:c+m+1:6].all() if m < r < W.shape[0]-m and m < c < W.shape[1]-m else False
MPP = 156543.03 * math.cos(math.radians(59.0)) / 2 ** Z   # m per raw px
# start: a deep-ish water point with lots of water around
from scipy.ndimage import distance_transform_edt
random.seed(int(sys.argv[1]) if len(sys.argv) > 1 else 3)
ds = distance_transform_edt(W[::20, ::20]); r0, c0 = np.unravel_index(np.argmax(ds), ds.shape); best = (c0 * 20, r0 * 20)
c, r = best; hd = random.random() * 6.28
pts = []; t = 1.7e12
plan = [('fast', 25), ('troll', 70), ('stop', 25), ('troll', 50), ('fast', 18), ('stop', 20), ('troll', 60), ('fast', 12)]
for kind, n in plan:
    for k in range(n):
        step = {'fast': 22, 'troll': 9, 'stop': 1.2}[kind]; dt = {'fast': 6, 'troll': 8, 'stop': 30}[kind]
        hd += random.gauss(0, {'fast': .06, 'troll': .45, 'stop': 1}[kind])
        for tr in range(40):
            nc, nr = c + math.cos(hd) * step / MPP, r + math.sin(hd) * step / MPP
            if wet(nc, nr): break
            hd += .4
        c, r = nc, nr; t += dt * 1000
        la, lo = ll(c, r); pts.append([round(la, 6), round(lo, 6), int(t)])
CENTER = pts[len(pts)//2]
wps = [{'lat': pts[i][0], 'lon': pts[i][1], 'name': n, 'uid': 'filip', 'by': 'Filip', 'type': ty}
       for i, n, ty in [(60, 'Kanten', 'abborre'), (130, 'Vassen', 'gadda'), (230, 'Djupet', 'gos')]]

OVER = r"""
(function(arg){
  var pts = arg.pts, kind = arg.kind;
  var tl = document.getElementById('trackLayer');
  var d = tl.querySelector('.trkLine').getAttribute('d');
  var m = d.match(/-?\d+\.?\d*/g).map(Number);
  function mx(lo){ return (lo + 180) / 360; }
  function my(la){ var s = Math.sin(la * Math.PI / 180); return 0.5 - Math.log((1 + s) / (1 - s)) / (4 * Math.PI); }
  var a = pts[0], b = pts[pts.length - 1];
  var sx = (m[m.length-2] - m[0]) / (mx(b[1]) - mx(a[1])), sy = (m[m.length-1] - m[1]) / (my(b[0]) - my(a[0]));
  function P(p){ return [m[0] + (mx(p[1]) - mx(a[1])) * sx, m[1] + (my(p[0]) - my(a[0])) * sy]; }
  var pxPerM = Math.abs(sx) / (40075016 * Math.cos(pts[0][0] * Math.PI / 180));
  var old = document.getElementById('demoOver'); if (old) old.remove();
  tl.style.display = kind === 'now' ? '' : 'none';
  if (kind === 'now') return;
  var NS = 'http://www.w3.org/2000/svg';
  var cv = document.createElement('canvas'); cv.id = 'demoOver';
  var dpr = 2, w = innerWidth, h = innerHeight;
  cv.width = w * dpr; cv.height = h * dpr; cv.style.cssText = 'position:absolute;left:0;top:0;width:' + w + 'px;height:' + h + 'px;z-index:13;pointer-events:none';
  tl.parentNode.insertBefore(cv, tl);
  var g = cv.getContext('2d'); g.scale(dpr, dpr); g.lineCap = g.lineJoin = 'round';
  var S = pts.map(P);
  function spd(i){ var j = Math.max(1, i); return 1.94384 * 1000 * Math.hypot(S[j][0]-S[j-1][0], S[j][1]-S[j-1][1]) / pxPerM / (pts[j][2] - pts[j-1][2]); } // knots
  function line(col, wd, f){ g.strokeStyle = col; g.lineWidth = wd; g.beginPath(); S.forEach(function(p, i){ i ? g.lineTo(p[0], p[1]) : g.moveTo(p[0], p[1]); }); g.stroke(); }
  function under(){ line('rgba(10,20,26,.8)', 4.5); }
  if (kind === 'speed'){
    under();
    for (var i = 1; i < S.length; i++){
      var k = Math.min(1, spd(i) / 12), c1 = [70,170,255], c2 = [255,138,31];
      g.strokeStyle = 'rgb(' + c1.map(function(v, j){ return Math.round(v + (c2[j] - v) * k); }) + ')'; g.lineWidth = 2.6;
      g.beginPath(); g.moveTo(S[i-1][0], S[i-1][1]); g.lineTo(S[i][0], S[i][1]); g.stroke();
    }
  }
  if (kind === 'tail'){
    var n = S.length;
    for (var i = 1; i < n; i++){ var o = Math.pow(i / n, 2.2);
      g.strokeStyle = 'rgba(10,20,26,' + (.8 * o) + ')'; g.lineWidth = 4.5; g.beginPath(); g.moveTo(S[i-1][0], S[i-1][1]); g.lineTo(S[i][0], S[i][1]); g.stroke();
      g.strokeStyle = 'rgba(255,138,31,' + (.1 + .9 * o) + ')'; g.lineWidth = 2.4; g.beginPath(); g.moveTo(S[i-1][0], S[i-1][1]); g.lineTo(S[i][0], S[i][1]); g.stroke(); }
  }
  if (kind === 'arrows' || kind === 'stops'){
    under(); line('#FF8A1F', 2.2);
  }
  if (kind === 'arrows'){
    var acc = 0;
    for (var i = 1; i < S.length; i++){ acc += Math.hypot(S[i][0]-S[i-1][0], S[i][1]-S[i-1][1]);
      if (acc > 70){ acc = 0; var an = Math.atan2(S[i][1]-S[i-1][1], S[i][0]-S[i-1][0]);
        g.save(); g.translate(S[i][0], S[i][1]); g.rotate(an); g.beginPath(); g.moveTo(6, 0); g.lineTo(-5, -5); g.lineTo(-2, 0); g.lineTo(-5, 5); g.closePath();
        g.fillStyle = '#FF8A1F'; g.strokeStyle = 'rgba(10,20,26,.9)'; g.lineWidth = 1.5; g.stroke(); g.fill(); g.restore(); } }
  }
  if (kind === 'stops'){
    var i = 1;
    while (i < S.length){
      if (spd(i) < 0.8){ var j = i, sx2 = 0, sy2 = 0; while (j < S.length && spd(j) < 0.8){ sx2 += S[j][0]; sy2 += S[j][1]; j++; }
        var cnt = j - i, mins = Math.round((pts[j-1][2] - pts[i-1][2]) / 60000);
        if (mins >= 2){ var cx = sx2 / cnt, cy = sy2 / cnt, R = 9 + Math.sqrt(mins) * 4;
          g.fillStyle = 'rgba(255,176,32,.22)'; g.strokeStyle = '#FFB020'; g.lineWidth = 2; g.beginPath(); g.arc(cx, cy, R, 0, 7); g.fill(); g.stroke();
          g.font = '600 12px -apple-system,system-ui,sans-serif'; g.textAlign = 'center';
          g.lineWidth = 3; g.strokeStyle = 'rgba(6,20,28,.9)'; g.strokeText(mins + ' min', cx, cy - R - 5); g.fillStyle = '#FFD27A'; g.fillText(mins + ' min', cx, cy - R - 5); }
        i = j; } else i++;
    }
  }
  if (kind === 'swept'){
    g.strokeStyle = 'rgba(70,170,255,.30)'; g.lineWidth = 35 * pxPerM; line('rgba(255,255,255,.32)', 35 * pxPerM);
    line('rgba(10,20,26,.6)', 3); line('#FF8A1F', 1.4);
  }
  if (kind === 'days'){
    function off(dx, dy, col){ g.strokeStyle = col; g.lineWidth = 2; g.beginPath(); S.forEach(function(p, i){ var q = [p[0] + dx + Math.sin(i / 9) * 14, p[1] + dy + Math.cos(i / 13) * 12]; i ? g.lineTo(q[0], q[1]) : g.moveTo(q[0], q[1]); }); g.stroke(); }
    off(-30, 40, 'rgba(154,211,106,.65)'); off(25, -35, 'rgba(120,200,255,.65)');
    under(); line('#FF8A1F', 2.2);
    var bx = document.createElement('div'); bx.id = 'demoDays';
    bx.style.cssText = 'position:absolute;left:50%;transform:translateX(-50%);bottom:calc(env(safe-area-inset-bottom,0px) + 128px);z-index:25;display:flex;gap:6px;font:600 13px -apple-system,system-ui,sans-serif;white-space:nowrap';
    [['I dag', '#FF8A1F'], ['Igår', '#78C8FF'], ['Lör', '#9AD36A'], ['Alla', '#fff']].forEach(function(x, i){ var s = document.createElement('span'); s.textContent = x[0];
      s.style.cssText = 'padding:6px 12px;border-radius:16px;background:rgba(6,20,28,.88);border:1px solid ' + (i == 0 ? x[1] : 'rgba(255,255,255,.18)') + ';color:' + x[1]; bx.appendChild(s); });
    document.body.appendChild(bx);
  } else { var ob = document.getElementById('demoDays'); if (ob) ob.remove(); }
  if (kind === 'fog'){
    g.fillStyle = 'rgba(6,20,28,.92)'; g.fillRect(0, 0, w, h);
    g.globalCompositeOperation = 'destination-out';
    var R = 150 * pxPerM, last = null;
    S.forEach(function(p){ if (last && Math.hypot(p[0]-last[0], p[1]-last[1]) < R / 4) return; last = p;
      var gr = g.createRadialGradient(p[0], p[1], 0, p[0], p[1], R); gr.addColorStop(0, 'rgba(0,0,0,.55)'); gr.addColorStop(.55, 'rgba(0,0,0,.35)'); gr.addColorStop(1, 'rgba(0,0,0,0)');
      g.fillStyle = gr; g.beginPath(); g.arc(p[0], p[1], R, 0, 7); g.fill(); });
    g.globalCompositeOperation = 'source-over';
    // the track itself is still drawn by the app (under nothing)
    tl.style.display = '';
    cv.style.zIndex = 12;
    var pl = document.createElement('div'); pl.id = 'demoDays';
    pl.style.cssText = 'position:absolute;left:50%;transform:translateX(-50%);bottom:calc(env(safe-area-inset-bottom,0px) + 128px);z-index:25;padding:7px 14px;border-radius:16px;background:rgba(6,20,28,.9);border:1px solid rgba(255,255,255,.18);color:#fff;font:600 13px -apple-system,system-ui,sans-serif';
    pl.textContent = 'Utforskat: 7 % av Regnaren'; document.body.appendChild(pl);
  }
})
"""

with sync_playwright() as p:
    b, ctx, pg, errs = new_page(p, geo=(pts[-1][0], pts[-1][1]), cfg={'waypoints': wps}, name='Filip')
    ctx.add_init_script("""((pts) => { var d = new Date(Date.now() - 6 * 3600000), day = d.getFullYear() + '-' + (d.getMonth() + 1) + '-' + d.getDate();
        var now = Date.now(), sh = now - pts[pts.length-1][2]; pts = pts.map(function(q){ return [q[0], q[1], q[2] + sh - 60000]; });
        localStorage.setItem('ffmap_track_v1', JSON.stringify({day: day, segs: [pts]})); })(%s)""" % json.dumps(pts))
    pg.reload(); pg.wait_for_timeout(2500)
    zoom = int(sys.argv[2]) if len(sys.argv) > 2 else 0
    for i in range(abs(zoom)):
        pg.mouse.move(195, 420); pg.mouse.wheel(0, -200 if zoom > 0 else 200); pg.wait_for_timeout(250)
    pg.wait_for_timeout(1500)
    for it in range(3):
        bb = pg.evaluate("(function(){var r=document.querySelector('#trackLayer .trkLine').getBBox();return [r.x+r.width/2,r.y+r.height/2,r.width,r.height]})()")
        print('bbox', bb)
        dx = max(-180, min(180, bb[0] - 195)); dy = max(-300, min(300, bb[1] - 470)); pg.mouse.move(195 + dx/2, 470 + dy/2); pg.mouse.down(); pg.mouse.move(195 - dx/2, 470 - dy/2, steps=3); pg.mouse.up(); pg.wait_for_timeout(600)
    pg.wait_for_timeout(2500)
    pts2 = pg.evaluate("JSON.parse(localStorage.getItem('ffmap_track_v1')).segs[0]")
    for k in ['now', 'speed', 'tail', 'arrows', 'stops', 'swept', 'days', 'fog']:
        pg.evaluate("(" + OVER + ")({pts: %s, kind: '%s'})" % (json.dumps(pts2), k))
        pg.wait_for_timeout(400)
        pg.screenshot(path=os.path.join(OUT, 'trk_%s.png' % k))
    print('errs', errs[:3])
    b.close()

from PIL import Image
ks=['now','speed','tail','arrows','stops','swept','days','fog']
ims=[Image.open(os.path.join(OUT,'trk_%s.png'%k)) for k in ks]
w,h=ims[0].size
g=Image.new('RGB',(w*4+30,h*2+10),(255,255,255))
for i,im in enumerate(ims): g.paste(im,((i%4)*(w+10),(i//4)*(h+10)))
g.save(os.path.join(OUT,'grid.png'))



