# Plan: ny appikon (loggan)

Från sidochatten 2026-10-06. Filip har valt den nya ikonen: **`tools/logo_ny.html`** (öppna via servern "repo":
http://localhost:8897/tools/logo_ny.html). Alla förslag som ledde dit: `tools/logo_forslag.html`.

Ikonen = fisken (`ff_logo.svg`, oförändrad) med svart kant på en sjö med djupkurvor på mörkblått, ett gult S-spår och
appens orange pil i 3D. Bara **appikonen** byts – startfilmen, startbilden (`launch-*.png`) och namnrutans logga
visar bara fisken och rörs inte.

## Webben (main-chatten) – gjort 2026-10-06
Skriptet: `py -3 tools/app_icon.py` (alla + favicon), `py -3 tools/app_icon.py 1024 <fil>` för appens AppIcon.

1. Exportera ikonen som PNG ur `logo_ny.html` (Playwright/Edge som `tools/launch_images.py`):
   **fyrkantig utan rundade hörn** (iOS och Android rundar själva; ta bort `clip-path="url(#rr)"` vid exporten),
   ingen genomskinlighet. Storlekar: `assets/apple-touch-icon.png` 180, `assets/icon-192.png` 192,
   `assets/icon-512.png` 512. Gör exporten till ett litet skript, `tools/app_icon.py` (så ikonen kan göras om).
2. Favicon: `src/head.html` rad 32 har en inbäddad 64×64-PNG (data-URI) – byt mot den nya i 64 px.
3. Höj `CACHE` i `src/sw.js` (`ffmap-v7` → `ffmap-v8`): ikonerna ligger i `STATIC` och har samma filnamn.
4. `py -3 tools/build.py`, tester med urval: `tests\run_all.ps1 review_fast3 testmode` (de nämner ikonerna;
   `test_testmode` kollar att meddelandebilden slutar på `icon-512.png` – filnamnet är kvar, så det håller).
5. Commit, push efter Filips ok.

**Viktigt för Filip:** iPhone sparar ikonen när appen läggs till på hemskärmen. Den nya syns först när man tar bort
appen från hemskärmen och lägger till den igen (namn, inställningar och offline-kartor finns kvar – samma adress).
Säg till gruppen.

## iPhone-appen (app-chatten, `E:\github\ffmap-app`, gren `app`)
- `ios/App/App/Assets.xcassets/AppIcon.appiconset/AppIcon-512@2x.png` = **1024×1024**, fyrkantig, ingen alfa
  (App Store kräver det). Exportera med samma skript.
- `assets/` i app-repot får de nya PNG:erna via `git merge origin/main`.
- Android (`android/app/src/main/res/mipmap-*`) om den byggs.
- Nytt bygge i Codemagic.
