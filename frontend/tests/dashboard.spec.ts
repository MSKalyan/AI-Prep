import { test, expect } from '@playwright/test';

test.describe('Dashboard Public Access', () => {
  test('should redirect to login when accessing dashboard without auth', async ({ page }) => {
    await page.goto('/dashboard');
    await expect(page).toHaveURL(/\/login/);
  });

  test('should redirect to login when accessing ai_service without auth', async ({ page }) => {
    await page.goto('/dashboard/ai_service');
    await expect(page).toHaveURL(/\/login/);
  });

  test('should redirect to login when accessing analytics without auth', async ({ page }) => {
    await page.goto('/dashboard/analytics');
    await expect(page).toHaveURL(/\/login/);
  });

  test('should redirect to login when accessing mocktest without auth', async ({ page }) => {
    await page.goto('/dashboard/mocktest');
    await expect(page).toHaveURL(/\/login/);
  });
});

test.describe('AI Service Page (No Auth)', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/dashboard/ai_service');
  });

  test('should redirect unauthenticated users to login', async ({ page }) => {
    await expect(page).toHaveURL(/\/login/);
  });
});

test.describe('Roadmap Page (No Auth)', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/dashboard/roadmap');
  });

  test('should redirect unauthenticated users to login', async ({ page }) => {
    await expect(page).toHaveURL(/\/login/);
  });
});

test.describe('Mocktest Page (No Auth)', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/dashboard/mocktest');
  });

  test('should redirect unauthenticated users to login', async ({ page }) => {
    await expect(page).toHaveURL(/\/login/);
  });
});

test.describe('Analytics Page (No Auth)', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/dashboard/analytics');
  });

  test('should redirect unauthenticated users to login', async ({ page }) => {
    await expect(page).toHaveURL(/\/login/);
  });
});
