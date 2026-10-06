# Namnvalet "Vem är du?" – ny design

Sidochatt-plan (2026-10-03). Inget är byggt i `src/`. Filip har sett och godkänt förslaget (Opus-varianten).

**Förslaget att titta på:** `tools/mock_namnval.html` (öppna i webbläsaren; servern "namnval" i `.claude/launch.json`,
port 8897, `http://localhost:8897/mock_namnval.html`). Källa `tools/mock_namnval.src.html`; `py -3 tools/mock_namnval.py`
bakar in profilbilderna, loggan och kartbilden. Mockupens CSS är facit för mått och färger nedan.
Tas bort (mock + .py + launch-posten) när det är byggt.

## Vad som ändras
Den lilla rutan i mitten (`#nameModal`, 340 px, chips med bara text) blir en **helskärm** med loggan, rubrik och
**profilbilderna i ett rutnät**. Identiteten ändras INTE: `nameSlug`, `canonicalName`, `saveUserName`, `NAME_ROSTER`,
`localStorage regnaren_user_name_v1`, Logga ut och flödet efter Fortsätt (`continueBootAfterName`, Hjälp första gången) är som förr.

## Utseende (stående telefon, 375 px)
Uppifrån och ner:
1. **Bakgrund:** kartan syns svagt bakom – `#nameBackdrop` blir täckande toning i nattvatten
   `linear-gradient(rgba(6,20,28,.55), rgba(6,20,28,.92) 45%, #06141C)` + `backdrop-filter: blur(6px) saturate(.6)`
   (`-webkit-` också). Om kartan inte hunnit ritas syns bara nattvatten – helt ok. (Mocken använder en kartbild i
   stället; i appen ligger riktiga kartan redan under.)
