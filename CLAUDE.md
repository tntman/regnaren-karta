# FF Map – projektanteckningar för Claude

## Vad det är
Webbapp (PWA, "Lägg till på hemskärmen" på iPhone) för fiskegruppen Fiskfiskarna,
flera sjöar (Regnaren, Sibbofjärden, Sjösjön, Vågsfjärden, Östra Vitten – väljs i menyn). Djupkarta + GPS + delade fiskeplatser och båtpositioner via Firebase
(Firestore, anonym inloggning; identitet = valt namn). Användaren (Filip) är admin.
All text i appen är på svenska. Svara Filip på svenska, kort och tydligt.

## Arbetssätt
- Repot ligger i `E:\github\regnaren-karta` (Windows, gren `main` = webbappen). Appen (Capacitor) ligger i
  `E:\github\ffmap-app` (gren `app`, egen chatt – `tools/APP_PLAN.md`). Filip använder inte terminalen själv.
  **Git (beslut 2026-10-01):** Claude committar själv när en ändring är klar (sammanfattning + beskrivning på
  svenska, bara filer som hör till ändringen). **Push bara efter Filips ok** (main = live för gruppen; `app` =
  iPhone-bygge i Codemagic). Main in i `app`: `git fetch` + `git merge origin/main`, konflikter löser Claude.
  Aldrig force-push, aldrig skriva om historik. GitHub Desktop finns kvar – Filip kan använda den när han vill.
- **Flera chattar samtidigt (beslut 2026-10-03):** main-chatten bygger webben; sidochattar i samma repo (t.ex. profiler)
  undersöker och lämnar en plan i `tools/PLAN_*.md`, sedan stängs de. Chattarna väntar inte på varandra: bara EN chatt
  i taget bygger `docs/`, kör testerna (port 8899) och committar/pushar. Ska en sidochatt bygga samtidigt → egen
  worktree/gren. Kolla `git status` före commit och committa bara egna filer.
- **Källa: `src/`** – `css/`, `html/`, `js/` (en fil per del, klistras ihop i namnordning till EN
  sida). **Läs `src/README.md`** (vilken fil som innehåller vad; alla js-filer är ETT skript i en
  funktion – ordningen spelar roll).
- **Bygg alltid `docs/` efter ändringar** (det är det som publiceras): `py -3 tools/build.py`
  (Python 3.12 via py-launchern sedan ominstallationen 2026-10-03).
- Tester: `powershell -ExecutionPolicy Bypass -File tests\run_all.ps1` (Python 3.12 + Playwright
  (pip --user), kör i installerade Edge eftersom Playwrights Chromium inte startar där; `tests/fakefb.py`
  låtsas vara Firebase). Kör alltid testerna efter ändringar och lägg till tester för ny funktion.
  Parallellt (6 åt gången, `TEST_JOBS`), ~3,5 min, mot `tests/serve.py` (egen webbserver med lång
  anslutningskö). Tester får inte ändra filer i `docs/` – blockera i webbläsaren (`pg.route`).
  **Urval:** `tests\run_all.ps1 heatmap filter` kör bara `test_*heatmap*.py` och `test_*filter*.py`.
  **Hur mycket som testas (Filips regel, 2026-10-01):** kör INTE hela sviten för små ändringar (text,
  färg, småfix). Kör områdets tester med urval + de testfiler som nämner det jag ändrat (sök i `tests/`
  efter id, klass, färg eller text jag rört – hittar "oväntade" tester, t.ex. test_types vid färgbyte).
  Skriv tydligt i svaret: "testat med urval: …". HELA sviten körs när Filip säger "klart"/"kör alla
  tester", vid större ändringar som rör flera filer/områden (gör det självmant när det känns så), och
  alltid innan en Hjälp-omgång. **Påminn Filip** att köra hela sviten när flera urvals-ändringar har
  samlats sedan senaste hela körningen. Allt är ett skript – en ändring kan bryta tester i helt andra filer.
