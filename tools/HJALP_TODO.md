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

**Senaste Hjälp-omgång:** 2026-11-08 (omgång 7: Sjö och Tävling, Hotzone 50 m, GPS-knappen, Mörk karta).
Föregående: 2026-10-29 (omgång 6: PB, Under ytan, GPS-knappen följer).
Innan dess: 2026-10-08 (omgång 5: Kartanalys Skala/Fiska nu, låset → påminnelse, Hotzone, Loggens filter).
Innan dess: 2026-10-06 (omgång 4: allt sedan 2026-09-30 – ny design, Kom igång, Tävlingarna, profiler,
spåren, Ledare, Kompass, Namn, Fog of war, tävlingslåset, Storlek/När, startfilmen, Mälaren och Östra Vitten m.m.).

---

## Att göra

<!-- mall:
- [ ] ÅÅÅÅ-MM-DD – Vad som ändrats. Hjälp: avsnitt X (text) + animering `namn`. Nyhet: "…" (NYTT/BÄTTRE/FIXAT)
-->
- [ ] 2026-11-08 – Ny sjö: Gryts Skärgård (Valdemarsviken ut till Flisdjupet). Bara Djupfärger; djup bara i en liten Genesis-remsa,
  flygfoto i övrigt. Hjälp: avsnittet om sjöar/kartlägen (att en sjö kan ha färre kartlägen och sakna djup där inget är lodat).
- [ ] 2026-11-09 – Tävlingens namn i liten text under sjönamnet uppe till vänster (pågående tävling, tryck = Välj tävling). Hjälp: Kartan /
  Tävlingarna (text). Nyhet: "Pågående tävling syns under sjöns namn – tryck för att byta" (NYTT)
- [ ] 2026-11-09 – Sjö och Tävling går tillbaka till Automatiskt varje ny dag. Hjälp: Kartan (Sjö) / Tävlingarna (Tävling-raden).
  Nyhet: "Valt sjö eller tävling själv? Nästa dag väljer appen automatiskt igen" (BÄTTRE)
  Nyhet: "Ny karta: Gryts Skärgård – Valdemarsviken ut till Flisdjupet, med djupfärger i hela skärgården" (NYTT)
- [ ] 2026-11-11 – Regnaren och Mälaren: djupfärger i nästan hela sjön – Filips egen loggning fyller där Genesis saknar djup (Genesis
  överst, kurvorna bara från Genesis). Hjälp: Kartan (var djupet kommer ifrån). Nyhet: "Regnaren och Mälaren har nu djupfärger i nästan hela sjön" (BÄTTRE)
- [ ] 2026-11-11 – Nytt kartläge: 3D-karta (håll kartknappen → 3D-karta). Botten och marken runt sjön i 3D med kartbilden på, skarp på nära håll.
  Ett finger flyttar kartan, nyp zoomar, vrid med två fingrar vrider, två fingrar upp/ner lutar (som i Google Maps); Höjd ×, Vatten, Till mig, norrpil. Marken har riktiga höjder på alla sjöar (Lantmäteriet).
  Där djup saknas (olodat, eller utanför sjökortet) är det hål i botten – bara vattenytan syns (2026-11-12).
  Knappen Djupfärg: botten i färger efter djupet. Knappen Skuggor: kastade skuggor. Märkena i 3D med spegelbild och linje
  till botten, spåren, knappen Fångster (prickar), knappen Kompass (ros + kil, pilen vrids dit telefonen pekar). På datorn: Alt + mus som i Maya/Houdini (2026-11-12).
  Hjälp: nytt avsnitt vid kartlägena + animering `map3d`.
  Nyhet: "Ny 3D-karta: se botten och marken runt sjön i 3D – håll kartknappen" (NYTT)

---

## Klart

- 2026-11-08 – Hjälp-omgång 7 (3 rader): Sjö och Tävling i menyn (Kom igång, Kartan, Tävlingarna), GPS-knappen vit/orange
  (Din position), Hotzone 50 m / 30 min (Tävlingarna), Heatmap 🌙 Mörk karta, PB-meddelanden 14 min, Platsnamn (Kartan, Filter).
  5 nyhetsrader. Alla 21 animeringar inspelade igen (GPS-knappen vit i alla; Hotzone-ringen mindre, Filter "Platsnamn", Heatmap-månen).

- 2026-10-29 – Hjälp-omgång 6 (3 rader): PB (Tävlingarna + Snabbmeddelanden), Under ytan (Kartlägen + Demo Mode, ny animering
  `underytan`), GPS-knappen följer båten (Din position, animeringen `position` inspelad igen). 4 nyhetsrader.

- 2026-10-08 – Hjälp-omgång 5 (7 rader): Kartanalys (ingen färgning – kartan syns där det stämmer, **Skala** i alla flikar,
  ny flik **Fiska nu**, Fångster utan Tänt/Skala, Mälaren räknas i 20 m-rutor); tävlingslåset borta → påminnelsen (Demo
  Mode-rutan, Fiskeplatser, Tävlingarna, Tips); **Hotzone** (Tävlingarna + Filter, ny animering `hotzone` – nu 20);
  Loggens filter (Spår & loggen). 7 nyhetsrader. Inspelade igen: `analys` (Skala, Fiska nu), `logg` (filtret), `filter`.

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
