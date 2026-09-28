# FF Map (Fiskfiskarna Map)

Djupkarta + GPS-app för Fiskfiskarna. En webbapp (läggs till på hemskärmen i
iPhone) som visar sjökort, din position, gruppens båtar och fiskeplatser, med
delning via Firebase. Stöder flera sjöar (just nu Regnaren, Sjösjön och Vågsfjärden) –
sjön väljs i menyn.

## Mappar

| Mapp | Innehåll |
|---|---|
| `src/app.html` | Hela appen (CSS + HTML + JavaScript). **Här ändrar man.** |
| `src/head.html` | `<head>`: titel, ikoner, manifest, Firebase-bibliotek |
| `src/sw.js` | Service worker (gör att appen startar utan nät) |
| `lakes/<id>/` | **En mapp per sjö**: `lake.json` (namn, geo-referens, djupskala, kartstilar, zoomnivåer) + `raw/` (inställningar och källdata för att bygga om sjön) |
| `docs/lakes/<id>/` | Sjöns bilder, gjorda av `tools/genesis_render.py`: kartbild (zoom 14), zoomnivåer i bitar `tiles_v*/z<zoom>/`, förhandsbilder, djupdata |
| `assets/` | Ikoner och manifest |
| `tools/build.py` | Bygger sajten till `docs/` |
| `tools/genesis_*.py` | Bygger en sjö från C-MAP Genesis Social Map (se nedan) |
| `tests/` | Webbläsartester (Playwright) med låtsas-Firebase |
| `docs/` | **Den färdiga sajten** – det GitHub Pages visar |
| `raw/` | Nedladdade kartrutor (stora, inte i git) |

## Bygga

    py -3 tools/build.py            (Windows; python3 tools/build.py på Mac/Linux)

## Testa

    py -3 -m pip install --user playwright numpy pillow scipy
    py -3 -m playwright install chromium
    powershell -ExecutionPolicy Bypass -File tests\run_all.ps1     (tests/run_all.sh på Mac/Linux)

Testerna körs parallellt, 6 åt gången (`$env:TEST_JOBS` ändrar), cirka 3 minuter.

Testerna kör mot `docs/` med en låtsas-Firebase och kan aldrig nå den riktiga
databasen (se `tests/fakefb.py`).

## Lägga till en sjö / ändra hur kartorna ritas

Allt om kartorna – receptet steg för steg (genesis_tiles → genesis_depth →
osm_water → genesis_render → build → test), hur man ser vilka zoomnivåer
Genesis har, Genesis egenheter, färgskalor, relief och vad som testats och
förkastats – står i **[tools/KARTOR.md](tools/KARTOR.md)**.

Kartdata: C-MAP Genesis Social Map, Bing-flygfoto, sjögränser © OpenStreetMap-bidragsgivare (ODbL).

## Publicera (GitHub Pages)

Repo → Settings → Pages → Source: *Deploy from a branch*, Branch: `main`, mapp `/docs`.
Efter det räcker det att bygga och pusha – sajten uppdateras av sig själv inom någon minut.

## Firebase

Firestore-samlingar: `waypoints`, `positions`, `usage`, `config`. Allt märks med
sjöns id (`lake`), och `config/<sjö>` har inställningarna per sjö, så sjöarna
blandas aldrig. Reglerna ligger i Firebase-konsolen (se CLAUDE.md).

## Obs

Alla sjöarna är byggda med Genesis-verktygen och djupet är kalibrerat mot
Genesis egna djupsiffror. Regnaren har behållit sitt gamla utsnitt, så
fiskeplatser hamnar rätt. Genesis har zoom 12–18 för alla sjöarna; i appen
används 14 och uppåt (se tools/KARTOR.md).
