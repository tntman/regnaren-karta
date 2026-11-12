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
  - **Höjdfilen pekar ut vattnet utan djup** (252 där, `uncharted()` i `tools/land_height.py`; `m3Void` i appen).
    Vatten = saknar djup + plant i Lantmäteriets höjder (rutan och dess 8 grannar inom 2 cm – deras höjder är helt plana
    över vatten: 0,000 m på öppet vatten i alla sju sjöar, medan låg strand, vass och öar inte är det) + i sjöns nivå
    (± 0,5 m: havet står olika mellan skanningarna) + sammanhängande med sjön (en egen damm förblir mark).
    Inte de bitar som bara har grunt lodat vatten intill sig (högst 1 m inom 2 rutor, `SHOAL`): ett grund eller en
    vassvik i grunt vatten ritas som förut, strax under ytan – där står ingen kulle.
  - **Appen avgör vad som blir hål** (`m3Make`): olodat vatten inom 15 m (`M3_REACH`) från något känt tar sitt djup
    därifrån – botten fortsätter en bit utanför sjökortets kant, går upp mot stranden och fyller smala luckor – och
    jämnas ut till en sluttning. Längre ut än så = hål (inga trianglar med ett hörn som fortfarande är hål).
    Punktens klass `wet`: 0 land, 1 vatten, 2 olodat (hål om det blir kvar), 3 olodat som fått djup. Djup vinner över
    olodat – en ny lodning syns även om höjdfilen är äldre.
  - Första versionen (v3, ute en timme 2026-11-12) gjorde hål bara där det olodade var minst 30 m brett och lät smalare
    bitar ligga vid ytan. De stod som pelare vid hålens taggiga kanter, 27 m höga (Filips skärmbild från Mälaren).
    Därför märker verktyget nu allt, och appen sköter kanterna.
  - Regnarens "olodade" fläckar är småöar (upp till 5 m höga) – inga hål där. Gryts likaså (skär). Det som fortfarande
    ritas vid ytan intill djupt vatten är sådant: 295 rutor på Mälaren, 267 på Gryt, inga plana (kollat 2026-11-12).
  - **Vattenytan ligger kvar över hålen** (Filips val): mörkblått vatten utan botten. Vatten av = helt tomt.
  - Långt bort är rutnätet grovt (ca 60 m på Mälaren och Gryt) och allt inom en ruta från känt djup fylls: små hål syns
    först på nära håll. Utan höjdfil (går inte att hämta) = inga hål, som förut.
  - Testkroken (`__ffMap3d`) frågar hela kartans rutnät bara där det ritas, inte där det är utskuret för det fina –
    det fina kan ha ett hål där.
- **Bilden:** vald kartstils kartbild som textur (flygfoto på land, Genesis färger och kurvor i vattnet – inget ritas av oss),
  ljus från nordväst som kartornas relief. Bilden hämtas som en egen `Image` (ur webbläsarens cache), INTE kartans `<img>`:
  three.js mäter texturen efter elementets storlek på sidan, och Mälarens och Gryts bild visas i dubbel storlek mot filen –
  hela marken blev svart långt ut (Filip 2026-11-11).
- **Skarp nära:** zoomnivåns bitar (samma som vanliga kartans: bas + kurvlager) sätts ihop på EN canvas om 2048 px
  (`m3Detail`) och visas i stället för kartbilden där den når (i shadern, `uDet`/`uDetR`). Nivån väljs så att canvasen når
  1,2 × avståndet (`m3DetLevel`); längre ut än lägsta nivån räcker = bara kartbilden. Flyttar man sig på samma nivå
  behålls det som redan är ihopsatt och bara nya bitar hämtas.
- **Vattenytan:** genomskinlig blå yta i nivå 0, bara över sjön. "Vatten" av = sjön "tömd".
- **Djupfärg** (knapp, av som standard, `m3Cfg.col`, Filip 2026-11-12): botten färgas efter djupet med Under ytans färger
  (gulgrönt grunt → mörkblått djupt, över sjöns största lodade djup, `m3MaxDepth`) i stället för kartbilden – formen syns
  tydligare. Genesis kurvor och siffror syns då inte. I shadern (`uCol`). Prövat (bilder 2026-11-12): djupdimma (grumligt),
  sandbotten, ljusblå → mörkblå – Filip valde knappen Karta/Djupfärg.
