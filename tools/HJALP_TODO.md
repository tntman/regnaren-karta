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
- [ ] 2026-10-03 – Spår sparas bara på vattnet (inte promenader/bilresor nära sjön). Hjälp: Spår (ny rad "bara på sjön sparas"). Nyhet: "Spåret sparas bara när du är på vattnet" (FIXAT)
- [ ] 2026-10-03 – NYTT: Profiler – tryck på en båt (eller Vem i en fångst, namnet i ett meddelande, Profil i menyn) = fiskarens ruta: rank, ELO, segrar, största fisk, senaste tävlingar, Visa på kartan, Fångster (heatmapen med bara personens fångster). Hjälp: ny rad under Båtar + Menyn. Nyhet: "Tryck på en båt för fiskarens profil" (NYTT)
- [ ] 2026-10-03 – NYTT: Under tävling ligger din senaste fisk först i snabbmeddelandena ("Gädda 78 cm · 14:32"), skickas för hand, kanten snurrar i artens färg; fotot syns i meddelandets ruta. Hjälp: Snabbmeddelanden + animering `meddelanden`. Nyhet: "Skicka din senaste fisk som snabbmeddelande – med foto" (NYTT)
- [ ] 2026-10-03 – Vem är du? – ny startskärm med loggan och profilbilderna (tryck på dig själv, "Fortsätt som …"). Hjälp: ev. ny bild i första välkomsten / avsnittet om namnet. Nyhet: "Nytt utseende när du väljer namn – hitta dig själv på bilden" (BÄTTRE)

<!-- mall:
- [ ] ÅÅÅÅ-MM-DD – Vad som ändrats. Hjälp: avsnitt X (text) + animering `namn`. Nyhet: "…" (NYTT/BÄTTRE/FIXAT)
-->

- [ ] 2026-10-05 – NY DESIGN (A): nästan svart, platt, vita ikoner, en orange accent; allt som ligger på kartan på frostad botten (väder, knapparna uppe till höger som en kapsel, de runda knapparna, fart/djup); sjönamnet utan versaler/serif; rutorna med 28 px hörn; rörelser (tryck som fjädrar, orange som tänds, menyer som växer ut). Hjälp: ALLA animeringar och skärmbilder spelas in igen (`py -3 tools/help_anim.py` – alla), texter som nämner "bärnsten"/"blå" gränssnitt. Nyhet: "Ny design – mörkare, renare, med frostade knappar" (NYTT)

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

- 2026-10-02 – Heatmap: genväg överst (färgad karta vänster om kartknappen, på/av), Filter-knappen smalare (bara ikon + pil), heatmapen flyttar/zoomar inte längre kartan när den slås på. Förslag nyhetsrad: "Ny knapp överst för Heatmap".
- 2026-10-02 – Kompass (Filter → Lager): kil 40° bred, vit, 500 m lång (justerbar: färg, längd, vinkel i Inställningar → Kartan) + rund kompassvisare nere till höger (N Ö S V) från din position mot dit telefonen pekar. iPhone frågar om lov första gången. Av vid appstart. Avsnitt: Filter (+ ev. ny animering). Förslag nyhetsrad: "Ny: Kompass i Filter – se var telefonen pekar".
- 2026-10-02 – Profilbilder: menyknappen visar din bild i cirkeln med en liten pil neråt (hamburgare om bilden saknas), "Logga ut <namn>" längst ner i menyn, namnet under sjöns rubrik borttaget. Avsnitt: Menyn/namn. Förslag nyhetsrad: "Din bild på menyknappen – tryck för menyn".
- 2026-10-02 – Namn (Filter → Lager): riktiga namn från OpenStreetMap (öar, uddar, vikar, gårdar, byar) som vit prick + namn på kartan, på som standard, på alla fyra sjöar. Avsnitt: Filter. Förslag nyhetsrad: "Ny: Namn i Filter – se vad öar och uddar heter".- Demo Mode centrerar på din position när det slås på; Inställningar → Kompassen: Kil/Cirkel kan stängas av var för sig (aldrig båda)

- 2026-10-02 – Spår sparas nu för evigt per sjö (i databasen; Demo Mode visar ett tillfälligt spår som inte sparas). Ny Spår-meny (tryck på Spår-ikonen i Filter): Mina + rullgardin för att se en annan persons spår, hur långt tillbaka, streckad/hel, färg, synlighet, Stopp som ringar ("13 min", med reglage för minsta tid). OBS: "Börja om" för spåret är borttaget – Hjälp-avsnittet Spår nämner det (rad i 40-help.html ~262). Nytt filter Fog of war (Lager): mörkt utom där du varit, 50 m. Avsnitt: Filter (+ ev. ny animering). Förslag nyhetsrader: "Spåren sparas nu – se var du åkt tidigare" och "Ny: Fog of war i Filter".

