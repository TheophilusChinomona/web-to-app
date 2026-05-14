
const { chromium } = require('playwright');
const fs = require('fs');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext();
  const page = await context.newPage();
  
  // Capture console logs
  page.on('console', msg => {
    console.log('CONSOLE:', msg.type(), msg.text());
  });
  
  page.on('pageerror', err => {
    console.log('PAGE ERROR:', err.message);
  });

  try {
    await page.goto('http://localhost:19006', { waitUntil: 'networkidle', timeout: 30000 });
    console.log('Page loaded');
    
    // Take screenshot
    await page.screenshot({ path: 'builder/debug-screenshot.png', fullPage: true });
    console.log('Screenshot saved to builder/debug-screenshot.png');
    
    // Get visible text
    const text = await page.textContent('body');
    console.log('Body text preview:', text.substring(0, 500));
    
    // Check for our expected elements
    const hasBuilderTitle = await page.locator('text=WebToApp Builder').count();
    console.log('Found "WebToApp Builder" instances:', hasBuilderTitle);
    
    const hasFab = await page.locator('text=Create App').count();
    console.log('Found "Create App" instances:', hasFab);
    
    await browser.close();
  } catch (err) {
    console.error('Playwright error:', err);
    await browser.close();
    process.exit(1);
  }
})();
