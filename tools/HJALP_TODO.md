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

**Senaste Hjälp-omgång:** 2026-09-29 (allt till och med Toppar via prominens, nya
snabbmeddelanden, Hem-plats, Liknande förtydligad).

---

## Att göra

- [ ] 2026-09-29 – Rutor nertill: en greppremsa överst (strecket) – dra den för att ändra storlek, snärta för att stänga; inne i rutan skrollar man. Hjälp: Kartanalys (sista punkten) + ev. Fiskeplatser. Nyhet: "Rutorna nertill: dra i strecket överst för att ändra storlek" (BÄTTRE)
- [ ] 2026-09-29 – Platsens ruta: rutorna bara rubrik + värde, ingen terräng-rad, "Sparad av **namn**" i fetstil. Kartanalys: Rensa grå utan val, tydlig med ljussvep när något är valt. Hjälp: Fiskeplatser (texten om vad rutan visar) + animeringar `platser`, `andra`. Nyhet: ingår i "Ny design på rutorna".
- [ ] 2026-09-29 – Kartanalys: hålor visas bara med gropens djupaste 0,6 m (inte hela djupbassänger); sjöns kontur streckad vit; förklaring av grynna/håla i rutan. Hjälp: Kartanalys (text) + animering `analys`. Nyhet: "Hålor visar bara själva gropen, sjöns kant syns i Kartanalys" (BÄTTRE)
- [ ] 2026-09-29 – Snabbmeddelanden: "Allt är problem" → "Egen text" (regnbåge + penna, egen text max 15 tecken). Hjälp: Snabbmeddelanden (text, valen) + animering `meddelanden`. Nyhet: "Snabbmeddelanden: skriv en egen text (15 tecken)" (NYTT)
- [ ] 2026-09-29 – "Toppar" heter nu "Grynnor" överallt i appen. Hjälp: Kartanalys, Fiskeplatser, Liknande-texter och gamla nyhetsrader som säger "toppar". Nyhet: – (ingår i Kartanalys-raden)
- [ ] 2026-09-29 – Rutornas överdel: ✕ i greppremsan (ingen Avbryt, ingen rubrik i Kartanalys), remsan lyser blått när man håller i den. Platsens ruta: typpiller, en knapprad Åk hit / Liknande / Ta bort / Spara; andras plats visar typen som mini-pill. Hjälp: Fiskeplatser (text) + animeringar `platser`, `andra`, `fara`, `analys`, `akhit`, `meddelanden` (spelas in igen). Nyhet: "Ny design på rutorna nertill" (BÄTTRE)
- [ ] 2026-09-29 – Kartanalys: av när appen startas om (kvar vid vridning); "Rensa" efter en avskiljare. Hjälp: Kartanalys (text). Nyhet: "Kartanalys börjar avstängd" (BÄTTRE)
- [ ] 2026-09-29 – Rättat: vägen sjövägen nådde inte hela sjön (Åk hit gav bara djup + avstånd). Om ingen väg hittas: prickad linje "fågelvägen". Hjälp: Lodet (text). Nyhet: "Åk hit och lodet hittar vägen till hela sjön" (FIXAT)
- [ ] 2026-09-29 – Åk hit (från plats och Liknande) visar nu hela vägen – kartan zoomar så båten, rutten och målet syns. Hjälp: Åk hit + animering `akhit` (spelas in igen). Nyhet: "Åk hit visar hela vägen på kartan" (BÄTTRE)

<!-- mall:
- [ ] ÅÅÅÅ-MM-DD – Vad som ändrats. Hjälp: avsnitt X (text) + animering `namn`. Nyhet: "…" (NYTT/BÄTTRE/FIXAT)
-->

---

## Klart

- 2026-09-29 – Hela Hjälp gjord och uppdaterad (20 avsnitt, 18 animeringar, sök).
