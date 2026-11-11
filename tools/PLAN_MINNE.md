# Minne – varför Mälaren kraschar och en övergripande fix (sidochatt 2026-10-07)

## Vad loggen visar
Två krascher (tools/KRASCHLOGG.md), båda på Mälaren med Kartanalys "Liknande abborre" på. Den ena kom efter
6 s utan zoom, den andra efter 20 s och tre zoombyten. Få kartbitar (max 18), canvas 23,6 MP. iOS stänger sidan
när WebContent-processen använder för mycket minne. Det är summan av allt som räknas, inte en enskild del.

## Mätt (Edge med iPhone-skärm 390×844 i 3×, efter minnesfixen 40635185)
| | Regnaren | Mälaren |
|---|---|---|
| Sjöns rutnät (djupdata) | 1,3 M rutor à 4,9 m | **3,9 M rutor** à 9,7 m |
| Översiktsbilden avkodad | 5 MB | **63 MB** |
| Kartanalys, rutnät som ligger kvar | ~75 MB | **~235 MB** |
| Kartanalys, allokerat under starten | ~70 MB | ~200 MB (450 före fixen) |
| Canvas i 3× (8 skärmstora lager) | 95 MB | 95 MB |
| Renderprocessen, topp (Kartanalys på) | 296 MB | **466 MB** |

Kartanalys på Mälaren håller i detalj: djup, utjämnat djup, lutning, grynna/håla, avstånd till land (5 × 16 MB),
de jämförda värdena inom 25 m (5 × 16 MB), fångststaplarna (6 × 4 MB) och lagren som ritas vid zoom (~40 MB).

## Tre saker som slösar oavsett sjö
1. **Canvas för avstängda lager.** Blixtar, Vind och lä och Heatmap (2 st) görs skärmstora i 3× vid varje ritning,
   även när de är av. De rensas bara. Strandlinjen och Kartanalys behåller sin storlek när de döljs. Det är 12 MB
   per lager, alltså ~50 MB i onödan på varje telefon.
   Lagren ritas dessutom från grova bilder (STEP) som förstoras, så 3× syns inte mot 2×.
2. **Liknande-cachen växer.** `anSimCache` sparar de jämförda värdena per radie (0/25/50/100 m) och släpper dem
   aldrig. Att klicka igenom radierna på Mälaren kostar upp till ~300 MB.
3. **Kartanalys släpper inget när den stängs av.** Rutnäten ligger kvar resten av körningen.

## Förslaget: en minnesbudget för sjöns rutnät + städning
**A. Rutnätsbudget (den övergripande fixen).** En funktion `gridStep()` räknar ut hur många djuprutor som ska slås
ihop till en arbetsruta, så att arbetsrutnätet högst har ~1,5 M rutor. Den används av allt som räknar på hela sjön:
Kartanalys (`anBase`, `anLoadBottom`), Vind och lä (`computeWindField`) och rutten (`routeGrid`: `rf` ≥ budgeten).
- Mälaren: 2 → 0,98 M rutor à 19,4 m. Kartanalys ~235 → ~60 MB och 4× snabbare. Vind/lä och rutten blir 4× mindre.
- **Alla andra sjöar: 1, alltså ingen ändring** (största är Regnaren med 1,29 M). Testerna påverkas inte.
- En framtida stor sjö (hela Mälaren, Vänern) klarar sig automatiskt.
- Priset: på Mälaren försvinner små saker under ~40 m i Kartanalys och branter ser lite flackare ut.
  Kartan, djupkurvorna, lodet och djupsiffrorna påverkas inte.

**B. Canvas.** Avstängda lager får storleken 0×0 (minnet släpps). Påslagna överlager ritas i högst 2×
(`Math.min(2, devicePixelRatio)`). Sparar ~50 MB alltid och ~25 MB till med Kartanalys. Inget syns.

**C. Cachen.** `anSimCache` behåller högst 25 m (används av fångsterna och Skala) och den senaste radien. När
Kartanalys stängs av släpps cachen, fångststaplarna och ritlagren. Själva grunden (`AN`) behålls, så att den startar snabbt igen.

**D. (Kart-chatten, valfritt)** Mälarens översiktsbild 3072×5120 = 63 MB. En översikt i halv storlek (16 MB),
där detaljbitarna tar över vid inzoomning, sparar ~47 MB. Det är kartformatet, så stäm av med kart-chatten.

**Väntat på Mälaren med Kartanalys:** de stora buffertarna går från ~390 MB (235 + 95 + 63) till ~140 MB (60 + 20 + 63).

## Gjort 2026-10-07 (Filip: "allt") – A, B, C byggda; D väntar på kart-chatten
- **B** `fitLayer(c, on, soft)` (50-wind-lee.js): avstängt lager = 1 × 1 (inte 0 × 0 – `getImageData` på 0 × 0 kastar),
  mjuka lager (Kartanalys, lä, strandlinje, fog) högst 2×. Blixtar har canvas bara när det finns blixtar att rita.
