import { test, expect } from '@playwright/test';
import path from 'path';

test.describe('Analysis Flow', () => {
    test.beforeEach(async ({ page }) => {
        await page.addInitScript(() => {
            localStorage.clear();
            sessionStorage.clear();
        });

        // Start from Dashboard
        await page.goto('/');
        await page.waitForLoadState('networkidle');

        // Click New Analysis
        await page.locator('.ui-feature-card--primary').click();
        await expect(page).toHaveURL(/\/analysis/);
        await page.waitForLoadState('networkidle');
    });

    test('should upload CSV and advance to next step', async ({ page }) => {
        // 1. Check initial state
        await expect(page.locator('.ui-upload-headline')).toBeVisible({ timeout: 5000 });

        // 2. Upload file
        const fileInput = page.locator('input[type="file"][accept=".csv"]');
        await fileInput.setInputFiles(path.resolve(process.cwd(), 'tests/e2e/fixtures/test-data.csv'));

        // 3. Wait for preview and Next button
        const nextButton = page.getByRole('button', { name: 'Next' });
        await expect(nextButton).toBeVisible({ timeout: 5000 });

        // 4. Click Next
        await nextButton.click();

        // 5. Verify transition to Step 2 (Columns + Parameters)
        await expect(page.locator('.ui-upload-headline')).not.toBeVisible();
        await expect(page.getByText('Select Columns')).toBeVisible();
        await expect(page.getByRole('heading', { name: /Parameters/i })).toBeVisible();
    });
});
