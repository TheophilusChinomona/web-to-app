# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: e2e.spec.ts >> WebToApp Builder E2E >> validates required fields on basic step
- Location: playwright-tests/e2e.spec.ts:66:7

# Error details

```
Test timeout of 30000ms exceeded.
```

```
Error: locator.click: Test timeout of 30000ms exceeded.
Call log:
  - waiting for getByRole('button', { name: /create app/i })

```

# Test source

```ts
  1   | import { test, expect, Page } from '@playwright/test';
  2   | import * as path from 'path';
  3   | import * as fs from 'fs';
  4   | 
  5   | // Helper to get test output directory
  6   | const getTestOutputDir = (testInfo: any) => {
  7   |   return path.join(process.cwd(), 'test-output', testInfo.titlePath.join('--'));
  8   | };
  9   | 
  10  | test.describe('WebToApp Builder E2E', () => {
  11  |   test.beforeEach(async ({ page }) => {
  12  |     // Navigate to builder web app (Expo web)
  13  |     await page.goto('/');
  14  |     // Wait for app to load
  15  |     await expect(page).toHaveURL('/');
  16  |   });
  17  | 
  18  |   test('home page displays correctly', async ({ page }) => {
  19  |     await expect(page.locator('text=WebToApp Builder')).toBeVisible();
  20  |     await expect(page.locator('text=No projects yet')).toBeVisible();
  21  |     // FAB should be visible
  22  |     await expect(page.getByRole('button', { name: /create app/i })).toBeVisible();
  23  |   });
  24  | 
  25  |   test('can create a new project via wizard', async ({ page }) => {
  26  |     // Click Create App
  27  |     await page.getByRole('button', { name: /create app/i }).click();
  28  |     await expect(page).toHaveURL(/.*create/);
  29  |     await expect(page.locator('text=Basic Information')).toBeVisible();
  30  | 
  31  |     // Fill basic info
  32  |     await page.getByLabel('App Name').fill('My Test App');
  33  |     await page.getByLabel('Website URL').fill('https://example.com');
  34  |     await page.getByLabel('Package Name \(Android\)').fill('com.example.testapp');
  35  | 
  36  |     // Next step
  37  |     await page.getByRole('button', { name: /next/i }).click();
  38  | 
  39  |     // Appearance step - skip image upload, just go next
  40  |     await expect(page.locator('text=Appearance')).toBeVisible();
  41  |     await page.getByRole('button', { name: /next/i }).click();
  42  | 
  43  |     // Features step
  44  |     await expect(page.locator('text=Features')).toBeVisible();
  45  |     await page.getByRole('button', { name: /next/i }).click();
  46  | 
  47  |     // Confirm step
  48  |     await expect(page.locator('text=Confirm \& Generate')).toBeVisible();
  49  |     await expect(page.locator('text=My Test App')).toBeVisible();
  50  | 
  51  |     // Submit
  52  |     await page.getByRole('button', { name: /generate app/i }).click();
  53  | 
  54  |     // Wait for alert
  55  |     await page.waitForEvent('dialog', { timeout: 5000 });
  56  |     // Accept alert
  57  |     const dialog = page.waitForEvent('dialog');
  58  |     await (await dialog).accept();
  59  | 
  60  |     // Should navigate to project detail or home
  61  |     await expect(page).toHaveURL(/.*projects/);
  62  |     // Project details should show name
  63  |     await expect(page.locator('text=My Test App')).toBeVisible();
  64  |   });
  65  | 
  66  |   test('validates required fields on basic step', async ({ page }) => {
> 67  |     await page.getByRole('button', { name: /create app/i }).click();
      |                                                             ^ Error: locator.click: Test timeout of 30000ms exceeded.
  68  | 
  69  |     // Try to proceed without filling
  70  |     await page.getByRole('button', { name: /next/i }).click();
  71  | 
  72  |     // Should see error messages
  73  |     await expect(page.locator('text=App name is required')).toBeVisible();
  74  |     await expect(page.locator('text=URL is required')).toBeVisible();
  75  |   });
  76  | 
  77  |   test('validates URL format', async ({ page }) => {
  78  |     await page.getByRole('button', { name: /create app/i }).click();
  79  | 
  80  |     // Enter invalid URL
  81  |     await page.getByLabel('App Name').fill('Test');
  82  |     await page.getByLabel('Website URL').fill('not-a-url');
  83  |     await page.getByRole('button', { name: /next/i }).click();
  84  | 
  85  |     await expect(page.locator('text=URL must start with http:// or https://')).toBeVisible();
  86  |   });
  87  | 
  88  |   test('can delete a project', async ({ page }) => {
  89  |     // Setup: create a project first
  90  |     await page.getByRole('button', { name: /create app/i }).click();
  91  |     await page.getByLabel('App Name').fill('Delete Me');
  92  |     await page.getByLabel('Website URL').fill('https://example.com');
  93  |     await page.getByRole('button', { name: /next/i }).click();
  94  |     await page.getByRole('button', { name: /next/i }).click();
  95  |     await page.getByRole('button', { name: /next/i }).click();
  96  |     await page.getByRole('button', { name: /generate app/i }).click();
  97  |     await (await page.waitForEvent('dialog')).accept();
  98  | 
  99  |     // Now delete
  100 |     await page.getByRole('button', { name: /delete/i }).click();
  101 |     // Confirm alert
  102 |     const dialog = page.waitForEvent('dialog');
  103 |     await (await dialog).accept();
  104 | 
  105 |     // Project should be removed from list
  106 |     await expect(page.locator('text=Delete Me')).not.toBeVisible();
  107 |   });
  108 | 
  109 |   test('dark mode toggle works', async ({ page }) => {
  110 |     // Go to settings
  111 |     await page.getByRole('button', { name: /settings/i }).click();
  112 |     await expect(page).toHaveURL(/.*settings/);
  113 | 
  114 |     // Toggle dark mode
  115 |     const toggle = page.getByRole('switch');
  116 |     const initialState = await toggle.isChecked();
  117 |     await toggle.click();
  118 | 
  119 |     // Should toggle
  120 |     const newState = await toggle.isChecked();
  121 |     expect(newState).toBe(!initialState);
  122 |   });
  123 | });
  124 | 
  125 | test.describe('Generator Integration', () => {
  126 |   test('generated project contains expected files', async ({ page }) => {
  127 |     // This test would require accessing the filesystem directly.
  128 |     // For now, we skip file-system checks as they require Node context.
  129 |     // In a full setup, the test would invoke GeneratorService directly.
  130 |     test.skip(true, 'Filesystem verification requires Node integration');
  131 |   });
  132 | });
  133 | 
```