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
svepande ljus), en knapprad: Åk hit, Liknande → Kartanalys "Liknande", Ta bort (röd), Spara.

## Kartanalys ("Hitta ställen")
- Knappen nere till höger `#anBtn` (ersatte uppdatera-knappen); Filter "Kartanalys" visar/döljer
  (på som standard). Panel `#anPanel`: Djup, Branta kanter, Grynnor & hålor, Växter, Hård botten,
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
- **Mjuka kanter**: fälten interpoleras bilinjärt, avstånd till kanten = (värde − 0,5) / lutning
  → kantutjämnat, som lä. Upplösning `viewStep()` (50-wind-lee.js): 1 css-px när kartan står
  still, grövre medan man drar (och på stora skärmar); steget ingår i cache-nyckeln.
- **Av efter omstart** (kvar vid vridning, `rotState`); inget att visa (t.ex. Liknande innan
  platserna laddats) = ingen gråtoning.
- Panelen: ingen rubrik, ✕ i greppremsan, "Rensa" efter en avskiljare, grå utan val, tydlig
  med ljussvep när något är valt. Dra = mindre, snärt/hela vägen = stäng (`sheetSwipe`, tools/UI.md).
- **Liknande**: välj vad som jämförs (djup, lutning, botten, växter, grynna/håla) och område
  (bara platsen/25/50/100 m = snittet inom radien, `anSimFeatures`), med förklaring. Platsen
  själv lyser och får en rosa ring (`.anLbl.simRef`), men står inte i listan (inget inom 60 m);
  listan = de 5 områden med mest lika ställe (små områden lite lägre). "Gå till" (`#anRefGo`).
- Räknas i telefonen på djupnätet (`anBase`: lutning, "högre/lägre än runt om" ~28 m, avstånd
  till land) + `docs/lakes/<id>/bottom_v<V>.txt` (vegetation bit 3, hårdhet 1–4 bit 0–2, RLE
  250 n n; görs av genesis_render, även `grid`) + vinden.
- Canvas `#anLayer` per skärmpunkt, etiketter i `#anLabels`. Val per sjö (`lakeKey`).
  `window.__ffGeo`, `__ffAnalysis()` för tester/verktyg.
