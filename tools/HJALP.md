# Hjälp-sidan – så görs och uppdateras den

Hjälp är en sida i appen (menyn → **Hjälp**) som visar alla funktioner med en kort
animering per avsnitt, plus "Nytt i appen". Den öppnas aldrig av sig själv: efter varje namnval kommer
välkomstrutan `#welcomeNote` ("Välkommen till Fiskfiskarnas Kart app!") som leder hit, med en välkomsthälsning.

Läs detta innan du ändrar Hjälp, lägger till en funktion i appen eller spelar in
animeringarna igen.

---

## 1. Var allt finns

| Vad | Var |
|---|---|
| Sidans text och avsnitt (HTML) | `src/html/40-help.html`, `<div id="helpView">` (sök `id="help-`) |
| Utseende (CSS) | `src/css/60-help.css` |
| Logik (öppna/stänga, nyheter, installera-flikar, prick) | `src/js/30-help.js` |
| "Nytt i appen" | `HELP_NEWS` i `src/js/30-help.js` |
| Animeringarna | `docs/help/<namn>.webp` (görs av verktyget, redigeras inte för hand) |
| Verktyget som spelar in animeringarna | `tools/help_anim.py` |
| Den ritade Safari-telefonen (Installera) | `tools/help_install_anim.html` |
| Test | `tests/test_help.py` |

---

## 2. Avsnitten och deras animeringar

| Avsnitt (`id`) | Animering(ar) | Scen i help_anim.py |
|---|---|---|
| Nytt i appen (`help-nytt`) | – | – |
| Installera appen (`help-installera`) | `installera` | `s_installera` (ritad Safari) |
| Kom igång (`help-start`): Vem är du?, startfilmen, välkomstrutan, menyn | – (bara text) | – |
| Kartan (`help-kartan`) | `kartan` | `s_kartan` |
| Kartlägen (`help-kartlagen`) | `kartlagen` | `s_kartlagen` |
| Din position (`help-position`) | `position` | `s_position` |
| Lodet (`help-lodet`) | `lodet` (+ tryck på lodets ruta = markering) | `s_lodet` |
| Fiskeplatser och markeringar (`help-platser`) | `platser` (lägg till), `andra` (ändra/ta bort) | `s_platser`, `s_andra` |
| Fara & Träffpunkt (`help-fara`) | `fara` | `s_fara` |
| Båtarna och profilerna (`help-batar`) | `batar` | `s_batar` |
| Tävlingarna (`help-tavling`): tävlingslåset, live, Ledare, senaste fisk, Demo Mode | – (bara text) | – |
| Mätverktyget (`help-mat`) | `mat` | `s_mat` |
| Väder, vind & lä (`help-vader`) | `vader` | `s_vader` |
| Blixtar (`help-blixtar`) | `blixtar` | `s_blixtar` |
| Kartanalys (`help-analys`) | `analys` (Djup + dra, 💡, + Branta kanter, Tumregler tar över, Fångster, tillbaka till Kartdata) | `s_analys` |
| Heatmap (`help-heatmap`) | `heatmap` (knappen överst, fyra stilar, När, tryck på en fångst) | `s_heatmap` (låtsasfångster `catch_rows()` via fakefb:s Fiskfiskarna-API, bara på vattnet: `water_catches()`) |
| Åk hit (`help-akhit`) | `akhit` | `s_akhit` |
| Snabbmeddelanden (`help-meddelanden`) | `meddelanden` (skicka + Calle och Pia i samma båt = en bubbla → tryck på Calles rad → rutan → Åk hit) | `s_meddelanden` |
| Filter (`help-filter`) | `filter` | `s_filter` |
| Spåren och loggen (`help-logg`) | `logg` (Filter → Spår-ikonen = spårmenyn, sedan Logg) | `s_logg` |
| Inställningar (`help-installningar`) – även Håll skärmen tänd | `installningar` (avsnitten; som "Calle" – Filip har Admin-raden) | `s_installningar` |
| Tips & felsökning (`help-tips`) | – (bara text) | – |
| Om appen (`help-om`) | – (källor + version) | – |

