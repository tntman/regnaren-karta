# Kartor från C-MAP Genesis Social Map – så gör vi

Allt vi lärt oss om att bygga en sjö i FF Map. Läs detta innan du gör en ny
sjö eller ändrar hur kartorna ritas, och **uppdatera filen** när något ändras
eller när vi lär oss något nytt (vi är inte klara – se "Öppna frågor").

---

## 1. Receptet – en ny sjö steg för steg

Alla kommandon körs från repots rot (`E:\github\regnaren-karta`), med `py -3`.

1. **Hitta sjön** på https://www.genesismaps.com/SocialMap/ och bestäm utsnittet
   (lat/lon-gränser). Ta med lite land runt sjön, som på Genesis.
   Från en länk `…/SocialMap/Index?mwID=<id>`: `POST https://www.genesismaps.com/api/SocialMap/GetTileBoundaries/<id>`
   (tom kropp; GET ger fel) svarar med Genesis ruta (zoom 10) där sjön ligger. Hämta b_-rutorna
   på zoom 12 i den rutan, sätt ihop dem och leta upp sjöns form → lat/lon. Filips skärmdump av
   utsnittet är ungefär zoom 14 – räkna ut gränserna från var datat börjar/slutar i bilden.
   OSM-id: Overpass `is_in(lat,lon)` + `natural=water` (skicka User-Agent, annars 406;
   namnsökning med å/ä/ö via curl missade Sjösjön – sök på position i stället).
2. **Ta reda på vilka zoomnivåer Genesis har** – se avsnitt 2. Gör det INNAN
   du laddar ner något.
3. **Ladda ner rutor** för varje zoomnivå 14 … högsta:
   `py -3 tools/genesis_tiles.py <id> <zoom> <lat_min> <lat_max> <lon_min> <lon_max> [lager]`
   Lager: `b` djupfärger, `t` kurvor + siffror, `v` vegetation, `c` bottenhårdhet,
   `a` flygfoto (Bing). Standard = alla. Hamnar i `raw/<id>/z<zoom>/` (inte i git).
   Rutorna cachas, så ett avbrutet/upprepat anrop hämtar inget två gånger; saknade
   rutor (403) sparas som `<ruta>.none` och frågas inte igen.
   **Snabbare:** en process per lager och zoom parallellt, och för stora lager (zoom 18
   ≈ 6 000 rutor/lager) dessutom `FF_SHARD=k/n` – processen tar bara var n:e rad från k
   och syr inte ihop. Kör flera shards samtidigt, sedan en gång utan FF_SHARD för att
   sy ihop (allt är cachat då, går fort). Regnaren z17+z18: 20 processer.
4. **Skriv `lakes/<id>/raw/source.json`** (se Vågsfjärden/Regnaren):
   `id`, `name`, `zoom` (= djupdatans zoom, den högsta nivån där djupet räknas –
   17 om den finns), `levels` (t.ex. `[14,15,16,17,18]`), `bbox` (eller `origin` +
   `size` för att behålla ett gammalt utsnitt), `center` (valfri), `version`
   (höj vid ny bildomgång), `grid_div`, `depth_step`, `osm`. (`top_styles` används inte
   längre sedan kartformatet 2026-10-06 – alla kartlägen får alla nivåer.)
5. **Kalibrera djupet:**
   `py -3 tools/genesis_depth.py <id> sheet` → `raw/<id>/z<zoom>/labels_sheet.png`
   Läs av Genesis djupsiffror på arket (liten siffra efter talet = tiondelar,
   t.ex. "4₃" = 4,3 m, "12₅" = 12,5 m) och skriv in dem som `depth_m` i
   `lakes/<id>/raw/depth_labels.json` (`null` där det inte är en siffra).
   Sedan `py -3 tools/genesis_depth.py <id>` → `depth_m.npy` + `water.npy`.
   Kontrollera utskriften "vs labels: median error … 90 % within …" (Vågsfjärden
   0,24 m, Regnaren 0,14 m). Gör gärna en extra kontroll med etiketter som INTE
   var med i kalibreringen (se avsnitt 5).
6. **Sjögränsen från OpenStreetMap:** hitta sjöns OSM-id (relation eller way,
   `natural=water` – sök via Overpass i bbox:en), lägg i source.json som
   `"osm": {"type": "relation", "id": …}` och kör `py -3 tools/osm_water.py <id>`.
   (Overpass är ofta upptagen – verktyget försöker igen.)
