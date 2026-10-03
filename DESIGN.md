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
  art-gos: "#3A86FF"
  art-fara: "#E5322D"
  art-traffpunkt: "#FFB23F"
  art-hem: "#A8693A"
  greppglod: "#58B4FF"
  glod-lag: "#5A1482"
  glod-mitt: "#BE288C"
  glod-hog: "#F56E3C"
  glod-topp: "#FFF5C8"
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
    fontSize: "11.5px"
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
    backgroundColor: "rgba(214,69,69,.12)"
    textColor: "#FF8A80"
    rounded: "{rounded.sm}"
    width: "48px"
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
  map-pill:
    backgroundColor: "rgba(11,42,58,.82)"
    textColor: "{colors.morgondimma}"
    rounded: "{rounded.md}"
    padding: "4px 11px 4px 8px"
  type-dot:
    backgroundColor: "{colors.art-abborre}"
    textColor: "{colors.sjokortsbla}"
    rounded: "{rounded.round}"
    size: "24px"
  settings-section:
    backgroundColor: "{colors.sjokortsbla-glas}"
    textColor: "{colors.morgondimma}"
    rounded: "{rounded.md}"
    padding: "12px 14px"
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
- Artfärger (abborre orange, gädda grön, gös blå, fara röd, hem brun) är signaler på kartan, inte dekoration.
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
- **Signalröd** (signalrod): Ta bort, fel och "Fara"-nivåer i gränssnittet (Fara-text på sjökortsblått i ljusare röd `#FF6B63` för att gå att läsa); blixtlarm (rött) och blixtvarning (orange `#DE8012`) är egna varningsytor.
- **Greppglöd** (greppglod): blått sken i greppremsan och överkanten medan en bottenruta hålls och dras.
- **Kartanalysens skala** (blått, cyan, gult, orange, rött) används bara i kartlagret, aldrig i knappar.
- **Glöd** (glod-lag → glod-mitt → glod-hog → glod-topp): heatmapens egen skala, mörklila → magenta → orange → bärnsten → varmvitt. Krockar aldrig med djupskalans blå/cyan/grön; samma i kartlagret, teckenförklaringen och Heatmap-pricken.

### Named Rules
**The Bärnsten Means On Rule.** Bärnsten används bara för det som är valt, påslaget eller är huvudhandlingen (Spara). Aldrig som dekoration, aldrig för varningar.

**The Map Owns Color Rule.** Gränssnittet självt är sjökortsblått, dimvitt och grått. Färgstarka ytor hör till kartan (djup, lä, analys, heatmap) och till arterna.

