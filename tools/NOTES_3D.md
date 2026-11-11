# 3D-karta (botten och mark i 3D)

Filip 2026-11-11. Kod: `src/js/73-map3d.js`, `src/css/79-map3d.css`, `#m3View` i `src/html/30-map-ui.html`.
Test: `tests/test_map3d.py`. Höjdfilerna görs av `tools/land_height.py`.

## Vad det är
- Rad **3D-karta** i kartlägeslistan (håll kartknappen), direkt efter kartstilarna. Heatmap och Under ytan ligger kvar sist.
  Egen helskärmsvy; vanliga kartan ligger orörd under.
- **Terrängen: två rutnät**, högst 400 punkter per sida vardera (`M3_NMAX`, `m3Make`):
  - hela kartan, grovt – finns alltid, så sjön syns ända bort (ingen dimma; prövat först med ett enda rutnät och dimma
    i kanten, Filip: "distance fog är för mycket");
  - ett fint runt punkten man tittar på, med varje djupruta (`m3Patch`, byggs om när fingrarna vilat 0,2 s). Hela kartans
    rutnät skärs ut där det fina ligger (`m3Hole`: fyra klipplan), marken en ruta längre in så att de överlappar.
    Så långt ut att det fina inte vore finare än hela kartans finns bara det senare.
  - Vatten = −djup (`depthAtImgPx`), land = höjd över sjön ur `LAKE.land` (minst 0,3 m). Vatten utan djup = hål (nästa
    punkt); smala olodade bitar och småöar som djupfilen räknar som sjö = strax under ytan, som förut.
    Markens punkter intill vattnet ligger i vattnets nivå – annars reser sig en brant strand i taggar ur vattnet.
- **Hål där vattnet saknar djup** (Filip 2026-11-12: ritat vid ytan blev det "stora kullar som egentligen inte finns"
  bredvid det lodade djupet). Två sorters vatten utan djup:
  - olodad del av sjön (djupfilens 252) – Östra Vitten 55 % av sjön, Sjösjön 29 %;
  - vatten utanför sjökortet, som djupfilen räknar som land (255 = land/okänt) – Mälaren 31 % av "marken" (västra och
    södra delen), Gryt 17 % (havet utanför).
  - **Höjdfilen pekar ut hålen** (252 där, `holes()` i `tools/land_height.py`) – appen har en enda källa (`m3Void`).
    Vatten = saknar djup + plant i Lantmäteriets höjder (rutan och dess 8 grannar inom 2 cm – deras höjder är helt plana
    över vatten: 0,000 m på öppet vatten i alla sju sjöar, medan låg strand, vass och öar inte är det) + i sjöns nivå
    (± 0,5 m: havet står olika mellan skanningarna) + sammanhängande med sjön (en egen damm förblir mark).
  - Av det blir det hål bara där det är **minst 30 m brett** (`WIDE` – en smal remsa mellan sjökortets kant och stranden
    ritas som förut, annars blir det en glipa längs stranden) och **ligger intill lodat vatten djupare än 1 m** (`SHOAL` –
    ett grund eller en vassvik i grunt vatten ritas som förut, där står ingen kulle).
  - Regnarens "olodade" fläckar är småöar (upp till 5 m höga) – inga hål där. Gryts likaså (skär).
  - I appen (`m3Make`): punktens klass `wet` = 0 land, 1 vatten, 2 hål (djup vinner över hål – en ny lodning syns även om
    höjdfilen är äldre). Trianglar ritas inte om alla tre hörn är hål, eller om hål och vatten möts (det var väggen upp
    mot ytan). Land + hål ritas: stranden ner till vattnet.
  - **Vattenytan ligger kvar över hålen** (Filips val): mörkblått vatten utan botten. Vatten av = helt tomt.
  - Långt bort är rutnätet grovt (ca 60 m på Mälaren och Gryt): små hål syns först på nära håll. Utan höjdfil (går inte
    att hämta) = inga hål, som förut.
- **Bilden:** vald kartstils kartbild som textur (flygfoto på land, Genesis färger och kurvor i vattnet – inget ritas av oss),
  ljus från nordväst som kartornas relief. Bilden hämtas som en egen `Image` (ur webbläsarens cache), INTE kartans `<img>`:
  three.js mäter texturen efter elementets storlek på sidan, och Mälarens och Gryts bild visas i dubbel storlek mot filen –
  hela marken blev svart långt ut (Filip 2026-11-11).
