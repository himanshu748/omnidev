import { test, expect } from "@playwright/test";

test("landing page navigation", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByText("All-in-One AI Developer Platform")).toBeVisible();
  await page.getByRole("link", { name: "DevOps Agent" }).first().click();
  await expect(page).toHaveURL(/\/devops/);
  await expect(page.getByRole("heading", { name: "DevOps Agent" })).toBeVisible();
});
