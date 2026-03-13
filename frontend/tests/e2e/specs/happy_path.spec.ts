import { test, expect } from '@playwright/test';

test.describe('Excell App Happy Path', () => {
    test('should load the dashboard and allow navigation', async ({ page }) => {
        // Navigate to the app
        await page.goto('/');

        // Ensure the page title or primary heading is visible
        await expect(page.locator('text=Excell App').first()).toBeVisible();

        // Navigate to Analysis view
        await page.click('text=Analysis');

        // Ensure the analysis wizard appears
        await expect(page.locator('.ui-wizard-container')).toBeVisible();

        // Simple validation that the file upload dropzone exists
        await expect(page.locator('.p-fileupload')).toBeVisible();
    });
});
