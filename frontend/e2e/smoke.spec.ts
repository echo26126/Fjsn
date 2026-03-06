
import { test, expect } from '@playwright/test';

test.describe('Smoke Tests - Key Pages', () => {
  
  test('should load Dashboard', async ({ page }) => {
    await page.goto('/dashboard');
    await expect(page).toHaveURL(/.*dashboard/);
    // Add more specific assertions here, e.g., checking for specific elements
    // await expect(page.locator('h1')).toContainText('态势感知'); // Example
  });

  test('should load Production Query', async ({ page }) => {
    await page.goto('/production');
    await expect(page).toHaveURL(/.*production/);
  });

  test('should load Inventory Monitor', async ({ page }) => {
    await page.goto('/inventory');
    await expect(page).toHaveURL(/.*inventory/);
  });

  test('should load Sales Management', async ({ page }) => {
    await page.goto('/sales');
    await expect(page).toHaveURL(/.*sales/);
  });

  test('should load Sales Forecast', async ({ page }) => {
    await page.goto('/sales-forecast');
    await expect(page).toHaveURL(/.*sales-forecast/);
  });

  test('should load Balance Optimize', async ({ page }) => {
    await page.goto('/balance');
    await expect(page).toHaveURL(/.*balance/);
  });

  test('should load Data Management', async ({ page }) => {
    await page.goto('/data');
    await expect(page).toHaveURL(/.*data/);
  });

});
