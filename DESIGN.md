---
name: FF Map
description: Sjökortet i handen – Fiskfiskarnas karta för tävlingsdagen på sjön.
colors:
  sjokortsbla: "#0B2A3A"
  sjokortsbla-glas: "rgba(11,42,58,.72)"
  nattvatten: "#06141C"
  barnsten: "#E8A33D"
  morgondimma: "#F4F7F8"
  vassgra: "#B7C4C9"
  blacksvart: "#14181C"
  signalrod: "#D64545"
  art-markering: "#E4E9EC"
  art-abborre: "#FF7A1A"
  art-gadda: "#35D24A"
  art-gos: "#FFD21A"
  art-fara: "#E5322D"
  art-traffpunkt: "#FFB23F"
  art-hem: "#3A86FF"
  greppglod: "#58B4FF"
typography:
  display:
    fontFamily: "Cambria, Georgia, \"Times New Roman\", serif"
    fontSize: "22px"
    fontWeight: 700
    letterSpacing: ".02em"
  title:
    fontFamily: "Calibri, \"Segoe UI\", system-ui, -apple-system, sans-serif"
    fontSize: "17px"
    fontWeight: 700
  body:
    fontFamily: "Calibri, \"Segoe UI\", system-ui, -apple-system, sans-serif"
    fontSize: "14px"
    fontWeight: 400
    lineHeight: 1.4
  label:
    fontFamily: "Calibri, \"Segoe UI\", system-ui, -apple-system, sans-serif"
    fontSize: "12.5px"
    fontWeight: 600
  overline:
    fontFamily: "Calibri, \"Segoe UI\", system-ui, -apple-system, sans-serif"
    fontSize: "10.5px"
    fontWeight: 700
    letterSpacing: ".08em"
rounded:
  xs: "8px"
  sm: "10px"
  md: "12px"
  chip: "14px"
  sheet: "18px"
  round: "50%"
spacing:
  gutter: "14px"
  sm: "6px"
  md: "10px"
  lg: "16px"
components:
  button-map:
    backgroundColor: "{colors.sjokortsbla-glas}"
    textColor: "{colors.morgondimma}"
    rounded: "{rounded.round}"
    size: "48px"
  button-locate:
    backgroundColor: "{colors.barnsten}"
    textColor: "{colors.sjokortsbla}"
    rounded: "{rounded.round}"
    size: "48px"
  chip:
    backgroundColor: "rgba(255,255,255,.07)"
    textColor: "{colors.morgondimma}"
    rounded: "{rounded.chip}"
    padding: "6px 10px"
  chip-on:
    backgroundColor: "{colors.barnsten}"
    textColor: "{colors.sjokortsbla}"
    rounded: "{rounded.chip}"
    padding: "6px 10px"
  segmented:
    backgroundColor: "rgba(255,255,255,.06)"
    textColor: "{colors.vassgra}"
    rounded: "{rounded.sm}"
    padding: "3px"
  segmented-on:
    backgroundColor: "{colors.barnsten}"
    textColor: "{colors.sjokortsbla}"
    rounded: "{rounded.xs}"
  sheet:
    backgroundColor: "{colors.sjokortsbla}"
    textColor: "{colors.morgondimma}"
    rounded: "{rounded.sheet}"
    padding: "8px 14px 16px"
  action-save:
    backgroundColor: "{colors.barnsten}"
    textColor: "{colors.sjokortsbla}"
    rounded: "{rounded.sm}"
    padding: "8px 2px"
  action-delete:
    backgroundColor: "{colors.signalrod}"
    textColor: "#FFFFFF"
    rounded: "{rounded.sm}"
    padding: "8px 2px"
  action-neutral:
    backgroundColor: "rgba(255,255,255,.08)"
    textColor: "{colors.morgondimma}"
    rounded: "{rounded.sm}"
    padding: "8px 2px"
  fact-tile:
    backgroundColor: "rgba(255,255,255,.06)"
    textColor: "{colors.morgondimma}"
    rounded: "{rounded.sm}"
    padding: "5px 8px 6px"
  input:
    backgroundColor: "rgba(255,255,255,.08)"
    textColor: "{colors.morgondimma}"
    rounded: "{rounded.sm}"
    padding: "11px 12px"
---

# Design System: FF Map

## Overview

**Creative North Star: "Sjökortet i handen"**

