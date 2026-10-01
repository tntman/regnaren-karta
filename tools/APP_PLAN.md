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

## Faserna (Du = Filip, Claude = Claude Code)

**Fas 0 – Förbered** ✅ (2026-10-01): grenen `app`, klonad till `E:\github\ffmap-app`.

**Fas 1 – Förslag och beslut (Claude)**
1. Förslag: kartorna inpackade i appen eller hämtade från GitHub Pages?
2. Förslag: hur offline-kartor fungerar i appen (utan service worker).
3. Förslag: vilket plugin för bakgrunds-GPS (t.ex. @capacitor-community/background-geolocation) och hur
   positionen skickas när appen ligger i bakgrunden.
4. Du väljer.

**Fas 2 – Android först (gratis)**
5. Du: installera Android Studio.
6. Claude: Capacitor + Android-projekt, bakgrunds-GPS-plugin, behörighetstext + notis
   ("FF Map delar din position"), samma Firestore-post och intervall som idag.
7. Du: öppna `android` i Android Studio → ▶ Run på mobilen (Claude guidar klick för klick).
8. Du: testa – minimera, lås skärmen, syns båten hos någon annan?
9. Claude: rättar; gör en APK som gruppens Android-användare kan installera.

**Fas 3 – Apple-konton (Du)**
10. Apple Developer Program (developer.apple.com/programs, ~1 100 kr/år, 1–2 dagar).
11. App Store Connect → ny app "FF Map", Bundle ID från Claude (t.ex. `se.fiskfiskarna.ffmap`).
12. App Store Connect → Användare och åtkomst → Integrationer → API-nyckel (roll App Manager):
    spara .p8, Key ID, Issuer ID. Ge den bara till Codemagic, inte till Claude.

**Fas 4 – iPhone via Codemagic (gratis nivå)**
13. Claude: iOS-projekt, texter för "Alltid"-plats, `codemagic.yaml` (bygg → TestFlight vid push av `app`).
14. Du: codemagic.io (logga in med GitHub) → lägg till repot.
15. Du: Codemagic → Teams → Integrations → App Store Connect → ladda upp .p8 + Key ID + Issuer ID.
16. Du: push grenen `app` → Codemagic bygger (~15–20 min).
17. Du: TestFlight → lägg till dig som intern testare → installera via TestFlight-appen.
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