- **Testerna får aldrig nå riktiga Firebase**: `fakefb.py` blockerar Firebase-SDK:t och googleapis
  i varje context, spärrar service workers (deras anrop går förbi blockeringen – opt-in med
  `new_page(..., sw=True)`) och låser `window.firebase` så att riktiga SDK:t inte kan ersätta
  låtsas-Firebase. Utan det skrev testerna i skarpa databasen (hände 2026-09-28). Ta aldrig bort
  de skydden. fakefb blockerar även opendata.fmi.fi och Open-Meteo (vädret – ett test som behöver väder lägger egen `ctx.route`).
- Admin (Filip, upplåst med koden på enheten) kan alltid ändra och ta bort allas fiskeplatser
  (`adminCanEditAll()` = `isAdminUnlocked()`). Admin-koden står aldrig i testerna: `fakefb.TEST_PIN`
  godtas bara i testwebbläsaren. Ny admin-kod = nytt `ADMIN_PIN_HASH` = sha256("ffmap-admin:" + kod).
- Publicering: GitHub Pages från `main` / `docs`. Commit + push = live. Adress **https://karta.fiskfiskarna.se**
  (`docs/CNAME`, sedan 2026-10-04, Enforce HTTPS på; `tntman.github.io/regnaren-karta` skickar dit). Ny adress =
  telefonens minne (localStorage, offline-cache) börjar om – namn, admin-kod, offline-kartor, hemskärmen på nytt.
- Filip vill ofta se **bilder/förslag innan** något implementeras ("visa först").
  När han skriver "svara först" – svara, implementera inte.
- **Hjälp uppdateras INTE vid varje ändring** (Filips beslut): skriv upp vad som ändrats i
  `tools/HJALP_TODO.md` (avsnitt, animering, förslag på nyhetsrad) och gör allt i en omgång när Filip
  säger till. **Påminn Filip** när listan har ≥ 5 rader eller äldsta raden är > 1 vecka.

## Anteckningar per område – läs den som berörs
| Område | Fil |
|---|---|
| Vilka som använder appen, när och varför (produktfakta för design, `/impeccable`) | `PRODUCT.md` |
| Utseendet: färger, typsnitt, former, komponenter, rörelser, regler (design A sedan 2026-10-05; ritytan med alla skärmar i DESIGN.md) | `DESIGN.md` (+ `.impeccable/design.json`) |
| Vilken källfil innehåller vad | `src/README.md` |
| Kartor (Genesis, zoomnivåer, djup, relief, OpenStreetMap, ny sjö) | `tools/KARTOR.md` |
| UI-byggstenar (bottenpaneler, chips, reglage, faktarutor, notiser) | `tools/UI.md` |
| Hjälp-sidan och animeringarna | `tools/HJALP.md`, `tools/HJALP_TODO.md` |
| Kartanalys, lodet, rutten, Åk hit, platsens ruta | `tools/NOTES_ANALYS.md` |
| Snabbmeddelanden | `tools/NOTES_MEDDELANDEN.md` |
| Väder, vind och lä, blixtar, åskvarning | `tools/NOTES_VADER.md` |
| Heatmap (fångster: Fiskfiskarnas API, när det hämtas, Fångstdata) | `tools/NOTES_HEATMAP.md` |
| Spår (sparas för evigt i Firestore `tracks`), Spår-menyn, stopp som ringar, Fog of war | `tools/NOTES_SPAR.md` |
| Båtikoner (valbar ikon för din båt – idé, förslagsblad, ej byggt) | `tools/boaticons.md` |
| Testläget (= Demo Mode: egen testdatabas, admin styr en låtsastävling) | `tools/NOTES_TESTLAGE.md` |

Uppdatera rätt anteckning när något ändras.