Kartan är allt. FF Map ska kännas som ett modernt sjökort som man håller i båten: djupfärgerna, kurvorna och vattnet fyller hela skärmen, och allt annat är diskreta instrument ovanpå. Knappar, chips och rutor är halvgenomskinliga i sjökortsblått, svävar över kartan med mjuk skugga och tar så lite plats som möjligt tills de behövs. Då blir de tydliga: en panel glider upp nerifrån, ett val lyser bärnstensorange och greppremsan glöder blått när man håller i den.

Färgen i appen kommer från kartan och från fiskarna. Gränssnittet håller sig själv mörkt och dämpat, sjökortsblått, dimvitt och vassgrått, så att djupfärgerna och artfärgerna syns. Det enda gränssnittet får lysa med är bärnsten, och bara för det som är valt eller påslaget. När kartan ska tolkas (Kartanalys, Heatmap) tonas den ner och gråtonas, och det som hittats lyser igenom med en tunn vit kant.

Täthet och tempo följer tävlingsdagen: allt viktigt nås med en hand, texter är korta och svenska, och inget kräver precision. Ytor och linjer är mjuka och kantutjämnade, aldrig pixliga eller trappiga.

**Key Characteristics:**
- Kartan fyller hela skärmen; gränssnittet svävar som mörkt, halvgenomskinligt glas ovanpå.
- Bärnsten är enda gränssnittsaccenten och betyder alltid "valt / på".
- Artfärger (abborre orange, gädda grön, gös gul, fara röd, hem blå) är signaler på kartan, inte dekoration.
- Bottenrutor med greppremsa är den gemensamma formen för allt som öppnas.
- Mjuka toningar i över- och underkant (nattvatten) i stället för hårda kanter mot kartan.

## Colors

Ett mörkt, kallt sjökortsgränssnitt med en enda varm accent, där all övrig färg hör till kartan och fiskarna.

### Primary
- **Bärnsten** (barnsten): valt eller påslaget – valt chip, aktivt läge i en segmentrad, på-läge på reglage, Spara, sikteknappen, värden i reglagerader, siffror som ska framhävas i resultattexter.

### Neutral
- **Sjökortsblå** (sjokortsbla): grunden för alla bottenrutor, menyer och sidor (Inställningar, Hjälp), och text på bärnstensytor.
- **Sjökortsblått glas** (sjokortsbla-glas): svävande kontroller över kartan – rundknappar, Filter-panelen, inställningsrader. Alltid med 6 px bakgrundsoskärpa.
- **Nattvatten** (nattvatten): statusraden i hemskärmsappen, bakgrunden utanför kartbilden och toningarna i över- och underkant (`rgba(6,20,28,…)`). Statusraden och sidan ska ha exakt samma nattvatten; ingen kant däremellan.
- **Morgondimma** (morgondimma): brödtext, rubriker och ikoner på mörk botten.
- **Vassgrå** (vassgra): sekundär text, beskrivningar, inaktiva segment och ✕ i greppremsan.
- **Becksvart** (blacksvart): text på ljusa artfärger (till exempel valt typpiller).
- **Genomskinligt vitt** (6–18 %) bygger ytorna i en ruta: 6–8 % för fält, chips och faktarutor, 12–18 % för kanter och avdelare.

### Signal Colors (kartans och artens färger)
- **Artfärgerna** markering, abborre, gädda, gös, fara, träffpunkt och hem gäller för fiskeplatser, typpiller, heatmapens per art-läge och Kartanalys "Från fångsterna". Samma art har alltid samma färg överallt.
- **Signalröd** (signalrod): Ta bort, fel och "Fara"-nivåer i gränssnittet; blixtlarm (rött) och blixtvarning (orange `#DE8012`) är egna varningsytor.
- **Greppglöd** (greppglod): blått sken i greppremsan och överkanten medan en bottenruta hålls och dras.
- **Kartanalysens och heatmapens skalor** (blått, cyan, gult, orange, rött) används bara i kartlager, aldrig i knappar.

### Named Rules
**The Bärnsten Means On Rule.** Bärnsten används bara för det som är valt, påslaget eller är huvudhandlingen (Spara). Aldrig som dekoration, aldrig för varningar.

**The Map Owns Color Rule.** Gränssnittet självt är sjökortsblått, dimvitt och grått. Färgstarka ytor hör till kartan (djup, lä, analys, heatmap) och till arterna.

