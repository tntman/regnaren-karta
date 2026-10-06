# Plan: nytt kartformat (bas + delat kurvlager) och Mälaren

Sidochatt 2026-10-06 → **kart-chatten** (worktree `.claude/worktrees/kartformat`, gren `worktree-kartformat`).

**Status 2026-10-06: byggt.** Alla fem sjöar i nya formatet (Regnaren 39 MB, Vågsfjärden 29,5, Sibbo 28,3,
Sjösjön 5,3, Östra Vitten 3,5 – förr 379 MB ihop), bitarna har 8 px kant från grannarna (skarvarna, KARTOR.md).
Mälaren byggd med `tools/genesis_big.py` (block). Inte inslaget i main / pushat ännu (Filip: ingen använder appen
på riktigt just nu – gör klart i lugn och ro).

**Beslutat (Filip):** nya formatet enligt avsnitt 2 (bas WebP 35 + delat kurvlager, 32 färger, zoom 18 för alla
kartlägen) för alla sjöar; Mälaren läggs till med området i `tools/malaren_polygon.json` (v2, avsnitt 5).
**Kartläget s5 "Flygfoto + linjer" tas bort** i alla sjöar (Filip 2026-10-06, avsnitt 2b) – 7 kartlägen kvar.
Mälarens djupkarta räknas i block (avsnitt 5). c1 Bottenhårdhet får ett eget vitt kurvlager (avsnitt 2). Inget öppet.
Bilder: `tools/fore.jpg`, `tools/efter.jpg`, `tools/fore_efter_detalj.png` (före/efter, Filip: "ser bra ut"),
`tools/kartbitar_test.html` (alla varianter + WebP-kvaliteter), `tools/malaren_polygon.jpg` (Mälarens område).

## 1. Varför

I dag har varje kartbit färger **och** Genesis kurvor inbakade, i JPG. Samma kurvor sparas alltså 8 gånger
(en gång per kartläge), och zoom 18 är så stor att bara s1 och g1 får den (`top_styles`).

Två saker vi mätt (Regnaren, bit 11_3):
- **Djupfärgerna är desamma på zoom 18 som på 17** (djupet räknas på 17, färgerna på 18 är förstorade). Zoom 18
  tillför bara Genesis tunnare kurvor och fler djupsiffror (+ skarpare flygfoto på land).
- **Kurvorna är likadana i alla kartlägen på samma zoom** (svarta – utom c1 Bottenhårdhet som har vita, tunnare linjer; s5 hade det också men tas bort).

## 2. Nya formatet

Per zoomnivå 15–17:
- **Bas** per kartläge = bara färger/flygfoto, inga kurvor. **WebP kvalitet 35** (Filip godkände 35 – ingen synlig
  skillnad, basen är mjuka färger). ~11 kB per 512-bit.
- **Kurvlager** = ett per zoomnivå, **delas av alla kartlägen**. Genesis t_ för just den zoomen, genomskinlig,
  **förlustfri WebP med 32 färger** (`quantize(32, FASTOCTREE)`). ~45 kB per bit på zoom 17.
  **Inte 8 färger:** då blir den mjuka vita ringen runt djupsiffrorna taggig med mörk kant (testat, syns).
  Inte förlustig WebP: suddiga linjer och ändå större.

Zoom 18:
- **Ingen bas** – zoom 17:s bas förstoras 2×. Bara **kurvlager 18** (samma format). Då får **alla 8 kartlägen**
  zoom 18 (i dag 2). `top_styles` behövs inte längre.
- Nackdel: flygfotot på land blir zoom 17 förstorat på zoom 18 (syns mest i g1, bara på land).

Zoom 14 (översiktsbilden `map_v<V>_<stil>.jpg`): som i dag (en bild per kartläge med kurvor inbakade).

**Varje zoomnivå har fortfarande sina egna Genesis-kurvor** – inget delas mellan nivåer, bara mellan kartlägen.