7. **Rita:** `py -3 tools/genesis_render.py <id>` → kartbilder, nivåbitar,
   förhandsbilder, djupnät rakt in i `docs/lakes/<id>/`, och `lakes/<id>/lake.json`.
   (`… <id> grid` = bara djupnät + lake.json, snabbt.)
8. **Namn från OpenStreetMap:** `py -3 tools/osm_names.py <id>` → `lakes/<id>/names.json` (öar, uddar, vikar, gårdar,
   byar med namn inom kartbildens yta; läser `lake.json` från steg 7, så kör den efter rit-steget). Visas som
   Filter → Lager → Namn (se slutet av filen). Kolla utskriften: en sjö kan ha 0 namn i vattnet (Sibbof. har det).
9. **Bygg:** `py -3 tools/build.py` (sjön dyker upp i menyn av sig själv; names.json bäddas in).
10. **Testa:** `powershell -ExecutionPolicy Bypass -File tests\run_all.ps1`
   (parallellt, ~3 min). Titta också på bilderna själv – jämför med Genesis
   på samma ställe och samma zoom.

---

## 2. Vilka zoomnivåer har Genesis?

- Rutor: `https://socialmap.genesismaps.com/img/{b|t|v|c}_<quadkey>.png`
  (Bing quadkey, 256 px, Web Mercator). **403 = rutan finns inte.**
- **Testa flera punkter UTE PÅ VATTNET** – t.ex. vid Genesis djupsiffror – på
  varje zoom (16, 17, 18, 19 …). En punkt som råkar ligga på land eller en ö
  ger 403 på alla höga zoomnivåer och ser ut som "zoom saknas".
  *Misstag vi gjort:* vi testade Regnarens mittpunkt (land), fick 403 på zoom 17
  och trodde i onödan att Regnaren bara fanns till zoom 16. Den har 17 och 18.
- Hittills: Regnaren, Vågsfjärden och Sjösjön har alla zoom 12–18 (19 = 403).

---

## 3. Zoomnivåer i appen

**Två olika "zoom" – blanda inte ihop dem (beslutat för ALLA sjöar):**
- **Djupkartan räknas på zoom 17** (`zoom` i source.json = 17): djupvärden per pixel
  (~0,6 m/px) → färger, relief, lodet, djupet under båten, rutter. En gång per sjö.
  Zoom 18 ger ingen mer djupinformation (Genesis färgband är utjämnade), bara större fil.
- **Lagren i appen är zoom 14–18** (`levels`): varje lager visar Genesis egna linjer och
  siffror för just den zoomen; färgerna/reliefen i alla lager kommer från samma
  zoom 17-djupkarta (förminskad/förstorad).

- **Kartbilden** (`map_v<V>_<stil>.jpg`) = zoom 14, lägsta nivån. Zoom 12–13
  används inte (Filips beslut). Man kan zooma ut förbi 14 – då visas 14-bilden förminskad.
- **Högre nivåer** = 512-px-bitar, bara bitar nära vatten. **Kartformatet (2026-10-06,
  `tools/PLAN_KARTFORMAT.md`):** varje bit = **bas** `tiles_v<V>/z<z>/<stil>/<c>_<r>.webp`
  (bara färger, WebP kvalitet 35) + **kurvlager** `tiles_v<V>/z<z>/lines/<c>_<r>.webp`
  (Genesis t_ för den zoomen, genomskinlig, förlustfri WebP 32 färger – **inte 8**, då blir
  siffrornas gloria taggig) som alla kartlägen delar; c1 har ljusa linjer i `lines_w/`
  (`"lines": "lines_w"` på kartläget i lake.json). Baser finns till `baseMax` (= djupdatans
  zoom, 17); zoom 18 har bara kurvlager och appen lägger dem på zoom 17-basen förstorad –
  ser likadant ut (färgerna på 18 var ändå zoom 17 förstorade). Regnaren 143 → 39 MB.
  **Varje bit har 8 px kant från grannarna** (528 × 528, `pad` i lake.json, `PAD` i genesis_render.py):
  appen visar bara insidan (`clip-path`) på exakt plats. Utan den förstorade webbläsaren varje bit för
  sig – linjerna knyckte och färgerna hoppade där bitar möttes (syntes tydligt på zoom 18,6, 2026-10-06).
  Sjöar som inte byggts om har kvar det gamla (en JPG per bit med linjerna inbakade) –
  appen klarar båda (`DETAIL.lines` finns/saknas). Appen visar nivån = zoomen avrundad; förra nivån ligger kvar
  tills den nya laddat. Zoomindikatorn: "Zoom 15,3 lager 15".
