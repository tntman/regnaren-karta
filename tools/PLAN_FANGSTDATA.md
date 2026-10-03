# Heatmap-fångster från Fiskfiskarnas API

## Context
CSV-inläsningen är borttagen (commit bf69348). Fångsterna ska i stället komma från Jonathans API
(`https://fiskfiskarna.se/api/`, ingen inloggning för läsning). Två delar:
- **Historik**: `dashboard.php` → nyckeln `heatmap` (alla fångster med GPS, ~909 st, samma fält som CSV:n:
  timestamp, competitionId, name, species, cm, lat, lng, lake). Svaret är ~530 kB (all statistik).
- **Live**: `tavling.php?action=bootstrap&competitionId=…` → `catches` för en pågående tävling
  (annullerade = rad med `displayValue:"VOID"` + `voidRef`; båda ska bort).
Datan ska gå att se även mellan tävlingarna (en gång i månaden) → telefonens kopia i localStorage.
Samma post som förut (`normCatch` tål redan exakt de fältnamnen), så heatmapen/Kartanalys ändras inte.

## CORS – LÖST (2026-10-03): Jonathan har lagt till båda; `dashboard.php` och `tavling.php` svarar nu med
`Access-Control-Allow-Origin` för `https://tntman.github.io` och `capacitor://localhost`. (Historik nedan.)
`curl -H "Origin: https://tntman.github.io"` → **ingen** `Access-Control-Allow-Origin`. Bara
`regnaren-b8b6a.web.app/.firebaseapp.com` är tillåtna. Webbappen (GitHub Pages) kan alltså inte läsa API:t
förrän **Jonathan lägger till i config.php**:
- `https://tntman.github.io` (webbappen)
- `capacitor://localhost` (iPhone-appen i ffmap-app – WKWebView-fetch omfattas av CORS, trots guidens "native behöver inget")
Koden kan byggas och testas innan dess (testerna låtsas vara API:t), men visar "Kunde inte hämta" live tills det är gjort.

## Ändringar
**`src/js/66-catches.js`** – ny källa i stället för Firestore:
- `CATCH_API = 'https://fiskfiskarna.se/api/'`.
- `loadHistory`: `fetch(dashboard.php)` → `data.heatmap.map(normCatch)` → bara fångster i **denna** sjö
  (återställ `catchLakeOf` från git, bf69348^: position inom sjöns karta + sjönamnet får inte säga en annan
  sjö – t.ex. Östra Vitten inom Regnarens kartbild). Spara aktiva tävlingar för sjön ur `data.competitions`
  (`status === 'active'`, `water` matchar sjöns namn med `catchPlain`, prefix åt båda håll: "Sibbo"/"Sibbofjärden").
- **När historiken hämtas** (kollas vid appstart och när heatmapen/Kartanalys-fångster slås på; aldrig periodiskt).
  Kopian sparar fångsterna + `at` + tävlingslistan (`id, date, days, status, water` ur `data.competitions`).
  `catchNeedsHistory()` = sant om något av:
  1. ingen kopia;
  2. kopian har en tävling med `status: 'active'` (den kan ha avslutats) – högst 1 gång/timme;
  3. kopian har en `planned` tävling vars `date` ≤ idag (den har börjat eller är klar);
  4. kopian äldre än 1 dygn (säkerhetsnät: "TBD"-datum, nyinlagda tävlingar, rättningar – Filips val 2026-10-03).
  Annars används kopian. Mellan tävlingarna = högst en hämtning per dygn per telefon (bara om appen startas).
- `loadLive` (Filips val 2026-10-03): bara när kopian säger att en tävling pågår på sjön och sidan är synlig
  (`document.visibilityState`). Direkt när appen startar / blir synlig igen (om > 60 s sedan senaste), sedan var
  **5:e minut**; var **30:e s** när heatmapen eller Kartanalys "Från fångsterna" är på. ~100 fångster ≈ 6,6 kB
  gzip i slutet av dagen, ≈ 0,5 MB/tävlingsdag per telefon. Live-datan ligger i `catchData` för annat senare.
  Vid varje hämtning: ta bort VOID + det de annullerar,
  slå ihop med historiken på `id` (dubbletter försvinner redan via `id = tid|namn|art|cm`), `catchesChanged()`.
  Stoppar när rutan stängs / appen hamnar i bakgrunden.
- localStorage-kopian (`CATCH_CACHE_KEY`, `catchPack/catchUnpack`) behålls → fungerar offline och mellan tävlingar.
- Bort: Firestore-källan, `catchDb` (`14-spots.js:28`, `26-sync.js:158`).