## Viktiga saker i koden
- **Testläge = Demo Mode** (`TEST_MODE`, `js/10-core.js`; NOTES_TESTLAGE.md): på/av = omladdning in i ett **eget
  Firebase-projekt** (`FIREBASE_TEST_CONFIG`, `js/14-spots.js`), telefonens kopior med egna nycklar (`testKey()`),
  ingen spårsynk, ingen Fiskfiskarna/FMI (undantag: profilerna läses ur den riktiga kopian, och profilens "Ladda in data" hämtar dem från API:t – `PF_DEMO_KEY`, `js/67-profiles.js`) (låtsastävlingen i `config/<sjö>.test`, `js/37-testmode.js`). Ny data som
  sparas i telefonen och speglar databasen → `testKey()`. Ny skrivning till Firestore behöver inget (projektet byts).
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
  `theme-color`: design A:s midnatt #141822 (21c, sedan 2026-10-05; innan dess #090B10 och #08080A, ännu tidigare mörkblå #06141C) – samma
  som kartans bakgrund (`#stage`), body, manifestet och toppens tona i stående hemskärmsapp (`html.iosApp`,
  börjar i #141822 och tonar ut). Ändrad statusrad kräver att appen läggs till på hemskärmen igen.
- **Ordning/hoisting:** många `var` deklareras i senare js-filer. Sätt checkbox-tillstånd som
  beror på sådana variabler i `boot()` (`js/90-boot.js`, se toggleDepth/toggleTrack).
- **Firebase-kvot** (gratis: 50k reads/dygn). Positioner delas var 20:e s vid rörelse
  (admin-inställning i `config/<lake>`, per sjö; sjö utan inställning = 20 s), var 60:e s stilla.
  Undvik onödiga get().
- **Flera sjöar:** en mapp per sjö, `lakes/<id>/` med `lake.json` (namn, center, geo-referens,
  djupskala, kartstilar, zoomnivåer) + `raw/`. build.py bäddar in alla lake.json som `LAKES`;
  bilderna ligger bara i `docs/lakes/<id>/`; `lakes/<id>/names.json` = OSM-namnen (`tools/osm_names.py`, steg 8 i KARTOR.md) som build.py också bäddar in. Vald sjö: localStorage `ffmap_lake_v1` (eller
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
- **Typer:** Markering, Abborre (orange), Gädda (grön), Gös (blå #3A86FF), Hem (brunt hus #A8693A, inte i Liknande), Fara (röd
  stoppskylt `.wpFara`, likadan för allas, ALDRIG dold av filter), Träffpunkt (`meet`: fyr med
  ringar, `expiresAt` = +1 h, en per person, bara ägaren/admin tar bort; utgångna döljs och
  ägarens app raderar dem).
- **Kartlägesknapp** (`#mapTypeBtn`): tryck = s1→s2→c1→v1, håll = alla.
- **Offline-nedladdning** (Inställningar): de fyra kartlägena i knappen (`QUICK_STYLES`), alla
  zoomnivåer + djupdata, i egen cache `ffmap-offline-<sjö>-<mapversion>` (sw.js rensar den inte).
  Status i localStorage (`lakeKey`), pausa/fortsätt, fortsätter efter rotation. Ny kartversion →
  "ladda ner igen". Regnaren ~1 200 bitar / 66 MB.
- **Filter**: två grupper – **Markeringar** (Mina, Andras, Båtar + typerna som en rad prickar
  `.visDot`: ifylld = visas, grå ring = dold) och **Lager** (Spår, Väder, Vind och lä, Blixtar,
  Kartanalys, Heatmap `#toggleHeatmap`, Fog of war `#toggleFog` (mörkt utom där du varit, 50 m, Demo Mode ger ett tillfälligt spår som inte sparas, `js/48-fog.js`, NOTES_SPAR.md), Kompass `#toggleCompass`: kil 40°/500 m, vit, mot telefonens kompass, iOS-lov vid trycket, `js/53-compass.js`, Namn `#toggleNames` (på som standard): OSM-namn på kartan ur `lakes/<id>/names.json`, `js/59-names.js`, KARTOR.md; utseendet i Inställningar → Kartan → Platsnamn: storlek, synlighet, prick, alla/bara vatten, `namesCfg`). Kartanalys och Heatmap i Filter visar/döljer bara –
  påslaget/avslaget sker i deras egna rutor. "Djup" (`#toggleDepth`), "Andras fiskeplatser 50/100 %" och
  "Håll skärmen tänd" ligger i Inställningar. Knapparna nere till höger = 2 × 2-rutnät (`--bb`).
- **Panorera över markeringar**: ett finger som börjar på en plats, båt, bubbla eller etikett
  panorerar kartan (`mapPointerDown(e, true)`: ingen långtryckning/lod); bara ett tryck utan att
  dra öppnar den (`mapDraggedJustNow()` i deras click).
- **Inställningar i avsnitt** (`<details class="setSec">`): namnet överst, sedan Kartan, Båten,
  Varningar, Kartanalys, Fångstdata, Offline, Avancerat. Stängt = rubrik + en rad med vad som är valt (`setSums()`,
  `js/28-menu.js`, läser av kontrollerna). Vilka som är öppna: `ffmap_settings_open_v1`; fakefb
  öppnar alla i testerna. "Åskvarning av"-skylten öppnar Varningar (`openSettingsSec('warn')`).
- **Skyltar under väderchipet**: `#hmPill` (Heatmap) och `#anPill` (Kartanalys, när något läge är
  på) – aldrig båda, lägena stänger av varandra. Tryck = rutan.
- **Håll skärmen tänd** (Inställningar → Båten, av som standard, `ffmap_wakelock_v1`): Wake Lock, tas igen när
  appen blir synlig. På = gul sol `#wakeBadge` under väderchipet; tryck = av + notis `#wakeNote`.
- **Hjälp** (menyn → Hjälp; öppnas själv efter första namnvalet): "Nytt i appen" = `HELP_NEWS`
  (`js/30-help.js`), animeringar av `tools/help_anim.py` – allt i `tools/HJALP.md`.
- **Ledare** (Filter → Lager `#toggleLeader`, av som standard, `js/69-leader.js`, `css/74-leader.css`): under en pågående tävling en lista under
  väderchipet (`#leadPill`, topp 5 + du) och 👑 efter ledarens namn på båtens etikett. Poäng = de 5 längsta av varje art (abborre, gädda, gös) ihop,
  bara fångster som räknas (API:ets `approved` + minimum abborre 25, gädda 50, gös 35 cm). Data = live-fångsterna för hela tävlingen (`catchLive.all`, alla vatten – heatmapen tar bara sjöns), ingen egen hämtning. Tryck på ett namn i listan = kartan centreras på personen; tryck på en båt = rutan som förut (profil, eller "Samma båt") med personens fångster listade (`pfCatchRows`, `js/67-profiles.js`).
- **Heatmap** (Kartlägen → Heatmap sist): fångster från tävlingarna, fyra stilar, egen bottenruta, inte
  samtidigt som Kartanalys, "Heatmap"-skylt under väder. Data från Fiskfiskarnas API (historik +
  live under tävling, kopia i telefonen, Inställningar → Fångstdata). Allt i `tools/NOTES_HEATMAP.md`.
- **Säkerhetskopia** (Admin, `js/36-admin.js`): hela databasen (waypoints alla sjöar, config, tracks, trackusers –
  inte positions/usage) till en JSON-fil och tillbaka. Gratisplanen har ingen egen backup, och reglerna kräver bara
  inloggning (vem som helst kan logga in anonymt). Återställ = `set` på allt i filen, bara till samma projekt. Ny
  samling som ska sparas för evigt → lägg till i `BACKUP_COLS`.
- **Tävlingslåset** (`mapEditAllowed()`/`showLockCard()` sist i `js/66-catches.js`, `tools/PLAN_TAVLINGSLAS.md`): platser kan bara
  läggas, ändras (namn/typ) och tas bort från 7 dagar före till 7 dagar efter en tävling på sjön (datum i API-kopian, eller status
  `active`) – även Fara/Träffpunkt. Annars rutan `#lockCard` (när det öppnar + Öppna Demo Mode). Alltid öppet: Demo Mode, upplåst
  admin, när appen inte vet (ingen kopia/API-fel), och när admin slagit av låset för alla (Admin → Tävlingslåset, `config/<sjö>.lockOff`). Båtpositioner, meddelanden, spår låses inte. Bara i appen – reglerna släpper in
  alla inloggade. Grindarna ligger i knapparnas handlers (24-boats.js), inte i `deleteWaypointById` (utgångna Träffpunkter, Avbryt
  på ny plats). Testerna: låset av i testwebbläsaren (`window.__ffNoLock`, fakefb) utom med `cfg={'lock': True}` (test_lock.py).
- **Strandlinje** (Inställningar → Kartan `#toggleShore`, på som standard, `ffmap_shore_v1`): sjöns kant som tunn vit linje på vanliga kartan,
  samma som Heatmap/Kartanalys ritar (`hmShoreLayer`, `js/68-heatmap.js`); döljs när de visas (de har sin egen).
- **Startfilm** (`js/35-splash.js`, `tools/PLAN_SPLASH.md`): 3D-loggan 3,5 s vid första starten och när appen inte använts på > 24 h
  (`ffmap_last_active_v1`, hela telefonen: skrivs vid start, varje minut när den syns och när den döljs – även tillbaka ur bakgrunden
  utan omladdning). Skriptet i `src/head.html` sätter `html.splash` före första bilden (allt svart, kartan blinkar aldrig fram).
  Namnrutan väntar (`afterSplash`). Inställningar → Avancerat → Startfilmen "Spela" visar den igen. Testerna: fakefb sätter nyckeln = nu i varje context (opt-in `splash=True`, test_splash).
- **Pushnotiser**: inte gjort (kräver server/Firebase-betalplan).

## Firestore-regler (aktuella, i Firebase-konsolen)
waypoints: read auth; create kräver uid/name(≤60)/lat/lon; update/delete auth.
positions: read auth; write kräver lat, lon (number) och name (string).
usage: read auth; write kräver day (string) och r/w/d (number).
config/{lake}: read auth; write kräver posIntervalS i [10,20,30,60] (därför skickas det med även när `lockOff`/`test` sparas).
catches/{lake}: används inte längre (fångsterna kommer från Fiskfiskarnas API) – regeln kan tas bort.
tracks/{id}: read auth; write kräver lake/uid/day/pts (string), n (number), pts ≤ 900 000 tecken – spåren (NOTES_SPAR.md). **Regeln ska läggas till i konsolen** (Filip) innan spår sparas i databasen.
Testprojektet (Demo Mode, NOTES_TESTLAGE.md) har samma regler.
trackusers/{lake}: read/write auth – register över vilka som har spår på sjön (`{users:{<safeUid>:{u,n}}}`), fyller Spår-menyns rullgardin. Filip har lagt regeln i konsolen.

## Idéer som diskuterats men inte gjorts
- Riktig iPhone-app via Capacitor + TestFlight (bakgrundsposition). Kräver Mac + Apple-konto.
- iOS Genvägar-automation som skickar position när appen är stängd.
- Fångstlogg/tävlingsläge, anteckningar på fiskeplatser, pushnotiser (Träffpunkt/Fara/blixt).
- Gruppkod (2026-10-04, väntar): skydda datan mot utomstående med ETT gemensamt Firebase-konto (Email/Password,
  `ffmap-grupp@example.com`, lösenord = koden, skrivs en gång per telefon). Sign-up och delete av under User actions;
  reglerna `request.auth.token.email == '…'` i stället för `request.auth != null` – först när alla skrivit koden
  (Admin visar vem), sedan Anonymous av. Testprojektet behåller anonym inloggning. iPhone-appen måste få det först.
- Tunga beräkningar (Kartanalys, rutten, lä-fältet) i en Web Worker – bara om det börjar hacka.
