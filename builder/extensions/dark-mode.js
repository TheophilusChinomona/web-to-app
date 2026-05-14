// Dark Mode Extension
// Injects CSS to force dark theme

(function() {
  'use strict';

  const style = document.createElement('style');
  style.textContent = `
    html, body {
      background-color: #121212 !important;
      color: #e0e0e0 !important;
    }
    * {
      background-color: transparent !important;
      border-color: #333 !important;
    }
    img {
      filter: brightness(0.8) !important;
    }
  `;
  document.head.appendChild(style);
  console.log('[DarkMode] Enabled');
})();
