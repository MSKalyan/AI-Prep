import { test, expect } from "@playwright/test";

test.describe("Navigation", () => {
  test("should have working navbar links", async ({ page }) => {
    await page.goto("/");
    
    const loginLink = page.getByRole("link", { name: "Login" });
    if (await loginLink.isVisible()) {
      await loginLink.click();
      await expect(page).toHaveURL("/login");
    }
  });

  test("should redirect to login when accessing protected route", async ({ page }) => {
    await page.goto("/dashboard");
    await expect(page).toHaveURL(/\/login/);
  });
});