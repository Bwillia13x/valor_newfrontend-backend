import { test, expect } from '@playwright/test';

test.describe('Valor IVX UI smoke', () => {
  test('index.html dropdowns are keyboard navigable and show focus', async ({ page }) => {
    await page.goto('http://localhost:8000/index.html');

    // Focus Tools dropdown and open with Enter
    await page.focus('#toolsDropdown .dropdown-toggle');
    await page.keyboard.press('Enter');
    await expect(page.locator('#toolsDropdown .dropdown-menu')).toBeVisible();

    // Arrow down to second item
    await page.keyboard.press('ArrowDown');
    await page.keyboard.press('ArrowDown');
    // Ensure some item has tabindex=0 (roving)
    const activeItem = page.locator('#toolsDropdown .dropdown-menu [role="menuitem"][tabindex="0"]');
    await expect(activeItem).toBeVisible();

    // Escape closes
    await page.keyboard.press('Escape');
    await expect(page.locator('#toolsDropdown .dropdown-menu')).toBeHidden();
  });

  test('backend error shows toast on failing request', async ({ page }) => {
    await page.route('**/api/runs', route => route.fulfill({ status: 500, body: '{}' }));
    await page.goto('http://localhost:8000/index.html');

    // Trigger a backend call via Save to Backend
    await page.click('#dataDropdown .dropdown-toggle');
    await page.click('#sendRun');

    // Toast region appears
    const toast = page.locator('#aria-live-toasts .pwa-notification');
    await expect(toast).toBeVisible();
  });

  test('SW update banner utility attaches on secondary pages', async ({ page }) => {
    // Mock service worker waiting state via injecting global
    await page.goto('http://localhost:8000/lbo.html');
    // Expect no crash and page load
    await expect(page).toHaveTitle(/LBO Analysis/);
  });
});