Admin står medvetet INTE i Hjälp (bara Filip). Demo Mode står med sedan 2026-10-04 (rutan överst, Tävlingarna,
Inställningar) – det är dit tävlingslåset skickar folk.

---

## 3. Recept

### En ny funktion eller förbättring i appen
**Gör det inte direkt:** skriv upp det i `tools/HJALP_TODO.md` och ta allt i en Hjälp-omgång när
Filip väljer det (påminn honom när listan har ≥ 5 rader eller är > 1 vecka gammal). Vid omgången:
1. **Lägg till en rad överst i `HELP_NEWS`** (nyast först):
   `{ d: 'ÅÅÅÅ-MM-DD', t: 'new' | 'better' | 'fixed', x: 'text (får ha <b>fetstil</b>)' }`
   → NYTT / BÄTTRE / FIXAT. Den som inte läst den får en orange prick på menyn.
   (Pricken bygger på antalet rader: `ffmap_help_seen_v1` = hur många man sett.
   Ta därför aldrig bort gamla rader – då räknas nästa nyhet som redan läst.)
2. Beskriv funktionen i rätt avsnitt – eller gör ett nytt avsnitt (se nedan).
3. Syns funktionen i en befintlig animering (knappar, rutor, färger ändrade)?
   Spela in den igen (se "Spela in animeringar").
4. Bygg + kör testerna.

### Ett nytt avsnitt
1. I `src/html/40-help.html`, inne i `#helpBody`, kopiera ett `<section class="helpCard" id="help-…">`.
   Rubrik `<h3><span class="hIc">EMOJI</span>Titel</h3>`, sedan animering och `<ul>` med
   korta punkter. `<b class="hA">…</b>` = orange (det man ska göra, t.ex. "Tryck").
   Flera animeringar i ett avsnitt: rubrik över varje med `<p class="helpSub">…</p>`.
2. Lägg till en länk i innehållsförteckningen `#helpToc`: `<a href="#help-…"><span>EMOJI</span>Titel</a>`.
   (Håll antalet jämnt – två kolumner, nu 22. test_help räknar länkarna och animeringarna (19): uppdatera siffrorna.)
3. Animering: `<div class="helpAnim"><img loading="lazy" src="help/NAMN.webp" alt="…"></div>`
   och en scen i `tools/help_anim.py` (se nedan). Verktyget skriver in `width`/`height`.
4. Uppdatera tabellen i avsnitt 2 här, och antalet animeringar i test_help.

### Spela in animeringar
```
py -3 tools/help_anim.py              (alla, ~5 min)
py -3 tools/help_anim.py lodet fara   (bara de namngivna)
py -3 tools/build.py                  (efteråt – storleken skrivs i src/html/40-help.html)
```
Titta alltid på resultatet innan det publiceras (t.ex. några bilder ur varje fil) –
särskilt att inget hamnat på land och att inget ligger i vägen.

---

## 4. Så fungerar help_anim.py

- **Riktiga appen i testwebbläsaren** (Playwright + Edge, som testerna), iPhone-storlek
  390 × 844, skärpa ×2. Egen webbserver (port 8896) för hela repot.
- **Aldrig riktiga tjänster:** `tests/fakefb.py` blockerar Firebase, googleapis och FMI;
  service workers är avstängda. Väder (Open-Meteo) och blixtar (FMI) får låtsassvar.
- **Låtsasdata:** fiskeplatser (`SPOTS`), båtar (`BOATS`), vind, blixtar – per scen.
- **Allt på sjön (Filips krav):** alla platser är fasta punkter på Regnarens vatten (`P`:
  B1–B5 och E1 i södra bassängen och viken österut, T1–T3 i norra). Mellanpunkter
  (`mix`) och varje GPS-steg kontrolleras med `check_water()` mot djupdatan
  (≥ 1 m) – hamnar något på land avbryts inspelningen. Båtar står inte där man trycker.
- **Båtfart:** `sail()` skickar GPS-positioner i båtfart (4,5–8 m/s ≈ 9–15 knop),
  en var 0,5 s. För fort ser konstigt ut på fartmätaren.