- **Skarp nära:** zoomnivåns bitar (samma som vanliga kartans: bas + kurvlager) sätts ihop på EN canvas om 2048 px
  (`m3Detail`) och visas i stället för kartbilden där den når (i shadern, `uDet`/`uDetR`). Nivån väljs så att canvasen når
  1,2 × avståndet (`m3DetLevel`); längre ut än lägsta nivån räcker = bara kartbilden. Flyttar man sig på samma nivå
  behålls det som redan är ihopsatt och bara nya bitar hämtas.
- **Vattenytan:** genomskinlig blå yta i nivå 0, bara över sjön. "Vatten" av = sjön "tömd".
- **Fingrarna som i kartapparna** (Filip 2026-11-11; först vred och lutade ett finger och två flyttade, som i en
  3D-modellvisare): ett finger = flytta kartan, nyp = zooma, vrid två fingrar = vrid kartan, två fingrar bredvid varandra
  som båda dras upp/ner = luta (upp = mot horisonten). Mus: Shift/Ctrl + dra = vrid och luta, hjulet = zooma.
  Egen kod – three.js-filen i appen har ingen OrbitControls.
  - Vad ett grepp är avgörs av dess första rörelse (`m3G`): två fingrar när båda rört sig 4 px (eller ett av dem 24 px).
    Kartan vrids först när fingrarna vridits 11° (`m3Tw`) – en nypning ska inte vrida kartan.
  - **Det fingret tog tag i ligger kvar under fingret** (botten, en kulle): `m3Cast` letar upp vad som ritas under fingret
    (mitten av två), och punkten man tittar på läggs i den höjden längs siktlinjen (`m3Slide` – kameran står still).
    Annars gled botten undan på nära håll: vattenytan ligger ovanför den, ×3 eller mer.
  - **Kameran håller höjden medan fingrar är nere** (`m3.ty`): annars åkte den upp och ner med marken under skärmens mitt
    när man drog över land. När alla fingrar släppt läggs punkten man tittar på tillbaka på marken längs siktlinjen –
    inget rör sig i bilden.
  - Gränserna (4/24 px, 11°, lutningens fart) är satta utan prov på telefon – justera efter vad Filip tycker.
- **Kameran** vrids kring en punkt PÅ marken och går aldrig under marken (`m3Ground`). Ritas bara när något
  ändrats, ingen loop. `logarithmicDepthBuffer`: en stor sjös bortre ände är 30 km bort och marken intill 50 m.
- **Märken:** din båt (`.m3Me`), fiskeplatser och andras båtar är kopior av vanliga kartans märken (`pinEls`,
  `#boatsLayer`) – samma filter och ikoner. Uppdateras efter varje full ritning av kartan (`m3MarksSync` sist i `render()`).
  Bara att titta på.
- **Reglage:** Höjd × 1–10, Vatten, Till mig, norrpil (tryck = norr upp – behövs oftare nu när två fingrar kan vrida), ✕. Sparas i `ffmap_3d_v1`. Överlever vridning (`st.m3`).
- **Minne:** allt lämnas tillbaka vid ✕: geometri, texturer, canvasen (16 MB), ritytan ner till 1 px, höjdnätet.
  Filip har kört det på sin iPhone på Regnaren ("funkade bra") och Mälaren (2026-11-11), ingen krasch rapporterad;
  inte mätt i siffror.

## Markens höjder
- **Källa: Lantmäteriet, Markhöjdmodell Nedladdning** – laserskannad markyta utan träd, 1 m, CC BY 4.0. Licensen kräver att
  källan anges: "Höjddata: Lantmäteriet" står i vyn (`LAKE.land.credit`).
  Katalog (öppen): `https://api.lantmateriet.se/stac-hojd/v1`, samling `dtm-cog`. Rutor om 10 × 10 km, `m<N>_<E>.tif`,
  upp till 320 MB styck, med färdiga nivåer i 1, 2, 4, 8 … m.
