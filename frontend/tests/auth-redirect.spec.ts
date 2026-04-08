import { test, expect } from "@playwright/test";

test.describe("Dashboard Page (Unauthenticated)", () => {
  test("should redirect unauthenticated user to login", async ({ page }) => {
    await page.goto("/dashboard");
    await expect(page).toHaveURL(/\/login/);
  });
});

// Note: These pages don't have auth guards implemented yet
// They currently remain on the same URL for unauthenticated users