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
  - Vatten = −djup (`depthAtImgPx`), sjö utan djup = strax under ytan, land = höjd över sjön ur `LAKE.land` (minst 0,3 m).
    Markens punkter intill vattnet ligger i vattnets nivå – annars reser sig en brant strand i taggar ur vattnet.
- **Bilden:** vald kartstils kartbild som textur (flygfoto på land, Genesis färger och kurvor i vattnet – inget ritas av oss),
  ljus från nordväst som kartornas relief. Bilden hämtas som en egen `Image` (ur webbläsarens cache), INTE kartans `<img>`:
  three.js mäter texturen efter elementets storlek på sidan, och Mälarens och Gryts bild visas i dubbel storlek mot filen –
  hela marken blev svart långt ut (Filip 2026-11-11).
- **Skarp nära:** zoomnivåns bitar (samma som vanliga kartans: bas + kurvlager) sätts ihop på EN canvas om 2048 px
  (`m3Detail`) och visas i stället för kartbilden där den når (i shadern, `uDet`/`uDetR`). Nivån väljs så att canvasen når
  1,2 × avståndet (`m3DetLevel`); längre ut än lägsta nivån räcker = bara kartbilden. Flyttar man sig på samma nivå
  behålls det som redan är ihopsatt och bara nya bitar hämtas.
- **Vattenytan:** genomskinlig blå yta i nivå 0, bara över sjön. "Vatten" av = sjön "tömd".
- **Kameran:** ett finger = vrid och luta, två = flytta, nyp = zooma (egen kod – three.js-filen i appen har ingen
  OrbitControls). Den vrids kring en punkt PÅ marken och går aldrig under marken (`m3Ground`). Ritas bara när något
  ändrats, ingen loop. `logarithmicDepthBuffer`: en stor sjös bortre ände är 30 km bort och marken intill 50 m.
- **Märken:** din båt (`.m3Me`), fiskeplatser och andras båtar är kopior av vanliga kartans märken (`pinEls`,
  `#boatsLayer`) – samma filter och ikoner. Uppdateras efter varje full ritning av kartan (`m3MarksSync` sist i `render()`).
  Bara att titta på.
- **Reglage:** Höjd × 1–10, Vatten, Till mig, norrpil (tryck = norr upp), ✕. Sparas i `ffmap_3d_v1`. Överlever vridning (`st.m3`).
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
- **Filer:** `docs/land/<id>_v2.txt` och `lakes/<id>/land.json` (fil, storlek, `max`, nivå, källa, vilket kartutsnitt).
  - Samma packning som djupfilen (255 = sjö, packade rader, base64), samma rutnät som djupet.
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
  | Mälaren | 9 st (657–659 × 63–65) | 3,8 MB | 1,0 m | 69 m |
  | Gryts Skärgård | 9 st (643–645 × 59–61) | 4,0 MB | 0,4 m | 81 m |

  Kontroll vid körningen: 93–100 % av sjöns rutor ligger inom 0,5 m från sjöns nivå i höjddatan, alltså ligger höjderna
  rätt mot kartan. Sjö utan höjdfil (ny sjö) = platt mark; vyn fungerar ändå.
- **Prövat och borttaget:**
  - Öppna 30 m-data (AWS Terrain Tiles, EU-DEM/SRTM): trädtopparna är med, så marken hoppade upp i taggar längs stranden.
  - Google: villkoren förbjuder att höjderna sparas, och appen ska fungera offline.

## Kvar och att tänka på
- iPhone-appen packar sjöfilerna i appen: app-chatten måste ta med mappen `land/`.
- Märkena syns genom kullar, eftersom de ligger ovanpå bilden.
- Inte i vyn: heatmap, Kartanalys, spår, väder, lodet, lägga eller ändra platser. Kartans färgreglage gäller inte heller där.
- Rutorna i Hämtade filer (5,6 GB) behövs bara om en höjdfil ska göras om, t.ex. efter ett nytt kartutsnitt.
