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
  var headerUserEl = document.getElementById('headerUser');
  var HEADER_USER_ICON = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="8" r="4"></circle><path d="M4 21c0-4 3.6-7 8-7s8 3 8 7"></path></svg>';
  function showUserName(){
    updateAdminVisibility();
    settingsNameDisplay.textContent = userName;
    if (userName){
      headerUserEl.innerHTML = HEADER_USER_ICON;
      var t = document.createElement('span');
      t.textContent = userName;
      headerUserEl.appendChild(t);
    } else {
      headerUserEl.innerHTML = '';
    }
  }
  showUserName();

  function saveUserName(v){
    userName = canonicalName(v).slice(0, 24);
    try { localStorage.setItem(USER_NAME_KEY, userName); } catch(e){}
  }

  var selectedRosterName = null;
  var otherNameMode = false;
  function renderNameList(){
    nameListEl.innerHTML = '';
    NAME_ROSTER.forEach(function(n){
      var b = document.createElement('button');
      b.type = 'button';
      b.className = 'nameChip';
      b.setAttribute('data-name', n);
      b.textContent = n;
      nameListEl.appendChild(b);
    });
    var other = document.createElement('button');
    other.type = 'button';
    other.className = 'nameChip nameChip--other';
    other.setAttribute('data-other', '1');
    other.textContent = 'Annat namn…';
    nameListEl.appendChild(other);
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
      setTimeout(function(){ nameInput.focus(); }, 50);
    } else {
      otherNameMode = false;
      selectedRosterName = chip.getAttribute('data-name');
      otherNameWrap.hidden = true;
      nameInput.blur();
    }
  });

  function showNameModal(){
    selectedRosterName = null;
    otherNameMode = false;
    Array.from(nameListEl.children).forEach(function(c){ c.classList.remove('selected'); });
    nameListEl.scrollTop = 0;
    otherNameWrap.hidden = true;
    nameInput.value = '';
    nameErrorEl.hidden = true;
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
  });

  // Name is locked once set — the only way to change identity is to log out
  // and re-enter a (possibly new) name via the mandatory modal.
  var logoutBtn = document.getElementById('logoutBtn');
  logoutBtn.addEventListener('click', function(){
    expireOwnPosition(); // so the old name's pip disappears for everyone now, not in an hour
    try { localStorage.removeItem(USER_NAME_KEY); } catch(e){}
    userName = '';
    myUid = null;
    lastPosWriteAt = 0;       // the next name gets shared right away
    lastWrittenLatLon = null;
    showUserName();
    showMapView();
    showNameModal();
  });