- **C** `anSimCache` håller 25 m + senaste radien. När Kartanalys stängs av släpps cachen, `cBins` och `anPyrBox`.
- **A** `workGrid()`/`gridStep()` (38-speed-depth.js, `GRID_MAX` 1,5 M) används av `anBase`, `anLoadBottom`, `computeWindField`/`gridAt`
  och `routeGrid` (`rf` ≥ `gridStep()`). Lodet/djupet (`depthAtImgPx`) och Strandlinje använder fortfarande djupgriden.
- Mätt (Edge 3×, Mälaren, Liknande abborre, zoom in/ut 3 ggr): renderprocessen topp 466 → 287 MB, efter GC 348 → 196 MB,
  canvas 20,9 → 5,7 MP. Mälaren ligger nu som Regnaren (305 / 194 MB).
- Kartanalys på Mälaren (samma vy): Grynnor & hålor 95 / 156 → 56 / 130 (små försvinner, några större flacka hålor dyker
  upp – "runt om" blev 39 m i stället för 29 m); Branta kanter 8 → 6 % av sjön, nästan samma bild.
- Tester: `test_memory.py` (3×-skärm: lager 1 × 1 när de är av, 2× på; högst 2 radier; släpps när Kartanalys stängs av;
  Regnaren på sin egen griden), `test_lakes.py` (Mälaren på 2 × 2-griden). `__ffAnalysis()` ger `grid` och `sim`.
- **D** (kart-chatten): mindre översiktsbild för Mälaren (63 MB) – inte gjort.

## Gjort 2026-11-10 – snabbare panorering, mindre skräp (kodgenomgångens punkter 25–30)
- **Inga nya canvasar medan kartan dras:** Strandlinje och Heatmap återanvänder sina arbetsytor (`hmScratch`, 68-heatmap.js) och
  strandlinjens buffertar (`hmShoreFl`/`hmShoreIm`). Förr en ny canvas per bild = skräpsamling 38 ms per drag, nu 4 ms.
- **Ett finger som drar = lagren flyttas, räknas inte om:** `scheduleRender(true)` (bara enfingersdraget) → `render(pan)` flyttar
  `#waypoints` och `#boats` med en transform (`layerBase`/`layerShift`, 12-map.js) i stället för `renderWaypoints`/`renderBoats`.
  Zoom, släppt finger och alla andra som ber om en ritning = full ritning. Spårens linjer: `setPath` (46-gps-track.js) räknar om
  `d` bara vid ny zoom eller nya punkter, annars `translate`. Nytt lager som ska följa med i draget: gör likadant.
- Mätt (Edge, 4× långsammare processor, 150 platser, spår med 4 000 punkter): 42 → 64 bilder/s, ritningen 7,6 → 3,0 ms per bild.
  Strandlinjen är kvar som största biten (ca 2 ms).
- **Platsens ruta bygger inte Kartanalys-griden** (28 MB + paus): lutningen räknas i ett litet fönster runt platsen
  (`anSlopeAt`, 56-analysis.js – samma oskärpa, samma siffra), och `anCompute` bygger inte griden när Kartanalys är av.
- **Liknande:** tröskeln (de 4 % mest lika) med typad sortering i stället för en vanlig lista med jämförelsefunktion.
- **Under ytan:** Avstånd bygger om botten när reglaget vilat 0,2 s (inte för varje steg); ✕ lämnar tillbaka allt från grafikkortet.
- **Båtpositioner:** bara sjöns egna läses (`posQ` = `where('lake', '==', sjön)`, 26-sync.js) – en båt som rör sig på en annan sjö
  kostar inga läsningar här. Positioner utan `lake` (från före flera sjöar) syns inte längre, inte heller i Admin.
- Tester: test_memory (drag: lagren flyttas, inga nya canvasar), test_track_history (spåret flyttas/räknas om), test_extras
  (lutningen = Kartanalys, griden byggs inte), test_ar (ett bygge per drag), test_lakes (bara sjöns positioner läses).

## 3D-karta (2026-11-11, `73-map3d.js`, `tools/NOTES_3D.md`)
- Bara medan vyn är öppen: två rutnät (hela kartan + ett fint runt punkten man tittar på, högst 400 × 400 punkter vardera,
  ca 10 MB var i minnet och lika mycket på grafikkortet), den skarpa bitens canvas (2048 × 2048 = 16 MB + grafikkortet, bara
  när man är så nära att en zoomnivå används), markens höjdnät (Regnaren 1,3 MB, Mälaren 3,9 MB) och kartbilden som textur
  (samma fil som kartans, ur webbläsarens cache: Mälaren 16 MB på grafikkortet).
- ✕ lämnar tillbaka allt: geometri, texturer, canvasen ner till 1 px, ritytan ner till 1 px (three.js `dispose()` behåller
  annars ritytan, ca 40 MB på en telefon), höjdnätet.
- Ritas bara när något ändrats (ingen loop). Den skarpa biten skickas till grafikkortet högst ~8 gånger per sekund medan bitarna kommer.
- Filip har kört det på sin iPhone på Regnaren och Mälaren (2026-11-11), ingen krasch rapporterad. Inte mätt i siffror.
