# Hotzone

Kod: `src/js/70-hotzone.js`, `src/css/77-hotzone.css`, `#hzLayer` (10-map.html), `#hzNote` + Filter-raden (30-map-ui.html).
Test: `tests/test_hotzone.py`.

## Regeln (Filip 2026-11-08, ersätter 200 m-regeln nedan)
- **Hett ställe** = 4 fiskar senaste timmen som alla ligger inom **50 m från fiskarnas mitt** (medelpunkten). Ringen = 50 m radie
  (100 m bred) runt mitten. En ny fisk inom 50 m från mitten håller stället vid liv och flyttar mitten (fiskarna senaste timmen).
  Stället dör **30 min** efter sista fisken (`HZ_LIVE`). Notisen, pausen 45 min och live-hämtningen som förut.
- Varför: 200 m runt 4:e fisken gav ringar där fiskarna låg upp till 336 m isär. Provkörning på Fångstloggen (1 039 fångster
  apr–nov 2026, `dashboard.php?del=fangstlogg`), heta ställen / notiser / längsta avstånd mellan två fiskar i ett ställe:
  idag 200 m 63 / 54 / 336 m; mitt 100 m 65 / 50 / 184 m; mitt 75 m 60 / 46 / 147 m; **mitt 50 m 61 / 45 / 79 m**.
  Glesa dagar (Vågsfjärden 23/5, Väringen 5/6 och 7/6: median 58–110 m till närmaste fisk, högst 3–5 fiskar inom 100 m på en timme)
  får inga ställen med 50 m – det nappade överallt, inget var hett. Heta dagar: 1–16 m till närmaste fisk, 9–48 inom 100 m på en timme.
  Livslängd med 1 h: median 66 min, men hälften fick sin sista fisk inom 6 min och 22 av 69 ingen alls efter ringen → 30 min.

## Förra regeln (Filip 2026-10-07)
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
