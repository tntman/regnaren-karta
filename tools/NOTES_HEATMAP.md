# Heatmap (fångster)

Kod: `src/js/66-catches.js` (datan: format, källa, CSV-inläsning), `src/js/68-heatmap.js` (ritning,
bottenrutan, fångstrutan, tryck på kartan), `src/css/72-heatmap.css`, HTML i `src/html/30-map-ui.html`
(`#hmPill`, `#hmPanel`, `#hmCard`), `10-map.html` (`#hmSat`, `#hmLayer`), admin-kortet i
`20-menu-settings.html`. Test: `tests/test_heatmap.py`.

## Så fungerar den
- **Kartlägen** (håll kartlägesknappen): **Heatmap** sist i listan (`.hmOpt`, `data-heat`) – inget kartläge
  utan en bottenruta som Kartanalys (`#hmPanel`). Kartan tonas ner och gråtonas som i Kartanalys
  (samma "Mörkare", `anSet.dim`) – kartläget under behålls.
- Fyra stilar: **Värme** (radie i meter + styrka), **Per art** (värme i artens färg, av/på per art),
  **Rutor** (sexkanter 30/60/120 m fästa i kartan, antal i rutan), **Prickar** (prick per fångst, större
  fisk = större prick, namn om man vill). Filter: art, tävling ("regnaren1" → "Regnaren 1 · 25–26 sep").
- **Tryck på kartan** (`hmTapAt`, anropas från `scheduleProbeTap`): närmaste fångst (+ de andra inom 50 m)
  eller rutans fångster → `#hmCard`: art + cm, vem, när (26/9 13:00), djup där, plats i tävlingen
  ("2 av 37" bland samma art), ‹ › mellan fångsterna där, **Åk hit** (lodet, heatmapen ligger kvar) och
  **Liknande** (Kartanalys Liknande med fångsten som plats: `anExtraRef` i `anSpots()`; heatmapen stängs).
- **Inte samtidigt som Kartanalys**: heatmap på → Kartanalys-läget av; ett Kartanalys-läge valt → heatmap av.
- Översta raden (`.pnHead`, som Kartanalys): resultatet + teckenförklaringen (`#hmLegend`), **ⓘ** (`pnInfo`: noterna i `#hmResult .note` i en ruta), **↺ Återställ** (`HM_DEFAULTS`, grå när allt är som från start) och **⏻ Stäng av heatmap** (`#hmOff`). Art/Tävling: radens namn först (`.rowLbl`), en rad var som skrollar i sidled.
- **När** (`#hmTime`, `hmRenderTime`, sist i bottenrutan): stapel per timme på dygnet (bara timmar med fångster; färg = glöd), "Bäst kl 11–14 · 95 %" (bästa tre timmarna i rad). Tryck en timme / dra över flera = tidsfönster `hmSet.h0..h1` som filtrerar kartan via `hmVisible()` (grafen själv ignorerar fönstret: `hmVisible(true)`); samma timme igen eller ↺ = alla. Resultatraden säger "kl 11–14". Timmar i enhetens lokala tid.
- Sjöns kant: tunn vit linje 50 % som i Kartanalys (`hmShoreLayer`: `anField` med egen cache, `edgeW`).
- Rutan stängd: skylten **Heatmap** under väderchipet (`#hmPill`, klass `.mapPill` som Kartanalys `#anPill`) öppnar den igen.
- **Filter → Lager → Heatmap** (`#toggleHeatmap`) visar/döljer bara, som Kartanalys: `hmOn` = påslagen (kartlägeslistan/rutan),
  `hmShow` = syns på kartan (`ffmap_show_heatmap_v1`, på som standard). Dold: inget ritas, ingen skylt, tryck på kartan gör inget,
  rutan säger "Dold – slå på Heatmap i Filter". Slås den på för hand (kartlägeslistan) blir den synlig igen.
- Färgskalan **"glöd"** (`hmRamp`): mörklila → magenta → orange → bärnsten → varmvitt – aldrig djupskalans
  blå/cyan/grön. Samma i teckenförklaringen, `.hmDot` och `.hmThumb`. Siffran i Rutor blir vit på mörka rutor.
- **Av efter omstart** (som Kartanalys), kvar vid vridning (`rotState.hm`: på, rutan, öppen fångst).
  Inställningarna sparas per sjö (`lakeKey('ffmap_heatmap_v1', …)`).
- Slås den på för hand och mindre än hälften av fångsterna syns ovanför rutan: kartan flyttas så alla syns.

## Datan – byggd för att bytas
- Allt blir samma lilla post: `{ id, t, comp, who, sp: 'abborre'|'gadda'|'gos', cm, lat, lon, px, py }`
  (`normCatch` tål CSV:ns kolumnnamn och liknande namn; komma-decimaler; "Gädda"/"Gadda"/"gadda").
  `id` = tid|namn|art|cm (dubbletter känns igen).
- **Sjö = position**: inom sjöns karta (`catchLakeOf`, geo i lake.json); står det ett sjönamn får det inte
  säga en annan sjö (en grannsjö inom samma kartbild).
- **Källa nu** (`CATCH_SOURCE`): Firestore `catches/<lake>` = `{ lake, n, rows: '<json [[t, comp, who, sp, cm,
  lat, lon], ...]>', updatedBy, updatedAt }` – en läsning när heatmapen används (+ kopia i localStorage).
  Ett dokument rymmer ~14 000 fångster (1 MiB).
- **Admin → Fångster (heatmap) → Läs in CSV-fil**: sorterar på sjö, lägger till nya, hoppar över dubbletter,
  andra sjöar och rader utan position – samma fil kan läsas in igen.
- **Senare (live-databasen)**: skriv en ny källa med samma `load(lakeId, cb)` som ger poster via
  `normCatch` och peka `CATCH_SOURCE` på den – ritning och rutor behöver inte ändras.

## Firestore-regel (läggs till i konsolen)
```
match /catches/{lake} {
  allow read: if request.auth != null;
  allow write: if request.auth != null && request.resource.data.rows is string && request.resource.data.n is number;
}
```
