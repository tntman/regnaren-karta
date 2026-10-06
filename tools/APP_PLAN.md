# FF Map som riktig app (Capacitor) – planen

Gren: **`app`** (mappen `E:\github\ffmap-app`). `main` (mappen `E:\github\regnaren-karta`) är webbappen
som är live – den påverkas inte av det här förrän Filip själv slår ihop grenarna.

**Mål:** en app för iPhone och Android som delar positionen även när appen är minimerad
(bakgrunds-GPS). Allt annat ska fungera som i webbappen.

**Det som redan finns och ska behållas:** positionsdelning till Firestore (en post per användare,
`positions`), andras båtar live på kartan, samma intervall (20 s vid rörelse / 60 s stilla, admin-inställning
i `config/<lake>`), Firebase anonym inloggning. Firebase-kvoten (50k läsningar/dygn) gäller – håll nere läsningarna.
Webbversionen (GitHub Pages, `docs/`) ska fortsätta fungera från samma kod.

**Kända fällor:**
- Service worker fungerar inte i iOS-appen (WKWebView) → offline-nedladdningen (Inställningar → Offline,
  Cache API) måste lösas på annat sätt i appen (t.ex. filer på telefonen).
- Kartbilderna är ~360 MB (`docs/lakes/`) → beslut: packa in i appen eller hämta från GitHub Pages.
- Vridnings-omladdningen (`checkRotationReload`, bara hemskärmsappen på iPhone) behövs inte i appen.
- Filip kör Windows (ingen Mac, ingen terminal): iOS byggs i Codemagic, Android i Android Studio.
- Filip vill se förslag innan något byggs. Inga git-kommandon – Filip gör commit/push i GitHub Desktop.

## Två chattar, två grenar – regler

- **"regnaren-karta"** (`E:\github\regnaren-karta`, gren `main`): webbappen, en egen Claude Code-chatt.
  Nya funktioner, fixar, Hjälp och sjöar görs DÄR – inte här.
- **"FF Map - app"** (`E:\github\ffmap-app`, gren `app`, den här mappen): bara det som gör webbappen till en
  riktig app – Capacitor-skalet (ios/, android/, capacitor.config, codemagic.yaml), bakgrunds-GPS och
  app-anpassningar.
- **Appens kod i egna filer:** t.ex. `src/js/95-native.js` (och egen css-fil vid behov) som bara gör något när
  den körs i appen (`window.Capacitor && Capacitor.isNativePlatform()`). Ändra befintliga filer i `src/` så lite
  som möjligt – helst en liten krok – annars blir det konflikter när `main` förs in hit.
- **Nyheter från main:** Filip gör GitHub Desktop → Branch → Update from main i "FF Map - app".
  Blir det konflikt: Claude hjälper till att lösa den.
- Behövs en ändring som är bra även för webben: säg det till Filip, så görs den i "regnaren-karta"-chatten.
- Senare (beslutas då): grenen `app` slås ihop med `main` när appen fungerar – appdelarna gör inget på webben.

## Faserna (Du = Filip, Claude = Claude Code)

**Fas 0 – Förbered** ✅ (2026-10-01): grenen `app`, klonad till `E:\github\ffmap-app`.

**Fas 1 – Förslag och beslut** ✅ (2026-10-01)
1. **Kartor: mellanväg.** Inpackat i appen (~15 MB): översiktskartan (zoom 14, `map_v*_*.jpg`) för alla sjöar
   och kartlägen, tumnaglar, djup- och bottendata. Detaljbitarna (`tiles_v*/`, zoom 15–18) hämtas från
   GitHub Pages. Ordning: det som säger vilken kartversion som gäller – nätet först; kartbilderna – sparad
   eller inpackad kopia först (versionen står i filnamnet, så en sparad bild blir aldrig gammal), annars nätet.
   Bitar man tittat på sparas automatiskt (som service workern gör på webben).
2. **Offline: filer i appens egen mapp** (Capacitor Filesystem) i stället för Cache API. Inställningar →
   Offline ser ut och fungerar som idag (samma lista, pausa/fortsätt, ny version, Ta bort). Firebase-biblioteken
   packas in så att appen startar utan nät. sw.js packas inte med i appen.
