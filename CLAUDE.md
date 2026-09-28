# FF Map – projektanteckningar för Claude

## Vad det är
Webbapp (PWA, "Lägg till på hemskärmen" på iPhone) för fiskegruppen Fiskfiskarna,
flera sjöar (Regnaren, Vågsfjärden – väljs i menyn). Djupkarta + GPS + delade fiskeplatser och båtpositioner via Firebase
(Firestore, anonym inloggning; identitet = valt namn). Användaren (Filip) är admin.
All text i appen är på svenska. Svara Filip på svenska, kort och tydligt.

## Arbetssätt
- Repot ligger i `E:\github\regnaren-karta` (Windows). Filip använder inte terminalen
  själv och git är inte installerat: kör **inga git-kommandon**. Filip gör commit och
  push själv i GitHub Desktop.
- **Bygg alltid `docs/` efter ändringar** (det är det som publiceras).
  På Filips dator: `py -3 tools/build.py` (Python 3.7 via py-launchern;
  `python`/`python3` pekar på Python 2.7 resp. Microsoft Store-stubben).
- Källa: `src/app.html` (allt i en fil). Bygg: `python3 tools/build.py` → `docs/`.
- Tester på Filips dator: `powershell -ExecutionPolicy Bypass -File tests\run_all.ps1`
  (Python 3.7 + Playwright 1.35, kör i installerade Edge eftersom Playwrights Chromium
  inte startar där). **Testerna får aldrig nå riktiga Firebase**: `fakefb.py` blockerar
  Firebase-SDK:t och googleapis i varje context, spärrar service workers (deras anrop
  går förbi blockeringen – opt-in med `new_page(..., sw=True)`) och låser `window.firebase`
  så att riktiga SDK:t inte kan ersätta låtsas-Firebase. Utan det skrev testerna i skarpa
  databasen (hände 2026-09-28). Ta aldrig bort de skydden.
- Admin-koden står aldrig i testerna: `fakefb.TEST_PIN` godtas bara i
  testwebbläsaren. Ny admin-kod = nytt `ADMIN_PIN_HASH` = sha256("ffmap-admin:" + kod).
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
- **Flera sjöar:** en mapp per sjö, `lakes/<id>/` med `lake.json` (namn, center,
  geo-referens, djupskala, kartstilar, detaljrutor). build.py bäddar in alla lake.json
  som `LAKES` i sidan och kopierar resten (utom `raw/`) till `docs/lakes/<id>/`.
  Vald sjö: localStorage `ffmap_lake_v1` (eller `?lake=<id>`); byte = omladdning.
  Sjöspecifika localStorage-nycklar via `lakeKey(gammalNyckel, namn)` – Regnaren behåller
  sina gamla nycklar. Firestore: allt märkt med `lake`, `config/<lake>` per sjö.
- **Service worker** (`src/sw.js`): nätet först för sidan (4 s), cache för bilder.
  Sidan skickar `precache` med sjöns startfiler. Ändras kartbilder: nytt filnamn
  (`map_v2_*`, `tiles_v2/`, `depth_v2.txt`) och höj `CACHE` i sw.js.
- **Kartstilar:** `lakes/<id>/map_v1_<stil>.jpg` (samma geo-referens som `latLonToImgPx`).
  Bara vald stil laddas ner. **Detaljrutor** (`lake.json` "detail"): full upplösning i
  512-px-bitar, läggs ovanpå (`#detailLayer`, skärmkoordinater – inte i `#world`, som
  har will-change och skulle bli suddig) när kartbilden blir suddig; bara synliga hämtas.
- **Djupdata:** `lakes/<id>/depth_v1.txt` (hämtas vid start; byte = djup/steg, 255 land,
  251 = land-RLE). Båda sjöarna byggda med Genesis-verktygen och kalibrerade mot Genesis
  djupsiffror: Regnaren (zoom 16, samma utsnitt/geo-referens som förr, filer v2, 0–10,5 m,
  47 siffror, 90 % inom 0,15 m), Vågsfjärden (zoom 17, 0–40 m, 86 siffror, 90 % inom 0,25 m).
  Genesis siffror: liten siffra efter talet = tiondelar. `lakes/<id>/raw/depth_raw.npz`
  = djup i full upplösning (används av testerna).
- **Positionsintervall** per sjö (`config/<lake>`, localStorage via `lakeKey`); sjö utan
  inställning i databasen = 20 s.
- **Ny sjö från Genesis Social Map:** `tools/genesis_tiles.py` → `genesis_depth.py`
  (sheet + avläsning) → `genesis_render.py` (se README). Lärdomar: Genesis
  djupfärger (b_) är platta band men inte jämna i meter; kurvorna (t_) går var 0,5 m på
  zoom 17 men smälter ihop i branter (går inte att räkna); djupaste partierna är
  ofärgade hål; datablocken har 1–2 px genomskinliga skarvar. Zoom 18 finns men ger inte
  mer information än 17.
- Väder: Open-Meteo (ingen nyckel), cache 30 min, lagras lokalt.

## Firestore-regler (aktuella, i Firebase-konsolen)
waypoints: read auth; create kräver uid/name(≤60)/lat/lon; update/delete auth.
positions: read auth; write kräver lat, lon (number) och name (string).
usage: read auth; write kräver day (string) och r/w/d (number).
config/{lake}: read auth; write kräver posIntervalS i [10,20,30,60].

## Idéer som diskuterats men inte gjorts
- Riktig iPhone-app via Capacitor + TestFlight (bakgrundsposition). Kräver Mac + Apple-konto.
- iOS Genvägar-automation som skickar position när appen är stängd.
- "Håll skärmen tänd" (Wake Lock; fungerar i hemskärmsappar från iOS 18.4).
- Fångstlogg/tävlingsläge, navigera till plats, anteckningar på fiskeplatser.