### Vita linjer (c1 Bottenhårdhet)
c1 har ingen vattenfärg där hårdhet inte är mätt (flygfoto) och därför vita, tunnare, genomskinliga linjer men
siffrorna som de är (`LINE_THIN`, `LINE_OPACITY`, `labels` i genesis_render.py; `lines` = (255,255,255) i STY).
c1 ligger i snabbknappen och i offline-nedladdningen.
**Beslut (Filip 2026-10-06): väg 1.** Övervägt:
1. Ett eget vitt kurvlager för c1 (`lines_w/`, ~+20 % kurvdata, Regnaren ~+1,5 MB). **Valt.** Samma format som
   det svarta (förlustfri WebP, 32 färger), samma `have`. Offline: c1 tar `lines_w/` i stället för `lines/`.
2. Samma kurvlager, omfärgat i telefonen (CSS `filter` räcker inte för "linjer vita men siffror som de är").
3. c1 får svarta linjer som de andra (inget extra lager, men svart syns sämre på mörkt flygfoto – visa Filip först).

### 2b. s5 "Flygfoto + linjer" tas bort (Filips beslut 2026-10-06)
Bara kartläget försvinner – flygfotot på land under sjön finns kvar i alla kartlägen.
- `tools/genesis_render.py`: ta bort raden `('s5', 'Flygfoto + linjer', …)` i `STY`; kommentaren vid `LINE_THIN`
  (rad ~33) och "light lines (Flygfoto + linjer)" (rad ~274) → gäller nu c1.
- Byggs om för alla sjöar ihop med nya formatet (ny `version` → s5-filerna försvinner ur `docs/`, rit-steget tömmer mappen).
- Appen: `MAP_STYLES` kommer från lake.json – s5 försvinner ur kartlägeslistan av sig själv. Den som har s5 sparat
  får Djupfärger (`js/16-map-settings.js` rad ~48 godtar bara kartlägen som finns). Inte i `QUICK_STYLES`.
- `src/html/40-help.html` rad ~91: ta bort "**Flygfoto + linjer**" ur listan (Hjälp-omgång: skriv i `tools/HJALP_TODO.md`).
- `tests/test_mapstyle.py` rad ~22–29 använder s5 som exempel (ingen färgskala; kartläge som inte kan laddas) –
  byt till c1 (har också `noBar`? kolla) eller g1.
- `tools/KARTOR.md`: s5-raden (avsnittet om kartlägen, ~rad 182) → "borttagen 2026-10-06", som Natt (s4).
- Sparar ~3 MB per sjö (Regnaren ~37 → ~34 MB); Mälaren ~−25 MB.

## 3. Ändringar

### `tools/genesis_render.py`
- Skriv `tiles_v<V>/z<z>/<stil>/<c>_<r>.webp` = bas (utan `ta`-blandningen) för z 15–17, kvalitet 35.
- Skriv `tiles_v<V>/z<z>/lines/<c>_<r>.webp` (+ `lines_w/` för c1) för z 15–18: RGBA `t[..., :3]` + alfa `ta`,
  32 färger, förlustfri. Samma `have` som idag.
- Zoom 18: bara kurvlagret (ingen bas, ingen flygfoto-/färgberäkning – går fortare).
- Höj `version` (ny V = nya filnamn, telefonerna hämtar nytt).
- `lake.json` → `detail`: `file` för bas + `lines` för kurvlagret, `base_max` = 17 (högsta nivå med bas).
- Testat hur man tar fram delarna: kopia av genesis_render.py med `NOLINES` (sätter `ta = 0`) och `LINESONLY`
  (sparar RGBA och hoppar över kartlägena) – se avsnitt 6.

### Appen
- `js/12-map.js` `renderDetail()`: två `<img>` per plats – bas (nivå = min(L.z, base_max), förstorad som idag
  när zoomen är högre) och kurvlager (nivå L.z) ovanpå. `detailLevel()` tar inte längre hänsyn till
  `L.styles` för zoom 18. Behåll "gamla bitar ligger kvar tills nya laddat" för båda.
- Kurvlagret måste ligga **under** allt annat som ligger ovanpå kartan idag (samma z-ordning som bitarna nu).
- `js/20-map-look.js`: filtret (`detailLayer.style.filter`) ska gälla både bas och kurvor som idag.
- `js/18-offline.js` `offlineFiles()`: QUICK_STYLES-baser + kurvlagren (en gång, inte per kartläge).
  Uppskattningen `n * 60000` → ~25 kB per fil.
