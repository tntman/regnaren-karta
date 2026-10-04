# Heatmap (fångster)

Kod: `src/js/66-catches.js` (datan: format, källa), `src/js/68-heatmap.js` (ritning,
bottenrutan, fångstrutan, tryck på kartan), `src/css/72-heatmap.css`, HTML i `src/html/30-map-ui.html`
(`#hmPill`, `#hmPanel`, `#hmCard`), `10-map.html` (`#hmSat`, `#hmLayer`), Fångstdata i
`20-menu-settings.html`. Test: `tests/test_heatmap.py`, `tests/test_catchapi.py`.

## Så fungerar den
- **Kartlägen** (håll kartlägesknappen): **Heatmap** sist i listan (`.hmOpt`, `data-heat`) – inget kartläge
  utan en bottenruta som Kartanalys (`#hmPanel`). Kartan tonas ner och gråtonas som i Kartanalys
  (samma "Mörkare", `anSet.dim`) – kartläget under behålls.
- Fyra stilar: **Värme** (radie i meter + styrka), **Per art** (värme i artens färg, av/på per art),
  **Rutor** (sexkanter 30/60/120 m fästa i kartan, antal i rutan), **Prickar** (prick per fångst, större
  fisk = större prick, namn om man vill). Filter: art, tävling ("regnaren1" → "Regnaren 1 · 25–26 sep").
- **Tryck på kartan** (`hmTapAt`, anropas från `scheduleProbeTap`): närmaste fångst (+ de andra inom 50 m)
  eller rutans fångster → `#hmCard`: art + cm, vem, när (26/9 13:00), djup där, plats i tävlingen
  ("2 av 37" bland samma art), ‹ › mellan fångsterna där, **Åk hit** (lodet, heatmapen ligger kvar) och
  **Liknande** (Kartanalys Liknande med fångsten som plats: `anExtraRef` i `anSpots()`; heatmapen stängs).
- **Inte samtidigt som Kartanalys**: heatmap på → Kartanalys-läget av; ett Kartanalys-läge valt → heatmap av.
- Översta raden (`.pnHead`, som Kartanalys): resultatet + teckenförklaringen (`#hmLegend`), **ⓘ** (`pnInfo`: noterna i `#hmResult .note` i en ruta), **↺ Återställ** (`HM_DEFAULTS`, grå när allt är som från start) och **⏻ Stäng av heatmap** (`#hmOff`). Art/Tävling: radens namn först (`.rowLbl`), en rad var som skrollar i sidled.
- **När** (`#hmTime`, `hmRenderTime`, sist i bottenrutan): stapel per timme på dygnet (bara timmar med fångster; färg = glöd), "Bäst kl 11–14 · 95 %" (bästa tre timmarna i rad). Tryck en timme / dra över flera = tidsfönster `hmSet.h0..h1` som filtrerar kartan via `hmVisible()` (grafen själv ignorerar fönstret: `hmVisible(true)`); samma timme igen eller ↺ = alla. Resultatraden säger "kl 11–14". Timmar i enhetens lokala tid.
- Sjöns kant: tunn vit linje 50 % som i Kartanalys (`hmShoreLayer`: `anField` med egen cache, `edgeW`).
- Rutan stängd: skylten **Heatmap** under väderchipet (`#hmPill`, klass `.mapPill` som Kartanalys `#anPill`) öppnar den igen.
- **Filter → Lager → Heatmap** (`#toggleHeatmap`) visar/döljer bara, som Kartanalys: `hmOn` = påslagen (kartlägeslistan/rutan),
  `hmShow` = syns på kartan (`ffmap_show_heatmap_v1`, på som standard). Dold: inget ritas, ingen skylt, tryck på kartan gör inget,
  rutan säger "Dold – slå på Heatmap i Filter". Slås den på för hand (kartlägeslistan) blir den synlig igen.
- Färgskalan **"glöd"** (`hmRamp`): mörklila → magenta → orange → bärnsten → varmvitt – aldrig djupskalans
  blå/cyan/grön. Samma i teckenförklaringen, `.hmDot` och `.hmThumb`. Siffran i Rutor blir vit på mörka rutor.
- **Av efter omstart** (som Kartanalys), kvar vid vridning (`rotState.hm`: på, rutan, öppen fångst).
  Inställningarna sparas per sjö (`lakeKey('ffmap_heatmap_v1', …)`).
- Slås den på för hand och mindre än hälften av fångsterna syns ovanför rutan: kartan flyttas så alla syns.

