# FF Map – projektanteckningar för Claude

## Vad det är
Webbapp (PWA, "Lägg till på hemskärmen" på iPhone) för fiskegruppen Fiskfiskarna vid
sjön Regnaren. Djupkarta + GPS + delade fiskeplatser och båtpositioner via Firebase
(Firestore, anonym inloggning; identitet = valt namn). Användaren (Filip) är admin.
All text i appen är på svenska. Svara Filip på svenska, kort och tydligt.

## Arbetssätt
- Källa: `src/app.html` (allt i en fil). Bygg: `python3 tools/build.py` → `docs/`.
- Tester: `tests/run_all.sh` (Playwright + `tests/fakefb.py` som låtsas vara Firebase).
  Kör alltid testerna efter ändringar och lägg till nya tester för ny funktion.
- Publicering: GitHub Pages från `main` / `docs`. Commit + push = live.
- Filip vill ofta se **bilder/förslag innan** något implementeras ("visa först").
  När han skriver "svara först" – svara, implementera inte.

## Viktiga saker i koden
- **iOS hemskärmsapp laddar om sidan vid rotation.** Allt tillstånd måste överleva:
  inställningar i localStorage, öppna vyer/halvgjort i `saveRotationState()`/
  `restoreRotationUi()` (sessionStorage). Nya UI-tillstånd ska läggas till där.
- **Ordning/hoisting:** många `var` deklareras långt ner i skriptet. Sätt checkbox-
  tillstånd som beror på sådana variabler i `boot()` (se toggleDepth/toggleTrack).
- **Firebase-kvot** (gratis: 50k reads/dygn). Positioner delas var 20:e s vid rörelse
  (admin-inställning i `config/<lake>`), var 60:e s stilla. Undvik onödiga get().
- **Service worker** (`src/sw.js`): nätet först för sidan (4 s), cache för bilder.
  Ändras kartbilder: nytt filnamn (`map_v2_*`) och höj `CACHE` i sw.js.
- **Kartstilar:** `assets/map_v1_s1..s6.jpg` (3600×1758, samma geo-referens som
  `latLonToImgPx`). Bara vald stil laddas ner.
- **Djupdata:** `data/depth_grid_b64.txt` (1200×586, 0–10 m i 4 cm-steg, 251 = land-RLE).
  OBS: metervärdena är härledda ur C-MAP-färger (rangordning), inte uppmätta –
  ordningen stämmer, exakta meter kan vara fel. Kalibrering föreslagen men inte gjord.
- Väder: Open-Meteo (ingen nyckel), cache 30 min, lagras lokalt.

## Firestore-regler (aktuella, i Firebase-konsolen)
waypoints: read auth; create kräver uid/name(≤60)/lat/lon; update/delete auth.
positions: read auth; write kräver lat, lon (number) och name (string).
usage: read auth; write kräver day (string) och r/w/d (number).
config/{lake}: read auth; write kräver posIntervalS i [10,20,30,60].

## Idéer som diskuterats men inte gjorts
- Kalibrera djupet mot C-MAP-siffror eller ekolodsmätningar.
- Riktig iPhone-app via Capacitor + TestFlight (bakgrundsposition). Kräver Mac + Apple-konto.
- iOS Genvägar-automation som skickar position när appen är stängd.
- "Håll skärmen tänd" (Wake Lock; fungerar i hemskärmsappar från iOS 18.4).
- Fångstlogg/tävlingsläge, navigera till plats, anteckningar på fiskeplatser.
