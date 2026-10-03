  /* ================= Snabbmeddelanden (quick messages) =================
     A small button at the bottom: tap -> the choices; tap one -> it shows as a bubble at
     your boat for everyone for 15 min (sent with your position, positions/<you>.msg).
     Tap your own bubble to take it back; tap someone else's to hide it for you. */
  var MSG_TEXTS = ['Fisk!!! 🎣', 'Kommer 🚤', 'Åker in 🏠', 'Mat? 🍔', 'Bajs 💩'];
  var MSG_OWN_MAX = 15;                // "Egen text": at most 15 characters (an emoji = 1)
  var MSG_NEW_MS = 5 * 60000;          // the first 5 min: a thin rainbow edge running round the bubble
  var MSG_MS = 15 * 60000;
  // your latest catch as a message ("Gädda 78 cm"): first in the choices while a competition is on; the edge spins in the species' colour
  var MSG_SP_COL = { gadda: '#35D24A', abborre: '#FF7A1A', gos: '#3A86FF' };
  function msgImgOk(u){ return typeof u === 'string' && /^https:\/\/res\.cloudinary\.com\//.test(u) ? u : null; }   // (only the catch photos, never any address someone writes)
  var ownMsg = null, msgHidden = {}, msgLayerEl = document.getElementById('msgLayer');
  var msgBtn = document.getElementById('msgBtn'), msgPop = document.getElementById('msgPop');
  msgPop.innerHTML = MSG_TEXTS.map(function(t){ return '<button type="button" data-t="' + t + '">' + t + '</button>'; }).join('') +
    '<button type="button" id="msgOwnBtn" class="msgOwnBtn"><b class="rbText">Egen text</b><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M4 20l4-1L19 8l-3-3L5 16z"></path><path d="M14 6l3 3"></path></svg></button>';
  var msgOwn = document.getElementById('msgOwn'), msgOwnIn = document.getElementById('msgOwnIn'), msgOwnN = document.getElementById('msgOwnN');
  function openMsgOwn(open){
    msgOwn.classList.toggle('show', open);
    if (open){ msgOwnIn.value = ''; msgOwnCount(); msgOwnIn.focus(); } else msgOwnIn.blur();
  }
  function msgOwnCount(){
    var ch = Array.from(msgOwnIn.value);
    if (ch.length > MSG_OWN_MAX){ msgOwnIn.value = ch.slice(0, MSG_OWN_MAX).join(''); ch = ch.slice(0, MSG_OWN_MAX); }
    msgOwnN.textContent = ch.length + '/' + MSG_OWN_MAX; msgOwnN.classList.toggle('full', ch.length >= MSG_OWN_MAX);
  }
  function sendMsgOwn(){
    var t = msgOwnIn.value.replace(/\s+/g, ' ').trim();
    openMsgOwn(false);
    if (t) sendMsg(Array.from(t).slice(0, MSG_OWN_MAX).join(''));
  }
  msgOwnIn.addEventListener('input', msgOwnCount);
  msgOwnIn.addEventListener('keydown', function(e){ if (e.key === 'Enter'){ e.preventDefault(); sendMsgOwn(); } if (e.key === 'Escape') openMsgOwn(false); });
  document.getElementById('msgOwnGo').addEventListener('click', function(e){ e.stopPropagation(); sendMsgOwn(); });
  msgOwn.addEventListener('pointerdown', function(e){ e.stopPropagation(); });
  msgOwn.addEventListener('click', function(e){ e.stopPropagation(); });
  document.addEventListener('pointerdown', function(e){ if (msgOwn.classList.contains('show') && !msgOwn.contains(e.target)) openMsgOwn(false); });
  function msgMyCatch(){   // your latest counted catch in the competition going on (live), or null
    var me = catchPlain(userName), L = (catchLive && catchLiveComp() ? catchLive.list : []).filter(function(c){ return !c.no && me && catchPlain(c.who) === me; });
    return L.length ? L.reduce(function(a, b){ return b.t > a.t ? b : a; }) : null;
  }
  function msgFishText(c){ return Array.from(hmSpName(c.sp) + ' ' + String(c.cm).replace('.', ',') + ' cm').slice(0, MSG_OWN_MAX).join(''); }
  function msgPopFill(){
    var old = document.getElementById('msgFishBtn'); if (old) old.remove();
    var c = msgMyCatch(); if (!c) return;
    var b = document.createElement('button'); b.type = 'button'; b.id = 'msgFishBtn'; b.className = 'msgFish'; b._c = c;
    b.style.setProperty('--sp', MSG_SP_COL[c.sp]);
    b.innerHTML = '<span class="hmSpDot" style="background:' + MSG_SP_COL[c.sp] + '"></span>' + escHtml(msgFishText(c)) + ' <small>· ' + fmtClock(c.t) + '</small>';
    msgPop.insertBefore(b, msgPop.firstChild);
  }
  function toggleMsgPop(open){ if (open) msgPopFill(); msgPop.classList.toggle('show', open); msgBtn.classList.toggle('open', open); }
  msgBtn.addEventListener('click', function(e){ e.stopPropagation(); toggleMsgPop(!msgPop.classList.contains('show')); if (msgPop.classList.contains('show')) showAnPanel(false); });
  msgPop.addEventListener('pointerdown', function(e){ e.stopPropagation(); });
  msgPop.addEventListener('click', function(e){
    e.stopPropagation();
    if (e.target.closest && e.target.closest('#msgOwnBtn')){ toggleMsgPop(false); openMsgOwn(true); return; }
    var f = e.target.closest ? e.target.closest('#msgFishBtn') : null;
    if (f){ toggleMsgPop(false); sendMsg(msgFishText(f._c), { sp: f._c.sp, img: f._c.img }); return; }
    var b = e.target.closest ? e.target.closest('button[data-t]') : null; if (!b) return;
    toggleMsgPop(false); sendMsg(b.getAttribute('data-t'));
  });
  document.addEventListener('click', function(e){ if (msgPop.classList.contains('show') && !msgPop.contains(e.target) && e.target !== msgBtn) toggleMsgPop(false); });
  function writeMsg(text, at, fish){
    var ll = lastOwnLatLon;
    if (!USE_FIREBASE || !posCol || !myUid || !ll) return;
    addUsage('w', 1);
    try {
      posCol.doc(posDocId(myUid)).set({ lat: ll.lat, lon: ll.lon, name: userName || '', uid: myUid, lake: LAKE_ID, msg: text, msgAt: at,
        msgSp: (fish && fish.sp) || null, msgImg: (fish && fish.img) || null,   // (a catch: its species' colour, its photo)
        updatedAt: firebase.firestore.FieldValue.serverTimestamp() }, { merge: true }).catch(function(e){ console.warn('meddelande', e); });
    } catch(e){ console.warn('meddelande', e); }
  }
  function sendMsg(text, fish){
    if (!(lastOwnLatLon && lastFix && lastFix.onMap)){ showMsgToast('Snabbmeddelanden fungerar när du är vid sjön.'); return; }
    ownMsg = { text: text, at: Date.now(), sp: fish && fish.sp, img: fish && fish.img };
    writeMsg(text, ownMsg.at, fish);
    renderMessages();
    showMsgToast('Syns i 15 minuter, tryck på meddelandet för att ta bort.');
    centerOnFix();
  }
  var msgToastT = null;
  function showMsgToast(t){
    var el = document.getElementById('msgToast');
    el.textContent = t; el.classList.add('show');
    clearTimeout(msgToastT); msgToastT = setTimeout(function(){ el.classList.remove('show'); }, 2600);
  }
  // the rainbow edge follows the bubble's outline, its little tail included: an SVG outline of the
  // shape is the mask of a spinning rainbow (conic gradient)
  function msgRainbow(el){
    var w = el.offsetWidth, h = el.offsetHeight, r = 14, P = 3, rb = el.querySelector('.msgRb'); if (!rb || !w) return;
    var d = 'M' + (P + r) + ' ' + P + 'H' + (P + w - r) + 'A' + r + ' ' + r + ' 0 0 1 ' + (P + w) + ' ' + (P + r) + 'V' + (P + h - r) +
      'A' + r + ' ' + r + ' 0 0 1 ' + (P + w - r) + ' ' + (P + h) + 'H' + (P + 26) + 'L' + (P + 19) + ' ' + (P + h + 7) + 'L' + (P + 12) + ' ' + (P + h) +
      'H' + (P + r) + 'A' + r + ' ' + r + ' 0 0 1 ' + P + ' ' + (P + h - r) + 'V' + (P + r) + 'A' + r + ' ' + r + ' 0 0 1 ' + (P + r) + ' ' + P + 'Z';
    var svg = 'url("data:image/svg+xml,' + encodeURIComponent('<svg xmlns="http://www.w3.org/2000/svg" width="' + (w + 2 * P) + '" height="' + (h + 7 + 2 * P) + '"><path d="' + d + '" fill="none" stroke="#000" stroke-width="3.2" stroke-linejoin="round"/></svg>') + '")';
    rb.style.width = (w + 2 * P) + 'px'; rb.style.height = (h + 7 + 2 * P) + 'px';
    rb.style.webkitMaskImage = svg; rb.style.maskImage = svg;
  }
  var msgItems = {};
  function renderMessages(){
    if (!msgLayerEl) return;
    var now = Date.now(), items = [];
    if (ownMsg && now - ownMsg.at < MSG_MS && lastOwnLatLon) items.push({ key: 'me', mine: true, text: ownMsg.text, who: 'du', at: ownMsg.at, sp: MSG_SP_COL[ownMsg.sp] && ownMsg.sp, img: msgImgOk(ownMsg.img), lat: lastOwnLatLon.lat, lon: lastOwnLatLon.lon });
    Object.keys(boatPositions || {}).forEach(function(id){
      var b = boatPositions[id];
      if (!b.msg || !b.msgAt || now - b.msgAt >= MSG_MS || msgHidden[id + '@' + b.msgAt]) return;
      items.push({ key: id + '@' + b.msgAt, mine: false, text: b.msg, who: b.name, at: b.msgAt, sp: MSG_SP_COL[b.msgSp] && b.msgSp, img: msgImgOk(b.msgImg), lat: b.lat, lon: b.lon });
    });
    // the same boat (as for the boat pins: closer than BOAT_CLUSTER_METERS) = one bubble; newest first
    items.sort(function(a, b){ return b.at - a.at; });
    var groups = [];
    items.forEach(function(it){
      var g = groups.filter(function(q){ return haversineKm(q.lat, q.lon, it.lat, it.lon) * 1000 < BOAT_CLUSTER_METERS; })[0];
      if (g) g.items.push(it); else groups.push({ lat: it.lat, lon: it.lon, items: [it] });
    });
    var keep = {};
    function fade(it){ return 1 - 0.55 * Math.min(1, (now - it.at) / MSG_MS); }       // fades over the 15 min
    groups.forEach(function(g){
      var gk = g.items.map(function(it){ return it.key.replace(/"/g, ''); }).join('|');
      keep[gk] = 1;
      var el = null; Array.prototype.forEach.call(msgLayerEl.children, function(c){ if (c.getAttribute('data-k') === gk) el = c; });
      if (!el){ el = document.createElement('div'); el.setAttribute('data-k', gk); msgLayerEl.appendChild(el); }
      el.className = 'msgBub' + (g.items.length === 1 && g.items[0].mine ? ' mine' : '') + (g.items.length > 1 ? ' multi' : '');
      var isNew = g.items.some(function(it){ return now - it.at < MSG_NEW_MS; }), sp = isNew && g.items[0].sp;   // (a catch, newest: its species' colour instead of the rainbow)
      var html = g.items.map(function(it){
        return '<div class="mLine' + (it.mine ? ' mine' : '') + '" data-k="' + escHtml(it.key.replace(/"/g, '')) + '">' + escHtml(it.text) + '<small>' + escHtml(it.who || '') + '</small></div>';
      }).join('');
      if (el.getAttribute('data-h') !== html + isNew + sp){
        el.setAttribute('data-h', html + isNew + sp);
        el.innerHTML = html + (isNew ? '<i class="msgRb' + (sp ? ' sp" style="--sp:' + MSG_SP_COL[sp] : '') + '"></i>' : '');
        if (isNew) msgRainbow(el);
      }
      var top = fade(g.items[0]);
      el.style.opacity = top.toFixed(2);
      Array.prototype.forEach.call(el.querySelectorAll('.mLine'), function(ln, k){ ln.style.opacity = (fade(g.items[k]) / top).toFixed(2); });
      g.items.forEach(function(it){ msgItems[it.key.replace(/"/g, '')] = it; });
      var p = latLonToImgPx(g.lat, g.lon);
      el.style.left = (originX + p.x * scale) + 'px'; el.style.top = (originY + p.y * scale) + 'px';
    });
    Array.prototype.slice.call(msgLayerEl.children).forEach(function(el){ if (!keep[el.getAttribute('data-k')]) el.remove(); });
  }
  msgLayerEl.addEventListener('pointerdown', function(e){ e.stopPropagation(); if (e.target.closest && e.target.closest('.msgBub')) mapPointerDown(e, true); });
  msgLayerEl.addEventListener('click', function(e){
    var el = e.target.closest ? e.target.closest('.msgBub') : null; if (!el) return;
    e.stopPropagation();
    if (mapDraggedJustNow()) return;
    var line = (e.target.closest && e.target.closest('.mLine')) || el.querySelector('.mLine');   // (a row of a shared bubble)
    if (line) openMsgCard(line.getAttribute('data-k'));
  });
  var msgCard = document.getElementById('msgCard'), msgCardK = null, msgCardT = null;
  function fmtClock(ms){ var d = new Date(ms); return ('0' + d.getHours()).slice(-2) + ':' + ('0' + d.getMinutes()).slice(-2); }
  function openMsgCard(k){
    var it = msgItems[k]; if (!it) return;
    msgCardK = k; if (msgCard._resetSize) msgCard._resetSize();
    var now = Date.now(), age = Math.max(0, now - it.at), left = Math.max(0, MSG_MS - age);
    document.getElementById('msgCardWho').textContent = (it.mine ? 'DU' : String(it.who || '').toUpperCase()) + ' · MEDDELANDE';
    document.getElementById('msgCardTxt').textContent = it.text;
    catchImg(document.getElementById('msgCardImg'), it.img);
    document.getElementById('msgCardWho').classList.toggle('pfLink', !!profileOf(it.mine ? userName : it.who));   // (tap: their profile)
    document.getElementById('msgCardWhen').innerHTML = 'Skrivet <b>' + fmtClock(it.at) + '</b> · ' + (age < 60000 ? 'nyss' : Math.round(age / 60000) + ' min sedan');
    document.getElementById('msgCardLeft').innerHTML = 'Försvinner om <b>' + Math.max(1, Math.ceil(left / 60000)) + ' min</b>';
    document.getElementById('msgCardBar').style.width = (100 * left / MSG_MS).toFixed(1) + '%';
    document.getElementById('msgCardGo').hidden = !!it.mine;
    document.getElementById('msgCardDrop').textContent = it.mine ? 'Ta bort (för alla)' : 'Dölj för mig';
    msgCard.classList.add('show');
    clearTimeout(msgCardT); msgCardT = setTimeout(function(){ if (msgCard.classList.contains('show') && msgItems[msgCardK]) openMsgCard(msgCardK); }, 20000);
  }
  function closeMsgCard(){ msgCard.classList.remove('show'); msgCardK = null; clearTimeout(msgCardT); }
  msgCard.addEventListener('pointerdown', function(e){ e.stopPropagation(); });
  sheetSwipe(msgCard, closeMsgCard);
  document.getElementById('msgCardClose').addEventListener('click', closeMsgCard);
  document.getElementById('msgCardWho').addEventListener('click', function(){ var it = msgItems[msgCardK]; if (it && this.classList.contains('pfLink')) openProfile(it.mine ? userName : it.who); });
  document.getElementById('msgCardGo').addEventListener('click', function(){
    var it = msgItems[msgCardK]; if (!it) return;
    closeMsgCard(); var p = latLonToImgPx(it.lat, it.lon); startNav(it.who, p.x, p.y);   // the lead line on their boat
  });
  document.getElementById('msgCardDrop').addEventListener('click', function(){
    var k = msgCardK; closeMsgCard();
    if (k === 'me'){ ownMsg = null; writeMsg(null, 0); }       // yours: taken back for everyone
    else msgHidden[k] = true;                                     // someone else's: hidden for you
    renderMessages();
  });
  setInterval(renderMessages, 20000);
  window.__ffMsgs = function(){ return Array.prototype.map.call(msgLayerEl.querySelectorAll('.mLine'), function(ln){ var b = ln.parentNode;
    return { k: ln.getAttribute('data-k'), t: ln.textContent, bubble: b.getAttribute('data-k'), o: +(b.style.opacity || 1) * +(ln.style.opacity || 1) }; }); };
  ltRender(); ltTick();

