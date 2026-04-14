const CACHE_NAME = 'lantunes-v1';
const STATIC_ASSETS = [
  '/',
  '/index.html',
  '/login.html',
  '/manifest.json',
  'https://unpkg.com/vue@3/dist/vue.global.js',
  'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css'
];

const CACHE_API_PATHS = [
  '/api/library/albums',
  '/api/library/tracks',
  '/api/library/artists',
  '/api/library/genres',
  '/api/playlists',
  '/api/config'
];

self.addEventListener('install', (event) => {
  console.log('[SW] Installing...');
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      console.log('[SW] Caching static assets');
      return cache.addAll(STATIC_ASSETS);
    }).then(() => {
      console.log('[SW] Installed');
      return self.skipWaiting();
    })
  );
});

self.addEventListener('activate', (event) => {
  console.log('[SW] Activating...');
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames
          .filter((name) => name !== CACHE_NAME)
          .map((name) => caches.delete(name))
      );
    }).then(() => {
      console.log('[SW] Activated');
      return self.clients.claim();
    })
  );
});

self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);
  const pathname = url.pathname;
  
  // Skip cross-origin requests
  if (url.origin !== location.origin) {
    return;
  }
  
  // API requests - network first, then cache
  if (pathname.startsWith('/api/')) {
    event.respondWith(
      fetch(event.request)
        .then((response) => {
          // Clone and cache successful responses
          if (response.ok && (pathname.includes('/albums') || pathname.includes('/tracks') || pathname.includes('/artists') || pathname.includes('/playlists'))) {
            const responseClone = response.clone();
            caches.open(CACHE_NAME).then((cache) => {
              cache.put(event.request, responseClone);
            });
          }
          return response;
        })
        .catch(() => {
          // Fall back to cache
          return caches.match(event.request);
        })
    );
    return;
  }
  
  // Static assets and pages - cache first, then network
  event.respondWith(
    caches.match(event.request).then((cachedResponse) => {
      if (cachedResponse) {
        return cachedResponse;
      }
      return fetch(event.request).then((response) => {
        // Cache successful responses for static content
        if (response.ok && (pathname.endsWith('.html') || pathname.endsWith('.js') || pathname.endsWith('.css') || pathname === '/' || pathname === '/index.html' || pathname === '/login.html'))) {
          const responseClone = response.clone();
          caches.open(CACHE_NAME).then((cache) => {
            cache.put(event.request, responseClone);
          });
        }
        return response;
      });
    })
  );
});