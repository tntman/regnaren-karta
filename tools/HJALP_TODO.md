# Hjälp – att uppdatera

Hjälp (texter, "Nytt i appen", animeringar) uppdateras **inte** vid varje ändring i appen.
I stället skrivs det som behöver ändras upp här, och Filip väljer när allt tas i en omgång
(se `tools/HJALP.md` för hur Hjälp görs).

**Regler**
- Ändras något som syns för användaren (ny funktion, ändrat utseende, flyttad knapp, ny text
  i appen): lägg till en rad under "Att göra" – vad, var i Hjälp (avsnitt / animering) och en
  föreslagen nyhetsrad till "Nytt i appen".
- Påminn Filip om att köra en Hjälp-omgång när listan har **5 rader eller fler**, eller när den
  äldsta raden är **mer än en vecka** gammal.
- Vid en Hjälp-omgång: gör allt i listan (texter, `HELP_NEWS`, animeringar som påverkas –
  `py -3 tools/help_anim.py <namn>`, bygg, testa), flytta raderna till "Klart" med datum.

**Senaste Hjälp-omgång:** 2026-10-06 (omgång 4: allt sedan 2026-09-30 – ny design, Kom igång, Tävlingarna, profiler,
spåren, Ledare, Kompass, Namn, Fog of war, tävlingslåset, Storlek/När, startfilmen, Mälaren och Östra Vitten m.m.).

---

## Att göra

- [ ] 2026-10-06 – Kartanalys färgar inte kartan: Tumregler, Liknande och Fångster "Tänt" visar bara kartan genom masken,
  som Kartdata (bara Fångster "Skala" har kvar sin färgskala). Hjälp: Kartanalys (Kartdata-radens "den vanliga kartan syns
  där det stämmer" gäller nu alla utom Skala) + animering `analys` (Tumregler Gös visas i blått). Nyhet: "Kartanalys färgar
  inte kartan – det som stämmer syns som vanligt, resten tonas ner" (BÄTTRE)

- [ ] 2026-10-06 – Kartanalys Fångster "Skala" filtreras också med Likhet: bara den yta Likhet tänder får färg (från likt
  till mest likt), resten tonas ner. Hjälp: Kartanalys, Fångster-raden ("Skala (hela sjön, starkast där det är mest likt)" →
  "Skala (samma yta i färg, starkast där det är mest likt)"). Nyhet: hör till raden ovan.

<!-- mall:
- [ ] ÅÅÅÅ-MM-DD – Vad som ändrats. Hjälp: avsnitt X (text) + animering `namn`. Nyhet: "…" (NYTT/BÄTTRE/FIXAT)
-->

---

## Klart

- 2026-10-06 – Hjälp-omgång 4 (≈ 40 rader sedan 2026-09-30): två nya avsnitt utan animering, **Kom igång** (Vem är du?,
  startfilmen, välkomstrutan, menyn med din bild) och **Tävlingarna** (tävlingslåset, live-fångster, Ledare, senaste fisk,
  Demo Mode); Båtarna → **Båtarna och profilerna**; Loggen & spår → **Spåren och loggen** (sparas för evigt, bara på vattnet,
  spårmenyn, Fog of war). Texter: Kartan (sjöarna, zoom 18 i alla lägen, "15,3 × L 15", strandlinje, Namn), Kartlägen (7,
  "Flygfoto + linjer" borta, heatmapknappen), Position (Kompass), Lodet (tryck på rutan = markering), Fiskeplatser (färgerna,
  Gös blå, Hem brun, Klar, låset, egna öppnas utan tangentbord), Kartanalys (flikar som minns, Kartdata kombinerat utan
  färg, Lutning över, Likhet/Storlek, 💡, ↺ allt), Heatmap (knappen, Storlek, När, live, Fångstdata), Snabbmeddelanden (7 min,
  färg 3 min, senaste fisk), Filter (Fog of war, Ledare, Namn, Kompass, Spår-ikonen), Inställningar (profilkortet,
  kompassen, platsnamnen, strandlinje, Fångstdata, Avancerat), Tips (låset, ny ikon), Om appen (Fiskfiskarna), Demo-rutan.
  33 nyhetsrader. Inställningar: "gul sol under vädret" (stod "vid ditt namn"). Den ritade Safari-telefonen visar
  karta.fiskfiskarna.se. Alla 19 animeringar inspelade igen i design A (`lodet`, `analys`, `heatmap`, `logg` med nya
  scener); help_anim.py hämtar fångsterna via fakefb:s Fiskfiskarna-API.

- 2026-09-30 – Hjälp-omgång 3 (11 rader): nytt avsnitt **Heatmap** (+ animering `heatmap`, låtsasfångster
  på vattnet), Kartanalys (kategorier, Fångster, Stäng av/Återställ, skylten), Blixtar (varningen alltid,
  Åskvarning av, dragit förbi), Fiskeplatser (papperskorgen + Ångra, nålen landar), Väder (blått lä, tryck
  på kartan stänger, solnedgång), Filter (Markeringar/Lager, prickar, Heatmap), Inställningar (avsnitten;
  Håll skärmen tänd flyttad dit – eget avsnitt borta), Tips (Täckning igen). 9 nyhetsrader. Animeringar
  inspelade igen: `kartlagen`, `platser`, `andra`, `vader`, `blixtar`, `filter`, `installningar`, `analys`.

- 2026-09-29 – Hjälp-omgång 2 (14 rader): rutorna nertill (strecket, ✕, knappraden, faktarutor), Kartanalys
  (grynnor, hålor = gropen, sjöns kant, mjuka kanter, Rensa, av vid start), egen text + gemensam
  meddelandebubbla, lodet "fågelvägen", Åk hit visar hela vägen, Djup/Andras i Inställningar, dra kartan
  över markeringar. 8 nya nyhetsrader, gamla "toppar" → "grynnor". Animeringar inspelade igen: `platser`,
  `andra`, `fara`, `vader`, `filter`, `installningar`, `analys`, `akhit`, `meddelanden`.

- 2026-09-29 – Hela Hjälp gjord och uppdaterad (20 avsnitt, 18 animeringar, sök).