## Datan – byggd för att bytas
- Allt blir samma lilla post: `{ id, t, comp, who, sp: 'abborre'|'gadda'|'gos', cm, lat, lon, px, py }`
  (`normCatch` tål olika kolumn-/fältnamn; komma-decimaler; "Gädda"/"Gadda"/"gadda").
  `id` = tid|namn|art|cm (dubbletter känns igen).
- **Källa: Fiskfiskarnas API** (Jonathan, `https://fiskfiskarna.se/api/`, ingen inloggning för läsning; CORS tillåter
  `https://tntman.github.io` och `capacitor://localhost` sedan 2026-10-03; `https://karta.fiskfiskarna.se` – nya
  adressen 2026-10-04 – väntar på Jonathan, tills dess blockeras hämtningen där och Fångstdata visar "ingen anslutning"):
  - **Historik** = `dashboard.php` → `heatmap` (alla fångster med GPS, ~900 st; svaret ~530 kB med all statistik)
    + `competitions`. Bara fångster i **denna** sjö (`catchLakeOf`: inom kartan och sjönamnet säger inte en annan
    sjö – Östra Vitten ligger inom Regnarens kartbild). Tävlingarna på sjön (`catchSameWater`, prefix åt båda
    håll: "Sibbo"/"Sibbofjärden") sparas med `id, name, date, status`.
  - **Kopian** i localStorage (`lakeKey('ffmap_catches_v1')`, `{v:2, at, total, comps, rows}`) – fungerar offline
    och mellan tävlingarna. Gammal Firestore-kopia (utan `v:2`) räknas som ingen kopia.
  - **När historiken hämtas** (vid start, när appen blir synlig, när heatmapen slås på – `catchHistDue()`):
    1. ingen kopia; 2. en tävling pågår och kopian > 1 h; 3. en planerad tävling med datum ≤ idag och kopian > 1 h;
    4. kopian > 1 dygn. Annars används kopian. Mellan tävlingarna = högst en hämtning per dygn per telefon.
  - **Live** = `tavling.php?action=bootstrap&competitionId=…` → `catches`, bara när kopian säger att en tävling
    pågår på sjön och sidan syns. Direkt vid start/synlig (om > 60 s sedan), sedan var 5:e min; var 30:e s när
    heatmapen eller Kartanalys "Från fångsterna" är på. Annullerade: rad med `displayValue:"VOID"` + `voidRef`
    (= den annullerade fångstens `timestamp`) – båda tas bort. Slås ihop med historiken på `id`.
    ~100 fångster ≈ 6,6 kB gzip, ≈ 0,5 MB per tävlingsdag och telefon.
- **Inställningar → Fångstdata** (`data-sec="catch"`, `catchRenderSettings`): senast hämtad, antal i sjön/totalt,
  kopians storlek, nästa hämtning + varför, tävlingarna på sjön, live (takt, senast), dagens anrop och data
  (`ffmap_catchnet_v1`), senaste fel, **Hämta nu** (`#ctFetch`).
- Testerna låtsas vara API:t (`fakefb.FakeApi`, `ctx.api`; riktiga fiskfiskarna.se blockeras). Hämtningen:
  `tests/test_catchapi.py`.
- Firestore `catches/<lake>` används inte längre (CSV-inläsningen borttagen 2026-10-02, API:t 2026-10-03) –
  regeln kan tas bort i konsolen.

## Genväg överst (2026-10-02)
`#hmBtn` (färgad karta) ligger vänster om kartknappen: tryck = Heatmap på (panelen öppnas) / av. Tänd (gul ring) = på och visad i Filter. Kartan flyttas/zoomas aldrig när heatmapen slås på (förr: `hmFitIfNone`, borttagen). Filter-knappen visar bara ikon + pil.

## Profiler och fångstmeddelanden (2026-10-03)
Samma `dashboard.php`-svar ger profilerna (anglers, anglerStats, dashboard, results, records) → `profPack` (`js/67-profiles.js`)
sparar en liten post per namn i kopian (`prof`, kopian är nu `v: 3` – äldre hämtas om). Heatmapen kan visa en persons
fångster (`hmSet.who`, "Bara Filip ✕"). Live-fångster får `img` (Cloudinary, 600 px) och `no` (inte godkänd). Snabbmeddelandet
med din senaste fisk + `msgSp`/`msgImg` på positionen: `tools/PLAN_PROFILER.md`.