- **Samma max zoom för alla sjöar** (beslutat, ej byggt än: 18,6). Varje sjö
  använder sitt högsta lager och förstorar det därifrån.
- **Varje nivå visar exakt Genesis kurvlager (t_) för den zoomen** – antalet
  linjer och siffror ökar när man zoomar in, precis som på Genesis.
- Zoom 18 HAR mer än 17: tunnare linjer och många fler djupsiffror.
- Nivåer över djupdatans zoom (t.ex. 18 när djupet är på 17): bara kurvlager, så **alla
  kartlägen har zoom 18** (förr bara s1/g1 via `top_styles`, för att de var stora).
- **Förhandsgranska innan bygge:** `py -3 tools/genesis_render.py <id> preview 14,15 <mapp>`
  ritar hela bilderna för de nivåerna i alla kartlägen till en valfri mapp, utan att
  röra `docs/` eller `lakes/`.
- **Ny kartversion och iPhone-appen (beslut 2026-10-06, app-chatten):** appen (Capacitor) packar in
  `lake.json` och hämtar detaljbitarna från webben. Får en sjö ny kartversion (`tiles_v<N>`) och den gamla
  mappen tas bort, visar appen suddiga bitar tills en ny app byggs. **Claude påminner Filip:** "Ny kartversion –
  be app-chatten bygga ny app."

---

## 4. Djupkurvor och siffror

**Vi ritar ALDRIG egna djupkurvor eller siffror.** Bara Genesis t_-lager, för
rätt zoom, och bara nära vår sjö (inte grannsjöar). Det vi ritar själva är
färger och relief (ur det kalibrerade djupet).
- Kartlägen utan vattenfärg (c1 Bottenhårdhet; förr Natt och Flygfoto + linjer): linjerna färgas ljusa. Siffrorna
  känns igen på sin ljusa gloria och lämnas som de är (inte på "svart klump" –
  då blir ihopsmälta linjer i branter fel).

---

## 5. Genesis egenheter (lärt den hårda vägen)

- **Djupfärgerna (b_) är platta band men INTE jämna i meter.** 60–90 färger,
  ljus = grunt. Hur många meter en färg motsvarar varierar (tätt grunt, glesare djupt).
  → Kalibrera färg → meter mot avlästa djupsiffror (steg 5 i receptet). Tabellen
  görs stigande (isotonisk) och interpoleras; högst 1 m extrapolering bortom
  djupaste avlästa siffra (sista färgerna är ofta sällsynta kantfärger).
- **Siffror:** liten siffra efter talet = tiondelar ("0₈" = 0,8 m). Vissa står upp
  och ner ("s6" = 9₅?) – använd färgen runt siffran/grannarnas värden för att avgöra.
- **Kurvintervall:** zoom 16 ~1 m eller tätare, zoom 17 ~0,5 m, zoom 18 samma men
  fler siffror. I branter smälter kurvorna ihop till svarta fält.
  *Testat och förkastat:* räkna kurvor från stranden för att få djupet – ihopsmälta
  kurvor gör att man tappar räkningen (blev alldeles för grunt).
- **Hål i färglagret = öar ELLER omappade områden** (genomskinligt i b_), aldrig
  "extra djupt". *Misstag vi gjort:* hål omgivna av djupa färger tolkades som djuphål
  och målades mörkast – de var omappade stråk mitt i sjön. Nu: hål får inget djup och
  ingen färg (flygfotot syns, en hård utskärning), OpenStreetMap avgör sjö/ö.
- **Utskärningar får inte påverka djupet eller reliefen runt sig:** före uppskalning
  fylls celler utan djup med närmaste kända djup (annars blandades "0 m" in i kanten –
  7 m för grunt och en mörk skuggrand), och i reliefen fylls omappade delar av sjön
  med närmaste djup (`solid` i `relief()`), så kanten inte blir en vägg.
- **Skarvar:** 1–2 px genomskinliga rader/kolumner mellan Genesis datablock
  (t.ex. var 4096:e px). De delar sjön i bitar om man inte lagar dem (genesis_depth
  fyller dem med grannfärgen och sparar `b_fixed.png`).
