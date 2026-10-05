---
name: FF Map
description: Design A – mörk, platt och lugn, med en orange accent som glöder. Fiskfiskarnas karta för tävlingsdagen på sjön.
colors:
  botten: "#090B10"
  yta-1: "#12161E"
  yta-2: "#1C222D"
  yta-3: "#29313F"
  frost: "rgba(18,22,30,.5)"
  text: "#EEF0F4"
  gra-text: "#8A93A5"
  accent: "#FF9A4D"
  text-pa-accent: "#1A0C02"
  linje: "rgba(170,190,230,.10)"
  ta-bort: "#FF6B63"
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
  family: "-apple-system, BlinkMacSystemFont, \"Segoe UI\", system-ui, sans-serif"
  sjonamn: { fontSize: "20px", fontWeight: 600, letterSpacing: "-.02em" }
  vytitel: { fontSize: "22px", fontWeight: 600, letterSpacing: "-.02em" }
  titel: { fontSize: "17px", fontWeight: 600 }
  brodtext: { fontSize: "14px", fontWeight: 400, lineHeight: 1.45 }
  etikett: { fontSize: "13.5px", fontWeight: 500 }
  liten: { fontSize: "12.5px", fontWeight: 500 }
rounded:
  knapp: "14px"
  meny-kort: "18–20px"
  ruta: "28px"
  kapsel: "999px"
  rund: "50%"
---

# Design System: FF Map – design A

Vald 2026-10-05 på ritytan (Claude Design): https://claude.ai/artifact/89dWVPfm4SALzbT5si8XFb – sidan
"A – alla skärmar" har appen som den var (riktiga skärmbilder) och samma 16 vyer i A + Byggstenar, sidan
"A – animationer" har klickbara skärmar med rörelserna. Koden: färgerna i `:root` (`src/css/10-base.css`),
formerna, det frostade och rörelserna i `src/css/95-design-a.css`, glöden som tänds i `src/js/91-motion.js`.

## Overview

**Kartan är allt, gränssnittet är tyst.** Bakgrunden är nästan svart, ikoner och text vita, och det enda som
lyser är en orange accent – för det som är på, valt eller viktigast. Allt som ligger fritt på kartan har en
tunn frostad botten (halvgenomskinligt mörkt + oskärpa), så kartan syns igenom. Paneler och sidor är helt
täckande och platta: inga ramar, inga lådor i lådor, tunna linjer i stället för kort. Allt är likformigt:
samma höjder, tre rundningar, samma tryck överallt.

Färgen i appen kommer från kartan och från fiskarna; gränssnittet tar bara accenten.

## Colors

Färgerna "midnatt + aprikos" (2026-10-05, variant 21 på ritytans sida Kontrast – menyer): bläckblå midnatt där varje lager
är tydligt ljusare, svala hårfina linjer, en tunn ljuskant överst på paneler och vald flik.