**The Species Is Its Color Rule.** Abborre är alltid orange (#FF7A1A), gädda grön (#35D24A), gös blå (#3A86FF), fara röd, hem brun (#A8693A) – på pinnar, prickar, chips och skalor (Kartanalys, Heatmap).

## Typography

**Display Font:** Cambria (med Georgia, Times New Roman, serif)
**Body Font:** Calibri (med Segoe UI, system-ui, -apple-system, sans-serif)

**Character:** En klassisk serif bara för sjöns namn, som på ett tryckt sjökort; allt annat i en rundad, lättläst sans-serif som känns vardaglig och svensk.

### Hierarchy
- **Display** (700, 22px, spärrad .02em, textskugga): bara sjöns namn uppe till vänster (REGNAREN). 19 px på smala skärmar.
- **View title** (700, 17px, versaler, spärrad .08em, sans-serif): rubriken överst i Inställningar, Logg, Hjälp och Admin; dialogrubriker 18 px.
- **Title** (700, 17px): namnet på en fiskeplats i dess ruta, stora värden (23 px för ett snabbmeddelande).
- **Body** (400, 13–14px, radavstånd 1.4): resultattexter, beskrivningar, inställningsrader.
- **Label** (600–700, 12–13.5px): chips, knappar, segment, värden i faktarutor (15 px).
- **Overline** (700, 11–11.5px, versaler, spärrad .06–.08em): rubriker i rutor ("HEATMAP · FÅNGSTER", "ART", "TÄVLING") och etiketter i faktarutor (DJUP, NÄR).

### Named Rules
**The Serif Is The Lake Rule.** Serifen används bara för sjöns namn. Allt annat är sans-serif.

## Layout

Kartan fyller hela skärmen (`#stage`, fast placerad, inset 0). Allt annat ligger i lager ovanpå:
- **Överkant:** meny (rund, vänster), sjönamn med användare, väderchip och skyltar (blixt, Åskvarning av, Heatmap eller Kartanalys) under varandra; kartlägesknapp och Filter till höger. En toning i nattvatten bakom.
- **Underkant:** skala, zoomnivå, fart/djup-pill och djupskala till vänster; snabbmeddelanden i mitten; fyra rundknappar i ett 2 × 2-rutnät till höger (48 px, 12 px mellanrum, 16 px från kanten; 42/10 px liggande). En toning i nattvatten bakom.
- **Bottenrutor** glider upp från nederkanten, som mest 62 % av höjden (88 % för en plats); liggande blir alla (även platsens ruta) en 420 px bred kolumn till höger så att kartan syns bredvid.
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
- **Handlingsrad i en ruta:** lika breda knappar, 10 px rundning, 13.5 px halvfet text. Neutral (8 % vitt), Spara (bärnsten med sjökortsblå text) längst till höger. **Ta bort** är en papperskorg längst till vänster (48 px, dämpad röd kontur), avskild från resten – och följs alltid av en Ångra-notis (6 s) innan något raderas.
- **Översta raden i Kartanalys och Heatmap:** resultatet (högst 2 rader, värdet i bärnsten) och tre ikonknappar 36 × 36 px: **ⓘ** (förklaringarna i en ruta under raden; bärnsten när den är öppen, telefonen minns), **↺ Återställ** (grå när allt redan är som från start; grön med bock en stund efter tryck) och **⏻ Stäng av** (bärnsten när något är på, grå annars). ✕ i greppremsan.

### Chips
- **Style:** kapselform (14 px), 7 % vitt, tunn 12 % kant, dimvit 13 px text, **minst 40 px hög** i rutorna (blöta fingrar; `85-touch.css`) – i Kartanalys och Heatmap **34 px** (Filips val: rutorna ska lämna plats åt kartan). Där ligger varje grupp på **en rad som skrollar i sidled** (toning i kanten), med radens namn först (ART, TÄVLING).
- **State:** valt = helt bärnsten med sjökortsblå halvfet text. Inaktiva (för få fångster) är halvt genomskinliga. Av/på-val i Liknande och Från fångsterna får rosa kant och ✓ när de är på.

### Segmented control
- **Style:** 6 % vit bädd med 3 px luft och 10 px rundning; segmenten genomskinliga med vassgrå text.
- **State:** valt segment är bärnsten med sjökortsblå text (8 px rundning). Minst 42 px hög (36 px i Kartanalys och Heatmap). Används för kategori/stil i Kartanalys och Heatmap och för val i Inställningar.

### Bottom Sheet (signaturkomponent)
- **Corner Style:** 18 px överst.
- **Background:** sjökortsblå, tunn ljus överkant (14 % vitt).
- **Greppremsa:** 30 px hög remsa överst med ett 40 × 5 px streck (30 % vitt) och ✕ i högra hörnet (16 px, samma grå). Bara remsan drar rutan: dra = mindre/större, snärt nedåt = stäng. Medan den hålls glöder överkanten och remsan blått.
- **Innehåll (Kartanalys, Heatmap):** översta raden (resultat + ⓘ ↺ ⏻), segmentrad, chips på en rad var, reglage (två sida vid sida med namn och värde ovanför). Inga förklarande texter i själva rutan – de ligger bakom ⓘ. Mål: rutan tar högst ungefär en tredjedel av skärmen så att kartan syns medan man ställer in.

### Inputs / Fields
- **Style:** 8 % vitt, 18 % kant, 10 px rundning, 16 px text (så iPhone inte zoomar).
- **Focus / Error:** ogiltigt värde får signalröd kant.

### Sliders
- **Style:** bärnstensfärgade reglage med etikett till vänster (58 px) och värde i bärnsten till höger; djupintervall visas som en stapel i djupskalans färger med två vita handtag.

### Fact Tiles
- **Style:** fyra lika breda rutor i rad (6 % vitt, 10 px rundning): overline-etikett över ett 13.5–15 px halvfett värde. Används i platsens och fångstens ruta.

### Skyltar (under väderchipet)
- **Style:** kapsel i 82 % sjökortsblått, 12 px rundning, 12 px halvfet dimvit text med en liten ikon eller prick först. En rad var, under väderchipet.
- **Vilka:** blixtar (gul, med avstånd), "⚡✕ Åskvarning av" (röd), "Heatmap" (glöd-prick) eller "Kartanalys" (lupp) – aldrig både Heatmap och Kartanalys, lägena stänger av varandra. Tryck = rutan eller inställningen det gäller.

### Toggles
- **Style:** iOS-lik kapsel (18 % vitt av, bärnsten på) i inställningsrader och Filter. Typerna i Filter är en rad artfärgade prickar i stället (ifylld = visas, grå ring = dold).
- **Inställningar:** avsnitt (Kartan, Båten, Varningar, Kartanalys, Offline, Avancerat) som hopfällbara kort; stängt visar rubriken och en rad med vad som är valt. Raderna inuti är platta med en tunn linje emellan.

### Namnvalet "Vem är du?" (startskärm)
- **Style:** helskärm över kartan (nattvattentoning + 6 px oskärpa), loggan (150 px, lutad −5°) överst, "Vem är du?" 28 px, "Tryck på dig själv".
  Medlemmarna som runda bilder 70 px i tre kolumner (liggande sex, 56 px), "Annat namn" sist som streckad cirkel med +.
- **State:** vald = bärnstensring + ✓-bricka, övriga dämpade (42 %, gråare); knappen längst ner (54 px) blir bärnsten "Fortsätt som <namn>".
- **Loggan i 3D** (`js/35-logo3d.js`, även i Hjälps och Inställningars sidhuvud, three.js r170 i `assets/three-r170*.js`): en tjock röd skylt med röd baksida och reflexer, vaggar lite av sig själv, snurrar när man drar (hårdare = snabbare) och stannar alltid rättvänd. Ingen telefonlutning (då måste iPhone fråga om lov). Äldre telefoner trappar ner själva: full → lätt (pixeltäthet 1, enkla lampor) → platt (bilden vriden med CSS, röd baksida med glansrand); nivån minns i `ffmap_logo3d_v1`.

## Do's and Don'ts

### Do:
- **Do** låt kartan synas: kontroller är glas (72 % sjökortsblått med 6 px oskärpa) och tar så lite plats som möjligt.
- **Do** använd bärnsten (#E8A33D) för exakt det som är valt eller på, och sjökortsblå text på den.
- **Do** öppna allt nytt som en bottenruta med greppremsa, ✕ och blå glöd när den dras – och lägg nya rutor i glöd- och greppreglerna.
- **Do** rita linjer och kanter på kartan kantutjämnade och aldrig tunnare än en ritad punkt (se lä och Kartanalys).
- **Do** håll tryckytor stora nog för blöta fingrar: i rutorna chips/piller minst 40 px, kategorirader 42 px, knapprader 46 px (Kartanalys och Heatmap: chips 34, kategorier 36, ikonknappar 36); rundknappar 48 px; greppremsa 30 px hög. Kartans egna knappar ändras inte utan att Filip säger till.
- **Do** ge statusraden, bakgrunden och toningarna samma nattvatten.
- **Do** håll småtexten i rutorna läsbar i sol: minst 11 px (faktarutornas rubriker 11, rutornas små rubriker 11,5). Kartans egen skala och zoomtext är undantag.
- **Do** låt kort över kartan (vädret) stängas med ett tryck på kartan – men inte när kartan dras.
- **Do** håll rörelser korta och meningsfulla: tryck 100–150 ms, lägesbyten 150–300 ms, rutor 250–450 ms, mjuk inbromsning (`cubic-bezier(.16,1,.3,1)`), ingen studs, inget som loopar i panelerna. Det enda "stora" ögonblicket är när en **ny plats landar**: nålen faller ner och en tunn ring i typens färg sprider sig exakt vid spetsen (`landPin`). Skyltar glider fram ur väderchipet, avsnitt i Inställningar glider fram när de öppnas (stängs direkt), dolda typprickar krymper till en grå ring. Med "Reducera rörelse" rör sig inget – det tonas bara in.
- **Do** låt loggans röda (#EE2A28) bara finnas i loggan (namnvalet, Hjälps och Inställningars sidhuvud) – ingen annanstans i appen.
- **Do** visa tangentbordsfokus med en 2 px bärnstensring (`:focus-visible`). Inställningar är en spalt på högst 600 px på breda skärmar.

### Don't:
- **Don't** rita egna djupkurvor eller djupsiffror – bara Genesis kartbilder.
- **Don't** använd bärnsten för varningar eller dekoration; varningar är orange (#DE8012) eller röda.
- **Don't** låt en art byta färg mellan vyer.
- **Don't** lägg helt täckande plattor över kartan eller hårda kanter mot statusraden.
- **Don't** låt Fara eller åskvarning gå att dölja med filter eller val; är varningen avstängd i Inställningar syns det med en skylt.
- **Don't** radera något delat utan Ångra, och lägg aldrig Ta bort bredvid Spara.
