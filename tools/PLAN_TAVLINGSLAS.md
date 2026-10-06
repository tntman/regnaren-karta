# Tävlingslås – kartan går inte att ändra mellan tävlingarna

Status: **byggt** (2026-10-04). Granskat av Opus, besluten tagna av Filip.

## Mål (Filip)
Mellan tävlingarna ska ingen kunna ändra platserna på den delade kartan. Försöker man visas en ruta med vad som gäller, när
kartan öppnar och en knapp till Demo Mode, där man får prova fritt.

## Beslut (Filip, 2026-10-04)
| Fråga | Beslut |
|---|---|
| Vad låses | Allt med platser: lägga, ändra namn/typ, ta bort – även sina egna |
| Fara och Träffpunkt | Låses också |
| När kartan är öppen | Från **7 dagar före** till **7 dagar efter** en tävling på sjön (tävlingens datum), och alltid när en tävling har status `active` |
| Appen vet inte (ingen kopia, API-fel, CORS) | Öppen |
| Båtpositioner, snabbmeddelanden, spår | Låses inte |
| Admin (upplåst) | Alltid öppen |
| Demo Mode | Alltid öppen |
| Nödbrytare | Admin → Tävlingslåset "På / Av för alla" (per sjö, `config/<sjö>.lockOff`, `js/26-sync.js`) |
| Rutan | Vad som gäller, när den öppnar ("Öppnar 17/10 inför Regnaren 5"), förklaring av Demo Mode, knapparna Öppna Demo Mode + Stäng |

## Hur det är byggt
- `mapEditAllowed()` sist i `js/66-catches.js`: `TEST_MODE || isAdminUnlocked() || compLockOff || !catchHist || catchErr` → sant; annars sant
  om någon av sjöns tävlingar i API-kopian är `active` eller har ett datum inom ±7 dagar från i dag.
- `showLockCard()` visar `#lockCard` (`html/50-sheets.html`, samma stil som båtrutan). Är kopian äldre än 1 h hämtas den igen
  i bakgrunden – svaret gäller från nästa försök (misslyckas hämtningen blir läget "vet inte" = öppet).
- Grindar (i `js/24-boats.js`): `placeWaypointAtScreen` (långtryck, "Lägg här", GPS-knappen), typknapparna, Spara och Ta bort i arket
  för en befintlig plats. **Inte** i `deleteWaypointById` – den används också när en utgången Träffpunkt tas bort, när din förra
  Träffpunkt ersätts och vid Avbryt på en ny plats. En ny plats (skapad medan kartan var öppen) går alltid att spara/avbryta.
- "Öppna Demo Mode" = som Hjälpens länk: Inställningar → Avancerat, scrollar till `#demoModeToggle`.

## Granskningen (Opus) – det som ändrades mot första planen
- Fara/Träffpunkt kunde inte undantas i `placeWaypointAtScreen` (platsen skapas som Markering innan typen väljs) → Filip: låses också.
- Ingen grind i `deleteWaypointById` (se ovan).
- "Tävlingen syns sent" försvann med veckofönstret.
- Testerna: `fakefb` svarar alltid utan tävlingar → alla tester hade blivit låsta. I stället är låset av i testwebbläsaren
  (`window.__ffNoLock`, satt av fakefb) utom med `cfg={'lock': True}` (`tests/test_lock.py`).

## Risker (godtagna)
- **Bara i appen.** Firestore-reglerna släpper in alla inloggade (anonymt) – en vänlig spärr, inte säkerhet. Hårt skydd = Gruppkod
  (CLAUDE.md, Idéer).
- En tävling som läggs upp i Fiskfiskarnas API mindre än en vecka innan syns när kopian hämtas (vid start/när appen blir synlig om
  kopian är > 1 dygn, eller direkt vid ett låst försök om den är > 1 h).
- iPhone-appen (gren `app`) får låset när main slås ihop in i den.
