# Kartanalys, lodet, rutten, Åk hit och platsens ruta

Kod: `src/js/56-analysis.js` + `src/css/70-analysis.css` (Kartanalys), `12-map.js` (lodet), `40-route.js` (rutten),
`58-akhit-spotdata.js` (Åk hit, faktarutorna), `24-boats.js` (platsens ruta öppna/spara).
Tester: `test_analysis.py`, `test_probe.py`, `test_newfeatures.py`, `test_types.py`.

## Lodet och rutten sjövägen
- **Lodet** visar djup · sträcka SJÖVÄGEN · restid. Rutt: grovt rutnät (~9 m), Dijkstra från
  lodet (en gång per lod) → sedan "gå nedför" från båten vid varje GPS-fix; håller avstånd
  från land; räta ut med siktlinjer. Fart: aktuell om ≥1,5 kn, annars snitt/marschfart.
- **Dijkstra** (`routeFieldTo`): köa det SPARADE float32-värdet – float64 i kön gjorde att
  sökningen stannade (bara djup + avstånd, ingen linje/tid; hände 2026-09-29). Hittas ingen
  väg: vit prickad linje rakt dit och "… fågelvägen" (`probeCrow`, `#routeLayer.crow`).

## Åk hit
Knapp i platsens ruta `#wpGo`, och i Kartanalys-listan: bara lodet släpps på platsen (djup,
sträcka sjövägen, tid, rutten); kartan zoomas så båten, rutten och målet syns (`startNav`).
Inget extra kort (Filip: behövs inte).

## Platsens ruta
✕ i greppremsan (ingen Avbryt – `#wpCancel` är krysset, 16 px, samma grå som strecket), namn,
vem/när (namnet i fetstil, + typen som mini-pill för andras, `ADMIN` när admin ändrar andras),
faktarutor under platsen (`renderWpData`: djup, lutning, botten = hårdhet närmast inom 15 m,
växter = andel inom 25 m; bara rubrik + värde), typpiller (dolda för andras; vald typ har ett
svepande ljus), en knapprad: papperskorg (Ta bort, längst till vänster, dämpad röd kontur, avskild),
Åk hit, Liknande → Kartanalys "Liknande", Spara. **Ta bort** tar bort platsen från kartan direkt men raderar
den (för alla) först efter 6 s: notisen "… borttagen · Ångra" (`#undoToast`) – lämnas appen innan dess
raderas den då (`pagehide`).

## Kartanalys ("Hitta ställen")
- Knappen nere till höger `#anBtn` (ersatte uppdatera-knappen); Filter "Kartanalys" visar/döljer
  (på som standard). När ett läge är på (och syns): skylten **Kartanalys** under väderchipet
  (`#anPill`, som Heatmaps) – tryck = rutan. Panel `#anPanel`: Djup, Branta kanter, Grynnor & hålor, Växter, Hård botten,
  Vindkant, Liknande + förinställt Abborre/Gädda/Gös (tumregler från vanliga fiskeråd, INTE data).
- Djupreglage = stapel i djupfärgerna med två handtag (`anDualRow`). "Mörkare" (standard 72 %)
  ligger i Inställningar (`#anDimSet`) + gråtoning (`#anSat`, mix-blend-mode saturation).
  Reglage för hård botten (hårdhet + djup). "Växter" = var det finns växter.
- **Grynnor & hålor (heter aldrig "toppar") = prominens** (`anDome`: h-dome med morfologisk
  rekonstruktion, bucket-kö i cm; land räknas HÖGT för grynnor och LÅGT för hålor så grunda
  hyllor längs land inte räknas): "kapsyler" ≥ 0,25 m som reser sig ≥ reglaget (standard 0,6 m /
  hålor 0,8 m). Hålor ritas bara med sin djupaste del (`AN_HOLE_CORE` 0,6 m) – annars blev en
  hel djupbassäng en jättehåla (upp till 28 ha). Etiketterna = bara djupet ("2,4 m").
