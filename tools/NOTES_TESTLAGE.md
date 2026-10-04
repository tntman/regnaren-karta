# Testläge (= Demo Mode)

Alla som har **Demo Mode** på är i ett gemensamt testläge. Där kan man prova appen tillsammans utan en riktig tävling och utan att något hamnar i den riktiga databasen.

Admin, Filip, styr en låtsastävling under **Admin → Testläge**. Rutan syns bara i Demo Mode.

## Hur det är separerat
- **Eget Firebase-projekt.**
  - `TEST_MODE` (`js/10-core.js`) bestäms en gång när sidan laddas. Då väljs `FIREBASE_CONFIG` = `FIREBASE_TEST_CONFIG` (`js/14-spots.js`). Hela anslutningen går till testdatabasen, även appens REST-skrivning i bakgrunden på grenen app, som bygger adressen av `FIREBASE_CONFIG.projectId`.
  - Inget ställe i koden kan "glömmas" och skriva i den riktiga databasen.
  - Testtrafiken räknas inte mot den riktiga gratiskvoten.
- **Byte = omladdning.**
  - När man slår på eller av Demo Mode, trycker på krysset i bannern eller när 15 minuter har gått, laddas sidan om (`setDemoMode`, `js/32-demo.js`).
  - Innan dess tas din båt bort i det läge du lämnar:
    - Riktig till test: din riktiga båt försvinner för de andra.
    - Test till riktig: testbåten försvinner.
  - Öppen sida (Inställningar) kommer tillbaka som efter en vridning, men utan fart, positionstakt och demokurs från det gamla läget.
- **Telefonens kopior får egna nycklar** (`testKey()`, nyckel + `_test`). Det gäller platserna (`WP_KEY`), synkflaggan, fångstkopian, positionsintervallet, "Åskan har dragit förbi" och användningsräknaren.
  - Inställningar som filter, varningsavstånd och kartläge delas mellan lägena.
- **Ingen spårsynk i testläget.** `tracksCol` och `trackUsersCol` = null.
  - Annars skulle ditt riktiga spår laddas upp till testdatabasen, markeras som uppladdat (`u = 1`) och aldrig komma till den riktiga.
  - Demo-spåret sparas som förut bara tillfälligt i telefonen.
- **Ingen Fiskfiskarna och ingen FMI i testläget.**
  - `catchGet` svarar från låtsastävlingen (`testApi`).
  - `ltFetch` tar bara testblixtarna (`testStrikes`).
  - Riktig åskvarning är alltså avstängd i Demo Mode, som Filip valt. Det står i Inställningar och i adminrutan.
- **Bannern** ("DEMO · TESTLÄGE") varnar om telefonens riktiga kopia av fångsterna visar en pågående tävling på sjön: "Riktig tävling pågår – du syns inte för de andra".

## Låtsastävlingen (`js/37-testmode.js`)
Fältet `test` i `config/<sjö>` i testdatabasen ser ut så här:

```
{ comp: {id, name, date, status: planned|active|finished} | null,
  catches: [rader som Fiskfiskarnas API: timestamp, competitionId, name, species, cm, lat, lng, lake, approved, imageUrl?],
  voids: [timestamp för annullerade fångster],
  lt: [{lat, lon, t}] }
```

- Alla testtelefoner lyssnar redan på `config/<sjö>` (`cfgDoc`). Vid ändring körs `testApply`, som hämtar om fångsterna och blixtarna direkt.
- Fångsterna går den vanliga vägen, så heatmapen, livefångsterna, Kartanalys "Från fångsterna" och "Senaste fisk" fungerar som i en riktig tävling. En annullerad fångst blir en VOID-rad, som i API:t.
- Avslutad tävling: fångsterna blir historik (heatmapen).
- Admin skriver hela fältet `test` i en skrivning, alltid med `posIntervalS` eftersom regeln kräver det. Högst 500 fångster. Blixtar äldre än 30 minuter rensas bort.

**Admin → Testläge**

| Del | Vad den gör |
|---|---|
| Tävling | Planerad, Pågår, Avslutad |
| Testbåtar | 0, 3 eller 5. Positionsdokumenten `bot_1…5` ("Testbåt 1–5"). De åker runt på vattnet som demobåten, skickar ibland ett snabbmeddelande och skickar "Senaste fisk" när de får en fångst. |
| Fångst | Vem (du, andra i Demo Mode, testbåtarna), art, cm (tom = slumpad), vid båten eller slumpad plats, Godkänd, Med bild (`icon-512.png`, som bara godtas i testläget). Knapparna "Lägg in fångst" och "Annullera senaste". Finns ingen tävling startas en. |
| Automatiska fångster | Var 30:e sekund, helst från en testbåt. En abborre under 25 cm är inte godkänd. |
| Åska | Blixt 20 / 8 / 2 km från din båt. "Åskan närmar sig" ger en blixt i minuten, 25 km och sedan 3 km närmare varje gång. "Ta bort blixtar" tömmer listan. |
| Rensa testläget | Tar bort testplatserna, döljer alla båtar och meddelanden (utom din båt) och nollställer tävlingen, fångsterna och blixtarna. |

**Testbåtar, automatiska fångster och åskan körs bara i adminens telefon** och bara medan appen är öppen. Testbåtarna och de automatiska fångsterna fortsätter efter en vridning.

## Skapa testprojektet (Filip, en gång)
1. Gå till [console.firebase.google.com](https://console.firebase.google.com) → **Lägg till projekt**.
   - Namn: `ffmap-test`, eller ett annat namn som innehåller "test".
   - Google Analytics behövs inte. Gratisplanen Spark räcker.
2. **Build → Authentication → Get started → Sign-in method** → slå på **Anonymous**.
3. **Build → Firestore Database → Create database.** Välj samma region som det riktiga projektet, eller `eur3`. Starta i **production mode**.
4. **Firestore → Rules:** klistra in samma regler som i det riktiga projektet (se CLAUDE.md → Firestore-regler) och **Publish**.
5. **Project settings (kugghjulet) → General → Your apps → Web (`</>`)** → registrera appen, till exempel "FF Map test", utan Hosting. Kopiera `firebaseConfig`, alltså apiKey, authDomain, projectId, storageBucket, messagingSenderId och appId, och ge den till Claude. Den klistras in i `FIREBASE_TEST_CONFIG` i `src/js/14-spots.js`.
   - Konfigurationen är inte hemlig, precis som den riktiga. Reglerna skyddar databasen.
6. **Authentication → Settings → Authorized domains:** lägg till `tntman.github.io`. `localhost` finns redan.

Tills konfigurationen är ifylld kan testläget inte logga in. Då visas "Offline · fiskeplatser sparas bara på telefonen", och adminrutan säger att testdatabasen inte är kopplad. Inget delas, och inget kan hamna fel.

## Tester
`tests/test_testmode.py`. fakefb kommer ihåg vilket projekt som startades: `window.__fbProject`, och ett annat projekt börjar tomt eller från `cfg.testDb`. Utgångna positioner sparas i `sessionStorage` (`__fbUpdates`), så att de syns även efter omladdningen.