- **Hämtning:** filerna kräver inloggning. Geotorget-kontot behöver behörigheten "Markhöjdmodell Nedladdning" (0 kr) – Filip har den.
  Claude hanterar inte lösenordet: Filip laddar ner i sin webbläsare (loggar in i rutan), filerna hamnar i Hämtade filer.
  `raw/hojdfiler.html` (utanför git) är en sida med alla länkar och en knapp per sjö.
- **Verktyget:** `py -3 -I tools/land_height.py <sjö> …`. Rutorna letas i mappen `DEM` (miljövariabel), annars Hämtade filer.
  Saknas någon skrivs länkarna ut och inget görs. Verktyget läser nivån strax under djupnätets ruta (Regnaren: 4 m-nivån
  → 4,9 m), räknar om SWEREF 99 TM till kartbildens rutnät (Krügers formler) och sparar höjd över sjön (sjöns nivå =
  medianen över vattenrutorna). `py -3 -I tools/land_height.py check` jämför omräkningen med Lantmäteriets egna hörn.
- **Filer:** `docs/land/<id>_v3.txt` och `lakes/<id>/land.json` (fil, storlek, `max`, nivå, källa, vilket kartutsnitt).
  - Samma packning som djupfilen (255 = sjö, 252 = hål – se ovan –, packade rader, base64), samma rutnät som djupet.
    v2 hade inga hål.
  - En byte per ruta: höjd över sjön = `max` × (byte / 250)². Stegen är alltså fina lågt ner, där stranden är (Regnaren:
    6 cm vid 1 m, 38 cm högst upp). v1 hade jämna steg – 1 m på Vågsfjärden (154 m höga berg) hade synts som trappsteg.
  - De ligger utanför `docs/lakes/<id>/`, som kart-chattens verktyg tömmer. `tools/build.py` bäddar in land.json som
    `LAKE.land`; gäller filen ett annat utsnitt hoppas den över med en varning, och marken är platt tills verktyget körts om.
  - Ny data för en sjö som redan är ute: `V` + 1 (service workern behåller en fil för alltid).
- **Alla sju sjöar har höjdfil** (2026-11-11):

  | Sjö | Rutor | Fil | Sjöns nivå | Högst över sjön |
  |---|---|---|---|---|
  | Regnaren | 652_54 | 1,3 MB | 51,2 m | 48 m |
  | Östra Vitten | 653_54, 654_54 | 0,5 MB | 64,7 m | 34 m |
  | Sibbofjärden | 651_63, 652_63 | 0,9 MB | 0,5 m | 52 m |
  | Sjösjön | 693_64, 694_64 | 0,5 MB | 35,7 m | 81 m |
  | Vågsfjärden | 697_66, 698_66 | 0,9 MB | 1,8 m | 154 m |
  | Mälaren | 9 st (657–659 × 63–65) | 2,7 MB | 1,0 m | 69 m |
  | Gryts Skärgård | 9 st (643–645 × 59–61) | 3,3 MB | 0,4 m | 81 m |

  Kontroll vid körningen: 93–100 % av sjöns rutor ligger inom 0,5 m från sjöns nivå i höjddatan, alltså ligger höjderna
  rätt mot kartan. Sjö utan höjdfil (ny sjö) = platt mark; vyn fungerar ändå.
- **Prövat och borttaget:**
  - Öppna 30 m-data (AWS Terrain Tiles, EU-DEM/SRTM): trädtopparna är med, så marken hoppade upp i taggar längs stranden.
  - Google: villkoren förbjuder att höjderna sparas, och appen ska fungera offline.

## Kvar och att tänka på
- iPhone-appen packar sjöfilerna i appen: app-chatten måste ta med mappen `land/`.
- Märkena syns genom kullar, eftersom de ligger ovanpå bilden.
- Småöar som djupfilen räknar som sjö utan djup (Regnaren: upp till 5 m höga) ritas strax under ytan. Höjdfilen kunde
  ge dem sin höjd (verktyget vet redan att de inte är vatten) – inte gjort.
- Vatten utan djup som inte gränsar till lodat djup (en vik bakom en smal kanal, en annan sjö) ligger kvar som platt mark
  med flygfotot på.
- Inte i vyn: heatmap, Kartanalys, spår, väder, lodet, lägga eller ändra platser. Kartans färgreglage gäller inte heller där.
- Rutorna i Hämtade filer (5,6 GB) behövs bara om en höjdfil ska göras om, t.ex. efter ett nytt kartutsnitt.
