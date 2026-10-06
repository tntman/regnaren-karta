  /* ---------------- Ditt namn (= din identitet, funkar över alla enheter) ----------------
     You pick your name from the club's member list (or "Annat namn" as a
     fallback). The name is still what identifies you and your spots, exactly
     as before: same name = same person, on any device. */
  var NAME_ROSTER = [
    'Henrik', 'Filip', 'Stisse', 'Matilda', 'Patrik', 'Sunbaum', 'Jörgen', 'Gurki', 'Calle', 'Peter',
    'Gurra', 'Camilla', 'Rode', 'Hedda', 'Holo', 'Pontus', 'Stephanie', 'Magnus', 'Alexis', 'Maya',
    'Rebeca', 'Jonas', 'Bella', 'Joel', 'Calum', 'Melsom', 'Jonathan', 'Laurent', 'Erika', 'Ludvig',
    'Andreas', 'Kristian', 'Gianni', 'Bystedt', 'Steven', 'Sebastian', 'Björn', 'Melle', 'Emnet'
  ].sort(function(a, b){ return a.localeCompare(b, 'sv'); });

  var USER_NAME_KEY = 'regnaren_user_name_v1';
  var userName = '';
  try { userName = localStorage.getItem(USER_NAME_KEY) || ''; } catch(e){}

  var nameBackdrop = document.getElementById('nameBackdrop');
  var nameModal = document.getElementById('nameModal');
  var nameListEl = document.getElementById('nameList');
  var otherNameWrap = document.getElementById('otherNameWrap');
  var nameInput = document.getElementById('nameInput');
  var nameSaveBtn = document.getElementById('nameSave');
  var nameErrorEl = document.getElementById('nameError');
  var settingsNameDisplay = document.getElementById('settingsNameDisplay');

  // Same name -> same id, on any device/browser. Trim + lowercase + collapse
  // whitespace so "Filip", " filip " and "FILIP" all resolve to one identity.
  function nameSlug(v){
    return (v || '').trim().toLowerCase().replace(/\s+/g, ' ');
  }
  // If a name matches someone on the member list (in any capitalisation),
  // use the list's spelling -- same identity, just displayed consistently.
  function canonicalName(v){
    var s = nameSlug(v);
    for (var i = 0; i < NAME_ROSTER.length; i++){
      if (nameSlug(NAME_ROSTER[i]) === s) return NAME_ROSTER[i];
    }
    return (v || '').trim();
  }
  userName = canonicalName(userName);
  var menuAva = document.getElementById('menuAva');
  var menuChev = document.getElementById('menuChev');
  var menuBurger = document.querySelector('#menuBtn > svg');
  var menuItemLogout = document.getElementById('menuItemLogout');
  function showUserName(){
    updateAdminVisibility();
    settingsNameDisplay.textContent = userName;
    var pic = AVATARS[userName], sa = document.getElementById('settingsAva');   // (the profile card on top of Inställningar)
    sa.textContent = pic ? '' : (userName || '?').charAt(0).toUpperCase();
    sa.style.backgroundImage = pic ? 'url("' + pic + '")' : '';
    menuAva.hidden = menuChev.hidden = !pic;
    menuBurger.style.display = pic ? 'none' : '';
    menuBtn.classList.toggle('hasAva', !!pic);
    if (pic) menuAva.src = pic;
    menuItemLogout.hidden = document.getElementById('menuLogoutSep').hidden = !userName;
    document.getElementById('menuLogoutText').textContent = 'Logga ut ' + userName;
  }
  showUserName();

  function saveUserName(v){
    userName = canonicalName(v).slice(0, 24);
    try { localStorage.setItem(USER_NAME_KEY, userName); } catch(e){}
  }

  var selectedRosterName = null;
  var otherNameMode = false;
  // the members as pictures (AVATARS; none -> their first letter), "Annat namn" last; they fade in one after another
  function renderNameList(){
    nameListEl.innerHTML = '';
    NAME_ROSTER.forEach(function(n, i){
      var b = document.createElement('button');
      b.type = 'button';
      b.className = 'nameChip';
      b.setAttribute('data-name', n);
      b.style.animationDelay = Math.min(i, 15) * 22 + 'ms';
      b.innerHTML = '<span class="ava">' + (AVATARS[n] ? '<img alt="" src="' + AVATARS[n] + '">' : escHtml(Array.from(n)[0] || '?').toUpperCase()) + '</span><b>' + escHtml(n) + '</b>';
      nameListEl.appendChild(b);
    });
    var other = document.createElement('button');
    other.type = 'button';
    other.className = 'nameChip nameChip--other';
    other.setAttribute('data-other', '1');
    other.style.animationDelay = Math.min(NAME_ROSTER.length, 15) * 22 + 'ms';
    other.innerHTML = '<span class="ava">+</span><b>Annat namn</b>';
    nameListEl.appendChild(other);
  }
  // the button says who you continue as ("Fortsätt som Filip"), amber once someone is chosen
  function updNameBtn(){
    var v = otherNameMode ? nameInput.value.trim() : (selectedRosterName || '');
    nameSaveBtn.classList.toggle('on', !!v);
    nameSaveBtn.textContent = v ? 'Fortsätt som ' + v : (otherNameMode ? 'Skriv ditt namn' : 'Välj dig själv');
    nameListEl.classList.toggle('has', !!selectedRosterName);
    nameModal.classList.toggle('otherMode', otherNameMode);
  }
  renderNameList();

  nameListEl.addEventListener('click', function(e){
    var chip = e.target.closest ? e.target.closest('.nameChip') : null;
    if (!chip) return;
    Array.from(nameListEl.children).forEach(function(c){ c.classList.toggle('selected', c === chip); });
    nameErrorEl.hidden = true;
    if (chip.getAttribute('data-other')){
      otherNameMode = true;
      selectedRosterName = null;
      otherNameWrap.hidden = false;
      setTimeout(function(){ nameInput.focus(); nameListEl.scrollTop = nameListEl.scrollHeight; }, 50);
    } else {
      otherNameMode = false;
      selectedRosterName = chip.getAttribute('data-name');
      otherNameWrap.hidden = true;
      nameInput.blur();
    }
    updNameBtn();
  });

  function showNameModal(){
    if (splashOn()){ afterSplash(showNameModal); return; }   // (after the start film, 35-splash.js)
    selectedRosterName = null;
    otherNameMode = false;
    Array.from(nameListEl.children).forEach(function(c){ c.classList.remove('selected'); });
    nameListEl.scrollTop = 0;
    otherNameWrap.hidden = true;
    nameInput.value = '';
    nameErrorEl.hidden = true;
    updNameBtn();
    nameBackdrop.classList.add('show');
    nameModal.classList.add('show');
  }
  function hideNameModal(){
    nameBackdrop.classList.remove('show');
    nameModal.classList.remove('show');
  }

  nameSaveBtn.addEventListener('click', function(){
    var v = otherNameMode ? nameInput.value.trim() : (selectedRosterName || '');
    if (!v){
      nameErrorEl.textContent = otherNameMode ? 'Skriv ditt namn för att fortsätta.' : 'Välj ditt namn i listan för att fortsätta.';
      nameErrorEl.hidden = false;
      if (otherNameMode) nameInput.focus();
      return;
    }
    saveUserName(v);
    showUserName();
    myUid = nameSlug(userName);
    hideNameModal();
    if (appStarted){
      // returning from "Logga ut" — geolocation/Firebase are already running,
      // just re-evaluate ownership of the pins already on screen under the new name
      renderWaypoints();
    } else {
      continueBootAfterName();
      if (!helpSeen()) showHelpView(true);   // the very first time on this phone: Hjälp, with a welcome
    }
  });
  nameInput.addEventListener('keydown', function(e){
    if (e.key === 'Enter') nameSaveBtn.click();
  });
  nameInput.addEventListener('input', function(){
    if (!nameErrorEl.hidden) nameErrorEl.hidden = true;
    updNameBtn();
  });

  // Name is locked once set — the only way to change identity is to log out
  // and re-enter a (possibly new) name via the mandatory modal.
  var logoutBtn = document.getElementById('logoutBtn');
  menuItemLogout.addEventListener('click', function(){ toggleMenu(false); logoutBtn.click(); });
  logoutBtn.addEventListener('click', function(){
    expireOwnPosition(); // so the old name's pip disappears for everyone now, not in an hour
    try { localStorage.removeItem(USER_NAME_KEY); } catch(e){}
    splashAfterLogout();     // (closed now and opened again: the start film)
    userName = '';
    myUid = null;
    lastPosWriteAt = 0;       // the next name gets shared right away
    lastWrittenLatLon = null;
    showUserName();
    showMapView();
    showNameModal();
  });

