# Fiskfiskarnas API (Jonathans live-data)

Källa: Jonathans PDF:er "Fiskfiskarna API – guide för appar" (2 okt 2026) och "API · heatmap" (okt 2026).
Bas: `https://fiskfiskarna.se/api/` – JSON. **Läsa kräver ingen inloggning.** Skriva kräver aktiv tävling
eller token. Kopplas till heatmapen via `load(lakeId, cb)` i `NOTES_HEATMAP.md` (inte gjort än).

## CORS
Webbappar på `regnaren-b8b6a.web.app` och `regnaren-b8b6a.firebaseapp.com` får anropa. Ny domän (t.ex.
GitHub Pages) måste Jonathan lägga till i `config.php`. Native-app (Capacitor) och Cloud Functions berörs inte.

## Filer
| Fil | Gör | Kräver |
|---|---|---|
| `dashboard.php` | All statistik i ett GET, inga parametrar (några hundra kB, räknas om vid varje anrop) | inget |
| `tavling.php` GET | Tävlingar, deltagare, fångster (`?action=…`) | inget |
| `tavling.php` POST | Registrera/annullera fångst, lägga till bild | aktiv tävling + deltagarnamn |
| `auth.php` | Logga in → token (90 dagar) | användarnamn + lösenord |
| `admin.php` | Tävlingar, fiskare, avsluta tävling | token, roll admin (annars 403) |

## dashboard.php → nycklar
- `dashboard`: en rad per fiskare, sorterad på ELO (`angler_id`, `rank`, `elo_out`, `totl`, `totalezcm`, `fisk_a`).
  Obs: guidens exempel använder `r.fiskfiskare` som namnfält – kolla verkligt svar innan det används.
- `anglers`: `angler_id`, `name`, `nickname`, `image_url`, `active` ("TRUE"), `bio_short`, `gear`
- `competitions`: `competition_id`, `competition_name`, `date` ("YYYY-MM-DD" eller "TBD"), `status`
  (done/planned/active), `water`, `days`, `participants`
- `results`: per fiskare och tävling – `rank`, `totl`, `fisk_a`, `lg/la/lgo` (längsta gädda/abborre/gös),
  `top5g/top5a/top5go`, `elo_in/out/gain/bonus`, `participation_bonus`
- `anglerStats`: `WIN%`, `TÄVLING(Antal)`, `FISKEDAGAR`, `CatchPerDay`, `BIG5 GÄDDA`, `100+Gäddor`, `BÄSTA TOTL`
- `records`: `RECORD_ART` (Pike/Perch/Zander), `RECORD_CM`, `RECORD_DATUM`, `RECORD_ACTIVE`
- **`heatmap`**: alla fångster med GPS (ordinarie, Open, event; inte annullerade/test). ~900 punkter.
  `{timestamp, competitionId, name, species, cm, lat, lng, lake}` – species `Gadda|Abborre|Gos`, tid UTC.
  Innehåller även fångster under minimimått; **inget "godkänd"-fält än** (be Jonathan om det behövs).
- `malarenOpen`, `fiskfiskarnaOpen`: Open-serierna (`year`, `angler_id`, `species`, `cm`, `approved`, `displayValue`)

Ingen filtrering i anropet – hämta en gång, filtrera i appen (art, sjö, tävling, längd, tid).

## tavling.php GET (`?action=`)
`getAllCompetitions` (→ `competitions:[{competitionId, competitionName}]`), `bootstrap&competitionId=…`
(namn, bild, `participants`, `catches`), `getReportData&competitionId=…` (samma, tävlingen som eget objekt),
`health`.
- Deltagare: `{participantId, name, imageFile}`
- Fångst: `{timestamp, competitionId, name, species, cm, approved, displayValue, reportedBy, voidRef, lat, lng, imageUrl}`
- **Annullerad fångst = två rader**: originalet + en rad med `displayValue:"VOID"` där `voidRef` = originalets
  `timestamp`. Filtrera bort båda vid poängräkning.

## tavling.php POST (JSON i body, helst `Content-Type: text/plain` → ingen CORS-preflight)
- `verifyAccessCode {code}` → `{ok, verified, competitionId}` (eller `reason:"inactive"`)
- ingen `action` = spara fångst: `competitionId, name, species, cm, reportedBy`, valfritt `lat, lng, imageUrl, userAgent` → `{ok, saved, competitionId}`
- `voidCatch {competitionId, voidRef, voidedBy}` → `{ok, voided}`
- `addImageToCatch {competitionId, catchTimestamp, imageUrl, updatedBy}` → `{ok, updated}`

Serverregler: tävlingen måste vara aktiv; `name` och `reportedBy` måste vara deltagare (matchas på namn, t.ex.
"Filip"); `cm` 0–300, under minimilängd sparas som ej godkänd; lat/lng med punkt eller komma; bilder bara från
`https://res.cloudinary.com/` (ladda upp dit först). Allt loggas.

## auth.php
`POST {action:"login", username, password}` → `{ok, token, user:{username,name,role}}`; `activate {username, code, password}`
(första gången, kod från Jonathan); `logout` + token; `GET ?action=me` + token (401 om ogiltig). Header
`Authorization: Bearer <token>`. Roller: `fiskare`, `arrangor`, `admin`. 8 felförsök/15 min → spärr en stund.
Token i Keychain (iOS), aldrig lösenord i appen/koden/testerna.

## Format och regler
- Tävlings-id i tavling.php: gamla `sibbo6`, `malarenOpen` och nya `sibbo_27_01` fungerar båda. I dashboard alltid koden (`sibbo_26_01`).
- `angler_id`: `ANG001` osv. för gamla, användarnamnet för nya.
- Arter: `Gadda`, `Abborre`, `Gos` (+ `Adel`). Minimilängd: gädda 50, abborre 25, gös 35, ädelfisk 30 cm.
- Tider UTC ISO med ms (`2026-09-25T07:27:18.684Z`) → visa i `Europe/Stockholm`.
- Fångsts-id = dess `timestamp` (skicka tillbaka exakt samma sträng vid annullering/bild).
- `displayValue`: `"55 cm"` om godkänd, annars `"-25 abborre"`.
- TotL = summan av de 5 längsta godkända per art; lika → summan av längsta gädda+abborre+gös.
- Profilbilder: filnamn (`ang001.jpg`; dashboarden `img/`, tävlingsappen `bilder/`). Fångstbilder: full Cloudinary-url.

## Hur ofta (delat webbhotell – var snäll)
- `dashboard.php`: vid start, sedan högst 1 gång/minut eller vid pull-to-refresh. Heatmapen ändras vid nya fångster.
- `tavling.php?action=bootstrap&competitionId=…`: var 10–30:e s, **bara när tävlingen är aktiv och vyn är öppen**.
- Pausa när appen ligger i bakgrunden/skärmen släckt. Fråga bara aktiva tävlingar (status `active` i dashboard).
- Live-poäng räknar appen själv från bootstrap-fångsterna; placering/ELO uppdateras först när admin avslutar.

## Exempel
```js
const API = 'https://fiskfiskarna.se/api/';
const data = await fetch(API + 'dashboard.php').then(r => r.json());
const gaddor = data.heatmap.filter(p => p.species === 'Gadda' && p.lake === 'Regnaren');
```