- **Botten** (`--bg` #090B10): sidorna (Inställningar, Logg, Hjälp, Admin), statusraden (`theme-color`),
  utanför kartbilden, toningarna i över- och underkant.
- **Yta 1** (`--navy` #12161E): paneler (bottenrutor), menyer, kort, kortlistor.
- **Yta 2** (`--s2` #1C222D): knappar, fält, chips och valda flikar inne i en panel.
- **Yta 3** (`--s3` #29313F): reglage som är av, reglagespår.
- **Frost** (`--navy-glass` + `--frost` = blur 14 px): allt som ligger fritt på kartan – väderpillret,
  skyltarna, kapseln uppe till höger, de runda knapparna, fart/djup, snabbmeddelandenas val, Ångra-notisen.
  Tunn kant 10 % vitt.
- **Text** #EEF0F4, **grå text** (`--text-muted` #8A93A5) för beskrivningar och etiketter.
- **Accent** (`--amber` #FF9A4D, varm aprikos): på / valt / huvudhandlingen (Spara, sikteknappen). Text och ikoner på
  accent: `--on-acc` #1A0C02.
- **Ta bort** #FF6B63 (papperskorgen, Logga ut), signalröd för fel och Fara-nivåer.
- **Artfärgerna** (markering, abborre, gädda, gös, fara, träffpunkt, hem) och **glöden** (heatmapen) är
  oförändrade och gäller överallt.

### Named Rules
**The Accent Means On Rule.** Orange bara för det som är valt, påslaget eller huvudhandlingen. Aldrig
dekoration, aldrig varningar (de är orange #DE8012 eller röda och har egna ytor).
**The Map Owns Color Rule.** Gränssnittet är svart, grått och vitt. Färgstarka ytor hör till kartan och arterna.
**The Species Is Its Color Rule.** Samma art har samma färg överallt (pinnar, prickar, chips, skalor).

## Typography

En sans-serif överallt (telefonens egen: SF på iPhone), även sjönamnet. Siffror med lika breda tecken.
Rubriker i vanlig skrift (inga versaler): "Regnaren", "Inställningar", "Art", "Tävling".
- Sjönamnet 20 px 600, vytitlar 22 px 600, titlar 17 px 600, brödtext 14 px, etiketter 13,5 px 500,
  små rubriker 12,5 px 500 i grått. Aldrig under 11 px i panelerna (läsbart i sol).

## Layout

Samma delar på samma ställen som förut (kartan fyller skärmen, allt annat i lager ovanpå):
- **Uppe till vänster:** profilbilden är menyknappen – en liten frostad cirkel med pilen skär ett hack i
  bilden (pilen vänds när menyn är öppen). Sjönamnet bredvid. Under: väderpillret och skyltarna, frostade.
- **Uppe till höger:** Heatmap, Kartläge och Filter som **en** frostad kapsel. Filter öppnas som ett eget kort under den – kapseln ändras inte.
- **Nere till vänster:** skalan (strecket överst, "100 m · 15,2 × L 15" under), fart/djup i en låg
  frostad kapsel (30 px), djupskalan som en tunn linje med siffror – ingen låda.
- **Nere till höger:** de runda knapparna i 2 × 2 (48 px, frostade), ny plats-nålen med platt orange +,
  sikteknappen helt orange. Meddelandeknappen i mitten. Lika långt ner som förut.
- **Paneler** glider upp nerifrån (högst 62 % av höjden, 88 % för en plats; liggande en 420 px kolumn).

## Shapes and elevation

Tre rundningar: knappar och fält 14 px, menyer och kort 18–20 px, paneler 28 px överst. Chips, skyltar och
pillren är kapslar. Platt: inga skuggor på det frostade; menyer och kort över kartan har en mjuk skugga
(0 18px 50px rgba(0,0,0,.55)). Huvudhandlingen (orange) har ett mjukt orange sken.

## Components

- **Rundknappar på kartan:** 48 px, frostade, vit ikon. På = orange ikon + orange ring + svagt sken.
  Sikteknappen är den enda helt orange (följ-läget: vit).
- **Knappar i panelerna:** 44–46 px, 14 px rundning, yta 2. Spara/huvudhandling orange. **Ta bort** är bara en
  röd papperskorg längst till vänster, avskild från resten – och följs alltid av Ångra (6 s).
- **Ikonknappar** (ⓘ ↺ ⏻, ✕): bara ikonen, ingen ruta. Grå = inget att göra, orange = på. ✕ i panelernas hörn
  16 px i samma grå som draglinjen (30 % vitt).
- **Chips:** kapslar i yta 2, valt = orange ton + orange text. **Typerna** (Markering, Abborre …): vit text med
  en färgprick, vald = artens färg som ton + text.
- **Flikar** (Kartdata/Tumregler …, Värme/Per art …): ingen bädd, vald flik = yta 2 med vit text.
- **Reglage:** av = yta 3, på = orange, utan sken (borttaget 2026-10-05).
- **Fakta** (Djup, Lutning, Botten, Växter): en rad med tunna streck emellan, inga rutor.
- **Kort i mitten** (båten, ett meddelande, tävlingslåset): solida, 20 px, mörk bakgrund bakom; namnet med › öppnar profilen.
- **Menyer** (Meny, Kartlägen, Filter): solida, 18 px, kompakta som förut. Valt = orange text / ljusare rad,
  ingen bock.
- **Listor** (Logg, Inställningar): ett kort med tunna linjer mellan raderna. Överst i Inställningar ett profilkort: bild, namn,
  "Admin · sjön" och "Byt namn" i orange.
- **Startskärmen:** loggan, "Vem är du?", medlemmarna i tre kolumner utan ring, knappen grå tills någon är vald.

## Motion

Kort och med lite fjäder, aldrig loopande (utom GPS-ringen).
- **Tryck:** allt som går att trycka krymper lite (93 %) och fjädrar tillbaka (0,18 s).
- **Orange tänds:** när något slås på blossar ett orange sken ut och tonas bort (0,8 s) – bara vid ett tryck på kartknapparna (inte reglagen),
  aldrig när en vy öppnas.
- **Menyer** växer ut ur sin knapp och raderna följer efter varandra (0,38 s, 20–30 ms mellan raderna).
  Pilen på profilbilden vänds.
- **Paneler** glider upp (0,42 s) och innehållet följer rad för rad. Valt chip studsar till.
- **Frost** klarnar fram när något frostat visas (skyltarna under vädret, notiser; snabbmeddelandenas val poppar upp ett i taget).
- **Avsnitt** (Inställningar) och ⓘ-rutorna fälls ut och ihop mjukt (höjden glider, 0,38 s). Valda fliken glider över, ↺ snurrar ett varv.
- **Heatmap och Kartanalys** tonar in på kartan.
- **En ny plats landar** (nålen faller, ringen sprids) – det enda stora ögonblicket.
- "Reducera rörelse": bara snabba toningar.

## Do's and Don'ts

### Do:
- **Do** låt kartan synas: frostat på kartan, solitt i panelerna, så lite som möjligt ovanpå.
- **Do** använd orange för exakt det som är på eller valt, med mörk text på.
- **Do** öppna allt nytt som en bottenpanel med draglinje och ✕.
- **Do** håll tryckytor stora för blöta fingrar (chips 34–40, knapprader 44–46, rundknappar 48 px).
- **Do** visa tangentbordsfokus med en 2 px orange ring.

### Don't:
- **Don't** rita egna djupkurvor eller djupsiffror – bara kartbilderna.
- **Don't** låt en art byta färg mellan vyer.
- **Don't** låt Fara eller åskvarning gå att dölja med filter.
- **Don't** radera något delat utan Ångra, och lägg aldrig Ta bort bredvid Spara.
- **Don't** lägg ramar, lådor i lådor eller versaler i rubriker.
