
const { chromium } = require('playwright');
(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  await page.goto('http://localhost:19006', { waitUntil: 'networkidle', timeout: 20000 });
  const title = await page.title();
  console.log('Page title:', title);
  const bodyText = await page.textContent('body');
  console.log('Body contains WebToApp:', bodyText.includes('WebToApp'));
  await browser.close();
})();
