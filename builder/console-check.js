
const { chromium } = require('playwright');
(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  
  const logs = [];
  page.on('console', msg => {
    logs.push(`${msg.type()}: ${msg.text()}`);
  });
  page.on('pageerror', err => {
    logs.push(`PAGEERROR: ${err.message}`);
  });
  
  await page.goto('http://localhost:19006', { waitUntil: 'networkidle', timeout: 30000 });
  
  // Wait a bit for React to render
  await page.waitForTimeout(3000);
  
  console.log('=== Console Logs ===');
  logs.forEach(l => console.log(l));
  
  const body = await page.textContent('body');
  console.log('\n=== Body preview (first 500) ===');
  console.log(body.substring(0, 500));
  
  await browser.close();
})();
