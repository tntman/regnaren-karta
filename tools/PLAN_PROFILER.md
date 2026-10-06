# Profiler (fiskarens profil + fångst som snabbmeddelande)

Sidochatt-plan (2026-10-03). Inget är byggt. Mockup visad för Filip i chatten (bottenruta/kort, appens stil).

## Mål
1. **Profilruta** för en fiskare: namn, smeknamn, sedan år, hemvatten, bio, rank/segrar/ELO, största fisk per art,
   senaste tävlingar. Knappar: **Visa på kartan**, **Hans fångster** (heatmap filtrerad på personen).
2. **Live-fångst som snabbmeddelande**: ny fångst i pågående tävling → bubbla ("Gädda 78 cm", ≤ 15 tecken) hos den som fångade.

## Data (verifierat mot API:et 2026-10-03)
Allt hänger på `angler_id`; **koppling till appens namn = `anglers.name`** (Filip: appens namnlista är samma lista).
- `dashboard.php` (redan hämtat för historiken, 530 kB; bara extra nycklar sparas i kopian, ca +100 kB):
  - `anglers` (46): `angler_id, name, nickname, image_url, active, joined_year, home_water, bio_short, gear, notes`
  - `anglerStats` (41, per `angler_id`): WIN%, WIN(A), CatchPerDay, G/A/Gös-PerDay, FISKEDAGAR, TÖVLING(Antal), TOPGädda/Abborre/Gös,
    100+Gäddor, BIG5-rader. **Fältnamnen har å/ä/ö/mellanslag/versaler** (`TOPGädda`, `100+Gäddor`, `BIG5 GÄDDA`) – läs defensivt
    (hitta nyckel via normaliserat namn), svaret kommer i UTF-8.
  - `dashboard` (41): per `angler_id` + `competition_id` (`'total'` = säsongen): `rank, totl, lg/la/lgo (längsta), elo_out, fisk_a`.
  - `results` (248): en rad per fiskare och tävling: `rank, totl, lg, la, elo_out, competition_name, competition_date`.
  - `records`: `RECORD_ART, RECORD_CM, RECORD_DATUM, RECORD_ACTIVE`.
  - `heatmap` har bara `name` (inget `angler_id`) → "Hans fångster" matchar på `name`.
- Live `tavling.php?action=bootstrap&competitionId=…`: `participants[{participantId,name,imageFile}]`, `catches[{timestamp, name, species,
  cm, displayValue, approved, reportedBy, voidRef, lat, lng, imageUrl (Cloudinary)}]`. Befintlig live-hämtning (`js/66-catches.js`) har redan allt.
- **Profilbilder:** finns redan i appen – `AVATARS[namn]` (`src/js/33-avatars.js`, genereras av `tools/make_avatars.py` ur `tools/fiskare/`), samma namn som namnlistan. API:ets `image_url` behövs inte. Saknas bilden (annat namn) → bokstavscirkel i bärnsten.
- Känd skevhet: `anglerStats` Gös-rekord (88) syns men "BIG5 gös" = 0; `records` (Sibbo 6) bekräftar 88.

## Förslag på bygge
**A. Data** – `66-catches.js` (eller ny `67-profiles.js`, före 68): spara `anglers`, `anglerStats`, `dashboard` (bara `total`), `results`
(bara senaste ~5/fiskare), `records` i samma kopia (`lakeKey('ffmap_catches_v1')`, höj `v` → 3, gammal kopia = ingen kopia).
Hämtningen/takten ändras inte. Ny hjälp `profileOf(name)` → färdigt objekt eller `null` (okänt namn/ingen data → ingen ruta).
**B. Ruta** – **bottenruta** som övriga (UI.md) – Filip valde 2026-10-03. Öppnas från: tryck på båt/namn på kartan, **egen post i menyn: Profil** (öppnar rutan för det valda namnet, så man ser sig själv),
namnet i en fångstruta (`#hmCard`), en rad i snabbmeddelandet. Stängs med ×/utanför. Med i `saveRotationState()`/`restoreRotationUi()`.
**C. Snabbmeddelande av senaste fisken (Filip 2026-10-03: skickas för hand, inget automatiskt)** – först i `#msgPop`-menyn (js/64-messages.js)
ett extra val med din senaste fångst: "Gädda 78 cm · 14:32" (art + cm + klockslag). Visas bara om live-/historikdatan har en fångst med `name` = mitt valda namn,
`approved`, ingen VOID, och tävling pågår (annars inget val). Tryck = skickas som vanligt (`positions/<du>.msg`, text ≤ 15 tecken). Valet och bubblan har
**snurrande kant i artens färg** (som regnbågskanten `.msgRb`/`rbSpin`, men conic-gradient i `#35D24A` gädda / `#FF7A1A` abborre / `#3A86FF` gös) – hela tiden i
menyn, i bubblan de första 5 min. Samma fisk skickas gång på gång? Tillåtet (inget "redan skickad"-lås). Annullerad fisk försvinner ur menyn.
Bubblans art-färg måste följa med i meddelandet (nytt fält `msgSp` bredvid `msg`/`msgAt`) så att andra ser rätt färg; äldre appar ignorerar fältet.
**D. Hjälp** – rad i `tools/HJALP_TODO.md` när det är byggt.

## Tester (tests/)
`fakefb.FakeApi` utökas med `anglers/anglerStats/dashboard/results/records` + `participants`. Nya: profil öppnas för känt/okänt namn,
å/ä/ö-nycklar i anglerStats, kopia v2 → hämtas om, fångst-meddelande skickas en gång / inte för andras / inte för VOID / inte gammal.
Berörda befintliga: `test_catchapi.py`, `test_heatmap.py`, `test_extras.py` (meddelanden), ev. rotation.

## Beslut (Filip, 2026-10-03)
- Bottenruta när man trycker på ett namn på kartan + en **Profil** i menyn (egen profil).
- Profilbilder: finns redan (`AVATARS`).
- Fångstmeddelandet skickas **för hand** (val i snabbmeddelandemenyn), snurrande kant i artens färg. Mockup godkänd/visad.

- **Foto** (`imageUrl`, Cloudinary) visas om det finns: i `#msgCard` när man trycker på en fångstbubbla, och i `#hmCard` (fångstrutan). Fältet `msgImg` (URL)
  följer med meddelandet så att alla ser det utan att själva ha fångstdatan. Ingen bild → rutan som förut. Bild laddas först när rutan öppnas (ingen förladdning, sparar data);
  offline/fel → bilden döljs tyst. Kolla att Cloudinary-URL:en är https och att service workern inte cachar den för evigt (sw.js: bara egna filer cachas idag).

## Öppna frågor
- Inga just nu.

## Status (2026-10-03): BYGGT
`js/67-profiles.js`, `css/76-profiles.css`, ändringar i 24-boats, 64-messages, 66-catches (kopian v3, `img`/`no` på live-fångster),
68-heatmap (`hmSet.who`), 92-rotation. Test: `tests/test_profiles.py`. Foton: bara `res.cloudinary.com` visas (andras `msgImg` kan vara vad som helst).
Känd gräns: fångstvalet kräver GPS på live-fångsten (fångster utan position kommer inte med i `catchLive`).
