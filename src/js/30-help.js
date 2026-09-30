  /* ---- Hjälp ----
     How to use the app + what's new. Menu -> Hjälp; opens by itself (with a welcome)
     right after the name is chosen the first time on a phone. A dot on the menu
     button / the menu item while there's news you haven't seen. The animations are
     made by tools/help_anim.py (docs/help/*.webp; one that's missing is just left out). */
  // newest first. t: 'new' (NYTT), 'better' (BÄTTRE), 'fixed' (FIXAT)
  var HELP_NEWS = [
    { d: '2026-09-30', t: 'new',    x: '<b>Heatmap</b> – var fisken tagits i tävlingarna (håll inne kartlägesknappen, sist i listan)' },
    { d: '2026-09-30', t: 'new',    x: 'Kartanalys <b>Fångster</b>: hitta ställen som liknar där abborre, gädda och gös tagits' },
    { d: '2026-09-30', t: 'better', x: 'Åskvarningen gäller alltid (även med Blixtar av i Filter) och säger till när <b>åskan dragit förbi</b>' },
    { d: '2026-09-30', t: 'better', x: '<b>Ångra</b> i 6 sekunder när du tar bort en plats – papperskorgen ligger längst till vänster' },
    { d: '2026-09-30', t: 'better', x: 'Kartanalys: välj kategori först; <b>Stäng av</b> och <b>Återställ</b> längst ner; skylt under vädret när den är på' },
    { d: '2026-09-30', t: 'better', x: 'Enklare <b>Filter</b> (Markeringar och Lager, typerna som prickar) och <b>Inställningar</b> i avsnitt' },
    { d: '2026-09-30', t: 'new',    x: 'Solnedgången i väderraden de sista 45 minuterna; skylten <b>Täckning igen</b> när nätet är tillbaka' },
    { d: '2026-09-30', t: 'better', x: 'Tydligare lä (blått), vädret stängs med ett tryck på kartan, nya platser landar på kartan, större knappar i rutorna' },
    { d: '2026-09-30', t: 'fixed',  x: 'Vridning av telefonen: inga "förskjutna" knappar, lä försvinner inte' },
    { d: '2026-09-29', t: 'better', x: 'Lättare att dra kartan – även när fingret börjar på en plats, båt eller bubbla' },
    { d: '2026-09-29', t: 'better', x: '<b>Djup</b> under båten och <b>Andras 50/100 %</b> finns nu i Inställningar' },
    { d: '2026-09-29', t: 'better', x: 'Flera meddelanden från samma båt samlas i en bubbla' },
    { d: '2026-09-29', t: 'new',    x: 'Snabbmeddelanden: skriv en <b>egen text</b> (15 tecken)' },
    { d: '2026-09-29', t: 'better', x: 'Kartanalys: "grynnor", hålor visar bara själva gropen, sjöns kant syns, mjukare kanter (även lä); börjar avstängd' },
    { d: '2026-09-29', t: 'better', x: '<b>Åk hit</b> visar hela vägen på kartan' },
    { d: '2026-09-29', t: 'fixed',  x: 'Lodet och Åk hit hittar vägen sjövägen till hela sjön' },
    { d: '2026-09-29', t: 'better', x: 'Ny design på rutorna nertill: dra i strecket för storlek, ✕ i hörnet, knapparna <b>Åk hit · Liknande · Ta bort · Spara</b>' },
    { d: '2026-09-29', t: 'better', x: 'Snabbmeddelanden: Fisk!!!, Mat?, Bajs; tryck för tid och <b>Åk hit</b>; tonas bort, regnbågskant när de är nya' },
    { d: '2026-09-29', t: 'new',    x: 'Ny typ av plats: <b>Hem</b> (hemmet eller bryggan)' },
    { d: '2026-09-29', t: 'better', x: 'Grynnor &amp; hålor räknas som hur mycket de reser sig över omgivningen – hittar grynnorna mitt i sjön' },
    { d: '2026-09-29', t: 'better', x: 'Liknande: platsen själv markerad med rosa ring, "Gå till", förklaring av område' },
    { d: '2026-09-29', t: 'better', x: 'Rutor nertill: dra = mindre, snärta = stäng. "Mörkare" för Kartanalys i Inställningar' },
    { d: '2026-09-29', t: 'new',    x: '<b>Sök</b> i hjälpen, och varje filter förklarat' },
    { d: '2026-09-29', t: 'better', x: 'Platsens ruta visar vad som finns under: djup, lutning, botten, växter' },
    { d: '2026-09-29', t: 'better', x: 'Kartanalys: djupreglage som skalan, mörkare/ljusare karta, reglage för grynnor/hålor och hård botten, dra ner för att stänga' },
    { d: '2026-09-29', t: 'better', x: '"Hitta liknande" direkt från en plats – välj vad som jämförs och hur stort område' },
    { d: '2026-09-29', t: 'better', x: 'Knapparna nere till höger i ett jämnt rutnät; gul sol när skärmen hålls tänd; "Namn" borta ur Filter' },
    { d: '2026-09-29', t: 'new',    x: '<b>Kartanalys</b> – hitta ställen: djup, branta kanter, grynnor &amp; hålor, växtkant, hård botten, vindkant, liknande ställen, Abborre/Gädda/Gös' },
    { d: '2026-09-29', t: 'new',    x: '<b>Åk hit</b> – pil, sträcka och tid sjövägen till en plats' },
    { d: '2026-09-29', t: 'new',    x: '<b>Snabbmeddelanden</b> vid båten (15 min)' },
    { d: '2026-09-29', t: 'new',    x: '<b>Åskvarning</b> med ljud när blixten är nära' },
    { d: '2026-09-29', t: 'new',    x: '<b>Håll skärmen tänd</b> i Filter' },
    { d: '2026-09-29', t: 'better', x: 'Förstoringsglaset nere till höger ersätter uppdatera-knappen' },
    { d: '2026-09-29', t: 'new',    x: '<b>Hjälp</b> – den här sidan, med animeringar för varje funktion' },
    { d: '2026-09-29', t: 'new',    x: '<b>Blixtar i realtid</b> – varning, radar och ⚡ på kartan' },
    { d: '2026-09-29', t: 'new',    x: '<b>Sjösjön</b> finns i menyn' },
    { d: '2026-09-29', t: 'better', x: 'Fara är en röd stoppskylt och syns alltid, för alla' },
    { d: '2026-09-29', t: 'better', x: 'Färgskalan går till sjöns eget maxdjup' },
    { d: '2026-09-29', t: 'fixed',  x: 'Hemskärmsappen på iPhone fyller hela skärmen' },
    { d: '2026-09-28', t: 'better', x: 'Jämn kant på lä-ytan på alla zoomnivåer' },
    { d: '2026-09-28', t: 'new',    x: '<b>Vind och lä</b> i Filter' },
    { d: '2026-09-28', t: 'new',    x: '<b>Ladda ner sjön för offline</b> i Inställningar' },
    { d: '2026-09-28', t: 'better', x: 'Orange vindpil i väderraden' },
    { d: '2026-09-28', t: 'new',    x: 'Nya kartor: fast djupskala, ny skuggning, 8 kartlägen, Regnaren ända till zoom 18' },
    { d: '2026-09-28', t: 'new',    x: '<b>Fara</b> och <b>Träffpunkt</b> (1 h)' },
    { d: '2026-09-28', t: 'new',    x: 'Lodet räknar sträcka <b>sjövägen</b> och restid' },
    { d: '2026-09-28', t: 'new',    x: 'Snabbknapp för kartlägen' },
    { d: '2026-09-28', t: 'new',    x: 'Zoomnivåer som på Genesis: fler kurvor och siffror när du zoomar in' },
    { d: '2026-09-28', t: 'new',    x: '<b>Vågsfjärden</b> – flera sjöar i menyn' }
  ];
  var HELP_SEEN_KEY = 'ffmap_help_seen_v1';   // how many news items you've seen
  var HELP_TAGS = { 'new': 'NYTT', better: 'BÄTTRE', fixed: 'FIXAT' };
  var MONTHS_SV = ['jan', 'feb', 'mar', 'apr', 'maj', 'jun', 'jul', 'aug', 'sep', 'okt', 'nov', 'dec'];
  var helpView = document.getElementById('helpView');
  var helpBody = document.getElementById('helpBody');
  (function(){
    document.getElementById('helpNewsList').innerHTML = HELP_NEWS.map(function(n, i){
      var p = n.d.split('-');
      return '<div class="helpNewsItem' + (i >= 5 ? ' old' : '') + '"><div class="date">' + (+p[2]) + ' ' + MONTHS_SV[+p[1] - 1] + '</div>' +
             '<div><span class="helpTag ' + n.t + '">' + HELP_TAGS[n.t] + '</span>' + n.x + '</div></div>';
    }).join('');
    document.getElementById('helpNewsMore').hidden = HELP_NEWS.length <= 5;
    document.getElementById('helpVer').textContent = 'Version ' + HELP_NEWS[0].d;
    // an animation that isn't there (not made yet / offline): leave the frame out
    Array.prototype.forEach.call(helpView.querySelectorAll('.helpAnim img'), function(im){
      im.addEventListener('error', function(){ im.parentNode.classList.add('missing'); });
    });
  })();
  /* search: every word must be in the same line (or its section's title) -- "filter djup" finds
     the Djup line under Filter. The best (most words in the line itself) first; tap = go there */
  var helpSearchEl = document.getElementById('helpSearch'), helpResEl = document.getElementById('helpResults'), helpIdx = null;
  function helpNorm(t){ return (t || '').toLowerCase().replace(/[^a-zåäö0-9 %]+/g, ' ').replace(/\s+/g, ' '); }
  function helpIndex(){
    if (helpIdx) return helpIdx;
    helpIdx = [];
    Array.prototype.forEach.call(helpBody.querySelectorAll('section.helpCard'), function(sec){
      var title = (sec.querySelector('h3') || {}).textContent || '';
      title = title.replace(/^[^A-Za-zÅÄÖåäö0-9]+/, '').trim();
      Array.prototype.forEach.call(sec.querySelectorAll('li, p:not(.helpSub):not(.helpVer), .helpStep'), function(li){
        helpIdx.push({ sec: sec, el: li, title: title, t: li.textContent.replace(/\s+/g, ' ').trim(), n: helpNorm(li.textContent), nt: helpNorm(title) });
      });
    });
    return helpIdx;
  }
  function helpMark(txt, words){
    var h = escHtml(txt.length > 150 ? txt.slice(0, 147) + '…' : txt);
    words.forEach(function(w){ if (w.length > 1) h = h.replace(new RegExp('(' + w.replace(/[.*+?^${}()|[\]\\]/g, '\\$&') + ')', 'ig'), '<mark>$1</mark>'); });
    return h;
  }
  function helpSearch(){
    var q = helpNorm(helpSearchEl.value).trim(), words = q ? q.split(' ') : [];
    if (!words.length){ helpResEl.classList.remove('show'); helpResEl.innerHTML = ''; return; }
    var hits = helpIndex().map(function(it){
      // each word: in the section's title counts most, a whole word in the line more than part of one
      var score = 0, all = true;
      words.forEach(function(w){
        var t = it.nt.indexOf(w) !== -1 ? 15 : 0, l = 0, k = it.n.indexOf(w);
        if (k !== -1) l = ((' ' + it.n + ' ').indexOf(' ' + w + ' ') !== -1) ? 14 : 10;
        if (!t && !l) all = false;
        score += Math.max(t, l) + (t && l ? 3 : 0);
      });
      return all ? { it: it, score: score - it.t.length / 1000 } : null;
    }).filter(Boolean).sort(function(a, b){ return b.score - a.score; }).slice(0, 8);
    helpResEl.innerHTML = hits.length ? hits.map(function(h, k){
      return '<button type="button" class="hsRes" data-k="' + k + '"><b>' + escHtml(h.it.title) + '</b><span>' + helpMark(h.it.t, words) + '</span></button>';
    }).join('') : '<div class="hsNone">Inget hittades – prova ett annat ord.</div>';
    helpResEl._hits = hits;
    helpResEl.classList.add('show');
  }
  helpSearchEl.addEventListener('input', helpSearch);
  helpResEl.addEventListener('click', function(e){
    var b = e.target.closest ? e.target.closest('.hsRes') : null; if (!b) return;
    var it = helpResEl._hits[+b.getAttribute('data-k')].it;
    helpResEl.classList.remove('show'); helpSearchEl.blur();
    // (the animations on the way load as it scrolls and can move things: set it again a couple of times)
    var go = function(){ helpBody.scrollTop += it.el.getBoundingClientRect().top - helpBody.getBoundingClientRect().top - 90; };
    go(); setTimeout(go, 250); setTimeout(go, 700);
    it.el.classList.remove('hit'); void it.el.offsetWidth; it.el.classList.add('hit');
  });
  document.getElementById('helpNewsMore').addEventListener('click', function(){ document.getElementById('help-nytt').classList.add('all'); });
  function helpSeen(){ var n = 0; try { n = parseInt(localStorage.getItem(HELP_SEEN_KEY), 10) || 0; } catch(e){} return n; }
  function updateHelpDot(){ document.body.classList.toggle('helpNew', helpSeen() < HELP_NEWS.length); }
  // the table of contents: scroll inside the page (no # in the address)
  document.getElementById('helpToc').addEventListener('click', function(e){
    var a = e.target.closest ? e.target.closest('a') : null; if (!a) return;
    e.preventDefault();
    var t = document.getElementById(a.getAttribute('href').slice(1));
    if (t){ var go = function(){ helpBody.scrollTop += t.getBoundingClientRect().top - helpBody.getBoundingClientRect().top - 10; }; go(); setTimeout(go, 250); setTimeout(go, 700); }
  });
  // installing: which phone/browser this is, and whether it's already the home-screen app
  var helpInstallEvt = null;
  window.addEventListener('beforeinstallprompt', function(e){
    e.preventDefault(); helpInstallEvt = e;
    document.getElementById('helpInstallBtn').hidden = false;
  });
  function helpPlatform(){
    var ua = navigator.userAgent || '';
    var ios = /iPhone|iPad|iPod/.test(ua) || (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1);
    if (ios) return /CriOS/.test(ua) ? 'ioschrome' : 'ios';
    if (/Android/.test(ua)) return 'android';
    return 'ios';                                     // (a computer: show the iPhone steps)
  }
  function helpIsInstalled(){
    return !!window.navigator.standalone || (window.matchMedia && window.matchMedia('(display-mode: standalone)').matches);
  }
  function setHelpOs(os){
    Array.prototype.forEach.call(document.querySelectorAll('#helpInstallSeg button'), function(b){ b.classList.toggle('on', b.getAttribute('data-os') === os); });
    Array.prototype.forEach.call(document.querySelectorAll('#helpInstallHow .helpSteps'), function(s){ s.classList.toggle('on', s.getAttribute('data-os') === os); });
  }
  document.getElementById('helpInstallSeg').addEventListener('click', function(e){
    var b = e.target.closest ? e.target.closest('button[data-os]') : null; if (b) setHelpOs(b.getAttribute('data-os'));
  });
  document.getElementById('helpInstallBtn').addEventListener('click', function(){
    if (!helpInstallEvt) return;
    helpInstallEvt.prompt();
    helpInstallEvt = null; document.getElementById('helpInstallBtn').hidden = true;
  });
  function showHelpView(first){
    var inst = helpIsInstalled();
    document.getElementById('helpInstalled').hidden = !inst;
    document.getElementById('helpInstallHow').hidden = inst;
    setHelpOs(helpPlatform());
    helpView.classList.toggle('first', !!first);
    document.getElementById('helpWelcomeName').textContent = userName ? ', ' + userName : '';
    helpView.classList.add('show');
    helpW = helpBody.clientWidth; helpLastPlace = null;
    toggleMenu(false);
    try { localStorage.setItem(HELP_SEEN_KEY, String(HELP_NEWS.length)); } catch(e){}
    updateHelpDot();
  }
  function hideHelpView(){ helpView.classList.remove('show', 'first'); }
  // where you are on the page, as "which section + how far into it" (the pixels change
  // when the phone is turned: other width, other line breaks)
  function helpPlace(){
    var bt = helpBody.getBoundingClientRect().top, best = null;
    Array.prototype.forEach.call(helpBody.querySelectorAll('section[id]'), function(sec){
      var t = sec.getBoundingClientRect().top - bt;
      if (t <= 12 && (!best || t > best.t)) best = { id: sec.id, t: t, h: sec.offsetHeight };
    });
    return { first: helpView.classList.contains('first'), top: helpBody.scrollTop,
             sec: best && best.id, frac: best ? Math.max(0, Math.min(1, -best.t / Math.max(1, best.h))) : 0 };
  }
  // remembered while you scroll -- when the phone is turned, the page has already been
  // laid out again (other width) before the rotation is noticed, so measure before that
  var helpLastPlace = null, helpW = 0;
  helpBody.addEventListener('scroll', function(){
    if (helpBody.clientWidth !== helpW){ helpW = helpBody.clientWidth; return; }   // (a turn, not you)
    helpLastPlace = helpPlace();
  }, { passive: true });
  function helpGoTo(pl){
    var sec = pl.sec && document.getElementById(pl.sec);
    if (!sec){ helpBody.scrollTop = pl.top || 0; return; }
    helpBody.scrollTop += sec.getBoundingClientRect().top - helpBody.getBoundingClientRect().top + (pl.frac || 0) * sec.offsetHeight - 10;
  }
  document.getElementById('menuItemHelp').addEventListener('click', function(){ helpBody.scrollTop = 0; showHelpView(false); });
  document.getElementById('helpBackBtn').addEventListener('click', hideHelpView);
  updateHelpDot();

