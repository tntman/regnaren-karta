# Väder, vind och lä, blixtar, åskvarning

Kod: `src/js/48-weather.js`, `50-wind-lee.js`, `52-lightning.js`, `60-lightning-alarm.js`.
Tester: `test_weather.py`, `test_wind.py`, `test_lightning.py`, `test_extras.py` (åsklarm).

## Väder
Open-Meteo (ingen nyckel), cache 30 min, lagras lokalt. Vindpilen i väderkortet/-chipet är
orange (#FFB23F).

## Vind och lä
- Filter, av som standard (`ffmap_show_wind_v1`). Canvas `#windLayer` i skärmkoordinater.
- Fetch (öppet vatten uppvinds, ±15°) på ruttnätet, interpolerat till djupnätet och utjämnat ~10 m.
- Lä = fetch < gräns = 3600/U² (vågformel, kalibrerad efter Filip: 6 m/s → 100 m; "5 cm-vågor"
  var för generöst), 30–400 m; < 1,5 m/s = hela sjön lä.
- Ritas per skärmpunkt (`drawLeeView`) – inte som förstorad bild, som blev kantig inzoomat.
  Steg `viewStep()`: 1 css-px stilla, 2 vid dragning; större skärm grövre så en dator aldrig
  räknar mer än ~90 000 punkter vid dragning / ~700 000 stilla (desktop blev seg). Görs om
  bara när vyn flyttas. Kanten kantutjämnad (lä-värde / lutning = avstånd till kanten).
  Ritningen får aldrig stanna: kartan kan vara 0 px mitt i en vridning (då ritas inget), och ett
  fel i en bildruta stoppar inte loopen (lä försvann annars efter vridning).
- Utseende: blå ton (170,215,255), starkast vid kanten och tonar inåt (~22 px, täckning 85–170/255)
  + tunn vit kant. (Streck i vindens riktning provades 2026-09-29 och togs bort igen.) Öppet vatten: "kometer" (tunt
  huvud, tjockare svans) som driver med vinden, fler/längre/snabbare vid mer vind. ~30 fps bara
  när påslaget och synligt.
- `window.__ffWind()`, `window.__ffViewStep(W, H, drag)` för testerna.

## Blixtar
- Filter, PÅ som standard (Filips val; `ffmap_show_lightning_v1` = '0' när avslaget).
- FMI (Finlands meteorologiska institut, öppen data, täcker Sverige, ingen nyckel, CC BY 4.0,
  några min fördröjning), WFS `fmi::observations::lightning::simple`, ~40 km runt sjön, senaste
  30 min, hämtas var 2:a min när påslaget och synligt (inte via Firebase).
- Varning `#ltPill` under väderchipet (närmaste inom 30 km, orange, röd < 10 km), radar `#ltRadar`
  under Filter (30 km, norr upp), ⚡ på canvas `#ltLayer` (gul 0–5 min, orange 5–15, grå/bleknar
  till 30; nya blinkar), markör vid skärmkanten mot närmaste när den är utanför bild.
- Avstånd från dig om du är vid sjön, annars från sjöns mitt. Inget visas när det är lugnt.
- `window.__ffLightning()` för testerna; fakefb blockerar opendata.fmi.fi i alla tester
  (test_lightning har egen låtsas-XML).

## Åskvarning
Inställningar: Av/5/10/20 km, ljud, vibration; standard 10 km. Nytt nedslag < 5 min och inom
avståndet → `#ltAlarm` + pip (WebAudio, låses upp vid första tryck) + vibration (finns inte på
iPhone). Varje nedslag larmar en gång.
