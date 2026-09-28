# FF Map – projektanteckningar för Claude

## Vad det är
Webbapp (PWA, "Lägg till på hemskärmen" på iPhone) för fiskegruppen Fiskfiskarna,
flera sjöar (Regnaren, Sjösjön, Vågsfjärden – väljs i menyn). Djupkarta + GPS + delade fiskeplatser och båtpositioner via Firebase
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
- Tester: `tests/run_all.ps1` / `run_all.sh` (Playwright + `tests/fakefb.py` som låtsas vara Firebase).
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
- **Kartorna (Genesis, zoomnivåer, djup, relief, OpenStreetMap): läs `tools/KARTOR.md`**
  innan du bygger en sjö eller ändrar hur kartor ritas – och uppdatera den när något ändras.
- **Flera sjöar:** en mapp per sjö, `lakes/<id>/` med `lake.json` (namn, center,
  geo-referens, djupskala, kartstilar, zoomnivåer) + `raw/`. build.py bäddar in alla
  lake.json som `LAKES` i sidan; bilderna ligger bara i `docs/lakes/<id>/`.
  Vald sjö: localStorage `ffmap_lake_v1` (eller `?lake=<id>`); byte = omladdning.
  Sjöspecifika localStorage-nycklar via `lakeKey(gammalNyckel, namn)` – Regnaren behåller
  sina gamla nycklar. Firestore: allt märkt med `lake`, `config/<lake>` per sjö.
- **Service worker** (`src/sw.js`): nätet först för sidan (4 s), cache för bilder.
  Sidan skickar `precache` med sjöns startfiler. Ändras kartbilder: nytt filnamn
  (`map_v2_*`, `tiles_v2/`, `depth_v2.txt`) och höj `CACHE` i sw.js.
- **Kartbilder = zoomnivåer som på Genesis** (se KARTOR.md): kartbilden är zoom 14, högre
  nivåer 512-px-bitar i `#detailLayer` (skärmkoordinater – inte i `#world`, som har
  will-change och skulle bli suddig). Båda sjöarna: djupkarta på zoom 17, lager 14–18
  (zoom 18 bara Djupfärger + C-MAP original). Max zoom 18,6 på alla sjöar (`MAX_ZOOM`).
  Fast djupskala (samma färg = samma djup i alla sjöar), 8 kartlägen (Natt borttagen).
- **Djupkurvor och siffror ritas ALDRIG av oss** (Filips krav) – bara Genesis t_-lager.
  Relief "T1 × AO, 1,2 m" bara i Djupfärger + Blå relief, se KARTOR.md avsnitt 8.
- **Djupdata:** `docs/lakes/<id>/depth_v<V>.txt` (hämtas vid start; byte = djup/steg,
  252 = sjö utan djupdata (OpenStreetMap), 255 land, 251/253 = packade rader).
  `lakes/<id>/raw/depth_raw.npz` = djup i full upplösning (används av testerna).
  `isLakeAtImgPx()` = sjö eller land.
- **Lodet** visar djup · sträcka SJÖVÄGEN · restid. Rutt: grovt rutnät (~9 m), Dijkstra från
  lodet (en gång per lod) → sedan "gå nedför" från båten vid varje GPS-fix; håller avstånd
  från land; räta ut med siktlinjer. Fart: aktuell om ≥1,5 kn, annars snitt/marschfart.
- **Typer:** Markering, Abborre, Gädda, Gös, Fara (röd, triangel), Träffpunkt (`meet`:
  fyr med ringar, `expiresAt` = +1 h, en per person, bara ägaren/admin tar bort; utgångna
  döljs och ägarens app raderar dem).
- **Kartlägesknapp** (`#mapTypeBtn`, vänster om Filter): tryck = s1→s2→c1→v1, håll = alla.
- **Offline-nedladdning** (Inställningar): de fyra kartlägena i knappen (`QUICK_STYLES`), alla
  zoomnivåer + djupdata, i egen cache `ffmap-offline-<sjö>-<mapversion>` (sw.js rensar den
  inte; `caches.match` hittar den). Status i localStorage (`lakeKey`), pausa/fortsätt,
  fortsätter efter rotation (sessionStorage-flagga). Ny kartversion → "ladda ner igen".
  Regnaren ~1 200 bitar / 66 MB.
- **Vindpilen** i väderkortet/-chipet är orange (#FFB23F).
- **Vind och lä** (Filter, av som standard, `ffmap_show_wind_v1`): canvas `#windLayer` i
  skärmkoordinater. Fetch (öppet vatten uppvinds, ±15°) på ruttnätet, interpolerat till
  djupnätet och utjämnat ~10 m. Lä ritas per skärmpunkt (var 2:a css-px, `drawLeeView`,
  görs om bara när vyn flyttas) – inte som förstorad bild, som blev kantig inzoomat. Lä = fetch < gräns = 3600/U² (vågformel, kalibrerad efter Filip: 6 m/s → 100 m;
  "5 cm-vågor" var för generöst), 30–400 m; < 1,5 m/s = hela sjön lä. Lä: ljus ton + tunn kant; öppet vatten: "kometer" (tunt huvud,
  tjockare svans) som driver med vinden, fler/längre/snabbare vid mer vind. ~30 fps bara
  när påslaget och synligt. `window.__ffWind()` för testerna.
- **Blixtar** (Filter, av som standard, `ffmap_show_lightning_v1`): blixtnedslag i realtid från
  FMI (Finlands meteorologiska institut, öppen data, täcker Sverige, ingen nyckel, CC BY 4.0,
  några min fördröjning), WFS `fmi::observations::lightning::simple`, ~40 km runt sjön, senaste
  30 min, hämtas var 2:a min när påslaget och synligt (inte via Firebase). Varning `#ltPill` under
  väderchipet (närmaste inom 30 km, orange, röd < 10 km), radar `#ltRadar` under Filter (30 km,
  norr upp), ⚡ på canvas `#ltLayer` (gul 0–5 min, orange 5–15, grå/bleknar till 30; nya blinkar),
  markör vid skärmkanten mot närmaste när den är utanför bild. Avstånd från dig om du är vid sjön,
  annars från sjöns mitt. Inget visas när det är lugnt. `window.__ffLightning()` för testerna;
  fakefb blockerar opendata.fmi.fi i alla tester (test_lightning har egen låtsas-XML).
- **Positionsintervall** per sjö (`config/<lake>`, localStorage via `lakeKey`); sjö utan
  inställning i databasen = 20 s.
- **Ny sjö:** receptet steg för steg + Genesis egenheter + vad som testats och förkastats
  står i `tools/KARTOR.md`.
- Tester körs parallellt (6 åt gången, `TEST_JOBS` ändrar), ~3 min. Tester får inte ändra
  filer i `docs/` (de körs samtidigt) – blockera i webbläsaren i stället (`pg.route`).
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