- **Skuggor** (knapp, av som standard, `m3Cfg.shadow`, Filip 2026-11-12): kastade skuggor från solen (three.js shadow map 2048²,
  mjuka kanter). Skuggkartan täcker en ruta på 2 × avståndet runt punkten man tittar på – längre ut inga kastade skuggor.
  16 MB på grafikkortet medan den är på, lämnas tillbaka när den slås av. Ljus och skugga på sluttningarna finns alltid.
- **Ljuset:** lägre sol från nordväst (3,0, höjd 0,5) och mindre allmänljus (1,0) sedan 2026-11-12, så att botten och marken
  syns som former. Under ytan har samma ljus.
- **Fingrarna som i kartapparna** (Filip 2026-11-11; först vred och lutade ett finger och två flyttade, som i en
  3D-modellvisare): ett finger = flytta kartan, nyp = zooma, vrid två fingrar = vrid kartan, två fingrar bredvid varandra
  som båda dras upp/ner = luta (upp = mot horisonten). Mus: Shift/Ctrl + dra = vrid och luta, hjulet = zooma.
  Egen kod – three.js-filen i appen har ingen OrbitControls.
  - **Mus som i Maya/Houdini** (Filip 2026-11-12): Alt + vänster = vrid och luta, Alt + mitten (eller bara mitten) = flytta,
    Alt + höger = zooma (dra höger/ner = närmare); högerklicksmenyn av i vyn.
  - Lutningen med två fingrar är förlåtande (2026-11-12, Filip: "kan inte ändra vinkeln"): båda ungefär upp eller ner, åt samma
    håll, utan att nypa – även om de börjar lite snett.
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
- **Märken som 3D-föremål** (Filip 2026-11-12, `m3Objs`/`m3ObjsPlace`): 3D-versioner av kartans märken – droppen i typens färg
  med vit och mörk kant, Fara stoppskylten med vitt X (vänds mot kameran), Träffpunkt en fyr med ring på vattnet, din båt
  den orange pilen och andras samma pil i vitt med mörka kanter. Allt står på vattenytan (på land: på marken), speglas upp
  och ner i ytan (mörkare, tonar bort neråt, `uFade`) och har en tunn linje ner till botten. Storleken går med avståndet.
  Vilka som visas = kartans egna (`pinEls`, `#boatsLayer` – samma filter); namnen ligger kvar som platta etiketter bredvid
  (2D-ikonen dold, `.m3Obj`). Uppdateras efter varje full ritning av kartan (`m3MarksSync` sist i `render()`). Bara att titta på.
  Andras båtar skickar ingen kurs: deras pil pekar mot norr. Din pil = telefonens riktning när Kompass är på, annars GPS-kursen.
- **Kompass** (knapp = Filters Kompass, `53-compass.js`; iOS frågar om lov i trycket): kompassros på vattnet runt din båt
  (N rött, Ö S V, streck var 30:e grad) och en ljus kil längs vattnet dit telefonen pekar (kompassinställningarnas längd,
  vinkel, färg). `m3CompassMake`/`m3CompassPlace`.
- **Spår:** samma som kartan visar (`renderTrack` → `m3TrkSync`): ditt i din färg, andras ljusblått, som linjer strax över
  vattnet/marken. Byggs om när de ändras eller Höjd × gör det.
- **Fångster** (knapp, av som standard, `m3Cfg.fish`): sjöns alla fångster (heatmapens `catchData`) som små prickar på botten
  där de togs, artens färg, några px oavsett avstånd (`T.Points`). Saknar telefonen kopian hämtas den en gång (`loadCatches`).
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
- **Filer:** `docs/land/<id>_v4.txt` och `lakes/<id>/land.json` (fil, storlek, `max`, nivå, källa, vilket kartutsnitt).
  - Samma packning som djupfilen (255 = sjö, 252 = vatten utan djup – se ovan –, packade rader, base64), samma rutnät
    som djupet. v2 hade inga 252, v3 bara det som var minst 30 m brett.
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
