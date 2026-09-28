# FF Map (Fiskfiskarna Map)

Djupkarta + GPS-app för Fiskfiskarna vid Regnaren. En webbapp (läggs till på
hemskärmen i iPhone) som visar sjökort, din position, gruppens båtar och
fiskeplatser, med delning via Firebase.

## Mappar

| Mapp | Innehåll |
|---|---|
| `src/app.html` | Hela appen (CSS + HTML + JavaScript). **Här ändrar man.** |
| `src/head.html` | `<head>`: titel, ikoner, manifest, Firebase-bibliotek |
| `src/sw.js` | Service worker (gör att appen startar utan nät) |
| `data/` | Djupdata (packad) och förhandsbilder för kartstilarna. Läggs in vid bygget. |
| `data/raw/depth_raw.npz` | Råa djupdata (för kalibrering/nya kartstilar och vissa tester) |
| `assets/` | Ikoner, manifest och de sex kartbilderna |
| `tools/build.py` | Bygger sajten till `docs/` |
| `tools/render_map_styles.py` | Skriptet som ritade kartstilarna (kräver originaldata, se nedan) |
| `tests/` | Webbläsartester (Playwright) med låtsas-Firebase |
| `docs/` | **Den färdiga sajten** – det GitHub Pages visar |

## Bygga

    python3 tools/build.py

## Testa

    pip install playwright numpy pillow
    python3 -m playwright install chromium
    python3 tools/build.py && tests/run_all.sh

## Publicera (GitHub Pages)

Repo → Settings → Pages → Source: *Deploy from a branch*, Branch: `main`, mapp `/docs`.
Efter det räcker det att bygga och pusha – sajten uppdateras av sig själv inom någon minut.

## Firebase

Firestore-samlingar: `waypoints`, `positions`, `usage`, `config`. Reglerna ligger i
Firebase-konsolen (se CLAUDE.md för aktuell version).

## Obs

`tools/render_map_styles.py` och `tools/build_depth_map_original.py` behöver de stora
originalfilerna (flygfoto- och djupkartsrutorna, ~2 GB) som inte ligger i repot.
Kartbilderna i `assets/` är färdiga och behövs inte göras om.