3. **Bakgrunds-GPS: @capacitor-community/background-geolocation** (gratis). Android: notisen
   "FF Map delar din position" håller GPS:en igång; iPhone: blå markering i statusraden, troligen räcker
   "Medan appen används" (testas i Fas 4; annars "Alltid"). Punkterna går till samma `maybeBroadcastPosition`
   (samma intervall, nära sjön, samma `positions`-post). I bakgrunden skrivs posten med ett vanligt anrop till
   Firestores REST-API (samma inloggning och fält) eftersom SDK:ts anslutning stryps. Stilla vid ankar: pluginet
   ställs in så att det ändå ger punkter, så båten inte blir grå. Svept bort app = delningen slutar.
   (Valdes bort: Transistorsoft – Android-licens ~4 000 kr.)
4. **Krokar på `main`** ✅ (inslagna i `app` 2026-10-01), gör inget på webben:
   - `lakeUrl(path)` (10-core.js) – alla sjöfiler: `mapFile`/`thumbFile`, detaljbitarnas `src`, djup- och bottendata.
   - `lakeImgError(el)` (10-core.js) – först i bildernas `onerror`; `true` = hanterat.
   - `offStore` (18-offline.js) – `available/has/size/put/clear` i stället för Cache API direkt.
     `put(url, response)` får ett fetch-svar. Offline-listan (`offlineFiles()`) går genom `lakeUrl`, så
     appens `lakeUrl` måste ge samma adress varje gång för samma fil (den adressen = nyckeln i `offStore`).
   - `writeOwnPosition(data)` (24-boats.js) – själva skrivningen av den egna positionen. `data.updatedAt` är
     SDK:ts `serverTimestamp()` – REST-varianten i bakgrunden måste ersätta den (serverns tid via `updateTransforms`).
   Ingen krok behövs för vridnings-omladdningen (bara `navigator.standalone`) eller service workern (sw.js saknas i appen).
   Appens kod: `src/js/95-native.js` (byter ut krokarna när `Capacitor.isNativePlatform()`).

**Fas 2 – Android först (gratis)**
5. Du: installera Android Studio ✅ (2026-10-01) + **Node.js** (nodejs.org → LTS, klicka Next).
   **Körs lokalt** (Claude Code i `E:\github\ffmap-app`, beslut 2026-10-01): Claude kör npm/`npx cap sync` och
   bygger själv med Android Studios SDK (`android\gradlew assembleDebug`, `adb install` när mobilen sitter i USB),
   så byggfel hittas innan Filip trycker Run. Filip kör fortfarande ingen terminal själv.
6. Claude: Capacitor + Android-projekt, bakgrunds-GPS-plugin, behörighetstext + notis
   ("FF Map delar din position"), samma Firestore-post och intervall som idag.
   **Förslaget (godkänt i princip – visa kort igen och få "ja" innan bygget):**
   - App: namn **FF Map**, app-id **`se.fiskfiskarna.ffmap`** (låses i Fas 3 – bekräfta med Filip).
   - Vad Filip ser: appen ser ut som webbappen. Första start: Android frågar om plats ("När appen används")
     och aviseringar (Tillåt – behövs för notisen). När appen minimeras/skärmen låses, med valt namn och nära en
     sjö (`isNearLake`): fast notis **"FF Map delar din position"**, båten rör sig hos andra (20 s rörelse / 60 s
     stilla, admin-inställningen). Långt från sjön: ingen bakgrunds-GPS, ingen notis. Svept bort app = slut.
   - Ny rad i Inställningar → Båten, bara i appen (läggs dit av 95-native.js): **"Dela position när appen är
     minimerad"**, på som standard.
   - Filer (nya, utom en rad i `tools/build.py` som även kör `build_app.py`):
     `src/js/95-native.js` (krokarna + bakgrunds-GPS + raden i Inställningar, gör inget på webben),
     `tools/build_app.py` (appens innehåll av `docs/`: sidan, ikoner, översiktskartor + tumnaglar + djup/botten
     ~15 MB, Firebase-biblioteken lokalt i stället för gstatic; utan sw.js och utan `tiles_v*/`),
     `capacitor.config.json`, `package.json`, `android/` (vanligt Capacitor-projekt; `node_modules/` checkas inte in),
     `tools/APP.md` (anteckningar för appen).
   **Byggt 2026-10-01** (Filip sa ja; app-id `se.fiskfiskarna.ffmap`). Hur: `tools/APP.md`. Avvikelser från förslaget:
   appkoden heter `11-native.js` (en fil efter 92-rotation.js når inte krokarna); `build.py` orörd (`npm run build`
   kör build.py + build_app.py + cap sync); notisen syns så länge du är vid sjön, även med appen öppen (pluginet).
   **Filip har ingen Android-mobil** → emulatorn i Android Studio först, sedan testar någon i gruppen en APK.
