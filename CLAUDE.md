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
- **Källa: `src/`** – `css/`, `html/`, `js/` (en fil per del, klistras ihop i namnordning till EN
  sida). **Läs `src/README.md`** (vilken fil som innehåller vad; alla js-filer är ETT skript i en
  funktion – ordningen spelar roll).
- **Bygg alltid `docs/` efter ändringar** (det är det som publiceras): `py -3 tools/build.py`
  (Python 3.7 via py-launchern; `python`/`python3` pekar på Python 2.7 resp. Microsoft Store-stubben).
- Tester: `powershell -ExecutionPolicy Bypass -File tests\run_all.ps1` (Python 3.7 + Playwright
  1.35, kör i installerade Edge eftersom Playwrights Chromium inte startar där; `tests/fakefb.py`
  låtsas vara Firebase). Kör alltid testerna efter ändringar och lägg till tester för ny funktion.
  Parallellt (6 åt gången, `TEST_JOBS`), ~3,5 min, mot `tests/serve.py` (egen webbserver med lång
  anslutningskö). Tester får inte ändra filer i `docs/` – blockera i webbläsaren (`pg.route`).
- **Testerna får aldrig nå riktiga Firebase**: `fakefb.py` blockerar Firebase-SDK:t och googleapis
  i varje context, spärrar service workers (deras anrop går förbi blockeringen – opt-in med
  `new_page(..., sw=True)`) och låser `window.firebase` så att riktiga SDK:t inte kan ersätta
  låtsas-Firebase. Utan det skrev testerna i skarpa databasen (hände 2026-09-28). Ta aldrig bort
  de skydden. fakefb blockerar även opendata.fmi.fi.
- Admin (Filip, upplåst med koden på enheten) kan alltid ändra och ta bort allas fiskeplatser
  (`adminCanEditAll()` = `isAdminUnlocked()`). Admin-koden står aldrig i testerna: `fakefb.TEST_PIN`
  godtas bara i testwebbläsaren. Ny admin-kod = nytt `ADMIN_PIN_HASH` = sha256("ffmap-admin:" + kod).
- Publicering: GitHub Pages från `main` / `docs`. Commit + push = live.
- Filip vill ofta se **bilder/förslag innan** något implementeras ("visa först").
  När han skriver "svara först" – svara, implementera inte.
- **Hjälp uppdateras INTE vid varje ändring** (Filips beslut): skriv upp vad som ändrats i
  `tools/HJALP_TODO.md` (avsnitt, animering, förslag på nyhetsrad) och gör allt i en omgång när Filip
  säger till. **Påminn Filip** när listan har ≥ 5 rader eller äldsta raden är > 1 vecka.

## Anteckningar per område – läs den som berörs
| Område | Fil |
|---|---|
| Vilken källfil innehåller vad | `src/README.md` |
| Kartor (Genesis, zoomnivåer, djup, relief, OpenStreetMap, ny sjö) | `tools/KARTOR.md` |
| UI-byggstenar (bottenpaneler, chips, reglage, faktarutor, notiser) | `tools/UI.md` |
| Hjälp-sidan och animeringarna | `tools/HJALP.md`, `tools/HJALP_TODO.md` |
| Kartanalys, lodet, rutten, Åk hit, platsens ruta | `tools/NOTES_ANALYS.md` |
| Snabbmeddelanden | `tools/NOTES_MEDDELANDEN.md` |
| Väder, vind och lä, blixtar, åskvarning | `tools/NOTES_VADER.md` |

Uppdatera rätt anteckning när något ändras.

## Viktiga saker i koden
- **iOS hemskärmsapp laddar om sidan vid rotation** (WebKit visar annars en gammal bild och trycken
  hamnar fel). Sidan minns om den laddades liggande/stående (`loadedLandscape`, `js/12-map.js`) och
  laddar om när skärmen lagt sig åt andra hållet – även efter en resize utan vridningshändelse (en
  omladdning mitt i en vridning rättar sig själv). Skydd mot loop: högst 4 omladdningar på 20 s
  (förr: ingen vridning inom 3 s → "förskjutna" knappar om man vred tillbaka snabbt). Allt tillstånd
  måste överleva: inställningar i localStorage, öppna vyer/halvgjort i `saveRotationState()`/
  `restoreRotationUi()` (sessionStorage, `js/92-rotation.js`; sparas när vridningen BÖRJAR, innan
  nya storleken flyttat skrollägen). Nya UI-tillstånd ska läggas till där.
