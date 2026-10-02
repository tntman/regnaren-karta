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
- [ ] 2026-09-30 – NY SJÖ: Sibbofjärden i menyn. Hjälp: Kartan (texten "Byt sjö i menyn ☰ (Regnaren, Sjösjön, Vågsfjärden)" → lägg till Sibbofjärden). Nyhet: "Ny sjö: <b>Sibbofjärden</b>" (NYTT)
- [ ] 2026-10-01 – Gös är blå och Hem brun överallt (pinnar, typknappar, Filter-prickar, Kartanalys, Heatmap). Hjälp: Fiskeplatser (texten "Hem (blått hus …)" → "brunt hus") + animeringar med gös/hem (`platser`, `andra`, `filter`, `logg`, `heatmap`, `analys`). Nyhet: "Gös är blå och Hem brun" (BÄTTRE)
- [ ] 2026-10-01 – Ny ikon för Kartanalys: karta med lupp (knappen nere till höger, skylten, Filter). Hjälp: Kartanalys (texten "förstoringsglaset nere till höger" → "kartan med luppen") + animeringar där knappen syns (spela in alla). Nyhet: "Ny ikon för Kartanalys" (BÄTTRE)
- [ ] 2026-10-01 – Tryck på lodets ruta = sätt en markering där (ljus sveper över rutan); zoomtexten "15,3 × L 14". Hjälp: Lodet (ny rad: "tryck på rutan för att sätta en markering där") + Kartan ("Zoom 15,3 lager 15" → "15,3 × L 15") + animering `lodet`. Nyhet: "Tryck på lodets ruta för att sätta en markering där" (NYTT)
- [ ] 2026-10-01 – NYTT: Kombinera i Kartdata – knapparna slås på/av, fler = där alla stämmer (växter, hård botten, grynnor, vindkant "inom … m"); "Inget kvar – …" säger vad som tar bort sista; ⓘ visar stegen. Hjälp: Kartanalys (ny rad om att kombinera; "Branta kanter – valfritt djup" och "Hård botten – välj hur hård och på vilket djup" stämmer inte längre: djupet ställs bara med Djup) + animering `analys`. Nyhet: "Kombinera i Kartanalys: djup + branta kanter + hård botten …" (NYTT)

- [ ] 2026-10-02 – Kartdata-lägena har ingen egen färg längre: området är bara kartan under, resten grått (kombinerat = en gemensam mask). Hjälp: Kartanalys (texter som nämner färgade områden, t.ex. "lyser rosa/gult/grönt") + animering `analys`. Nyhet: "Kartanalys visar den vanliga kartan i det som stämmer – inga färger" (BÄTTRE)
- [ ] 2026-10-02 – NYTT: Heatmap "När" – stapel per timme på dygnet, "Bäst kl 06–09", tryck/dra = tidsfönster som filtrerar kartan (↺ återställer). Hjälp: Heatmap (ny rad) + animering `heatmap`. Nyhet: "Heatmap: se när det nappar bäst – tryck på en timme" (NYTT)
- [ ] 2026-10-02 – Snabbmeddelande: efter skickat visas notisen "Syns i 15 minuter, tryck på meddelandet för att ta bort" och kartan centreras på dig. Hjälp: Snabbmeddelanden + animering `meddelanden`. Nyhet: "Snabbmeddelanden: kartan centreras på dig och en notis säger hur länge det syns" (BÄTTRE)

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