7. Du: Android Studio första gången (SDK + emulator); Claude bygger och kör i emulatorn.
   **Gjort 2026-10-01:** emulatorn Pixel 8 (Android 17), SVM påslaget i BIOS. Provkörning med namnet "Test app"
   (riktiga Firebase, Filips ok): minimerad + låst skärm → positionen skrevs via REST var 20:e s (17 st, alla 200),
   notisen syntes; utloggad efteråt.
8. Testa – emulatorn (låtsad GPS-rutt), sedan en Android-användare i gruppen: minimera, lås skärmen, syns båten?
9. Claude: rättar; gör en APK som gruppens Android-användare kan installera.

**Fas 3 – Apple-konton (Du)**
10. ✅ (2026-10-06) Apple Developer Program (developer.apple.com/programs, ~1 100 kr/år, 1–2 dagar).
11. ✅ (2026-10-06) App Store Connect → ny app "FF Map", Bundle ID från Claude (t.ex. `se.fiskfiskarna.ffmap`).
12. App Store Connect → Användare och åtkomst → Integrationer → API-nyckel (roll App Manager):
    spara .p8, Key ID, Issuer ID. Ge den bara till Codemagic, inte till Claude.

**Fas 4 – iPhone via Codemagic (gratis nivå)**
13. Claude: iOS-projekt, texter för "Alltid"-plats, `codemagic.yaml` (bygg → TestFlight vid push av `app`).
    **Gjort 2026-10-01** (medan Apple-kontot var "Pending"). Apple-ID-numret (6819667300) inlagt i `codemagic.yaml` 2026-10-06
    (`APP_STORE_APPLE_ID`).
14. ✅ Du: codemagic.io (logga in med GitHub) → lägg till repot (grenen `app`).
15. ✅ Du: Codemagic (personligt konto: **Settings**, inte Teams) → Integrations → Developer Portal: nyckeln
    "FF Map" (.p8 + Key ID + Issuer ID); Code signing identities → iOS certificates → Generate (Apple Distribution).
    **Plus:** provisioning profile "FF Map App Store" skapad på developer.apple.com (Profiles → App Store Connect)
    och hämtad i Codemagic (iOS provisioning profiles → Fetch) – utan den: "No matching profiles found".
16. ✅ Bygge startat för hand (pushar startar inte byggen än – kolla Webhooks). `submit_to_testflight: false`:
    externa testare kräver Beta App Review-info, interna inte.
17. ✅ (2026-10-06) Intern grupp "Fiskfiskarna" (automatisk distribution), bygge 1 installerat på Filips iPhone.
18. Du: testa bakgrunds-GPS på iPhone (välj "Alltid").

**Fas 5 – Gruppen**
19. Du: gruppens iPhone-användare som interna testare (max 100; deras Apple-ID läggs till i App Store Connect).
20. Du: skicka APK:n till Android-användarna.
21. Claude: kort instruktion till gruppen (installera, varför "Alltid"-plats).

**Fas 6 – Underhåll**
22. Webbappen på `main` fungerar som förut.
23. Ändringar i `main` → till `app` via GitHub Desktop (Branch → Update from main; Claude guidar).
24. TestFlight-versioner gäller 90 dagar → ny push = ny version. Claude påminner.

**Kostnad:** ~1 100 kr/år (Apple). Allt annat gratis i gruppens storlek.
**Risker:** batteri; Apple kan ifrågasätta "Alltid"-plats (påverkar inte interna TestFlight-testare).
