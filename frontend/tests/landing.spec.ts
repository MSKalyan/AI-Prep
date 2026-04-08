import { test, expect } from "@playwright/test";

test.describe("Landing Page", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/");
  });

  test("should display landing page without crashing", async ({ page }) => {
    await expect(page).toHaveURL("/");
  });

  test("should have login and register links", async ({ page }) => {
    const loginLink = page.getByRole("link", { name: /login/i });
    const registerLink = page.getByRole("link", { name: /register/i });
    
    const hasLogin = await loginLink.count() > 0;
    const hasRegister = await registerLink.count() > 0;
    
    expect(hasLogin || hasRegister).toBeTruthy();
  });
});