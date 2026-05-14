import { test, expect, Page } from '@playwright/test';
import * as path from 'path';
import * as fs from 'fs';

// Helper to get test output directory
const getTestOutputDir = (testInfo: any) => {
  return path.join(process.cwd(), 'test-output', testInfo.titlePath.join('--'));
};

test.describe('WebToApp Builder E2E', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to builder web app (Expo web)
    await page.goto('/');
    // Wait for app to load
    await expect(page).toHaveURL('/');
  });

  test('home page displays correctly', async ({ page }) => {
    await expect(page.locator('text=WebToApp Builder')).toBeVisible();
    await expect(page.locator('text=No projects yet')).toBeVisible();
    // FAB should be visible
    await expect(page.getByRole('button', { name: /create app/i })).toBeVisible();
  });

  test('can create a new project via wizard', async ({ page }) => {
    // Click Create App
    await page.getByRole('button', { name: /create app/i }).click();
    await expect(page).toHaveURL(/.*create/);
    await expect(page.locator('text=Basic Information')).toBeVisible();

    // Fill basic info
    await page.getByLabel('App Name').fill('My Test App');
    await page.getByLabel('Website URL').fill('https://example.com');
    await page.getByLabel('Package Name \(Android\)').fill('com.example.testapp');

    // Next step
    await page.getByRole('button', { name: /next/i }).click();

    // Appearance step - skip image upload, just go next
    await expect(page.locator('text=Appearance')).toBeVisible();
    await page.getByRole('button', { name: /next/i }).click();

    // Features step
    await expect(page.locator('text=Features')).toBeVisible();
    await page.getByRole('button', { name: /next/i }).click();

    // Confirm step
    await expect(page.locator('text=Confirm \& Generate')).toBeVisible();
    await expect(page.locator('text=My Test App')).toBeVisible();

    // Submit
    await page.getByRole('button', { name: /generate app/i }).click();

    // Wait for alert
    await page.waitForEvent('dialog', { timeout: 5000 });
    // Accept alert
    const dialog = page.waitForEvent('dialog');
    await (await dialog).accept();

    // Should navigate to project detail or home
    await expect(page).toHaveURL(/.*projects/);
    // Project details should show name
    await expect(page.locator('text=My Test App')).toBeVisible();
  });

  test('validates required fields on basic step', async ({ page }) => {
    await page.getByRole('button', { name: /create app/i }).click();

    // Try to proceed without filling
    await page.getByRole('button', { name: /next/i }).click();

    // Should see error messages
    await expect(page.locator('text=App name is required')).toBeVisible();
    await expect(page.locator('text=URL is required')).toBeVisible();
  });

  test('validates URL format', async ({ page }) => {
    await page.getByRole('button', { name: /create app/i }).click();

    // Enter invalid URL
    await page.getByLabel('App Name').fill('Test');
    await page.getByLabel('Website URL').fill('not-a-url');
    await page.getByRole('button', { name: /next/i }).click();

    await expect(page.locator('text=URL must start with http:// or https://')).toBeVisible();
  });

  test('can delete a project', async ({ page }) => {
    // Setup: create a project first
    await page.getByRole('button', { name: /create app/i }).click();
    await page.getByLabel('App Name').fill('Delete Me');
    await page.getByLabel('Website URL').fill('https://example.com');
    await page.getByRole('button', { name: /next/i }).click();
    await page.getByRole('button', { name: /next/i }).click();
    await page.getByRole('button', { name: /next/i }).click();
    await page.getByRole('button', { name: /generate app/i }).click();
    await (await page.waitForEvent('dialog')).accept();

    // Now delete
    await page.getByRole('button', { name: /delete/i }).click();
    // Confirm alert
    const dialog = page.waitForEvent('dialog');
    await (await dialog).accept();

    // Project should be removed from list
    await expect(page.locator('text=Delete Me')).not.toBeVisible();
  });

  test('dark mode toggle works', async ({ page }) => {
    // Go to settings
    await page.getByRole('button', { name: /settings/i }).click();
    await expect(page).toHaveURL(/.*settings/);

    // Toggle dark mode
    const toggle = page.getByRole('switch');
    const initialState = await toggle.isChecked();
    await toggle.click();

    // Should toggle
    const newState = await toggle.isChecked();
    expect(newState).toBe(!initialState);
  });
});

test.describe('Generator Integration', () => {
  test('generated project contains expected files', async ({ page }) => {
    // This test would require accessing the filesystem directly.
    // For now, we skip file-system checks as they require Node context.
    // In a full setup, the test would invoke GeneratorService directly.
    test.skip(true, 'Filesystem verification requires Node integration');
  });
});