2. **Loggan** `assets/ff_logo.svg` (röd gädda "FISK FISKARNA"), 150 px bred, centrerad, `rotate(-5deg)`,
   `filter: drop-shadow(0 6px 14px rgba(0,0,0,.5))`, toppen `env(safe-area-inset-top) + 22px`.
   Faller in en gång: `opacity 0 → 1, translateY(-14px) scale(.9) → 0`, 450 ms, `cubic-bezier(.16,1,.3,1)`.
   **Färgundantag:** loggans röda (#EE2A28) får bara finnas här – skriv in det i DESIGN.md (Brand / Do's).
3. **Rubrik** "Vem är du?" 28 px 700, morgondimma, 10 px under loggan. **Undertext** "Tryck på dig själv" 14 px vassgrå.
   Den gamla långa förklaringen (`.modalDesc`) tas bort.
4. **Rutnätet** (`#nameList`, skrollar, resten av höjden): `grid-template-columns: repeat(3,1fr)`, `gap: 16px 6px`,
   `padding: 18px 14px 110px` (plats för knappen), mjuk kant upptill `mask-image: linear-gradient(transparent, #000 18px)`.
   Varje person (`.nameChip`, en `<button>`): rund bild **70 px** (`AVATARS[namn]`, `object-fit: cover`) med
   `box-shadow: 0 0 0 2px rgba(255,255,255,.16), 0 4px 12px rgba(0,0,0,.4)`, namnet under (13,5 px 600, 6 px mellanrum).
   Saknas bild (gammal/ny i listan) → bokstavscirkel i bärnsten med sjökortsblå bokstav (samma som profilplanen).
   Tonas fram vid öppning: `opacity 0, translateY(8px)` → på plats, 300 ms, fördröjning `min(i,15) × 22 ms`.
   Tryck: bilden `scale(.94)`.
5. **Valt:** ring `0 0 0 3px #E8A33D, 0 0 0 7px rgba(232,163,61,.22)`, namnet bärnsten, liten bärnstensbricka med ✓
   (24 px, nere till höger, 2 px kant i nattvatten). **Alla andra** `opacity .42` + `grayscale(.7)` (200 ms).
6. **"Annat namn"** = sista rutan i rutnätet (`.nameChip--other`, `data-other`): streckad cirkel 70 px
   (`2px dashed rgba(255,255,255,.3)`) med ett "+" (34 px, vassgrå), texten "Annat namn" vassgrå. Vald: hel
   bärnstensring 3 px, "+" och text i bärnsten; alla personer `opacity .3` + `grayscale(1)`; textfältet visas
   ovanför knappen och får fokus, rutnätet skrollar till botten (`padding-bottom` 180 px så rutan syns ovanför fältet).
7. **Nederkant** (fast, `padding: 28px 16px env(safe-area-inset-bottom)+10px`, toning `rgba(6,20,28,0) → #06141C 34 %`):
   - `#otherNameWrap` / `#nameInput`: 50 px högt, 10 px rundning, 8 % vitt, 18 % kant, 16 px text (som förr), 10 px under.
   - `#nameSave`: hela bredden, **54 px**, 12 px rundning, 17 px 700.
     Inget valt: 10 % vitt, vassgrå text "Välj dig själv" (Annat namn utan text: "Skriv ditt namn").
     Valt: bärnsten med sjökortsblå text **"Fortsätt som <namn>"** (även för skrivet namn, uppdateras vid `input`).
     Knappen är aldrig `disabled` – tryck utan val visar `#nameError` som förr (rött, ovanför knappen).
8. **Reducera rörelse:** inga animeringar/övergångar (bara tona in).

**Liggande** (`@media (orientation: landscape) and (max-height: 500px)`): loggan 80 px, rubrik + undertext på samma rad
bredvid, rutnätet `repeat(6,1fr)`, bilder 56 px. **Breda skärmar:** innehållet högst 520 px brett, centrerat.

## Kod (main-chatten bygger)
- `src/html/50-sheets.html`: `#nameModal` får `<img class="nameLogo" src="ff_logo.svg" alt="Fiskfiskarna">`,
  rubrik, undertext, `#nameList`, `#otherNameWrap`, `#nameError`, `#nameSave`. Behåll alla id:n.
- `src/css/40-spots-boats.css`: byt `#nameBackdrop`/`#nameModal`/`.nameList`/`.nameChip*`-reglerna mot ovan
  (`#nameModal` blir `position:fixed; inset:0; display:flex; flex-direction:column`, z-index som förr, 40/41).
  `.modalTitle`/`.modalDesc` används av andra rutor – rör inte dem, ge namnvalet egna klasser.
- `src/js/34-name.js`:
  - `renderNameList()`: chip = `<span class="ava"><img src=AVATARS[n]></span>` + namn (eller bokstav), `style.animationDelay`;
    Annat namn-rutan = `<span class="ava">+</span>Annat namn`. Behåll klasserna `nameChip`, `nameChip--other`,
    `data-name`, `data-other` (fakefb, test_rotation och 92-rotation.js använder dem).
  - Klick: lägg `has` på `#nameList` (dämpar övriga) och `otherMode` på `#nameModal`; ny `updNameBtn()` sätter
    knappens text + klass `on`; anropas vid klick, `nameInput` `input`, `showNameModal()`.
  - Annat namn: `nameListEl.scrollTop = nameListEl.scrollHeight` efter att fältet visats.
- `src/js/92-rotation.js`: oförändrad logik (sel/other/text/scroll); kalla `updNameBtn()` efter återställningen.
- `tools/build.py`: kopierar inte `.svg` ur `assets/` – släpp igenom `ff_logo.svg`
  (`if f.endswith('.svg') and f != 'ff_logo.svg': continue`). Lägg den i sidans `precache`-lista (sw.js tar bilder
  ur cachen) så att den finns offline efter Logga ut.

## Tester
- Befintliga ska gå som förr: `tests\run_all.ps1 avatar rotation review3` (+ fakefb:s namnval i alla tester).
- Ny `tests/test_name_picker.py`: rutnätet har en bild per namn i listan + Annat namn sist; tryck på ett namn →
  `.selected`, knappen "Fortsätt som X" med klass `on`; Annat namn → fältet syns, skriv → knappen följer texten;
  Fortsätt utan val → `#nameError` syns; loggan laddad (`naturalWidth > 0`); liggande 6 kolumner.
- Större ändring (CSS + JS + build) → kör **hela sviten** efteråt.

## Status (2026-10-03): BYGGT
HTML `50-sheets.html`, CSS `40-spots-boats.css`, JS `34-name.js` (`updNameBtn`), 92-rotation (precache + `updNameBtn`), build.py
(`ff_logo.svg` till docs/). Test: `tests/test_name_picker.py`. Mockfilerna och launch-posten är borttagna, DESIGN.md uppdaterad.

## Efteråt
- `tools/HJALP_TODO.md`: "Vem är du? – ny startskärm med profilbilder och loggan" (ev. ny skärmbild i Hjälp/första
  välkomsten; nyhetsrad: "Nytt utseende när du väljer namn – hitta dig själv på bilden").
- DESIGN.md: loggans rödfärg som undantag på startskärmen; namnvalet som helskärm (Components).
- Ta bort `tools/mock_namnval*` och launch-posten "namnval".
