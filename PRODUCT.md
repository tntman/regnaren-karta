# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

(En PWA: används mest som "Lägg till på hemskärmen"-app på iPhone, även i vanlig webbläsare och på Android. Publiceras som statisk sida via GitHub Pages.)

## Users

- **Fiskfiskarna**: en privat fiskegrupp på ungefär 20 personer. Appen är bara till för dem; det finns ingen plan på fler användare.
- **Huvudsituationen är gruppens fisketävlingar**: ute i båten, telefonen i handen, ofta med en hand, i starkt solljus och med blöta eller kalla händer. Vanliga fisketurer finns också, men tävlingsdagen är det som räknas.
- **Filip** är admin och den som äger appen. Han bestämmer hur den ska se ut och fungera, men använder inte terminalen själv. Han gör commit och push i GitHub Desktop.

## Product Purpose

En gemensam karta för tävlingsdagen. För sjöarna gruppen fiskar i (nu Regnaren, Sjösjön och Vågsfjärden) visar den
- djupkarta
- egen position
- gruppens fiskeplatser
- var de andras båtar är
- snabbmeddelanden
- väder, vind och lä
- blixtvarning

Till det kommer analysverktyg som hjälper till att hitta ställen: Kartanalys med kartdata, tumregler, tävlingarnas fångster per art och liknande platser, plus en Heatmap över tävlingsfångsterna.

Appen lyckas när alla i gruppen ser samma levande bild under tävlingen, hittar till fisken och kan ta sig säkert till och från vattnet.

## Positioning

Appen kombinerar detaljerade djupkartor (C-MAP Genesis) över just gruppens sjöar med gruppens egen, levande data: platser, båtar och meddelanden, plus historiken från gruppens egna tävlingsfångster. Ingen allmän fiskeapp har gruppens fångster, positioner och platser samlade.

## Operating Context

- Ute på sjön i båt, främst under tävlingar. Mobilnätet kan vara dåligt, därför kan sjöarna laddas ner för offline.
- iPhone-hemskärmsappen laddar om sidan när telefonen vrids, så allt tillstånd måste överleva en omladdning.
- Fångsterna registreras i en separat tävlingsdatabas ("fiskfiskardaDatabasBackend"). Nu kommer de till appen via en CSV-fil som admin läser in. Senare ska de komma direkt från den databasen.
- Gruppen tävlar även i sjöar som ännu inte finns i appen, till exempel Mälaren, Sibbo, Gryts skärgård, Väringen och Täljaren.

## Capabilities and Constraints

- All text i appen är på svenska.
- Statisk sida (GitHub Pages) plus Firebase (Firestore med anonym inloggning, där identiteten är det valda namnet). Gratiskvoten gäller: 50 000 läsningar per dygn, så onödiga läsningar ska undvikas. Ingen egen server.
- Sidans adress är offentlig, så känslig data (fångstpositioner och namn) hålls i Firebase och inte i de publicerade filerna.
- Djupkurvor och djupsiffror ritas aldrig av appen själv. De kommer bara från Genesis.
- Varken pushnotiser eller position i bakgrunden finns: det första kräver en betalplan eller server, det andra en riktig app.
- Säkerhet går före filter: Fara-markeringar och åskvarning kan aldrig döljas.
- **Obeslutat:**
  - hur kopplingen till tävlingsdatabasens liveflöde ska se ut
  - om det ska bli en riktig iPhone-app (Capacitor/TestFlight)
  - pushnotiser

## Brand Commitments

- Namnet är **FF Map** (i manifestet "Fiskfiskarna Map"). Appen och gruppen heter Fiskfiskarna.
- Den befintliga texten i appen är kort, vardaglig svenska med en lätt, lekfull ton, till exempel "Fisken läser inte kartan 🙂" och snabbmeddelandet "Bajs 💩". Analysernas texter är ärliga om vad datan visar, som "Visar var man fick fisk – inte var all fisk finns".

## Evidence on Hand

- **Tävlingsfångster:** CSV med 902 fångster från 2026-03-28 till 2026-09-27, 20 personer och flera sjöar. 190 av dem finns i appens sjöar: Regnaren 88 och Vågsfjärden 102. Arterna är abborre, gädda och gös.
- **Kartor:** Genesis-kartor och djup- och bottendata för Regnaren, Sjösjön och Vågsfjärden (`lakes/`, `docs/lakes/`).
- **Hjälp-sidan** med animeringar av varje funktion (`docs/help/`).
- Det finns inga omdömen, användarsiffror eller pressklipp, och sådant ska inte hittas på.

## Product Principles

1. **Byggd för tävlingsdagen i båten.** Det viktigaste ska gå att se med en blick och göra med en hand, även i sol och med blöta fingrar.
2. **Gruppens egen data först, ärligt redovisad.** Visa vad datan bygger på och hur säker den är; inga påhittade slutsatser.
3. **Säkerhet kan inte stängas av.** Fara, åskvarning och vägen hem ska alltid synas.
4. **Billig och enkel att driva.** Allt ryms i en statisk sida och Firebases gratiskvot, och Filip ska kunna publicera utan terminal.
5. **Filip bestämmer.** Förslag och bilder visas innan något byggs.

## Accessibility & Inclusion

- **Starkt solljus:** texter, linjer och markeringar måste ha hög kontrast och gå att läsa i sol och med reflexer från vattnet.
- **Blöta eller kalla händer:** tryckytor ska vara stora och förlåtande, och inget viktigt får kräva precisionstryck.
