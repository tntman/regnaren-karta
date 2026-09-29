# UI-delar i FF Map – så byggs de

Alla delar finns i `src/app.html` (en fil: CSS överst, HTML i mitten, skript sist).
Använd de här byggstenarna när något nytt ska in, så att allt ser ut och beter sig
likadant. Färger: `--navy` (#0B2A3A, bakgrund), `--navy-glass` (halvgenomskinlig),
`--amber` (#E8A33D, det man ska trycka på / valt), `--offwhite`, `--text-muted`.
Typsnitt: Calibri/Segoe UI; rubriker (sjöns namn, vyer) Cambria (`.kicker`).

---

## Panel från botten (bottom sheet)

Exempel: platsens ruta `#wpSheet`, Kartanalys `#anPanel`.

- `position:absolute/fixed; left:0; right:0; bottom:0`, `background:var(--navy)`,
  rundade hörn upptill (`border-radius:16–18px 16–18px 0 0`), skugga uppåt.
- Dold med `transform:translateY(105%)`, visas med klassen `.show` (`transform:none`)
  och en `transition` på ~0,25 s.
- Ett litet grepp överst: `<div class="grab">` (38 × 5 px, ljus, rundad).
- Bottenmarginal: `calc(env(safe-area-inset-bottom,0px) + 16px)`.
- **Dra ner för att stänga:** `sheetSwipe(panel, stäng)` (i skriptet). Panelen följer
  fingret nedåt; släpps den långt nog (eller snärtas) stängs den, annars studsar den
  tillbaka. Fält, knappar, reglage och `.noSwipe` startar ingen dragning. Lägg till
  `.dragging{transition:none}` för panelen.
- `pointerdown` på panelen ska `stopPropagation()` (annars tolkas det som ett tryck på kartan).
- Liggande läge: panelen till höger, `width:420px`.

## Chips (val)

`.anChips button` – rundade (`border-radius:14px`), ljus kant; vald = `.on` (amber
bakgrund, navy text, fet). Ett val i taget (Kartanalys-lägen) eller flera
(`.anFactors button.on` med ✓ för "Jämför"-valen).

## Segmentknappar

`.segmented` (Inställningar) / `.anSeg` / `.helpSeg`: en rad knappar i en mörk ränna,
vald = `.on`/`.active` (amber). För få, fasta val (Av/5/10/20 km, Bara platsen/25/50/100 m).

## Reglage

- **Ett handtag:** `anRangeRow(id, etikett, min, max, steg, värde, format)` →
  etikett – `<input type=range>` (amber, `accent-color`) – värdet till höger (`output`, amber).
- **Djupintervall, två handtag:** `anDualRow(nyckel)` → en stapel i djupfärgerna
  (samma som skalan nere till vänster: `MAP_STYLES[0].legend`, 0 → sjöns maxdjup),
  två vita runda handtag (26 px), det valda omringat av en vit ram, siffror under
  (`legendTicks`). Dras med pekaren (`anDrag`), steg 0,5 m, handtagen kan inte korsa
  varandra. Registrera nycklarna i `AN_DUAL` (t.ex. `depth: ['lo','hi']`).
  `touch-action:none` på stapeln.

## Av/på-rader (Filter, Inställningar)

`<label class="visRow">` med ikon (`.visSwatch`), text (`.visLabel`) och
`<span class="toggle"><input type="checkbox"><span class="toggleTrack"><span class="toggleThumb"></span></span></span>`.
Sparas i `localStorage` (nyckel `ffmap_…_v1`); sjöspecifikt via `lakeKey()`.

## Faktarutor (platsens ruta)

`.wpData` = rutnät med 4 `.wpTile` (`<i>RUBRIK</i><b>värde</b><small>förklaring</small>`)
+ en rad `.wpTerrain` över hela bredden. Kort text – värdet får inte bli för långt
(t.ex. "Mkt hård", inte "Mycket hård").

## Runda knappar på kartan

Nere till höger: 2 × 2-rutnät, alla lika stora (`--bb`: 48 px, 42 px liggande; mellanrum
`--bgap`), `#locateBtn` (amber) längst ner till höger. Övriga: `--navy-glass`,
`backdrop-filter:blur(6px)`, tunn ljus kant, skugga; aktiv = amber kant/ikon (`.on`).
Lägg nya knappar i rutnätet – inte på egen hand (då hamnar de fel liggande).
Längst ner i mitten: `#msgBtn` (snabbmeddelanden).

## Kort / notiser ovanpå kartan

- **Varning:** `#ltPill` (liten, under väderraden), `#ltAlarm` (stor röd ruta med OK).
- **Info som försvinner själv:** `#wakeNote` – mörk ruta med gul kant, ✕ uppe till höger,
  tonar bort (`.fade`, `transition:opacity`) efter 20 s.
- **Kort toast:** `#msgToast` – liten ruta ovanför knappen, försvinner efter ~2,5 s.

## Märken

`#wakeBadge` – liten gul rund ikon (sol) bredvid ditt namn under sjön; syns bara när
funktionen är på; tryck = stäng av + förklarande notis.

## Pratbubblor vid båtar

`.msgBub` (vit, egen = ljusgul `.mine`), pil nedåt, placeras i skärmkoordinater i
`#msgLayer` och flyttas i `render()`.

## Ritlager (canvas) i skärmkoordinater

Vind/lä, blixtar, Kartanalys: en `<canvas>` i `#stage` över kartan, ritas om i
`render()`. Per skärmpunkt (var 2:a css-px) och cachat per vy (nyckel = origin, skala,
storlek, version) – blir aldrig kantigt inzoomat. Kartanalysens gråtoning: en andra
canvas med `mix-blend-mode:saturation` (grå där kartan ska avfärgas).

## Rotation

iOS hemskärmsapp laddar om sidan vid vridning: öppna paneler/val måste sparas i
`saveRotationState()` och återställas i `restoreRotationUi()` (se CLAUDE.md).

## Tester

Varje ny UI-del ska ha test (Playwright): synlig/dold, val sparas, dra-för-att-stänga,
rotation. Kolla också en skärmdump i stående och liggande (390 × 844 / 844 × 390).
