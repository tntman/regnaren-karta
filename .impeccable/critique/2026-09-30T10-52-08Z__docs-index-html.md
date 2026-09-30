---
target: hela appen (docs/index.html)
total_score: 25
max_score: 40
na_heuristics: 
p0_count: 1
p1_count: 3
target_identity: "file:E:\\github\\regnaren-karta\\docs\\index.html"
target_fingerprint: "sha256:2d289bc18408e72782d1508f724171a7485bcb665fabb9e0c0cdbc9d0e2ddf94"
target_path: "E:\\github\\regnaren-karta\\docs\\index.html"
timestamp: 2026-09-30T10-52-08Z
slug: docs-index-html
---
Method: dual-agent (A: design review with screenshots · B: impeccable detector CLI + browser), both against the fake-Firebase test harness.

# Critique: FF Map (docs/index.html)

| # | Heuristic | Score | Key issue |
|---|---|---|---|
| 1 | Visibility of system status | 3 | Speed/depth, Heatmap pill, "uppdaterad" good; freshness of boats/weather only inside cards |
| 2 | Match system / real world | 3 | Good fishing Swedish; "Zoom 15,2 lager 15" jargon; heatmap rainbow collides with depth rainbow |
| 3 | User control and freedom | 2 | "Ta bort" deletes for everyone without confirm/undo; weather card doesn't close on map tap |
| 4 | Consistency and standards | 2 | DESIGN.md rules broken: amber for non-selected, serif view titles, pink Liknande accent, full-width landscape spot sheet |
| 5 | Error prevention | 2 | Ta bort adjacent to Spara (35px); lightning alarm silenced by hiding the Blixtar layer |
| 6 | Recognition rather than recall | 2 | Heatmap only via long-press; "hold = all map styles" invisible; no Heatmap in Help |
| 7 | Flexibility and efficiency | 3 | Tap/hold map styles, Åk hit everywhere, Liknande from spot/catch |
| 8 | Aesthetic and minimalist design | 3 | Map at rest clean; Settings 2,900px, Filter 15 toggles, Liknande note heavy |
| 9 | Error recovery | 2 | Deleted spot gone for all; silent Firestore failures |
| 10 | Help and documentation | 3 | Rich searchable Help, but a 20-tile wall; not competition-day oriented |
| Total | | 25/40 | Acceptable |

## Priority issues
- [P0] Lightning alarm only fires when the Blixtar layer is on (60-lightning-alarm.js:36). Fix: decouple, "Åskvarning av" badge, "Åk hem" action, 48px full-width OK. /impeccable harden
- [P1] Delete without guard (24-boats.js:426): separate from Spara, undo toast "Borttagen · Ångra" 6 s. /impeccable harden
- [P1] Touch targets below 48px: header 40, Filter hit area 20px tall, weather chip 25, segments 26, chips 29, type pills 31, actions 35, alarm OK 34. /impeccable adapt
- [P1] DESIGN.md rules broken (amber decoration, serif headings, pink accent, landscape sheet width, add-button, contrast Fara 3.4:1, disabled chip 2.5:1, grip ✕ 2.6:1). /impeccable polish, colorize
- [P2] Too much at once: Filter 15 toggles mixed kinds, Heatmap long-press only + depth rainbow, Settings one long scroll. /impeccable distill, layout

## Detector (B)
docs/index.html: 285 findings (193 design-system-color advisory, 39 gray-on-color = false positive 8.3:1, 10 undersized-ui-text real, 3 low-contrast (Ta bort 4.4:1 real), broken-image #mapImg false positive, cyan-gradient on data scales false positive, layout-transition #offBarFill real). src/html: 10 (mostly unstyled-fragment artefacts). No user-visible overlay (headless).

## Personas
Casey: top-corner controls, 20px Filter hit area, message chips over scale, focus in name field. Sam: 10px zoom text on imagery, 12px segments, Fara 3.4:1, species dot on amber chip. Tävlingsfiskaren: 4 steps to mark with 31/35px targets next to Ta bort, 72% glass in sun, alarm OK 34px no next step, heat blobs hide contours, no competition clock.

## Questions
1. Competition mode? 2. Should safety own the strong signal colours? 3. Heatmap/Liknande answering one question: where next and how far?