- **Grannsjöar** finns i samma bilder → ta största sammanhängande vattnet, och
  lägg Genesis lager (t_, b_, v_, c_) bara nära vår sjö.
- **Täckning:** Genesis har bara data där någon loggat med ekolod. Regnaren:
  5,4 av 8,1 km². Hårdhet (c_) finns bara längs loggade spår; vegetation (v_) är
  en ja/nej-mask.
- Djupfältet ur färgbanden är **slätt** – det finns ingen klipp-/steninfo som i
  multibeam-kartor (Garmin/Navionics-bilderna). Relief kan inte hitta på detaljer.

---

## 6. Sjögränsen: OpenStreetMap

- Genesis vatten = bara loggade delar. Sjöns riktiga strand kommer från
  OpenStreetMap (i Sverige Lantmäteriets karta) – följer flygfotots stränder exakt.
- Djupnätet: 0–250 = djup/steg, **252 = sjö men okänt djup** (i OSM-sjön, ej loggat),
  255 = land. Rader packas: 251 n n = land, 253 n n = okänt djup.
- Kartbilderna färgas INTE där Genesis saknar data – flygfotot syns (Filips val).
  Lodet visar "Okänt djup"; rutter sjövägen går även där.
- *Testat och förkastat:* hitta vatten i flygfotot (mörkt + ej grönt + slätt).
  Mörk skog ser ut som vatten → öar och strandskog blev "sjö".

---

## 7. Kartlägen, färger och djupskala

- **FAST djupskala, samma i alla sjöar** (Filips beslut): samma djup = samma färg överallt.
  Mest färgskifte 0–10 m (där man fiskar) = 2/3 av skalan, 10–50 m = sista 1/3
  (blått → mörkblått), djupare än 50 m = som 50 m. `DEPTH_KNOTS_M/F` i genesis_render.py.
  Legend (nere till vänster): **0 → sjöns eget maxdjup** (hela meter upp till 20 m, annars 5 m-steg;
  Regnaren 0/4/8/12, Sjösjön 0/7/14, Vågsfjärden 0/20/40), jämnt i meter, med skalans färger för
  just de djupen. *Förkastat:* 0/5/10/50 m för alla – såg ut som att sjön var 50 m djup (Filip).
  *Förkastat:* skala relativ till sjöns maxdjup (0–DMAX) – samma djup fick olika färg i
  olika sjöar. (DMAX används nu bara som `depth.max` i lake.json.)
  Följd: djupa sjöar (Vågsfjärden) blir mest blå med färg bara längs kanterna – avsiktligt.
