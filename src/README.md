# src/ – appens källkod

`py -3 tools/build.py` klistrar ihop allt till **en** sida, `docs/index.html` (det som publiceras):

```
head.html  +  <style> css/*.css </style>  +  html/*.html  +  <script> js/*.js </script>
```

Filerna i varje mapp tas i **namnordning** (siffrorna först styr). Ny del mellan två befintliga:
välj ett ledigt nummer emellan, t.ex. `55-…`.

**Viktigt om js/:** alla filerna blir ETT skript i EN funktion – `(function(){ "use strict";` står
överst i `10-core.js` och `})();` sist i `92-rotation.js`. Filerna är alltså inte fristående:
variabler och funktioner syns i alla filer, och kod som körs direkt (inte i en funktion) körs i
filordning. `var` som deklareras i en senare fil finns (hoisting) men är `undefined` tills den
filen körts – sätt sådant i `boot()` (90-boot.js). Samma sak för CSS: senare filer vinner vid lika
specificitet.

| Mapp/fil | Innehåll |
|---|---|
| `head.html` | `<head>`: titel, ikoner, manifest, Firebase-SDK, statusrad (iOS) |
| `sw.js` | service worker (kopieras som den är) |
| **css/** | |
| `10-base.css` | färger (`:root`), layout, kartan, rubriken, din pil, skala/zoom |
| `20-map-tools.css` | knopmätare, mätverktyg, lodet, rutten (+ "fågelvägen"), spår |
| `30-controls.css` | Filter, kartlägesknapp, knappar, meny, Inställningar, GPS-rad, liggande läge |
| `40-spots-boats.css` | platstyper (Fara, Träffpunkt, Hem …), andras platser, båtar, platsens ruta (+ faktarutorna) |
| `50-weather-settings.css` | väder, blixtvarning/radar, kartstil, offline, admin, fart, åsklarm, håll skärmen tänd (solen, notisen) |
| `60-help.css` | Hjälp (+ sökrutan) |
| `70-analysis.css` | Kartanalys och Liknande |
| `72-heatmap.css` | Heatmap: lagren, skylten under väder, bottenrutan, fångstrutan |
| `73-names.css` | Namn: OSM-namnen på kartan (vit prick + text) |
| `75-messages.css` | snabbmeddelanden (knappen, valen, egen text, bubblorna, rutan) |
| `80-panels.css` | bottenpanelerna: greppremsan, dra mindre / skrolla (Kartanalys, meddelande, plats) |
| `85-touch.css` | stora tryckytor i bottenrutorna (blöta fingrar): chips 40, kategorirad 42, knapprader 46 px – kartans egna knappar orörda; läsbar småtext i rutorna (≥ 11 px), Inställningar som spalt på bred skärm, fokusring, "Reducera rörelse" för panelernas rörelser |
| `90-buttons.css` | de fyra knapparna nere till höger i 2 × 2 (sist: bestämmer storlek/plats över allt ovan) |
| **html/** | |
| `10-map.html` | `#app`, kartan och lagren (`#stage`, platser, båtar, bubblor, lodet, heatmap) |
| `20-menu-settings.html` | menyknapp, meny, Logg, Inställningar, Admin, PIN |
| `30-map-ui.html` | rubrik, väderkort, mätpanel, knappar, meddelanden, Kartanalys-panel, Heatmap-rutorna, Filter, radar |
| `40-help.html` | Hjälp-sidan (bildstorlekarna skrivs av `tools/help_anim.py`) |
| `50-sheets.html` | platsens ruta, namnrutan, båtinfo |
| **js/** | |
| `10-core.js` | start på skriptet, sjöar (`LAKES`), geo-referens, `MAX_ZOOM` |
| `12-map.js` | panorera/zooma, lodet, zoomnivåer (detaljbitar), fingrar/mus (`mapPointerDown`) |
| `14-spots.js` | fiskeplatser (pinnar) |
| `16-map-settings.js` | platsstorlek, kartstil, kartlägesknappen |
| `18-offline.js` | ladda ner sjön för offline |
| `20-map-look.js` | kartans färg, pulserande ring |
| `22-filter.js` | Filter |
| `24-boats.js` | båtarna (andras positioner), platsens ruta öppna/spara |
| `26-sync.js` | dra-för-att-stänga platsens ruta, offline-rad, Firebase-räkning, `config/<lake>` |
| `28-menu.js` | meny, byta sjö |
| `30-help.js` | Hjälp, `HELP_NEWS` |
| `32-demo.js` | Demo Mode |
| `33-avatars.js` | profilbilderna (`AVATARS`, genereras av `tools/make_avatars.py` ur `tools/fiskare/`) |
| `34-name.js` | ditt namn, profilbild på menyknappen, "Logga ut" i menyn |
| `36-admin.js` | admin, export (GPX/CSV) |
| `38-speed-depth.js` | fart, riktningspilen, djup |
| `40-route.js` | rutten sjövägen, snittfart |
| `42-measure.js` | mätverktyget |
| `44-demo-motion.js` | demo: simulerad rörelse |
| `46-gps-track.js` | GPS, spår, tillbaka till appen |
| `48-weather.js` | väder (Open-Meteo) |
| `50-wind-lee.js` | vind och lä (`viewStep`, `drawLeeView`) |
| `52-lightning.js` | blixtar (FMI) |
| `53-compass.js` | Kompass: kil mot dit telefonen pekar (Filter → Lager) |
| `54-panels.js` | bottenpaneler (`sheetSwipe`) |
| `56-analysis.js` | Kartanalys |
| `57-an-catches.js` | Kartanalys "Från fångsterna (data)": per art ur tävlingarnas fångster |
| `58-akhit-spotdata.js` | Åk hit, vad som finns under en plats |
| `59-names.js` | Namn (Filter → Lager): OSM-namn ur `LAKE.names`, avlusning, av som standard |
| `60-lightning-alarm.js` | åskvarning |
| `62-wakelock.js` | håll skärmen tänd |
| `64-messages.js` | snabbmeddelanden |
| `66-catches.js` | fångsterna: format, källa (Firestore `catches/<lake>`), admins CSV-inläsning |
| `68-heatmap.js` | Heatmap: ritning (värme, per art, rutor, prickar), bottenrutan, fångstrutan, tryck på kartan |
| `90-boot.js` | start (`boot()`) |
| `92-rotation.js` | vridning: spara/återställ läget, service worker-registrering, slutet på skriptet |

## Krokar för appen (får inte tas bort)

Grenen `app` (mappen `E:\github\ffmap-app`, "FF Map - app" i GitHub Desktop) gör webbappen till en riktig
iPhone/Android-app med Capacitor. Dess kod ligger i `src/js/11-native.js` (bara på grenen `app`) och byter ut
de här krokarna. På webben gör de ingenting – men **ta inte bort dem och gå inte förbi dem**, annars slutar
appen fungera när `main` förs över till `app`.

| Krok | Fil | Vad |
|---|---|---|
| `lakeUrl(p)` | `10-core.js` | varje sjöfil laddas genom den: `mapFile()`/`thumbFile()`, detaljbitarna, djup- och bottendata, offline-listan |
| `lakeImgError(el)` | `10-core.js` | anropas först när en kartbild/detaljbit inte laddas; `true` = appen tog hand om det |
| `offStore` | `18-offline.js` | offline-lagringen (`available`, `has`, `size`, `put`, `clear`) – här Cache API |
| `writeOwnPosition(data)` | `24-boats.js` | skriver din egen position (merge) – appens bakgrunds-GPS skriver också genom den |
