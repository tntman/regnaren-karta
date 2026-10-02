"""Gör profilbilderna: tools/fiskare/<Namn>.jpg|png -> src/js/33-avatars.js (AVATARS = namn -> data-URL, 88 px kvadrat).
    py -3 tools/make_avatars.py
"""
import os, io, json, base64
from PIL import Image
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src = os.path.join(ROOT, 'tools', 'fiskare')
out = {}
for f in sorted(os.listdir(src)):
    im = Image.open(os.path.join(src, f)).convert('RGB')
    w, h = im.size; s = min(w, h)
    x = (w - s) // 2; y = 0 if h > w else 0   # porträtt: toppen (ansiktet); liggande: mitten
    im = im.crop((x, y, x + s, y + s)).resize((88, 88), Image.LANCZOS)
    b = io.BytesIO(); im.save(b, 'JPEG', quality=78, optimize=True)
    out[os.path.splitext(f)[0]] = 'data:image/jpeg;base64,' + base64.b64encode(b.getvalue()).decode()
js = '  /* Profilbilder (genereras av tools/make_avatars.py – redigera inte för hand) */\n  var AVATARS = ' + json.dumps(out, ensure_ascii=False, separators=(',', ':')) + ';\n'
open(os.path.join(ROOT, 'src', 'js', '33-avatars.js'), 'w', encoding='utf-8').write(js)
print(len(out), 'bilder,', len(js) // 1024, 'kB')
