# Plan: Startfilm (splash) med 3D-loggan

**Byggd 2026-10-06** (main-chatten). Avvikelse: HTML:en ligger i `src/html/05-splash.html` (först i sidan, så att den finns
redan i första bilden) i stället för 60-. Testkrok: `window.__ffSplashLoadMs` (gränsen 1,5 s; testerna väntar längre).
Filip 2026-10-06: vid "Spela" (utan omladdning) byter iOS inte statusradens färg → då rörs den inte, och toppen tonar i stället
från #141822 ner i det svarta (`.spTop`, `#splash.tint`). Vid start (head-skriptet före första bilden) sätts den till #000.
**Kvar:** Filip kollar att statusraden är svart vid en riktig start.

Från sidochatten 2026-10-06. Mockupen som Filip godkände (förslag 7) finns i `tools/splash_mockup.html`
(öppna via servern "repo" i `.claude/launch.json`: http://localhost:8897/tools/splash_mockup.html;
`?t=1.5` fryser bilden vid den tiden).

## Vad det är
En startfilm på 3,5 s. Den visas när appen startar första gången och när den inte varit igång på över 24 timmar.

| Tid | Händelse |
|---|---|
| 0–0,25 s | helt svart |
| 0–1,9 s | fisken snurrar in, ett lugnt varv (`1-(1-a)²`) som saktar in, från 55 % till full storlek. Ljuset tonar upp långsamt (`seg^1.8`) och är fullt precis när fisken står rätt |
| 1,9–2,5 s | fisken står still i fullt ljus och vaggar lite. Nyckelljuset glider över = glansen i lacken |
| 2,5–3,1 s | fisken vrider sig och flyger genom kameran (skala ×10, +140°), varm blixt vid 3,0 s |
| 2,9–3,5 s | det svarta löses upp, appen under går från suddig (14 px, skala 1,06, mörkare) till skarp |

