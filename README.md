# FF Map (Fiskfiskarna Map)

Djupkarta + GPS-app för Fiskfiskarna. En webbapp (läggs till på hemskärmen i
iPhone) som visar sjökort, din position, gruppens båtar och fiskeplatser, med
delning via Firebase. Stöder flera sjöar (just nu Regnaren och Vågsfjärden) –
sjön väljs i menyn.

## Mappar

| Mapp | Innehåll |
|---|---|
| `src/app.html` | Hela appen (CSS + HTML + JavaScript). **Här ändrar man.** |
| `src/head.html` | `<head>`: titel, ikoner, manifest, Firebase-bibliotek |
| `src/sw.js` | Service worker (gör att appen startar utan nät) |
| `lakes/<id>/` | **En mapp per sjö**: `lake.json` (namn, geo-referens, djupskala, kartstilar), kartbilder `map_v1_<stil>.jpg`, djupdata `depth_v1.txt`, förhandsbilder `thumbs/`, detaljrutor `tiles_v1/` |
| `lakes/<id>/raw/` | Källdata/inställningar för att bygga om sjön (kopieras inte till sajten) |
| `assets/` | Ikoner och manifest |
| `tools/build.py` | Bygger sajten till `docs/` |
| `tools/genesis_*.py` | Bygger en sjö från C-MAP Genesis Social Map (se nedan) |
| `tests/` | Webbläsartester (Playwright) med låtsas-Firebase |
| `docs/` | **Den färdiga sajten** – det GitHub Pages visar |
| `raw/` | Nedladdade kartrutor (stora, inte i git) |

## Bygga

    py -3 tools/build.py            (Windows; python3 tools/build.py på Mac/Linux)

## Testa

    py -3 -m pip install --user playwright numpy pillow
    py -3 -m playwright install chromium
    powershell -ExecutionPolicy Bypass -File tests\run_all.ps1     (tests/run_all.sh på Mac/Linux)

Testerna kör mot `docs/` med en låtsas-Firebase och kan aldrig nå den riktiga
databasen (se `tests/fakefb.py`).

## Lägga till en sjö (från Genesis Social Map)

1. Hitta sjön på genesismaps.com/SocialMap och ta fram lat/lon-gränser för utsnittet.
2. `py -3 tools/genesis_tiles.py <id> 17 <lat_min> <lat_max> <lon_min> <lon_max>`
   – laddar ner djupfärger, djupkurvor, vegetation, bottenhårdhet och flygfoto till `raw/<id>/z17/`.
3. Skriv `lakes/<id>/raw/source.json` (se Vågsfjärden).
4. `py -3 tools/genesis_depth.py <id> sheet` – gör ett ark med Genesis djupsiffror.
   Läs av siffrorna (liten siffra efter = tiondelar) och fyll i `depth_m` i `lakes/<id>/raw/depth_labels.json`.
5. `py -3 tools/genesis_depth.py <id>` – räknar fram djupet i meter (kalibrerat mot siffrorna).
6. `py -3 tools/genesis_render.py <id>` – ritar kartstilar, detaljrutor, djupdata och `lake.json`.
7. Bygg och testa. Sjön dyker upp i menyn av sig själv.

## Publicera (GitHub Pages)

Repo → Settings → Pages → Source: *Deploy from a branch*, Branch: `main`, mapp `/docs`.
Efter det räcker det att bygga och pusha – sajten uppdateras av sig själv inom någon minut.

## Firebase

Firestore-samlingar: `waypoints`, `positions`, `usage`, `config`. Allt märks med
sjöns id (`lake`), och `config/<sjö>` har inställningarna per sjö, så sjöarna
blandas aldrig. Reglerna ligger i Firebase-konsolen (se CLAUDE.md).

## Obs

Båda sjöarna är byggda med Genesis-verktygen ovan och djupet är kalibrerat mot
Genesis egna djupsiffror. Regnaren finns bara till zoom 16 i Genesis (Vågsfjärden
till 17) och har behållit sitt gamla utsnitt, så fiskeplatser hamnar rätt.
Genesis djupsiffror: den lilla siffran efter talet är tiondelar.