- `sw.js`: `.webp` cachas som bilder (kolla filtret på filändelse), höj `CACHE`.
- Ny kartversion → "Ny kartversion finns – ladda ner igen" (offline) fungerar redan.
- Capacitor-appen (`ffmap-app`, gren `app`) får det via merge av main.

### Tester
- Testerna som räknar/laddar `tiles_v*/…jpg` (sök i `tests/` efter `tiles_v`, `.jpg`, `detailLayer`, `top_styles`,
  `offline`) – uppdatera till bas + lines. Nytt test: på zoom 18 syns kurvlager 18 ovanpå förstorad z17-bas,
  i ett kartläge som inte var s1/g1.

### Ordning
1. genesis_render.py + Regnaren, titta på bilderna (jämför med `tools/fore_efter_detalj.png`).
2. Appen + tester. 3. Bygg om de andra sjöarna (Genesis-rutorna är cachade i `raw/`, bara rit-steget).
4. Mälaren (avsnitt 5).

## 4. Storlek (docs/lakes, uppskattat utom Regnaren)

| Sjö | Före | Efter |
|---|---|---|
| Regnaren | 143 MB | ~37 MB (räknat på alla bitar) |
| Vågsfjärden | 102 MB | ~27 MB |
| Sibbo | 100 MB | ~26 MB |
| Sjösjön | 19 MB | ~5 MB |
| Östra Vitten | 15 MB | ~4 MB |
| **Nuvarande sjöar** | **379 MB** | **~99 MB** |
| Mälaren (ny, polygon v2) | ~1,3 GB | ~300–330 MB |
| **Totalt** | **~1,7 GB** | **~400–430 MB** (GitHub Pages ~1 GB) |

Regnaren efter, uppdelat: baser z15–17 alla 8 kartlägen ~22 MB, kurvlager z15–18 ~7,6 MB (z18 4,7),
översiktsbilder 3,6 MB, djup m.m. ~4 MB. ~2 200 filer (idag ~2 900). Offline-nedladdningen blir ~4× mindre.

Kartlägen som kan tas bort om plats behövs (kostar bara ~3 MB/sjö var nu): s6 Blå relief, sedan s2 Förenklad.
Ingen statistik finns på vilka som används – inget tas bort utan Filips beslut.

## 5. Mälaren

