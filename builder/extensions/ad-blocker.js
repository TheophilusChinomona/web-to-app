// Ad Blocker Extension
// Blocks common ad scripts and domains

const BLOCKED_DOMAINS = [
  'googleads.g.doubleclick.net',
  'pagead2.googlesyndication.com',
  'ads.yahoo.com',
  'doubleclick.net',
  'adservice.google.com',
];

const BLOCKED_KEYWORDS = [
  '/ad/',
  '/ads/',
  '/advert',
  '/banner',
  '/promo',
  '/sponsor',
];

(function() {
  'use strict';

  // Block image requests matching ad patterns
  const originalCreateElement = Document.prototype.createElement;
  Document.prototype.createElement = function(tagName) {
    const element = originalCreateElement.apply(this, arguments);
    if (tagName.toLowerCase() === 'img') {
      Object.defineProperty(element, 'src', {
        set: function(value) {
          if (BLOCKED_KEYWORDS.some(k => value.includes(k))) {
            console.log('[AdBlocker] Blocked image:', value);
            return;
          }
          Object.getOwnPropertyDescriptor(HTMLImageElement.prototype, 'src').set.call(this, value);
        }
      });
    }
    return element;
  };

  // Intercept fetch/XHR
  const originalFetch = window.fetch;
  window.fetch = function(resource, init) {
    const url = typeof resource === 'string' ? resource : resource.url;
    if (BLOCKED_DOMAINS.some(d => url.includes(d)) || BLOCKED_KEYWORDS.some(k => url.includes(k))) {
      console.log('[AdBlocker] Blocked request:', url);
      return new Response(null, { status: 403 });
    }
    return originalFetch.apply(this, arguments);
  };

  // Remove ad elements from DOM
  const observer = new MutationObserver((mutations) => {
    document.querySelectorAll('[id*="ad"], [class*="ad"], [class*="ads"]').forEach(el => {
      el.remove();
    });
  });

  observer.observe(document, { childList: true, subtree: true });

  console.log('[AdBlocker] Enabled');
})();
