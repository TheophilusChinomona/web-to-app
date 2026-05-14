// User-Agent Spoofing Extension
// Spoofs browser fingerprint

(function() {
  const SPOOFED_UA = 'Mozilla/5.0 (Linux; Android 14; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36';

  Object.defineProperty(navigator, 'userAgent', {
    get: () => SPOOFED_UA,
  });

  Object.defineProperty(navigator, 'platform', {
    get: () => 'Linux armv81',
  });

  console.log('[Spoofing] User-Agent set to Android Chrome');
})();
