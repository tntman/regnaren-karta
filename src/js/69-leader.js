  /* ================= "Ledare" (Filter, Lager) -- off by default =================
     While a competition is going on on this lake: a list under the weather chip (top 5 + you) and a crown
     after the leader's name on the map. Counted like Fiskfiskarna do: the 5 longest of each species added up
     (perch + pike + zander, cm), only catches that count (approved by the API, and at least the minimum size).
     The data is the live catches (66-catches.js); nothing extra is fetched. Tap-through: nothing. */
  var LEAD_KEY = 'ffmap_leader_v1';
  var LEAD_MIN = { abborre: 25, gadda: 50, gos: 35 };   // (cm: what counts at Fiskfiskarna's competitions)
  var leadOn = false;
  try { leadOn = localStorage.getItem(LEAD_KEY) === '1'; } catch(e){}
  var leadPill = document.getElementById('leadPill'), toggleLeadEl = document.getElementById('toggleLeader');
  var leadList = [];   // [{ who, total, n }] best first
  function leadCompute(){
    var by = {};
    (catchLive && catchLiveComp() ? catchLive.all : []).forEach(function(c){   // (the whole competition, other waters too)
      if (c.no || c.cm < LEAD_MIN[c.sp]) return;
      var k = catchPlain(c.who); if (!k) return;
      var p = by[k] || (by[k] = { who: c.who, sp: { abborre: [], gadda: [], gos: [] } });
      p.sp[c.sp].push(c.cm);
    });
    return Object.keys(by).map(function(k){
      var p = by[k], t = 0;
      Object.keys(p.sp).forEach(function(s){ p.sp[s].sort(function(a, b){ return b - a; }).slice(0, 5).forEach(function(cm){ t += cm; }); });
      return { who: p.who, total: Math.round(t) };
    }).sort(function(a, b){ return b.total - a.total || (a.who < b.who ? -1 : 1); });
  }
  // the leader's name on a boat label (24-boats.js asks)
  function leadCrownFor(name){ return leadOn && leadList.length > 0 && catchPlain(name) === catchPlain(leadList[0].who) ? ' \u{1F451}' : ''; }
  function leadRender(){
    var was = leadList.length ? leadList[0].who : '';
    leadList = leadCompute();
    var show = leadOn && leadList.length > 0, me = catchPlain(userName);
    leadPill.hidden = !show;
    if (show){
      var top = leadList.slice(0, 5), mine = leadList.map(function(r){ return catchPlain(r.who); }).indexOf(me);
      var row = function(i, r){
        return '<div class="ldRow' + (me && catchPlain(r.who) === me ? ' me' : '') + '"><span class="ldN">' + (i + 1) + '</span><span class="ldW" data-who="' + escHtml(r.who) + '">' + escHtml(r.who) + (i === 0 ? ' \u{1F451}' : '') + '</span><span class="ldT">' + r.total + ' cm</span></div>';
      };
      leadPill.innerHTML = top.map(function(r, i){ return row(i, r); }).join('') +
        (mine >= 5 ? '<div class="ldGap">…</div>' + row(mine, leadList[mine]) : '');
    }
    if ((leadList.length ? leadList[0].who : '') !== was || !show) renderBoats();   // (the crown moves)
  }
  leadPill.addEventListener('pointerdown', function(e){ e.stopPropagation(); });
  leadPill.addEventListener('click', function(e){   // a name: the map goes to that person's boat
    var r = e.target.closest ? e.target.closest('.ldRow') : null, b = r && pfBoat(r.querySelector('.ldW').getAttribute('data-who'));
    if (b) b.me ? centerOnFix() : centerOnWaypoint(b);
  });
  catchListeners.push(leadRender);
  toggleLeadEl.checked = leadOn;
  toggleLeadEl.addEventListener('change', function(){
    leadOn = toggleLeadEl.checked;
    try { localStorage.setItem(LEAD_KEY, leadOn ? '1' : '0'); } catch(e){}
    leadRender(); renderBoats();
  });
  window.__ffLeader = function(){ return { on: leadOn, list: leadList.slice(), shown: !leadPill.hidden }; };   // (for the tests)