- s1 **Djupfärger:** rött 0 m (#d62728), orange 1,5 (#ff7f0e), gult 3 (#ffdd00), grönt 5
  (#2ca02c), turkos 7,5 (#17becf), blått 10 (#1f4fd6), mörkare blått 25 (#0f2c8a), nästan
  svartblått 50 m (#03081f) + relief. (Djupaste gjordes mörkare på Filips begäran.)
- s2 **Förenklad:** exakt samma färger som Djupfärger, men ingen relief (Filips beslut;
  tidigare `turbo_r` – samma djup fick annan nyans än i Djupfärger)
- ~~s4 Natt~~ – **borttagen, skapa den aldrig** (Filips beslut). Id `s4` används inte.
- ~~s5 Flygfoto + linjer~~ – **borttagen 2026-10-06** (Filips beslut). Dess ljusa linjer
  (alfa^2,5, 55 %, `LINE_THIN`, `LINE_OPACITY`, siffrorna 100 %) lever kvar i c1.
- s6 **Blå relief:** #cfeefa → #6fc3e8 → #2a86c9 → #12509a → #0a2c63 + relief
- g1 **C-MAP original:** flygfoto + Genesis b_ + t_ (som på Genesis)
- v1 **Vegetation:** Blå reliefs färger UTAN relief + grönt (#46dc3c, 72 %) där v_ säger växtlighet
- **Relief bara i Djupfärger (s1) och Blå relief (s6).** Alla andra lägen: ingen relief.
- c1 **Bottenhårdhet:** Genesis 4 nivåer (mjuk → hård) omfärgade med mer kontrast,
  palett "warm" (beslutad): ljusgul → gul-orange → röd-orange → mörkröd. Där ingen hårdhet
  är mätt: **ingen färg alls** – flygfotot + tunna ljusa djuplinjer (eget kurvlager `lines_w/`).
  *Förkastat:* dämpad blå bakgrund där data saknas (såg ut som data), Genesis egna
  färger (för lika varandra), "bluered" blå → röd.
- s3 **Sjökort:** blå band som börjar vid fasta djup 0, 1, 2, 3, 5, 7,5, 10, 20, 30 m.
- Lagerordning: flygfoto → vattnets färg/relief (bara vatten) → Genesis t_ (bara vid sjön).

---

## 8. Relief (skuggning)

**BESLUTAT (Filip): T1 × AO, utjämning ~1,2 m, Genesis linjer 100 %.** Byggt i båda sjöarna.
- Höjdkarta = −djup, utjämnad ~1,2 m (i meter, så samma utseende på alla zoomnivåer),
  höjderna × 12. Normal map ur höjdkartan (Sobel).
- T1 = diffust ljus (Lambert) från NV (315°), 45° över horisonten.
- AO = ambient occlusion, horisontbaserad: 16 riktningar, ~25 m runt varje punkt.
- Ljusfaktor = (1 + (T1 − median) × 2 × 0,5) × (1 + (AO − median) × 2 × 0,4), var för
  sig normaliserade 2–98 %; klämd 0,3–1,6; multipliceras på djupfärgens RGB.
- Testat men valt bort i samma omgång: T2 (lågt ljus 25°: bortvända sluttningar helt
  mörka), kastade skuggor (stora svarta fläckar på vår släta botten), utjämning 2–3 m
  (tar bort svaga ränder från Genesis färgband men Filip föredrog skärpan).
- Känt: vid 1,2 m syns svaga ränder parallellt med stranden i ljuslagret (trappsteg
  mellan Genesis färgband); linjerna döljer dem nästan helt på kartan.

### Historik – vad som testats före beslutet

Regler som gäller oavsett metod: räknas i full upplösning (djupdatans zoom) och
skalas till varje nivå; multipliceras bara på ljusstyrkan (nyansen ändras aldrig);
bara i vattnet.

**Gamla kartan (före Genesis-ombyggnaden, `build_depth_map_original.py`, borttagen):**
djup = färgens rang (ej kalibrerat) × 10 m; utjämning σ 4,5 px; Sobel-lutning,
överdrift zf 30; ljus azimut 350°, höjd 40°; normaliserat 2–98 %; faktor
1 ± 0,55 (0,55–1,45). Den såg bra ut för att:
- **nästan allt var mörkblått** (rangen hamnade i djupa änden) – skuggning syns
  starkt på mörkblått, svagt på gult/grönt;
- **djupet var en trappa** med ~63 platta steg – utjämningen gav små kanter som
  såg ut som detaljer.

**Testat efter ombyggnaden (på kalibrerat djup):**
| Namn | Vad | Resultat |
|---|---|---|
| C | gamla metoden, σ 6, 0,45 | platt, för svag |
| E | ljus N (350°/38°) + NV fyllnad, σ 3, 0,75, branter mörkare | nu i appen; stora mörka fält på långa sluttningar |
| G | skarpt riktat ljus + lokal relief | tydligt men stora mörka fält |
| L | ljus från alla håll + lokal relief | inga mörka sidor, lite platt |
| L2 | lokal + riktat | mörka fält kvar |
| L3 | ljus från 8 håll + lokal relief i två storlekar (≈10 m och 30 m) | gropar/ryggar framträder, inga mörka fält |
| D | djupare = mörkare (+ lite lokal) | lugn, lättläst |
| H | riktat ljus från högre höjd (60°) | långa sluttningar blir ändå mörka |
| D+H | båda | mörka fält kvar |
| "Förslag" | lokal + djupare mörkare + högt ljus | favorit hittills (Claude) |

- **Linjerna på 100 % döljer reliefen** (Genesis kurvor är mycket täta). Med
  40–55 % (siffror på 100 %) syns reliefen mycket bättre. *Ej beslutat.*
- **Grundproblemet med riktat ljus:** en lång jämn sluttning blir ett enda stort
  ljust eller mörkt fält – det Filip inte vill ha ("lokal skugga" önskas).
- Pågår (linjer 100 %, zoom 17, Regnaren vid djuphålorna):
  **A** = bara djupare = mörkare (ljusfaktor 1,12 − 0,62 × djup/DMAX, inget ljus alls);
  **B** = gamla metoden exakt (σ 4,5 px vid z16, zf 30, azimut 350°, 2–98 %, ±0,55)
  men ljuset högre upp: 60° i stället för 40°. Väntar på Filips val.

---

## 9. Testat och förkastat (gör inte om)

- Djup ur kurvräkning från stranden (kurvor smälter ihop i branter).
- Anta 0,5 m per färgband (stämmer bara till ~20 m på Vågsfjärden).
- Vatten ur flygfoto (skog = vatten).
- En enda testpunkt för att se vilka zoomnivåer som finns (hamnade på land).
- Bilderna i både `lakes/` och `docs/` (dubblade repot) – bara i `docs/lakes/`.
- Egna djupkurvor (Filip vill bara ha Genesis).
- Web Share vid export i test (Edge på Windows) – testet stänger av canShare.

---

## 10. Öppna frågor / att göra

- [x] Välj relief (se 8) och linjestyrka – T1 × AO, 1,2 m, linjer 100 %.
- [x] Relief (T1 × AO) bara i Djupfärger + Blå relief; alla andra utan. Natt borttagen.
      (Beslutat, `relief()` i genesis_render.py.)
- [x] Max zoom 18,6 för alla sjöar (beslutat).
- [x] ~~Zoom 18 bara för Djupfärger + C-MAP original (`top_styles`)~~ – ersatt av kartformatet
      (bas + delat kurvlager, 2026-10-06): alla kartlägen får zoom 18.
- [x] Samma max zoom för alla sjöar (18,6) – byggt (`MAX_ZOOM` i src/js/10-core.js).
- [x] Regnaren ombyggd med djupkarta på zoom 17 (53 avlästa siffror, 90 % inom
      0,11 m; tidigare zoom 16: 47 siffror, 0,14 m) och lager 14–18. Filer v4
      (Vågsfjärden v3). Regnaren 139 MB, Vågsfjärden 99 MB i docs/lakes/.
- [x] Sjösjön (mwID 1270210, OSM relation 2375527, 62,5600–62,5808 N, 17,8037–17,8253 O):
      21 avlästa siffror, 90 % inom 0,11 m, maxdjup 13,5 m, `grid_div` 4 (liten sjö), filer v1,
      18 MB. Norra delen av sjön (OSM) saknar Genesis-data → okänt djup. Tog ~5 min totalt.
- [x] Sibbofjärden (`sibbo`, mwID 1206257, OSM relation 1924380, 58,7540–58,8125 N, 17,2760–17,3365 O):
      57 avlästa siffror, 90 % inom 0,12 m, maxdjup 11,2 m (legend 0/4/8/12), `grid_div` 8, filer v1,
      97 MB, ~26 000 rutor (z18 i 3 shards per lager, ~15 min nedladdning). 2026-09-30.
- [x] Östra Vitten (`vitten`, mwID 1275694, OSM way 154946903, 58,9830–58,9990 N, 15,7080–15,7400 O, Vingåker):
      24 avlästa siffror, 90 % inom 0,14 m, maxdjup 4,5 m, `grid_div` 4, filer v1, 15 MB, 8 namn (0 i vattnet).
      Genesis har bara norra delen (ringen runt ön) – södra delen = okänt djup. Steg 1–8 i sidochatt
      2026-10-05, steg 9–10 (bygg + tester) i main-chatten 2026-10-06. (matplotlib saknades
      efter ominstallationen – `py -3 -m pip install --user matplotlib`.)
- [ ] **Mälaren + nytt kartformat (bas + delat kurvlager, WebP): plan i `tools/PLAN_KARTFORMAT.md` (2026-10-06).**
- [x] **Mälaren (stor sjö, 2026-10-06):** bara området i `tools/malaren_polygon.json` (175 km², ~66 km² vatten med
      Genesis-data; convex hull runt alla fångster +20 %, östra sidan rak – Filips ritning). Byggs med
      `tools/genesis_big.py` (avsnittet "Stora sjöar" nedan), inte genesis_depth/genesis_render. 70 avlästa siffror
      0,3–48 m, 90 % inom 0,22 m, maxdjup 49 m, `depth_step` 0,3 m, `grid_div` 16 (cell ~10 m). Ska kunna
      utökas med fler områden (Filip): större polygon i malaren_polygon.json → hämta (cachat) → bygg om.

## Stora sjöar: `tools/genesis_big.py` (block)

För sjöar för stora för minnet (Mälaren: 24 576 × 40 960 px på zoom 17). Samma kartlägen och ritkod som
genesis_render.py (`make_styles`, `style_image`, `line_layer`, `bake`, `pack_depth`), men allt räknas i **block om
4 096 × 4 096 px** (zoom 17) och bara block som rör sjöns polygon (`"clip"` i source.json, `"blocks": 4096`).
Genesis-rutorna läses direkt ur `raw/<id>/z<z>/<lager>/` – sys aldrig ihop (för stort).
1. **Hämta:** `FF_CLIP=<polygon.json> py -3 tools/genesis_tiles.py …` hämtar bara rutor inom polygonen (+ 2 rutor).
   Zoom 14–17 alla lager, **zoom 18 bara `t`** (baserna kommer från zoom 17). Mälaren: `sh tools/malaren_fetch.sh`
   (shards parallellt, ~45 min, ~70 000 rutor). **Vänta tills den är helt klar** (skriver "done") innan render – zoom 14–16 hämtas
   sist, och ritades Mälaren medan de kom saknades kurvor/vegetation/hårdhet på zoom 16 (fick ritas om).
2. `py -3 tools/genesis_big.py <id> colours` – alla Genesis djupfärger i polygonen, rangordnade grunt → djupt.
3. `FF_PER=2 py -3 tools/genesis_big.py <id> sheet` → `raw/<id>/z17/labels_sheet.png`; läs av siffrorna in i
   `lakes/<id>/raw/depth_labels.json` (positioner i globala px, `gx`/`gy`). FF_PER = siffror per 3 färger (2 räckte).
4. `… depth [k/n]` – djupet per block (`raw/<id>/z17/depth/<bx>_<by>.npz`), marginal 640 px. Kör 8 st `k/8`
   parallellt, sedan en gång utan (maxdjup + kontroll mot siffrorna). Mälaren: ~2 min/block.
5. `… relief [k/n]` – T1 × AO per block (marginal 128 px) + **en ljusskala för hela sjön** (percentiler ur
   stickprov från alla block) – annars får blocken olika ljushet och skarvar.
6. `… render [k/n]` – bitar (bas + kurvlager, med kant från grannarna), per block `render_parts/` (översiktsbild,
   tumnaglar, have-listor, djup-/bottennät). Utan k/n: sätter ihop allt + lake.json. ~80 s/block, ~1,4 GB/process
   (5 parallellt gick bra). Allt är återupptagbart: klara block hoppas över (ta bort filerna för att göra om).
Översiktsbilden (zoom 14) = flygfoto överallt i bbox:en, blockens bilder ovanpå. Inget `depth_raw.npz` (bara
Regnarens används i testerna).
**Minnet i appen:** allt som räknas för hela sjön (Kartanalys, Vind och lä, rutten) går på `workGrid()` (`js/38-speed-depth.js`),
högst 1,5 M rutor (`GRID_MAX`); större djupnät slås ihop 2×2 (4×4 …). Mälaren 1 536 × 2 560 räknas som 768 × 1 280 (~20 m);
blir den större (fler områden) och passerar 6 M djupceller blir det automatiskt 4×4 (~40 m). Översiktsbilden avkodad =
imgW × imgH × 4 byte hela tiden (Mälaren 63 MB, Regnaren 5 MB) – se `tools/PLAN_MINNE.md`.

## Namn på kartan (OpenStreetMap)

Filter → Lager → **Namn** (på som standard, `ffmap_names_v1` = 0 om avstängd): riktiga namn runt sjön som vit prick + text. Data i
`lakes/<id>/names.json` = `[[lat, lon, namn, "w"|"p"], ...]` (w = ö, udde, vik, sund; p = gård, by), skapad av
`py -3 tools/osm_names.py [sjö]` (Overpass, inom kartbildens yta, bara objekt med `name`; försöker igen om servern är
upptagen). build.py bäddar in den som `LAKE.names`. Ny sjö: steg 8 i receptet (kör skriptet, bygg). `js/59-names.js` ritar; vatten-namn
går före land, krockande etiketter göms (zooma in = fler). Data © OpenStreetMap-bidragsgivare (ODbL).