- Genesis: **mwID 1078786** (https://www.genesismaps.com/SocialMap/Index?mwID=1078786). Genesis har z12–18.
- **Området = polygonen i `tools/malaren_polygon.json` (`polygon_latlon`)**, Filips beslut 2026-10-06:
  convex hull runt alla 315 fångster med GPS i Mälaren (Fiskfiskarnas API `dashboard.php` → `heatmap`,
  `lake == "Mälaren"`; 311 Mälaren Open 2026, 2 fiskfiskOpen, 2 Tjockholmen), förstorad 1,2× från hörnens
  mittpunkt (= `polygon_v1_latlon`), och sedan (v2, Filips ritning) östra sidan rak: norra kanten österut till
  östligaste longituden, rakt ner till sydöstra hörnet. **175 km², ~66 km² vatten med Genesis-data** (v1: 125 / 49).
  Bbox oförändrad 59,302–59,501 N, 17,465–17,703 O (→ samma Genesis-hämtning, översiktsbild och djupfil).
  Bitar (512 px) inom polygonen nära vatten: z15 106, z16 327, z17 1 078, z18 3 701 (v1: 84/252/829/2 799).
  Storlek i nya formatet ~300–330 MB, ~21 000 filer (v1 ~260 MB) → totalt med de andra sjöarna ~420 MB.
  Bild: `tools/malaren_polygon.jpg` (gul = polygonen, vit streckad = v1).
- **Bara bitar inom polygonen**: hämta Genesis-rutor för bbox:en men låt `have` = 0 för bitar som inte rör
  polygonen (utöver dagens "nära vatten"). Ny nyckel i source.json, t.ex. `"clip": "tools/malaren_polygon.json"`.
  Allt utanför polygonen: inga bitar (översiktsbilden visar det förstorat, eller tona ned det som Kartanalys).
- Hämtning: zoom 14–18, lager a b t v c, ~28 000 rutor per lager (z18 ~21 000) ≈ 140 000 anrop (hälften
  403 = land), ~0,6 GB i `raw/malaren/`, ~1–1,5 h med shards (KARTOR.md steg 3). Zoom 14 a/b/t finns redan
  (hämtat för bilderna, 59,29–59,51 N, 17,44–17,72 O).
- **Risker att kolla först:**
  - Djupkartan räknas på zoom 17 för hela bbox:en: ~22 000 × 36 000 px (Regnaren 13 000 × 6 400) – genesis_depth/
    render håller allt i minnet som float32: grovt ~30 GB RAM (Regnaren ~3 GB). Filips dator har 48 GB.
    **Beslut (Filip 2026-10-06): räkna i block** – säkrare, och klarar fler stora sjöar framöver. Så här:
    block om t.ex. 4 096 × 4 096 px på zoom 17 (= hela 512-bitar på alla nivåer, så skarvarna hamnar mellan bitar),
    bara block som rör polygonen. Varje block läses med en **marginal** (~64 px) som räknas men inte sparas – relief/AO
    (~25 m runt varje punkt), utjämningen och `binary_dilation` (near/nearw) behöver grannarna, annars syns skarvar.
    Djupkalibreringen (`depth_labels.json`) gäller hela sjön, inte per block. Djupfilen till telefonen
    (`depth_v*.txt`) bara inom polygonen (resten = 255 land/okänt). Kontroll: rendera Regnaren både som förut och
    i block – bitarna ska bli identiska (eller nästan, jämför pixelvis). Påverkar bara bygget, inte avsnitt 4.
  - Översiktsbilden zoom 14 ≈ 2 800 × 4 500 px = 12,6 MP – under iPhone Safaris gräns (16,7 MP), OK.
  - Kartanalys räknar hela sjön – ~66 km² vatten med data mot Regnarens ~5,4 (~12×). Kan börja hacka (Web Worker-idén i CLAUDE.md).
  - Djupfilen `depth_v*.txt` växer med bbox:en; `grid_div` kanske högre.
  - OSM-strand (`osm_water.py`): Mälaren är en jättepolygon – klipp till bbox:en.
  - Fångstdata: `catchLakeOf` (inom kartan + sjönamn) och `catchSameWater` ("Mälaren") borde fungera direkt.
    Tävlingen "Mälaren 1" (2025) har inga fångster i API:t.

## 6. Hur testbilderna gjordes (för att kunna göra om)

Scratch-kopia av `genesis_render.py` med ROOT satt till repot och efter `ta = t[..., 3:4] / 255 * near`:
```python
if os.environ.get('LINESONLY'):
    Image.fromarray(np.dstack([t[..., :3], ta * 255]).clip(0, 255).astype(np.uint8), 'RGBA').save(os.path.join(PREV, 'lines_z%d.png' % z)); continue
if os.environ.get('NOLINES'): ta = ta * 0
```
Körs med `PYTHONPATH=tools`, `NOLINES=1 … regnaren preview 14,15,16,17 <mapp>` och `LINESONLY=1 … preview 15,16,17,18 <mapp>`.
Mätt (bit 11_3, s1): z17 idag JPG 83 kB → bas 11 + kurvor 45 = 56 kB; z18 idag 253 kB (4 bitar) → kurvor 110 kB.
Bas WebP 80/65/50/35 = 21/16/14/11 kB.

## Framtid: repots storlek (2026-10-06)

Varje kartversion ligger kvar i git-historiken (de gamla kartorna är borttagna ur `docs/`, men inte ur historiken).
Repot var ~1 GB lokalt efter kartformatet + Mälaren (GitHub rekommenderar < 1 GB, varnar vid 5 GB; Pages-gränsen
1 GB gäller bara den publicerade sidan – ~380 MB nu). Skriv inte om historiken i vardagen (inget force-push, beslut).
Om repot närmar sig några GB:
1. **Kartorna i ett eget repo/annan lagring** (t.ex. eget GitHub Pages-repo `ffmap-kartor` eller molnlagring), appens
   repo förblir litet; `lakeUrl()` (`js/10-core.js`) pekar dit. Bäst på sikt, särskilt om fler stora sjöar kommer.
2. **Engångsrensning av historiken** (git filter-repo på `docs/lakes/`), planerad med Filip, när inga andra kopior
   används (app-grenen, GitHub Desktop, andra chattars worktrees) – kräver force-push en gång.
Kolla storleken: `git count-objects -vH` (size-pack).
