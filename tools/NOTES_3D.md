# 3D-karta (botten och mark i 3D)

Filip 2026-11-11. Kod: `src/js/73-map3d.js`, `src/css/79-map3d.css`, `#m3View` i `src/html/30-map-ui.html`.
Test: `tests/test_map3d.py`. Höjdfilerna görs av `tools/land_height.py`.

## Vad det är
- Rad **3D-karta** i kartlägeslistan (håll kartknappen), direkt efter kartstilarna. Heatmap och Under ytan ligger kvar sist.
  Egen helskärmsvy; vanliga kartan ligger orörd under.
- **Terrängen:** ETT rutnät, högst 400 punkter per sida (`M3_NMAX`), runt punkten man tittar på. Nära = litet område med
  varje djupruta, långt ut = hela kartan grövre (`m3Build`, byggs om när fingrarna vilat 0,2 s).
  Vatten = −djup (`depthAtImgPx`), sjö utan djup = strax under ytan, land = höjd över sjön ur `LAKE.land` (minst 0,3 m).
- **Bilden:** vald kartstils kartbild som textur (flygfoto på land, Genesis färger och kurvor i vattnet – inget ritas av oss),
  ljus från nordväst som kartornas relief.
- **Skarp nära:** zoomnivåns bitar (samma som vanliga kartans: bas + kurvlager) sätts ihop på EN canvas om 2048 px
  (`m3Detail`) och visas i stället för kartbilden där den når (i shadern, `uDet`/`uDetR`). Nivån väljs så att canvasen når
  1,2 × avståndet (`m3DetLevel`); längre ut än lägsta nivån räcker = bara kartbilden. Flyttar man sig på samma nivå
  behålls det som redan är ihopsatt och bara nya bitar hämtas.
- **Vattenytan:** genomskinlig blå yta i nivå 0, bara över sjön. "Vatten" av = sjön "tömd".
- **Kameran:** ett finger = vrid och luta, två = flytta, nyp = zooma (egen kod – three.js-filen i appen har ingen
  OrbitControls). Den vrids kring en punkt PÅ marken och går aldrig under marken (`m3Ground`). Ritas bara när något
  ändrats, ingen loop.
- **Märken:** din båt (`.m3Me`), fiskeplatser och andras båtar är kopior av vanliga kartans märken (`pinEls`,
  `#boatsLayer`) – samma filter och ikoner. Uppdateras efter varje full ritning av kartan (`m3MarksSync` sist i `render()`).
  Bara att titta på.
- **Reglage:** Höjd × 1–10, Vatten, Till mig, norrpil (tryck = norr upp), ✕. Sparas i `ffmap_3d_v1`. Överlever vridning (`st.m3`).
- **Minne:** allt lämnas tillbaka vid ✕: geometri, texturer, canvasen (16 MB), ritytan ner till 1 px, höjdnätet.
  Inte mätt på iPhone eller Mälaren ännu.

## Markens höjder
- **Källa: Lantmäteriet, Markhöjdmodell Nedladdning** – laserskannad markyta utan träd, 1 m, CC BY 4.0. Licensen kräver att
  källan anges: "Höjddata: Lantmäteriet" står i vyn (`LAKE.land.credit`).
  Katalog (öppen): `https://api.lantmateriet.se/stac-hojd/v1`, samling `dtm-cog`. Rutor om 10 × 10 km, `m<N>_<E>.tif`,
  260 MB styck, med färdiga nivåer i 1, 2, 4, 8 … m.
- **Hämtning:** filerna kräver inloggning. Geotorget-kontot behöver behörigheten "Markhöjdmodell Nedladdning" (0 kr) – Filip har den.
  Claude hanterar inte lösenordet: Filip öppnar länken i sin webbläsare, loggar in i rutan, och filen hamnar i Hämtade filer.
- **Verktyget:** `py -3 -I tools/land_height.py <sjö>`. Rutorna letas i mappen `DEM` (miljövariabel), annars Hämtade filer.
  Saknas någon skrivs länkarna ut och inget görs. Verktyget läser nivån strax under djupnätets ruta (Regnaren: 4 m-nivån
  → 4,9 m), räknar om SWEREF 99 TM till kartbildens rutnät (Krügers formler) och sparar höjd över sjön (sjöns nivå =
  medianen över vattenrutorna). `py -3 -I tools/land_height.py check` jämför omräkningen med Lantmäteriets egna hörn.
- **Filer:** `docs/land/<id>_v1.txt` (samma format som djupfilen: byte = höjd / steg, 255 = sjö, packade rader, base64) och
  `lakes/<id>/land.json` (fil, storlek, steg, nivå, källa, vilket kartutsnitt). De ligger utanför `docs/lakes/<id>/`, som
  kart-chattens verktyg tömmer. `tools/build.py` bäddar in land.json som `LAKE.land`; gäller filen ett annat utsnitt
  hoppas den över med en varning, och marken är platt tills verktyget körts om. Ny data för en sjö som redan är ute: `V` + 1.
- **Rutor per sjö** (2026-11-11):

  | Sjö | Rutor | Läge |
  |---|---|---|
  | Regnaren | 652_54 | klar, 1,26 MB |
  | Sibbofjärden | 651_63, 652_63 | saknas |
  | Sjösjön | 693_64, 694_64 | saknas |
  | Vågsfjärden | 697_66, 698_66 | saknas |
  | Östra Vitten | 653_54, 654_54 | saknas |
  | Mälaren | 9 st (657–659 × 63–65) | saknas |
  | Gryts Skärgård | 9 st (643–645 × 59–61) | saknas |

  Sjö utan höjdfil = platt mark; vyn fungerar ändå.
- **Prövat och borttaget:**
  - Öppna 30 m-data (AWS Terrain Tiles, EU-DEM/SRTM): trädtopparna är med, så marken hoppade upp i taggar längs stranden.
  - Google: villkoren förbjuder att höjderna sparas, och appen ska fungera offline.

## Kvar och att tänka på
- Höjdfiler för övriga sex sjöar: 26 rutor, ca 7 GB att ladda ner till datorn. Appens filer blir ca 1 MB per sjö.
- iPhone-appen packar sjöfilerna i appen: app-chatten måste ta med mappen `land/`.
- Märkena syns genom kullar, eftersom de ligger ovanpå bilden.
- Inte i vyn: heatmap, Kartanalys, spår, väder, lodet, lägga eller ändra platser. Kartans färgreglage gäller inte heller där.