- Sjöns kontur ritas heldragen vit 50 %.
- **Mjuka kanter** (som lä): områdena är ja/nej per rutnätscell – ritat rakt av blev kanten pärlig
  och fladdrade vid panorering utzoomat. Därför ritas de från ett mjukt fält (`anField`: rutnätet
  halveras med medelvärde tills en cell ≈ en ritad punkt, sedan 1-2-1-filter; cachat per resultat
  och nivå), avstånd till kanten = (värde − 0,5) / lutning. Små bitar (< 0,5 i fältet) visas svagt.
  Linjerna aldrig smalare än en ritad punkt åt varje håll, svagare i stället (`edgeW(STEP, css)` i
  50-wind-lee.js) – annars pärlband när varannan px ritas. `tests/test_smooth.py` mäter fladdret. Upplösning `viewStep()` (50-wind-lee.js): 1 css-px när kartan står
  still, grövre medan man drar (och på stora skärmar); steget ingår i cache-nyckeln.
- **Av efter omstart** (kvar vid vridning, `rotState`); inget att visa (t.ex. Liknande innan
  platserna laddats) = ingen gråtoning.
- Panelen (som heatmapens): rubrik "Kartanalys · hitta ställen", **kategorirad** överst (`#anCatSeg`:
  Kartdata / Tumregler / Fångster / Liknande – `anSet.cat`, `anCatOf(mode)`; kategorin med det som är på
  får en amber understrykning), sedan bara den kategorins knappar. Liknande = kategorin själv (inget extra
  val). Längst ner: **✕ Stäng av kartanalys** (`#anClear`, grå när inget är på) och **↺ Återställ**
  (`#anReset`: alla inställningar i panelen tillbaka till start – `AN_DEFAULTS`; läget som visas och
  "Mörkare" i Inställningar behålls; grå när allt redan är som från start). Tumreglerna ser ut som
  vanliga knappar. Dra = mindre, snärt/hela vägen = stäng (`sheetSwipe`, tools/UI.md).
- **Liknande**: välj vad som jämförs (djup, lutning, botten, växter, grynna/håla) och område
  (bara platsen/25/50/100 m = snittet inom radien, `anSimFeatures`), med förklaring. Platsen
  själv lyser och får en rosa ring (`.anLbl.simRef`), men står inte i listan (inget inom 60 m);
  listan = de 5 områden med mest lika ställe (små områden lite lägre). "Gå till" (`#anRefGo`).
- Räknas i telefonen på djupnätet (`anBase`: lutning, "högre/lägre än runt om" ~28 m, avstånd
  till land) + `docs/lakes/<id>/bottom_v<V>.txt` (vegetation bit 3, hårdhet 1–4 bit 0–2, RLE
  250 n n; görs av genesis_render, även `grid`) + vinden.
- Canvas `#anLayer` per skärmpunkt, etiketter i `#anLabels`. Val per sjö (`lakeKey`).
  `window.__ffGeo`, `__ffAnalysis()` för tester/verktyg.

## Från fångsterna (data) – per art
Kod: `src/js/57-an-catches.js` (+ inkopplat i 56-analysis.js), test `tests/test_ancatches.py`.
- Egen rad i Kartanalys under tumreglerna: **Abborre n · Gädda n · Gös n** (tävlingarnas fångster i sjön,
  66-catches.js). Under 10 fångster: grå, "för få". Bara sjön man är i.
- För varje fångst: platsen (inom 25 m, `anSimFeatures(A, 25)`) – djup, lutning, botten, växter, från land
  (`A.shore`), grynna/håla – i steg (`anCatchBins`, cachat per sjö). Jämfört med hela sjön: hur mycket
  vanligare fångsterna var i varje steg ("lift", utjämnad +1). Varje punkt i sjön får summan av log-lift
  för värdena som är på.
- **Tänt**: från mest lik och nedåt tills "Typiskt" av 10 fångster ryms (reglage 5–9, standard 7) – datan
  bestämmer ytan: litet tänt = tydligt mönster (< 12 % tydligt, 12–25 % måttligt, > 25 % svagt).
  **Skala**: hela sjön olikt → mest likt (`anRes.G`, 4:e kanalen i `anField`, färger som heatmapen).
- Av/på per värde (minst ett på); prickarna ●○○–●●● = hur mycket värdet ENSAMT pekar ut arten här
  (tänd yta för samma andel fångster jämfört med ingen information).
- Fångsterna ritas som små vita prickar (`anRes.pts`). Texten säger vad som sticker ut + att det visar var
  man fick fisk (inte var all fisk finns), månad(er), fångster utanför djupkartan räknas inte.
- Inte samtidigt som heatmapen (som alla Kartanalys-lägen).
