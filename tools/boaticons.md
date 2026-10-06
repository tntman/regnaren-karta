# Båtikoner – valbar ikon för "min position" (idé, inte byggd)

Status 2026-10-02: två förslag ritade och visade för Filip. **Inget är byggt i appen.** Väntar på hans val.

## Målet (Filips beställning)
- Man väljer ikon för sin båt i Inställningar → Båten. Valet sparas i localStorage och delas med gruppen
  via ett extra fält `icon` i positions-dokumentet (Firestore-reglerna tillåter extra fält).
- Ikonen vrids med färdriktningen (nosen uppåt vid 0°) och visar personens färg på något sätt.
- Tydlig i 28–40 px mot mörka och ljusa kartlägen, följer DESIGN.md ("Sjökortet i handen"), ingen emoji.
- Ingen three.js (för tungt i en PWA på iPhone). Förrenderade PNG i 16 vinklar kan komma senare.

## Så ritas båtarna i dag
- **Du själv:** orange pil `#dotArrow` (SVG, viewBox 24) i `#dot`/`#marker`, `src/html/30-map-ui.html`,
  CSS i `src/css/10-base.css` (vit halo + mörk kontur + pulserande ring `#dotGlow`). Vrids i `js/38-speed-depth.js`.
- **Andra:** vita romber `.boatDot` i `.boatPip` + namnetikett `.boatName`, `src/js/24-boats.js`
  (`renderBoats`, positionerna läses i `applyPositionsSnapshot`), CSS i `src/css/40-spots-boats.css`.
- **Personlig färg finns inte i dag** – den måste läggas till (förslag: fältet `color` bredvid `icon`).

## Förslag 1 – platta ikoner (för enkla enligt Filip)
`boaticons/forslag1_platt.html` (öppna i webbläsaren; bilder: `forslag1_platt.jpg`, `forslag1_3d.jpg`, `forslag1_karta.jpg`).
12 ikoner + dagens pil: fiskebåt, roddbåt, kajak, pontonbåt, bassboat, segelbåt, sjöbuss, fisk, anka, haj, ubåt, UFO.
Båten i personens färg, vit halo + mörk kontur, både platt och "3D-känsla".

## Förslag 2 – leksaksbåtar i "thiings"-stil (Filips riktning)
`boaticons/forslag2_leksak.html` (bilder: `forslag2_leksak.jpg`, `forslag2_karta.jpg`).
Filip gillade stilen på thiings.co (piratskepp, vikingaskepp, Iowa-slagskepp) – men de bilderna har
**oklar licens** och är ritade snett från sidan (går inte att vrida), så vi ritar egna, rakt uppifrån.
- 13 st: piratskepp, vikingaskepp, slagskepp, fiskebåt, roddbåt, kajak, badanka, segelbåt, gul ubåt,
  UFO (grön pilot), haj, flotte, gummibåt.
- Material med gradienter (trä, segelduk, stål, gummi, glas), plankor, kanoner, sköldar osv.
- Personens färg = **ring** runt båten (båten behåller sina egna färger). Alternativ: vimpel i personens färg.

## Teknik (samma i båda bladen, funktionen `icon()`)
- Varje ikon = `hull` (siluett, viewBox 48, nosen uppåt) + `under` (motor, åror, fenor) + `top` (detaljer)
  + `over` (segel, paddel – lyfts 1,3 och får egen skugga).
- 3D i ren SVG: suddig skugga (`feGaussianBlur`) förskjuten snett nedåt, "sidan" = skrovet ritat 4 gånger
  0,7–3 enheter neråt med 40 % svart, högdager = gradient (`#hl`) klippt med det vridna skrovet.
  Skugga, sida och ljus ligger i skärmkoordinater – bara båten vrids, så ljuset står still.
- Gradienter/mönster (`wood`, `cream`, `steel`, `stripes` …) i en gemensam `<defs>`. `clipPath`-id måste vara
  unikt per ritad ikon.

## Öppna frågor till Filip
1. Platt eller leksak (förslag 2)? Förslag: förslag 2.
2. Storlek: leksaksbåtarna behöver ca 40–44 px (egen 40, andras 36?).
3. Färgen: ring, vimpel eller något annat? Välja färg själv eller räknas fram ur namnet?
4. Vilka båtar ska med? Fler idéer: hjulångare, ångbåt, Titanic, motorbåt, pontonbåt, bassboat.
5. Ska andras båtar också visa sin ikon (vit romb kvar för gamla appversioner)?

## Steg 2 (när Filip sagt ok)
Väljare i Inställningar → Båten, localStorage (`lakeKey` behövs inte – gäller alla sjöar), fälten `icon`
(+ `color`) i positions-dokumentet, rita i `#dot` och `.boatPip`, spara i `saveRotationState` om väljaren
är öppen, tester, `tools/HJALP_TODO.md`, commit på svenska, push först efter ok.