**Inställningar → nytt avsnitt "Fångstdata"** (`<details class="setSec" data-sec="catch">` i
`src/html/20-menu-settings.html`, efter Kartanalys; för alla användare, gäller denna telefon). Stängt = rubrik +
`setSums()`-rad (`js/28-menu.js`), t.ex. "86 fångster · Live: Regnaren 2" / "86 fångster · hämtad 14:02".
Öppet (läses av en ny `catchStats`-post i 66-catches.js, ritas om vid `catchesChanged()` och när avsnittet öppnas):
- **Historik**: senast hämtad (tid + "för 3 h sedan"), fångster i sjön / i hela API:t, storlek på kopian,
  nästa hämtning + varför (regel 1–4 i klartext, t.ex. "vid start efter kl 14:02 i morgon").
- **Tävlingar på sjön**: pågår / planerade (namn, datum) ur kopian.
- **Live**: på/av och varför ("ingen tävling pågår"), takt just nu (5 min / 30 s), senaste hämtning, antal live-fångster.
- **Idag**: antal anrop och ungefärlig data (`Content-Length`/svarets längd), historik resp. live (räknas i
  localStorage per dag, `lakeKey`).
- **Senaste fel** (om något), t.ex. "Ingen anslutning 13:40".
- Knapp **"Hämta nu"** (tvingar historik + live).
`fakefb` öppnar redan alla avsnitt (lägg till `"catch"` i `ffmap_settings_open_v1`-listan).
Visa en bild av avsnittet för Filip innan det byggs (screenshot från testsidan).

**`src/js/68-heatmap.js`** – felraden: "Kunde inte hämta fångsterna (ingen anslutning?)" behålls; ev. en rad
"Live: <tävling>" i resultatet när live-hämtningen är igång (liten, i `.note`).

**Tester** (`tests/fakefb.py`, `test_heatmap.py`, `test_ancatches.py`):
- fakefb: `ctx.route('**/fiskfiskarna.se/**', …)` – svarar med `cfg.catches` som dashboard-JSON
  (`{heatmap:[…], competitions:[…]}`) resp. bootstrap; **aldrig** nå riktiga API:t (som Firebase/fmi).
  Ta bort `catchesCol` och `__catchDocs/__catchSets`.
- Gör om testdatan i test_heatmap/test_ancatches från `rows` till heatmap-poster (liten hjälpfunktion).
- Nytt: Östra Vitten-fångst inom kartan räknas inte till Regnaren; aktiv tävling → bootstrap-fångst dyker upp,
  VOID-par syns inte; API nere → kopian från localStorage visas; reglerna 1–4 (rätt hämtning/ingen hämtning);
  live var 5 min/30 s styrs av heatmapen och synligheten; Fångstdata-avsnittet visar siffrorna, "Hämta nu" hämtar.
  Rotation: inget nytt tillstånd (avsnittets öppet/stängt sparas redan).

**Dokumentation**: `tools/NOTES_HEATMAP.md` (källa, uppdatering, CORS), CLAUDE.md (Firestore `catches` inte
längre använd – regeln kan tas bort i konsolen), `tools/HJALP_TODO.md` (rad om live-heatmap).

## Verifiering
1. `py -3 tools/build.py`
2. `tests\run_all.ps1 heatmap ancatches admin` – sedan hela sviten (rör flera filer).
3. Efter Jonathans CORS-ändring: `curl -H "Origin: https://tntman.github.io" -D - …/dashboard.php` visar
   rätt header → öppna heatmapen i webbläsaren, se ~86 fångster i Regnaren.

## Status (2026-10-03)
Klart:
- Koden: `66-catches.js` (API, kopia, regler, live, Fångstdata), `28-menu.js`, `68-heatmap.js` (Live i raden),
  `92-rotation.js` (öppen fångst efter vridning), `14-spots.js`/`26-sync.js` (catchDb bort), HTML + CSS.
- Testerna: `fakefb.FakeApi`, `test_heatmap.py`, `test_ancatches.py` (båda gröna), nytt `test_catchapi.py`.
- Dokumentation: `NOTES_HEATMAP.md`, `CLAUDE.md`, `src/README.md`, `HJALP_TODO.md`.
- Playwright installerades om (filer var tomma, 0 byte).

Kvar:
1. Köra `test_catchapi.py` + heatmap (`run_all.ps1 heatmap catchapi`), rätta fel.
2. Hela sviten.
3. Bild av Inställningar → Fångstdata till Filip.
4. Commit (svenska, Opus-attribution). Push bara efter Filips ok.
