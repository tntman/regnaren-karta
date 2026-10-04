# Snabbmeddelanden

Kod: `src/js/64-messages.js`, CSS i `src/css/75-messages.css`. Test: `tests/test_extras.py`.

- `#msgBtn` längst ner i mitten: Fisk!!!, Kommer, Åker in, Mat?, Bajs + **Egen text**
  (regnbåge som glider genom texten `.rbText`, pennan efter; liten ruta `#msgOwn`, max 15 tecken
  räknat med Array.from – en emoji = 1, räknaren "n/15", Enter/➤ skickar, tryck utanför = stäng).
- Skickas med din position (`positions/<du>.msg/msgAt`), bara vid sjön. Bubbla vid båten 7 min
  (`MSG_MS`), tonas till ~45 %. Liten bubbla (12 px) med tunn enfärgad ram (ingen regnbågskant sedan 2026-10-04).
- **Text och namn turas om** (`.mWin`, 10 s per varv): texten står ~6 s, glider åt höger ut, "Calle…" (`.mN`) glider in från vänster
  ~2,4 s, och tillbaka. Fisk = artens färg sveper genom texten (`.mT.sp`, `--sp`), Egen text = regnbåge (`.mT.rbText`),
  färdiga val svarta. Egen bubbla ljusgul men samma regler.
- **Flera i samma båt** (< `BOAT_CLUSTER_METERS`): EN bubbla (`.msgBub.multi`), en rad per person
  (`.mLine`, egen `data-k`), nyast överst, äldre rader blekare; egen rad ljusgul.
- Tryck på en rad = rutan `#msgCard` (skrivet kl, försvinner om, Åk hit = lodet på båten, Dölj för
  mig / Ta bort (för alla) för egna).
- `window.__ffMsgs()` för testerna: raderna `{k, t, bubble, o}`.

## Din senaste fisk som meddelande (2026-10-03)
Under en pågående tävling ligger din senaste godkända live-fångst först i valen (`#msgFishBtn`, "Gädda 78 cm · 14:32"),
skickas för hand. Positionen får `msgSp` (art → kantens färg: gädda #35D24A, abborre #FF7A1A, gös #3A86FF) och `msgImg`
(fotot, visas i `#msgCard` – bara `res.cloudinary.com`-adresser). Namnet i rutan öppnar profilen (`js/67-profiles.js`).
