# Spår, Spår-menyn och Fog of war

Koden: `src/js/46-gps-track.js` (data, historik, Firestore, ritning), `47-track-panel.js` (menyn),
`48-fog.js` (Fog of war), `src/css/22-track.css`. Test: `tests/test_track_history.py`.

## Spåret
- **Dagens spår** `{day, segs:[[[lat,lon,ms],...]]}` i localStorage (`ffmap_track_v1`, per sjö via `lakeKey`).
  Ett spårdygn går 06:00–06:00 (`dayStr()`, dag som `YYYY-MM-DD`). Ny segment efter hopp > 250 m eller paus > 10 min,
  punkter närmare än 8 m sparas inte, högst 6 000 punkter/dag.
- **Spelas inte in i Demo Mode** (`onFix` hoppar över `recordTrack` när `demoMode`) – bara riktig körning räknas.
- **Historik** per sjö `trkHist` (`ffmap_trackhist_v1`): `{ "2026-10-01": {p, s, n, u} }` där `p` = packat spår
  (förenklat till ≥ 12 m), `s` = stopp `[[lat,lon,min]]`, `n` = antal punkter, `u` = uppladdad. När dygnet byts
  (eller appen startas nästa dag) flyttas gårdagen hit (`archiveTrack`). Blir telefonens lagring full tas äldsta dagen
  bort lokalt (finns kvar i databasen).
- **Packat format** (`packSegs`/`unpackSegs`): segment skilda med `|`, punkter med `;`, varje punkt `dLat,dLon,dSek` i
  bas 36 (1e-6 grader, sekunder). ≈ 10 byte/punkt → en lång dag ≈ 40–60 kB.
- **Stopp** (`findStops`): punkter som stannar inom 40 m från där stoppet började i ≥ 2 min. Räknas på orensade punkter
  (före förenklingen) och sparas med dagen.

## Databasen: Firestore `tracks`
Ett dokument per person, sjö och dag. **Id:** `<sjö>_<uid>_<dag>` (uid = namnet, tecken utanför a–z 0–9 åäö → `_`).

| fält | innehåll |
|---|---|
| `lake`, `uid`, `name`, `day` | sjö, personen (`nameSlug`), visningsnamn, `YYYY-MM-DD` |
| `pts` | packat spår (sträng) |
| `st` | stopp som sträng `lat,lon,min;…` |
| `n` | antal punkter (number) |
| `lakeDay` | `<sjö>_<dag>` – för "allas spår en viss tid" |
| `ownKey` | `<sjö>_<uid>_<dag>` – för "mina dagar" (ny telefon) |
| `updatedAt` | serverTimestamp |

Båda frågorna är intervall på **ett** fält (`>=` och `<=`) – inga sammansatta index behövs.

**Regel att lägga till i Firebase-konsolen** (utan den sparas inget, och appen skriver bara en varning i konsolen):
`tracks: read auth; write kräver lake/uid/day/pts (string) och n (number), pts ≤ 900 000 tecken.`

**Kostnad:** skrivning = dagens dokument (≈ 40–60 kB) högst var 5:e min när det kommit nya punkter + när appen går i
bakgrunden + färdiga dagar en gång. Ingen lyssnare, så ingen läser andras skrivningar. **Läsning:** mina dagar en gång
per telefon (`fetchMyTracks`, flagga `ffmap_tracksync_v1`); andras bara när "Andras" är på – en read per person och dag
i valt intervall, sparade i minnet tills sidan stängs (`fetchOthersTracks`, nytt hämtande först vid bredare intervall
eller efter 5 min).

## Spår-menyn `#trkPanel`
Öppnas av **Spår-ikonen** i Filter (liten amber prick = går att trycka på; reglaget till höger är fortfarande på/av) eller
Inställningar → Spår → Öppna. Stänger Filter och Kartanalys/Heatmap-rutan. Val i `trkCfg` (`ffmap_track_cfg_v1`):
Mina/Andras, I dag · 7 · 30 · Allt, Streckad/Hel, färg (6), Synlighet (gamla reglaget `trackOpSlider`, flyttat hit),
Stopp som ringar (av som standard), Börja om. Andras spår: en färg (ljusblå), tunnare, utan namn. Överlever rotation
(`st.trk` i `92-rotation.js`).

## Ritning
`renderTrack()` ritar i `#trackLayer`: `.trkOther` (andras), `.trkUnder` + `.trkLine` (mina), `.trkStops` (ringar,
radie 8 + √min·3,4 px, "13 min"). Spåren omräknas till bildpixlar en gång (`trkPx`-cache) – panorering är bara en
multiplikation.

## Fog of war (Filter → Lager, av som standard)
Mörkt (`rgba(6,20,28,.93)`) överallt utom där du varit: mjukt hål, **radie 50 m**, tonar ut. Bygger på **dina egna**
spår (idag + historiken) på just den här sjön, plus där du är nu (även i demo). Hålen ritas en gång i en dold mask
(4 m per pixel, ett hål per 10 m-ruta längs spåret) och skalas på kartan varje bildruta. z-ordning: namn 11, fog 12,
spår 13, platser/båtar över. Byggs om vid start, efter "Börja om" och när mina dagar hämtats från databasen.

## Idéer kvar
Fart som färg, tonande svans, riktningspilar, "Utforskat x %" (förslagsbilder: `tools/track_ideas/`).