- **Fingret:** en vit prick visas där "fingret" trycker (`FINGER_JS`).
- **Inspelning:** webbläsarens egen skärminspelning (CDP `Page.startScreencast`) –
  mjukt och i verklig takt. Bildkvittot skickas från vänteloopen, inte från
  händelsen (annars stannar inspelningen efter några bilder).
- **Fil:** animerad WebP, 432 px bred, högst ~6 bilder/s, kvalitet 42 → 150–1000 kB
  styck. Utsnitt per scen med `Y(y0, y1)` (en del av skärmen) för att hålla nere storleken.
- **Hjälpfunktioner i appen** (bara för test/verktyg): `window.__ffGeo`
  (`depthAt`, `lake`, `screenOf`, `at`), `window.__ffLightningFetch()`, och i
  låtsas-Firebase `__addPos()` (flytta en båt).
- **Installera** kan inte spelas in (Safaris menyer är inte en webbsida): en ritad
  telefon i `tools/help_install_anim.html` med en tidslinje i `play()`.

- **Inställningar börjar med alla avsnitt stängda** i verktyget (`open_app` sätter `ffmap_settings_open_v1` = `[]`;
  testerna öppnar alla via fakefb) – scenen öppnar dem själv.
- Blixtar-scenen har nedslag nära båten → **åsklarmet** poppar upp; scenen trycker OK.
  Ändras något som täcker kartan (larm, rutor) – kontrollera att scenerna fortfarande visar det de ska.
- Byts en knapp i appen (t.ex. uppdatera → förstoringsglaset) syns den i nästan alla
  animeringar: spela in alla igen.

### Lärdomar från första inspelningen
- Skärmbilder (`page.screenshot`) är för långsamma (~2 bilder/s, hackigt) → screencast.
- Första versionen tryckte på Calles båt i stället för kartan – ställ inga båtar där
  scenen trycker.
- Dubbeltryck zoomar kring punkten: flytta först sjön till mitten (`bring`), annars
  zoomar man in på land.
- Blixtarna måste ligga nära (1–2 km) och kartan får inte zoomas ut för mycket –
  annars hamnar de utanför bild eller sjön blir pytteliten.
- Utan förbokad storlek hoppade sidan när animeringarna laddades (och vridning hamnade
  fel) → `width`/`height` på varje `<img>` (skrivs av verktyget).

---

## 5. Beteende att känna till

- **Öppnas aldrig själv** (sedan 2026-10-06): välkomstrutan efter varje namnval leder hit (`showHelpView(true)` = med
  hälsningen). Testerna startar med Hjälp "läst" och utan välkomstruta (fakefb sätter `ffmap_help_seen_v1` och
  `__ffNoWelcome`), utom test_help och test_splash som använder `help_seen=False`.
- **Installera-avsnittet** väljer flik efter webbläsare: iPhone Safari, iPhone Chrome
  (`CriOS`), Android (knappen **Installera** via `beforeinstallprompt` om Chrome erbjuder
  det). I hemskärmsappen (`navigator.standalone` / `display-mode: standalone`) visas bara
  "✓ Du använder redan hemskärmsappen".
- **Vridning** (hemskärmsappen laddar om sidan): Hjälp sparas i `saveRotationState()` som
  "vilket avsnitt + hur långt in" (`helpPlace()`/`helpGoTo()`), inte pixlar. Platsen mäts
  **när man skrollar** (`helpLastPlace`) – när vridningen märks har sidan redan ritats om i
  den nya bredden och mätningen skulle ge fel avsnitt.
- **Sök** (`#helpSearch`, överst): varje ord måste finnas i samma rad eller i avsnittets rubrik;
  rubrik väger mest, helt ord mer än del av ord. Tryck på en träff = dit, raden blinkar.
  Ny text i Hjälp blir sökbar av sig själv (alla `li`, `p` och steg indexeras).
- **Filter-avsnittet** förklarar varje filter i en lista (`.helpDefs`) – nytt filter = ny rad där.
- Animeringarna laddas först när man skrollar fram till dem (`loading="lazy"`); en som
  saknas döljs.
