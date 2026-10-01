# FF Map som app (Capacitor) – anteckningar

Planen och besluten: `tools/APP_PLAN.md`. Här står hur det är byggt.

## Delarna
| Fil | Vad |
|---|---|
| `src/js/11-native.js` | all appkod i sidan. Gör inget på webben (`NATIVE` = `Capacitor.isNativePlatform()`). Ligger direkt efter `10-core.js`: krokarna `lakeUrl`/`lakeImgError` används redan när nästa filer körs. Inte `95-…` som planen sa: `})();` (skriptets slut) och `boot()` ligger i `92-rotation.js`, så en fil efter den når inte krokarna. |
| `tools/build_app.py` | `app/www/` (Capacitors webDir) ur `docs/`: sidan med Firebase-SDK:t lokalt (`app/vendor/`, hämtas en gång från gstatic) och Capacitors JS (`vendor/capacitor.js` ur node_modules – utan den finns inte `Capacitor.registerPlugin`), ikoner, Hjälp, per sjö allt utom `tiles_v*/`. Inte sw.js. ~22 MB. |
| `capacitor.config.json` | app-id `se.fiskfiskarna.ffmap`, namn FF Map, `android.useLegacyBridge` (annars stannar bakgrunds-GPS:en efter 5 min). |
| `package.json` | Capacitor 8 + `@capacitor-community/background-geolocation` + `@capacitor/filesystem`. `node_modules/` checkas inte in. |
| `android/` | vanligt Capacitor-projekt. Egna ändringar: `MainActivity.java` (frågar om aviseringar, Android 13+), `res/values/strings.xml` (notisens kanal, ikon, färg), `res/drawable/ic_stat_ffmap.xml` (notisikonen), ikoner och startbild (gjorda av `docs/icon-512.png`), `styles.xml` (startbildens färg). |
| `ios/` | Capacitor-projekt (Swift Package Manager, ingen CocoaPods – skapat på Windows, byggs på Mac hos Codemagic). Egna ändringar: `App/App/Info.plist` (platsfrågornas texter, `UIBackgroundModes` = location, `ITSAppUsesNonExemptEncryption` = false så TestFlight inte frågar om kryptering, språk sv), ikon 1024 px (förstorad `icon-512.png` – SVG:n är bara fisken) och startbild. |
| `codemagic.yaml` | iPhone: push av grenen `app` → npm ci, build_app.py, cap sync ios, signering (Codemagic hämtar/gör profil), byggnummer = senaste i TestFlight + 1, bygge, TestFlight. Kräver integrationen "FF Map" (App Store Connect API-nyckel) och ett iOS-certifikat i Codemagic, samt `APP_STORE_APPLE_ID` (appens Apple-ID-nummer). |
| `tests/test_native.py` | appkoden med en låtsad Capacitor i testwebbläsaren. |

## Bygga
```
py -3 tools/build.py          (docs/, som vanligt)
py -3 tools/build_app.py      (app/www/)
npx cap sync android          (kopierar in i android/ + plugins)
android\gradlew assembleDebug (i android/; JAVA_HOME = Android Studios jbr)
```
`npm run build` gör de tre första (och `cap sync` för iOS). docs/ måste vara byggd och pushad – Codemagic kör bara build_app.py. APK:n: `android/app/build/outputs/apk/debug/app-debug.apk`.

## Hur det fungerar
- **Kartor:** översiktskartor, tumnaglar, djup/botten och Hjälp är inpackade (relativa adresser, som på webben).
  Detaljbitarna kommer från GitHub Pages (`APP_REMOTE`); varje bit som laddats sparas i appens mapp
  (Filesystem, `DATA`), förteckning i localStorage `ffmap_app_files_v1` (sökväg → byte). Sparad bit = den används
  (`Capacitor.convertFileSrc`); laddas den inte (`lakeImgError`) glöms den och nätet tas.
- **Offline (Inställningar):** `offStore` byts mot `appOffStore` (samma lista/knappar), nyckel = filens sökväg
  `lakes/<id>/…`. Inpackade filer räknas som redan sparade. Byts ut när alla filer körts (`offStore` sätts i 18-offline.js).
- **Ny kartversion:** sidan (och därmed `LAKES`, kartornas filnamn) är inpackad → ny kartversion kräver ny app.
  Tas gamla `tiles_v*` bort från `docs/` slutar gamla appar få bitar de inte sparat. *(Planens "versionen från nätet" är inte gjort.)*
- **Bakgrunds-GPS:** en watcher (pluginet) startas när du har ett namn, inställningen är på och senaste riktiga
  GPS-positionen är vid sjön (`isNearLake`); kollas var 5:e s medan appen är öppen (Android tillåter inte start från
  bakgrunden). Medan den finns visar Android notisen **"FF Map delar din position"** – även när appen är öppen (pluginet
  visar den alltid). Lämnar du sjön tas den bort. Svept bort app = pluginet stoppar tjänsten.
- **I bakgrunden** (`pause`/dold sida) går pluginets punkter till `handleGpsFix` (samma intervall, spår, nära sjön).
  `writeOwnPosition` skriver då med Firestores REST-API (`documents:commit`, `updatedAt` = serverns tid) via
  CapacitorHttp (WebView-anrop stryps efter 5 min). Inloggningen: ID-token tas från SDK:t när appen göms och förnyas
  med refresh-token (`securetoken.googleapis.com`) när < 5 min återstår.

## Bygga på Filips dator
Android Studios Java är 25 → Gradle 9.1 (wrappern) + foojay i `android/settings.gradle` (hämtar Java 21 som
pluginen vill ha). `JAVA_HOME` = `C:\Program Files\Android\Android Studio\jbr`, SDK i `%LOCALAPPDATA%\Android\Sdk`.

## Emulator
`Pixel_8` (Android 17). Kräver SVM i BIOS (ASUS: Advanced → CPU Configuration → SVM Mode) + Windows Hypervisor Platform.
Starta: `emulator -avd Pixel_8`; GPS: `adb emu geo fix <lon> <lat>`. Styra sidan: `adb forward tcp:9222
localabstract:webview_devtools_remote_<pid>` → Playwright `connect_over_cdp` (debug-bygget).
Skärmdump: `adb shell screencap -p /data/local/tmp/s.png` + `adb pull` (inte `> fil` i PowerShell).
