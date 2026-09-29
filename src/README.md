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
| `20-map-tools.css` | knopmätare, mätverktyg, lodet, rutten, spår |
| `30-controls.css` | Filter, kartlägesknapp, knappar, meny, Inställningar, GPS-rad, liggande läge |
| `40-spots-boats.css` | platstyper (Fara, Träffpunkt, Hem …), andras platser, båtar, platsens ruta |
| `50-weather-settings.css` | väder, blixtvarning/radar, kartstil, offline, admin, fart |
| `60-help.css` | Hjälp |
| `70-features.css` | senare tillägg: Kartanalys, meddelanden, åsklarm, sol, 2×2-knappar, Liknande, hjälpsök, greppremsan |
| **html/** | |
| `10-map.html` | `#app`, kartan och lagren (`#stage`, platser, båtar, bubblor, lodet) |
| `20-menu-settings.html` | menyknapp, meny, Logg, Inställningar, Admin, PIN |
| `30-map-ui.html` | rubrik, väderkort, mätpanel, knappar, meddelanden, Kartanalys-panel, Filter, radar |
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
| `34-name.js` | ditt namn |
| `36-admin.js` | admin, export (GPX/CSV) |
| `38-speed-depth.js` | fart, riktningspilen, djup |
| `40-route.js` | rutten sjövägen, snittfart |
| `42-measure.js` | mätverktyget |
| `44-demo-motion.js` | demo: simulerad rörelse |
| `46-gps-track.js` | GPS, spår, tillbaka till appen |
| `48-weather.js` | väder (Open-Meteo) |
| `50-wind-lee.js` | vind och lä (`viewStep`, `drawLeeView`) |
| `52-lightning.js` | blixtar (FMI) |
| `54-panels.js` | bottenpaneler (`sheetSwipe`) |
| `56-analysis.js` | Kartanalys |
| `58-akhit-spotdata.js` | Åk hit, vad som finns under en plats |
| `60-lightning-alarm.js` | åskvarning |
| `62-wakelock.js` | håll skärmen tänd |
| `64-messages.js` | snabbmeddelanden |
| `90-boot.js` | start (`boot()`) |
| `92-rotation.js` | vridning: spara/återställ läget, service worker-registrering, slutet på skriptet |
