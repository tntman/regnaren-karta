/* FF Map service worker: lets the app open even without coverage.
   - The app page itself: always tries the network first (so a new version
     reaches everyone as soon as they have coverage), but gives up after
     4 s and uses the saved copy instead.
   - Icons, manifest, the map pictures and the Firebase library: served
     from the saved copy (fetched and saved the first time).
   - Firebase's own traffic (the database, sign-in) is never touched here --
     the app's offline data is handled by Firebase itself. */
var CACHE = 'ffmap-v9';
var APP_KEY = './';   // the page is stored under one key, whatever URL it was opened with
var FIREBASE_LIBS = [
  'https://www.gstatic.com/firebasejs/12.19.0/firebase-app-compat.js',
  'https://www.gstatic.com/firebasejs/12.19.0/firebase-auth-compat.js',
  'https://www.gstatic.com/firebasejs/12.19.0/firebase-firestore-compat.js'
];
var STATIC = ['./manifest.webmanifest', './apple-touch-icon.png', './icon-192.png', './icon-512.png'];
// A lake's own files (its map picture, depth data) are saved when the page
// asks for them (message 'precache' below, sent on every start with the
// current lake's files) or the first time they're used; the same goes for
// other map styles and the detail tiles you've zoomed in on.

self.addEventListener('install', function(e){
  e.waitUntil(caches.open(CACHE).then(function(c){
    var jobs = [];
    jobs.push(fetch(APP_KEY, { cache: 'reload' }).then(function(r){ if (r.ok) return c.put(APP_KEY, r); }).catch(function(){}));
    STATIC.forEach(function(u){ jobs.push(fetch(u, { cache: 'reload' }).then(function(r){ if (r.ok) return c.put(u, r); }).catch(function(){})); });
    FIREBASE_LIBS.forEach(function(u){ jobs.push(fetch(new Request(u, { mode: 'no-cors' })).then(function(r){ return c.put(u, r); }).catch(function(){})); });
    return Promise.all(jobs);
  }));
  self.skipWaiting();
});

self.addEventListener('activate', function(e){
  e.waitUntil(caches.keys().then(function(keys){
    // (a lake downloaded for offline -- "ffmap-offline-<lake>-<version>" -- is kept; the
    //  page itself removes it when you press "Ta bort" or download a newer version)
    return Promise.all(keys.filter(function(k){ return k !== CACHE && k.indexOf('ffmap-offline-') !== 0; }).map(function(k){ return caches.delete(k); }));
  }).then(function(){ return self.clients.claim(); }));
});

self.addEventListener('message', function(e){
  var d = e.data || {};
  if (d.type !== 'precache' || !Array.isArray(d.urls)) return;
  e.waitUntil(caches.open(CACHE).then(function(c){
    return Promise.all(d.urls.map(function(u){
      var abs = new URL(u, self.registration.scope).href;
      return c.match(abs).then(function(hit){
        if (hit) return;
        return fetch(abs).then(function(r){ if (r.ok) return c.put(abs, r); }).catch(function(){});
      });
    }));
  }));
});

function isAppPage(req, url){
  return req.mode === 'navigate' ||
    (url.origin === self.location.origin && (/\/$/.test(url.pathname) || /\/index\.html$/.test(url.pathname)));
}

self.addEventListener('fetch', function(e){
  var req = e.request;
  if (req.method !== 'GET') return;
  var url = new URL(req.url);

  if (isAppPage(req, url)){
    e.respondWith(new Promise(function(resolve){
      var done = false;
      function useSaved(){
        if (done) return;
        caches.match(APP_KEY).then(function(r){
          if (done) return;
          if (r){ done = true; resolve(r); }
        });
      }
      var timer = setTimeout(useSaved, 4000); // weak coverage: don't keep people waiting
      fetch(req).then(function(r){
        if (r.ok){
          var copy = r.clone();
          caches.open(CACHE).then(function(c){ c.put(APP_KEY, copy); });
        }
        if (!done){ done = true; clearTimeout(timer); resolve(r); }
      }).catch(function(){
        clearTimeout(timer);
        caches.match(APP_KEY).then(function(r){
          if (done) return;
          done = true;
          resolve(r || new Response('FF Map kunde inte laddas utan nät.', { status: 503, headers: { 'Content-Type': 'text/plain; charset=utf-8' } }));
        });
      });
    }));
    return;
  }

  var sameOrigin = url.origin === self.location.origin;
  var isLib = url.href.indexOf('https://www.gstatic.com/firebasejs/') === 0;
  if (!sameOrigin && !isLib) return; // Firebase database / sign-in etc.: straight to the network

  e.respondWith(caches.match(req.url).then(function(hit){   // (looks in every cache, the offline ones too)
    if (hit) return hit;
    return fetch(req).then(function(r){
      if (r && (r.ok || r.type === 'opaque')){
        var copy = r.clone();
        caches.open(CACHE).then(function(c){ c.put(req.url, copy); });
      }
      return r;
    });
  }));
});
