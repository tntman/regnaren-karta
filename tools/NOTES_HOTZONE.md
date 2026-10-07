# Hotzone

Kod: `src/js/70-hotzone.js`, `src/css/77-hotzone.css`, `#hzLayer` (10-map.html), `#hzNote` + Filter-raden (30-map-ui.html).
Test: `tests/test_hotzone.py`.

## Regeln (Filip 2026-10-07)
- Bara under en pågående tävling på sjön (`catchLiveComp()`), live-fångsterna i sjön (`catchLive.list`), alla arter, vem som helst.
- **Hett ställe** = 4 fiskar inom 200 m senaste timmen. Fångsten som gör den 4:e blir mitten. Lever så länge det nappar inom 200 m
  (fångst inom en timme); dör en timme efter sista fisken (`hzTick` räknar om varje minut).
- **Ring** (200 m, röd streckad, andas på 3 s) + skylt 🔥 n (fiskar senaste timmen inom 200 m) för varje hett ställe.
- **Notis** (`.topNote`): "Hotzone: 4 abborrar senaste timmen" / "vid <närmaste OSM-namn inom 1,5 km> · 800 m bort · tryck för att åka dit".
  Blandade arter = "fiskar". Försvinner efter 10 s. En per ställe, **högst en per 45 min**; ställen som blir heta under pausen får bara ringen.
  Vad som sagts sparas per sjö (`ffmap_hotzone_note_v1`) – ingen ny notis efter vridning/omladdning.
- Live-hämtningen var 2:a min när Hotzone är på (`CATCH_LIVE_HZ`; heatmapen/Kartanalys 30 s, annars 5 min).

## Provkörningen (API:ts historik, utan Open-tävlingarna)
200 m, 4 fiskar/timme, notiser per dag med olika paus:

| Dag | Fångster | Ingen paus | 30 min | 60 min |
|---|---|---|---|---|
| Sibbo 26/4 | 139 | 13 | 9 | 5 |
| Vågsfjärden 22/5 | 53 | 5 | 5 | 4 |
| Vågsfjärden 23/5 | 49 | 2 | 2 | 1 |
| Väringen 5–7/6 | 22/14/19 | 2/0/1 | 2/0/1 | 2/0/1 |
| Regnaren 25–27/9 | 49/37/12 | 4/2/0 | 4/2/0 | 3/2/0 |

Prövat och valt bort: 100 m (för snålt – Vågsfjärden 23/5 gav 0), krav på 2–3 olika personer (Filip: zonen handlar om fisk på en
plats, inte vem), zonen måste ha 30–40 % av sjöns fångster, notis när hetaste stället byter plats. Utseendet: variant 2 av 4
(röd streckad ring som andas, liten skylt).

## Inte gjort
- Notis när appen är stängd (kräver server; iPhone-appen kan göra lokala notiser senare).
- Mellan tävlingarna (ingen live-data).