- 2026-10-03 – Heatmap: fångsterna kommer från Fiskfiskarnas databas (alla tidigare tävlingar + live under en pågående tävling, "Live" i heatmapens rad), finns kvar i telefonen mellan tävlingarna. Nytt avsnitt Inställningar → Fångstdata (vad som hämtats, när nästa hämtning sker, Hämta nu). Avsnitt: Heatmap, Inställningar. Förslag nyhetsrad: "Heatmapen visar fångsterna live under tävlingen".
- [ ] 2026-10-04 – Loggan är en 3D-skylt på "Vem är du?" och i Hjälps och Inställningars sidhuvud: vaggar själv, dra för att snurra den. Hjälp: troligen inget avsnitt. Nyhet: "Snurra på loggan när du väljer namn" (KUL)
- [ ] 2026-10-04 – Demo Mode = testläge: alla i Demo Mode ser bara varandra (egen testdatabas, inget sparas på riktigt), admin kan köra en låtsastävling (fångster, testbåtar, blixtar). Riktig åskvarning är av i Demo Mode. Avsnitt: Inställningar (Demo Mode). Nyhet: "Testa appen ihop i Demo Mode – utan att något sparas på riktigt"
- [ ] 2026-10-04 – Ledare (Filter → Lager, av som standard): under en pågående tävling en lista under väderchipet med de som leder (poäng = de 5 längsta av varje art ihop) och en 👑 efter ledarens namn på kartan. Avsnitt: Filter (Lager), Kartan/Båtarna. Nyhet: "Se vem som leder tävlingen live – slå på Ledare i Filter".

- Ledare/båtar: tryck på namn i listan = centrera; båtrutan/profilen listar personens fångster.

- Snabbmeddelanden: 7 min (inte 15), mindre bubblor med tunn ram, namnet "Calle…" turas om med texten, fisk i artens färg, Egen text regnbåge. (Hjälp-texten rad ~237 säger 15 min + regnbågskant – skriv om.)

- Snabbmeddelanden (uppdatering): färger i 3 min sedan tonas de och blir svarta; fiskmeddelandet "Gädda 78 🐟"; namnet efter texten (ingen rotation).

- Inställningar → Kartan → Platsnamn på kartan: storlek, synlighet, prick, alla namn/bara vatten, Återställ (standard = som förut).

- Tävlingslåset: platser kan bara läggas/ändras/tas bort från en vecka före till en vecka efter en tävling; annars en ruta med "Öppna Demo Mode". Admin och Demo Mode alltid öppet. Nyhetsrad: "Kartan är låst mellan tävlingarna – prova i Demo Mode".

- Profilen öppnas alltid (alla namn, även utan profil hos Fiskfiskarna: namn, fångster, båt); inga profiler i telefonen → "Ladda in data". Demo Mode visar de riktiga profilerna.

- Båten: rutan visar bara fångsterna i tävlingen som pågår (hela tävlingen, även andra sjöar); namnet öppnar profilen. Profilen och Ledare räknar alla fiskar i tävlingen, även de som tas i en annan sjö (heatmapen bara sjön). Nyhetsrad: "Profilen och Ledare räknar alla fiskar i tävlingen, även de som tas i en annan sjö".

- Strandlinje: tunn vit linje där vattnet möter land på vanliga kartan (Inställningar → Kartan, kan stängas av). Nyhetsrad: "Sjöns kant syns nu som en tunn vit linje".

- Design A-justeringar: Filter öppnas som eget kort under knapparna; ett tryckt meddelande öppnar samma kort i mitten som en båt (inte en panel nerifrån); "Egen text" och "Syns i 7 minuter" ligger där valen var. Ingen egen nyhetsrad (hör till NY DESIGN).

- Inställningar: överst ett profilkort (bild, namn, "Byt namn") i stället för "Ditt namn" + "Logga ut (Byt namn)". Hör till NY DESIGN.

- Samma båt: fiskare räknas som samma båt upp till 40 m + så långt båten hinner mellan deras positioner (max 200 m) – förr 30 m, då delades båten i fart. Nyhetsrad: "Samma båt håller ihop bättre när ni kör"

- Storlek: Heatmap (under Tävling) och Kartanalys → Från fångsterna har ett reglage min–max cm. Avsnitt Heatmap + Kartanalys. Nyhetsrad: "Filtrera fångsterna på storlek i Heatmap och Kartanalys"
- Heatmap Per art: Art-valet är nu Alla / en art som i de andra stilarna (förr av/på per art). Avsnitt Heatmap. Ingen egen nyhetsrad (hör till Storlek-raden).
- Kartanalys: "Typiskt" heter nu Likhet (Mest likt – Mindre likt, visar % av sjön); Fångster: kort rad ("Fiska i det tända: 70 % av gäddorna på 15 % av sjön · Se ⓘ"), hela förklaringen i ⓘ (inledningsrad, meningen med "5× tätare än om fångsterna låg jämnt över sjön", Fångster); Likhet visar "15 % av sjön · 70 % av gäddorna"; Fångster kräver inget minsta antal. Avsnitt Kartanalys. Nyhetsrad: "Kartanalys förklarar resultatet tydligare"
- Ny sjö: Östra Vitten (Vingåker) i sjömenyn – djup bara i norra delen (Genesis saknar södra). Avsnitt Sjöar/Kartan. Nyhetsrad: "Ny sjö: Östra Vitten"
- Startfilm: 3D-loggan snurrar in (3,5 s) första gången och när appen inte använts på ett dygn; ett tryck hoppar över, äldre telefoner får den platta loggan; Inställningar → Avancerat → Startfilmen "Spela" visar den igen. Avsnitt Om appen/Kom igång. Nyhetsrad: "Ny startfilm när appen inte använts på ett dygn"
