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

**Senaste Hjälp-omgång:** 2026-09-29 (allt till och med gemensam meddelandebubbla, mjuka
kanter, Djup/Andras till Inställningar, panorera över markeringar).

---

## Att göra

- [ ] 2026-09-29 – Vind och lä: lä är nu blått och tydligare, starkast vid kanten; snabbare panorering på dator. Hjälp: Väder, vind & lä (text: "den ljusa ytan" → "den blå ytan") + animering `vader`. Nyhet: "Tydligare lä-område, mjukare kanter i Kartanalys när man panorerar" (BÄTTRE)
- [ ] 2026-09-29 – Rättat: efter vridning av telefonen kunde knapparna vara "förskjutna" och lä försvinna; statusraden i hemskärmsappen är appens blå, samma som bakgrunden (ingen kant). Hjälp: – . Nyhet: "Vridning av telefonen fungerar bättre" (FIXAT)
- [ ] 2026-09-30 – NYTT: Heatmap över tävlingarnas fångster (Kartlägen → Heatmap): Värme / Per art / Rutor / Prickar, art- och tävlingsfilter, tryck på en fångst (vem, när, djup, placering, Åk hit, Liknande), "Heatmap"-skylt under väder. Hjälp: nytt avsnitt "Heatmap" (+ i Kartlägen) + ny animering `heatmap` (help_anim.py behöver låtsasfångster) + Inställningar/Admin nämner inte (admin står inte i Hjälp). Nyhet: "<b>Heatmap</b> – var fisken tagits i tävlingarna" (NYTT)
- [ ] 2026-09-30 – NYTT: Kartanalys "Från fångsterna (data)" per art: tänder det som liknar där arten togs (datan bestämmer ytan, "Typiskt" 5–9 av 10), Tänt/Skala, av/på per värde med prickar för hur mycket det betyder. Hjälp: Kartanalys (text) + animering `analys`. Nyhet: "Kartanalys per art från tävlingarnas fångster" (NYTT)
- [ ] 2026-09-30 – Kartanalys-rutan ny design: kategorirad (Kartdata / Tumregler / Fångster / Liknande), "Stäng av kartanalys" och "Återställ" längst ner (ersätter "Rensa"); tumreglerna vanliga knappar. Heatmap: "Återställ" + sjöns vita kantlinje. Hjälp: Kartanalys (texten om Rensa, hur man väljer) + animering `analys`. Nyhet: "Ny ordning i Kartanalys: välj kategori först; Återställ i Kartanalys och Heatmap" (BÄTTRE)
- [ ] 2026-09-30 – Säkerhet: åskvarningen gäller alltid (även med Blixtar av i Filter), "Åskvarning av"-skylt när den stängts av, större "OK, jag har sett". Ta bort = papperskorg till vänster + "Ångra" i 6 s. Hjälp: Blixtar (texten om Filter/varningen), Fiskeplatser (Ta bort/Ångra) + animering `andra`. Nyhet: "Åskvarningen gäller alltid; Ångra när man tar bort en plats" (BÄTTRE)
- [ ] 2026-09-30 – Filter i två grupper: "Markeringar" (typerna som en rad prickar) och "Lager" (+ Heatmap av/på); "Håll skärmen tänd" flyttad till Inställningar → Båten. Inställningar i avsnitt (Kartan, Båten, Varningar, Kartanalys, Offline, Avancerat) med en rad om vad som är valt. Heatmap egen färgskala "glöd". Skylten "Kartanalys" under vädret när ett läge är på. Hjälp: Filter (text + animering `filter`: typerna är prickar), Inställningar (text + animering `installningar`: öppna Kartan först), Skärmen tänd (var den finns), Heatmap (färgerna), Kartanalys (skylten). Nyhet: "Enklare Filter och Inställningar; Kartanalys-skylt under vädret" (BÄTTRE)
- [ ] 2026-09-30 – Väderkortet stängs med ett tryck på kartan (inte när man drar). Hjälp: Väder (text "stäng med ✕" → "tryck på kartan eller ✕"). Nyhet: "Vädret stängs när du trycker på kartan" (BÄTTRE)

<!-- mall:
- [ ] ÅÅÅÅ-MM-DD – Vad som ändrats. Hjälp: avsnitt X (text) + animering `namn`. Nyhet: "…" (NYTT/BÄTTRE/FIXAT)
-->

---

## Klart

- 2026-09-29 – Hjälp-omgång 2 (14 rader): rutorna nertill (strecket, ✕, knappraden, faktarutor), Kartanalys
  (grynnor, hålor = gropen, sjöns kant, mjuka kanter, Rensa, av vid start), egen text + gemensam
  meddelandebubbla, lodet "fågelvägen", Åk hit visar hela vägen, Djup/Andras i Inställningar, dra kartan
  över markeringar. 8 nya nyhetsrader, gamla "toppar" → "grynnor". Animeringar inspelade igen: `platser`,
  `andra`, `fara`, `vader`, `filter`, `installningar`, `analys`, `akhit`, `meddelanden`.

- 2026-09-29 – Hela Hjälp gjord och uppdaterad (20 avsnitt, 18 animeringar, sök).