- **iOS hemskärmsapp:** statusraden är `default` (src/head.html), INTE `black-translucent`: med
  translucent gör iOS 26 webbvyn en statusrad för kort – en död rand längst ner som ingen CSS
  når (WebKit-bugg 301108). `default` lägger sidan under statusraden (som `black`) men ger raden
  `theme-color`: appens mörkblå #06141C – samma som kartans bakgrund (`#stage`), body, manifestet
  och toppens tona i stående hemskärmsapp (`html.iosApp`, börjar i #06141C och tonar ut). Filip vill
  ha den blå, inte svart (svart provades 2026-09-29). Ändrad statusrad kräver att appen läggs till
  på hemskärmen igen.
- **Ordning/hoisting:** många `var` deklareras i senare js-filer. Sätt checkbox-tillstånd som
  beror på sådana variabler i `boot()` (`js/90-boot.js`, se toggleDepth/toggleTrack).
- **Firebase-kvot** (gratis: 50k reads/dygn). Positioner delas var 20:e s vid rörelse
  (admin-inställning i `config/<lake>`, per sjö; sjö utan inställning = 20 s), var 60:e s stilla.
  Undvik onödiga get().
- **Flera sjöar:** en mapp per sjö, `lakes/<id>/` med `lake.json` (namn, center, geo-referens,
  djupskala, kartstilar, zoomnivåer) + `raw/`. build.py bäddar in alla lake.json som `LAKES`;
  bilderna ligger bara i `docs/lakes/<id>/`. Vald sjö: localStorage `ffmap_lake_v1` (eller
  `?lake=<id>`); byte = omladdning. Sjöspecifika localStorage-nycklar via `lakeKey(gammalNyckel, namn)`
  – Regnaren behåller sina gamla nycklar. Firestore: allt märkt med `lake`, `config/<lake>` per sjö.
- **Service worker** (`src/sw.js`): nätet först för sidan (4 s), cache för bilder. Sidan skickar
  `precache` med sjöns startfiler. Ändras kartbilder: nytt filnamn (`map_v2_*`, `tiles_v2/`,
  `depth_v2.txt`) och höj `CACHE` i sw.js.
- **Kartbilder = zoomnivåer som på Genesis** (KARTOR.md): kartbilden är zoom 14, högre nivåer
  512-px-bitar i `#detailLayer` (skärmkoordinater – inte i `#world`, som har will-change och skulle
  bli suddig). Lager 14–18, max zoom 18,6 (`MAX_ZOOM`). Fast djupskala, 8 kartlägen.
- **Djupkurvor och siffror ritas ALDRIG av oss** (Filips krav) – bara Genesis t_-lager.
- **Djupdata:** `docs/lakes/<id>/depth_v<V>.txt` (byte = djup/steg, 252 = sjö utan djupdata,
  255 land, 251/253 = packade rader). `lakes/<id>/raw/depth_raw.npz` = full upplösning (testerna).
  `isLakeAtImgPx()` = sjö eller land.
- **Typer:** Markering, Abborre, Gädda, Gös, Hem (blått hus, inte i Liknande), Fara (röd
  stoppskylt `.wpFara`, likadan för allas, ALDRIG dold av filter), Träffpunkt (`meet`: fyr med
  ringar, `expiresAt` = +1 h, en per person, bara ägaren/admin tar bort; utgångna döljs och
  ägarens app raderar dem).
- **Kartlägesknapp** (`#mapTypeBtn`): tryck = s1→s2→c1→v1, håll = alla.
- **Offline-nedladdning** (Inställningar): de fyra kartlägena i knappen (`QUICK_STYLES`), alla
  zoomnivåer + djupdata, i egen cache `ffmap-offline-<sjö>-<mapversion>` (sw.js rensar den inte).
  Status i localStorage (`lakeKey`), pausa/fortsätt, fortsätter efter rotation. Ny kartversion →
  "ladda ner igen". Regnaren ~1 200 bitar / 66 MB.
- **Filter**: rubriken "Visa markeringar"; "Namn" borttaget (namnen visas alltid). "Djup" (djupet
  under båten, `#toggleDepth`) och "Andras fiskeplatser 50/100 %" (`#othersOpacitySeg`) ligger i
  Inställningar. Knapparna nere till höger = 2 × 2-rutnät (`--bb`).
- **Panorera över markeringar**: ett finger som börjar på en plats, båt, bubbla eller etikett
  panorerar kartan (`mapPointerDown(e, true)`: ingen långtryckning/lod); bara ett tryck utan att
  dra öppnar den (`mapDraggedJustNow()` i deras click).
- **Håll skärmen tänd** (Filter, av som standard, `ffmap_wakelock_v1`): Wake Lock, tas igen när
  appen blir synlig. På = gul sol `#wakeBadge` vid namnet; tryck = av + notis `#wakeNote`.
- **Hjälp** (menyn → Hjälp; öppnas själv efter första namnvalet): "Nytt i appen" = `HELP_NEWS`
  (`js/30-help.js`), animeringar av `tools/help_anim.py` – allt i `tools/HJALP.md`.
- **Pushnotiser**: inte gjort (kräver server/Firebase-betalplan).

## Firestore-regler (aktuella, i Firebase-konsolen)
waypoints: read auth; create kräver uid/name(≤60)/lat/lon; update/delete auth.
positions: read auth; write kräver lat, lon (number) och name (string).
usage: read auth; write kräver day (string) och r/w/d (number).
config/{lake}: read auth; write kräver posIntervalS i [10,20,30,60].

## Idéer som diskuterats men inte gjorts
- Riktig iPhone-app via Capacitor + TestFlight (bakgrundsposition). Kräver Mac + Apple-konto.
- iOS Genvägar-automation som skickar position när appen är stängd.
- Fångstlogg/tävlingsläge, anteckningar på fiskeplatser, pushnotiser (Träffpunkt/Fara/blixt).
- Tunga beräkningar (Kartanalys, rutten, lä-fältet) i en Web Worker – bara om det börjar hacka.
