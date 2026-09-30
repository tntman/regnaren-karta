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

**Senaste Hjälp-omgång:** 2026-09-30 (allt till och med Heatmap, Kartanalys Fångster, Filter/Inställningar
i avsnitt, Ångra, åskvarningen alltid + "dragit förbi", solnedgången, Täckning igen).

---

## Att göra

- [ ] 2026-09-30 – Kartanalys och Heatmap tightare: resultatet + ⓘ (förklaringar) + ↺ Återställ + ⏻ Stäng av i översta raden (inte längre längst ner), valen på en rad som skrollar i sidled, lägre knappar, två reglage sida vid sida. Hjälp: Kartanalys + Heatmap (texten "Längst ner: Stäng av … Återställ" → översta raden + ⓘ) + animeringarna `analys` och `heatmap` spelas in igen. Nyhet: "Kartanalys och Heatmap tar mindre plats – förklaringarna bakom ⓘ" (BÄTTRE)

<!-- mall:
- [ ] ÅÅÅÅ-MM-DD – Vad som ändrats. Hjälp: avsnitt X (text) + animering `namn`. Nyhet: "…" (NYTT/BÄTTRE/FIXAT)
-->

---

## Klart

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