**The Species Is Its Color Rule.** Abborre är alltid orange (#FF7A1A), gädda grön (#35D24A), gös gul (#FFD21A), fara röd, hem blå – på pinnar, prickar, chips och skalor.

## Typography

**Display Font:** Cambria (med Georgia, Times New Roman, serif)
**Body Font:** Calibri (med Segoe UI, system-ui, -apple-system, sans-serif)

**Character:** En klassisk serif bara för sjöns namn, som på ett tryckt sjökort; allt annat i en rundad, lättläst sans-serif som känns vardaglig och svensk.

### Hierarchy
- **Display** (700, 22px, spärrad .02em, textskugga): bara sjöns namn uppe till vänster (REGNAREN). 19 px på smala skärmar.
- **Title** (700, 17px): namnet på en fiskeplats i dess ruta, stora värden (23 px för ett snabbmeddelande).
- **Body** (400, 13–14px, radavstånd 1.4): resultattexter, beskrivningar, inställningsrader.
- **Label** (600–700, 12–13.5px): chips, knappar, segment, värden i faktarutor (15 px).
- **Overline** (700, 10–10.5px, versaler, spärrad .06–.08em): rubriker i rutor ("HEATMAP · FÅNGSTER", "ART", "TÄVLING") och etiketter i faktarutor (DJUP, NÄR).

### Named Rules
**The Serif Is The Lake Rule.** Serifen används bara för sjöns namn. Allt annat är sans-serif.

## Layout

Kartan fyller hela skärmen (`#stage`, fast placerad, inset 0). Allt annat ligger i lager ovanpå:
- **Överkant:** meny (rund, vänster), sjönamn med användare, väderchip och skyltar (blixt, Heatmap) under varandra; kartlägesknapp och Filter till höger. En toning i nattvatten bakom.
- **Underkant:** skala, zoomnivå, fart/djup-pill och djupskala till vänster; snabbmeddelanden i mitten; fyra rundknappar i ett 2 × 2-rutnät till höger (48 px, 12 px mellanrum, 16 px från kanten; 42/10 px liggande). En toning i nattvatten bakom.
- **Bottenrutor** glider upp från nederkanten, som mest 62 % av höjden (88 % för en plats); liggande blir de en 420 px bred kolumn till höger.
- Marginal mot skärmkanten är 14–18 px; inuti rutor 14–16 px sidled. Mellanrum mellan chips 6 px, mellan rader 8–12 px.
- Säkra zoner (`env(safe-area-inset-*)`) respekteras överallt; iPhone-hemskärmsappen laddar om vid vridning.

## Elevation & Depth

Djup skapas med svävande glas: halvgenomskinligt sjökortsblått med 6 px oskärpa och mjuka, mörka skuggor som lyfter kontrollerna från kartan. Bottenrutor är helt täckande sjökortsblått med en tunn ljus överkant och en skugga uppåt. Kartan under en analys tonas ner (mörkare + gråtonad) i stället för att få en ruta ovanpå.

### Shadow Vocabulary
- **Svävande kontroll** (`box-shadow: 0 4px 14px rgba(0,0,0,.35)`): rundknappar, Filter, chip över kartan.
- **Bottenruta** (`box-shadow: 0 -10px 30px rgba(0,0,0,.45)`): Kartanalys, Heatmap, meddelande, fångst; platsens ruta `0 -8px 24px rgba(0,0,0,.4)`.
- **Dialog** (`box-shadow: 0 10px 30px rgba(0,0,0,.5)`): väderkortet, larm och notiser som ligger fritt.
- **Greppglöd** (`box-shadow: 0 -10px 30px rgba(0,0,0,.45), 0 -2px 14px rgba(88,180,255,.9)`): överkanten medan en bottenruta dras.

### Named Rules
**The Glass Over Chart Rule.** Kontroller ovanpå kartan är alltid halvgenomskinligt sjökortsblått med oskärpa och mjuk skugga – aldrig helt täckande plattor som skär bort kartan.

## Shapes

Mjukt rundade former utan skarpa hörn. Rundknappar över kartan är helt runda (50 %). Chips är kapselformade (14 px), knappar och fält har 10 px, inställningsrader och Filter-panelen 12 px, bottenrutor 18 px i överkanten och raka i underkanten. Fiskeplatser är droppformade pinnar (rundade utom spetsen), Fara en röd åttakant, Träffpunkt en fyr med ringar, båtar vita romber. Linjer på kartan är tunna och kantutjämnade (kanter, strand, rutt).

## Components

### Buttons
- **Rundknapp över kartan:** 48 × 48 px, helt rund, sjökortsblått glas, dimvit ikon (21–24 px), svävande skugga; trycks ner till 92 %. Aktiv (t.ex. Kartanalys på) får bärnstensfärgad kant och ikon.
- **Sikteknappen:** samma form men helt bärnstensfärgad med sjökortsblå ikon – den viktigaste knappen.
- **Handlingsrad i en ruta:** lika breda knappar, 10 px rundning, 13.5 px halvfet text. Neutral (8 % vitt), Ta bort (signalröd), Spara (bärnsten med sjökortsblå text).
- **Stäng av / Återställ** längst ner i Kartanalys och Heatmap: chips; "Stäng av" med bärnstenskant och ett ljus som sveper igenom när något är på, grå och platt annars. "Återställ" grå när allt redan är som från start.

### Chips
- **Style:** kapselform (14 px), 7 % vitt, tunn 12 % kant, dimvit 12.5 px text.
- **State:** valt = helt bärnsten med sjökortsblå halvfet text. Inaktiva (för få fångster) är halvt genomskinliga. Av/på-val i Liknande och Från fångsterna får rosa kant och ✓ när de är på.

### Segmented control
- **Style:** 6 % vit bädd med 3 px luft och 10 px rundning; segmenten genomskinliga med vassgrå text.
- **State:** valt segment är bärnsten med sjökortsblå text (8 px rundning). Används för kategori/stil överst i Kartanalys och Heatmap och för val i Inställningar.

### Bottom Sheet (signaturkomponent)
- **Corner Style:** 18 px överst.
- **Background:** sjökortsblå, tunn ljus överkant (14 % vitt).
- **Greppremsa:** 30 px hög remsa överst med ett 40 × 5 px streck (30 % vitt) och ✕ i högra hörnet (16 px, samma grå). Bara remsan drar rutan: dra = mindre/större, snärt nedåt = stäng. Medan den hålls glöder överkanten och remsan blått.
- **Innehåll:** overline-rubrik, segmentrad, chips, reglage, resultattext, och längst ner en rad med Stäng av + Återställ.

### Inputs / Fields
- **Style:** 8 % vitt, 18 % kant, 10 px rundning, 16 px text (så iPhone inte zoomar).
- **Focus / Error:** ogiltigt värde får signalröd kant.

### Sliders
- **Style:** bärnstensfärgade reglage med etikett till vänster (58 px) och värde i bärnsten till höger; djupintervall visas som en stapel i djupskalans färger med två vita handtag.

### Fact Tiles
- **Style:** fyra lika breda rutor i rad (6 % vitt, 10 px rundning): overline-etikett över ett 13.5–15 px halvfett värde. Används i platsens och fångstens ruta.

### Toggles
- **Style:** iOS-lik kapsel (18 % vitt av, bärnsten på) i inställningsrader och Filter.

## Do's and Don'ts

### Do:
- **Do** låt kartan synas: kontroller är glas (72 % sjökortsblått med 6 px oskärpa) och tar så lite plats som möjligt.
- **Do** använd bärnsten (#E8A33D) för exakt det som är valt eller på, och sjökortsblå text på den.
- **Do** öppna allt nytt som en bottenruta med greppremsa, ✕ och blå glöd när den dras – och lägg nya rutor i glöd- och greppreglerna.
- **Do** rita linjer och kanter på kartan kantutjämnade och aldrig tunnare än en ritad punkt (se lä och Kartanalys).
- **Do** håll tryckytor stora nog för blöta fingrar (rundknappar 48 px, greppremsa 30 px hög) och text läsbar i sol.
- **Do** ge statusraden, bakgrunden och toningarna samma nattvatten.

### Don't:
- **Don't** rita egna djupkurvor eller djupsiffror – bara Genesis kartbilder.
- **Don't** använd bärnsten för varningar eller dekoration; varningar är orange (#DE8012) eller röda.
- **Don't** låt en art byta färg mellan vyer.
- **Don't** lägg helt täckande plattor över kartan eller hårda kanter mot statusraden.
- **Don't** låt Fara eller åskvarning gå att dölja med filter eller val.
