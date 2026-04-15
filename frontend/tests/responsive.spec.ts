import { test, expect } from '@playwright/test';

test.describe('Responsive Design', () => {
  const viewports = [
    { name: 'mobile', width: 375, height: 667 },
    { name: 'tablet', width: 768, height: 1024 },
    { name: 'desktop', width: 1280, height: 720 },
  ];

  for (const viewport of viewports) {
    test(`${viewport.name} - login page should be usable`, async ({ page }) => {
      await page.setViewportSize({ width: viewport.width, height: viewport.height });
      await page.goto('/login');

      await expect(page.getByRole('heading', { name: 'Login' })).toBeVisible();
      await expect(page.getByLabel('Email')).toBeVisible();
      await expect(page.getByLabel('Password')).toBeVisible();
      await expect(page.getByRole('button', { name: 'Login' })).toBeVisible();
    });

    test(`${viewport.name} - register page should be usable`, async ({ page }) => {
      await page.setViewportSize({ width: viewport.width, height: viewport.height });
      await page.goto('/register');

      await expect(page.getByRole('heading', { name: 'Create Account' })).toBeVisible();
      await expect(page.getByLabel('Full Name')).toBeVisible();
      await expect(page.getByLabel('Username')).toBeVisible();
      await expect(page.getByLabel('Email')).toBeVisible();
      await expect(page.getByLabel('Password', { exact: true })).toBeVisible();
      await expect(page.getByLabel('Confirm Password')).toBeVisible();
      await expect(page.getByRole('button', { name: 'Register' })).toBeVisible();
    });
  }
});
