import { test, expect } from "@playwright/test";

test("landing page navigation", async ({ page }) => {
  await page.goto("/");
  await expect(
    page.getByRole("heading", { name: /Your AI dev cockpit/ }),
  ).toBeVisible();
  await expect(page.getByRole("link", { name: "Download for macOS" }).first()).toBeVisible();
  await expect(page.getByText("Fully offline with Gemma 4.")).toBeVisible();
  await page.getByRole("link", { name: /DevOps Agent/ }).first().click();
  await expect(page).toHaveURL(/\/devops/);
  await expect(page.getByRole("heading", { name: "DevOps Agent", exact: true })).toBeVisible();
});
