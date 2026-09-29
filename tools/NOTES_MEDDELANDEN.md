# Snabbmeddelanden

Kod: `src/js/64-messages.js`, CSS i `src/css/75-messages.css`. Test: `tests/test_extras.py`.

- `#msgBtn` längst ner i mitten: Fisk!!!, Kommer, Åker in, Mat?, Bajs + **Egen text**
  (regnbåge som glider genom texten `.rbText`, pennan efter; liten ruta `#msgOwn`, max 15 tecken
  räknat med Array.from – en emoji = 1, räknaren "n/15", Enter/➤ skickar, tryck utanför = stäng).
- Skickas med din position (`positions/<du>.msg/msgAt`), bara vid sjön. Bubbla vid båten 15 min
  (`MSG_MS`), tonas till ~45 %; de första 5 min (`MSG_NEW_MS`) en snurrande regnbågskant
  (`.msgRb`, SVG-mask av bubblans form inkl. flärpen – `msgRainbow`).
- **Flera i samma båt** (< `BOAT_CLUSTER_METERS`): EN bubbla (`.msgBub.multi`), en rad per person
  (`.mLine`, egen `data-k`), nyast överst, äldre rader blekare; egen rad ljusgul; regnbågskanten
  om någon rad är < 5 min.
- Tryck på en rad = rutan `#msgCard` (skrivet kl, försvinner om, Åk hit = lodet på båten, Dölj för
  mig / Ta bort (för alla) för egna).
- `window.__ffMsgs()` för testerna: raderna `{k, t, bubble, o}`.
