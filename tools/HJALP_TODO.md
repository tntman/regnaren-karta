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

(inget just nu)

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