Ljuset: varmt nyckelljus (SpotLight #ffd9b0) som glider från vänster till höger, kallt motljus (#7fb0ff) bakifrån,
varmt fyllnadsljus (#ff9a60) nedifrån, ACES-tonmappning, `MeshPhysicalMaterial` med klarlack. Varmt
radiellt sken bakom, vinjett och filmbrus. Den falska glöden är kartans ram, liten och suddig, lagd med
`screen` ovanpå. **Ingen** ljuskägla eller linsreflex (Filip tog bort dem).

## När den visas
- Ny nyckel `ffmap_last_active_v1` (tidsstämpel i localStorage, gäller hela telefonen, ingen `lakeKey`/`testKey`).
  Den skrivs vid start, varje minut medan appen syns och vid `visibilitychange` → hidden.
- Vid start: saknas nyckeln eller är den äldre än 24 h → visa filmen.
- Omladdningar (rotation, byte av sjö, Demo Mode på/av, Logga ut) sker strax efter att nyckeln skrivits, så de
  visar aldrig filmen. Ingen specialkod behövs. Om telefonen vrids mitt i filmen: omladdning → appen utan film (godtagbart).
- **Beslut (Filip 2026-10-06):** filmen visas också när appen legat i bakgrunden > 24 h och kommer tillbaka *utan*
  omladdning (iOS håller ofta hemskärmsappen vid liv). Kolla vid `visibilitychange` → visible, innan nyckeln skrivs om.
  Då är sidan redan ritad: sätt `html.splash` direkt (det svarta täcker allt) och kör som vid start.

## Viktigt: inget får blinka fram
Kartan får inte synas innan filmen börjar. Därför:
1. Ett litet inline-skript i `src/head.html` läser nyckeln **innan sidan ritas** och sätter
   `document.documentElement.classList.add('splash')`.
2. `html.splash #splash` = svart lager över allt (z-index högst) direkt från CSS, redan i första bilden.
3. JS laddar three.js och bygger skylten. Filmens klocka startar först när allt är klart.
   - Tar laddningen över **1,5 s** (första starten på dåligt nät; three.js ≈ 700 kB): hoppa över fisken och tona bara
     bort det svarta (0,5 s).
   - Laddningen misslyckas → samma sak.
4. Statusraden: `theme-color` är #141822, så det blir en rand ovanför det svarta. **Testa på iPhone:** byt
   `meta[name=theme-color]` till #000 medan filmen går och tillbaka efteråt. Om iOS inte uppdaterar den dynamiskt
   i hemskärmsappen: starta filmen från #141822 i stället för #000 (nästan samma i mörkret).

## Filer
- `src/head.html`: inline-skriptet (punkt 1), max några rader.
- `src/html/60-splash.html` (ny, sist = överst): `<div id="splash">` med svart, sken, loggans canvas,
  glöd-canvas, blixt, vinjett, brus. Hålls dold med CSS utan `html.splash`.
- `src/css/96-splash.css` (ny, efter 95-design-a): det mesta av mockupens CSS. Filmbruset är en SVG-data-URI.
- `src/js/35-splash.js` (ny, efter 35-logo3d.js i namnordning):
  - **Återanvänd** från `35-logo3d.js`: `nlLib()` (laddar three + SVG + Room + loggan, en gång) och nivåerna
    `nlTier`. Bryt ut skyltbygget i `35-logo3d.js` till en egen funktion `nlMakeSign(T, SVGLoader, svg, opts)`
    som både logo3d och splash använder (splash: `MeshPhysicalMaterial` + klarlack, logo3d: som i dag).
  - Tidslinjen `pose(t)` rakt från mockupen (samma kurvor och tal).
  - Efteråt: `renderer.dispose()`, ta bort canvas och `html.splash`. Inget ligger kvar och drar batteri.
  - `window.__ffSplash()` för testerna: `{ shown, running, t }`.
- `src/js/34-name.js`: `showNameModal()` väntar tills filmen är klar (`afterSplash(fn)`). Då startar namnrutans
  3D-logga inte under filmen, och det blir aldrig två WebGL samtidigt.
- `src/js/30-help.js`: Hjälp som öppnas själv efter första namnvalet påverkas inte (det kommer efter namnrutan).
- `src/js/92-rotation.js`: inget. Loggans filer finns redan i `precache`-listan, så filmen fungerar offline
  efter första starten.

## Äldre telefoner, Reducera rörelse (beslut: platt version, inte ingen film)
- `nlTier === 'full'`: allt.
- `'lite'`: pixelratio 1, ingen glöd-canvas, inget filmbrus, enklare ljus.
- `'flat'` (ingen WebGL) eller Reducera rörelse: ingen 3D. Den platta loggan (`ff_logo.svg`) tonar fram ur mörkret,
  står kvar och tonar bort med det svarta (2 s totalt, ingen snurr).
- Filmen mäter inte själv och trappar inte ner (den visas för sällan). Den följer bara nivån som logo3d redan lärt sig.

## Tryck för att hoppa över
Ett tryck var som helst → hoppa direkt till upplösningen (det svarta tonas bort på 0,4 s). **Beslut: ja.**

## Tester
- `tests/fakefb.py`: skriv `ffmap_last_active_v1` = nu i varje context (som `help_seen`), så att ingen av de
  befintliga testerna får 3,5 s film. Opt-in: `new_page(..., splash=True)`.
- Ny `tests/test_splash.py`:
  1. Första starten (`splash=True`): `#splash` syns från första bilden (`html.splash` före `DOMContentLoaded`),
     filmen kör, är borta efter ~3,5 s, renderaren städad (`__ffSplash().running === false`).
  2. Omladdning inom 24 h → ingen film.
  3. Nyckeln satt till 25 h sedan → film.
  4. Namnrutan visas först **efter** filmen (ny användare).
  5. Tryck → hoppar till slutet.
  5b. Sidan dold → nyckeln 25 h bakåt → `visibilitychange` visible → filmen visas utan omladdning.
  6. Ingen WebGL (`nlTier = 'flat'` i localStorage) → plattversionen, ingen three.js laddas.
  7. three.js blockeras (`pg.route` → abort) → det svarta tonas bort inom ~2 s, appen går att använda.
- Rör inga filer i `docs/` (testerna blockerar som vanligt).
- Kör hela sviten efteråt (rör head, html, css, js och fakefb).

## Dokumentation
- `src/README.md`: raderna för 35-splash.js, 60-splash.html, 96-splash.css.
- `CLAUDE.md`, "Viktiga saker i koden": en punkt om startfilmen (nyckeln, 24 h, head-skriptet, fakefb-skyddet).
- `DESIGN.md`, rörelser: startfilmens tidslinje och ljus.
- `tools/HJALP_TODO.md`: nyhetsrad "Ny startfilm när appen inte använts på ett dygn".
- Capacitor-appen (`app`) får den vid nästa merge. Kolla att den inte krockar med appens egen native-splash
  (den bör vara svart/#141822 så att övergången blir sömlös).

## Ordning
1. Bryt ut `nlMakeSign` i 35-logo3d.js och kör `tests\run_all.ps1 logo` (inget ska ändras).
2. head-skript + HTML + CSS + 35-splash.js, bygg, titta i webbläsaren (skärmbilder vid 0,5 / 1,9 / 3,0 s).
3. Namnrutan väntar, fakefb-skyddet, test_splash.py, hela sviten.
4. Filip provar på iPhone (statusraden, mjukhet på hans telefon) innan push.

## Beslut (Filip 2026-10-06)
Ja på alla tre: filmen visas även vid återkomst ur bakgrunden efter > 24 h, ett tryck hoppar över, och äldre
telefoner och Reducera rörelse får den platta versionen.

## Ändrat (Filip 2026-10-06, senare)
Filmen visas inte längre vid första starten eller efter 24 h – **bara när ett namn väljs** (ny telefon, efter Logga ut,
varje gång) och från "Spela". Nyckeln `ffmap_last_active_v1`, head-skriptet och bakgrundskollen är borttagna. Varje start
har i stället en startbild (loggan på #141822, samma som iOS-startbilderna) som appen tonar in över.
