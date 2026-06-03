import { test, expect } from "@playwright/test";
import { mockApiError, mockJson } from "./helpers";

test("scraper happy path", async ({ page }) => {
  await mockJson(page, "**/api/scraper/scrape", {
    url: "https://example.com",
    title: "Example Domain",
    status_code: 200,
    content: "Example content",
    screenshot_b64: null,
    pdf_b64: null,
    links: null,
    metadata: null,
  });
  await page.goto("/scraper");
  await page.fill("#scraper-url", "https://example.com");
  await page.getByRole("button", { name: "🕷️ Start Scraping →" }).click();
  await expect(page.locator(".scraperTitle", { hasText: "Example Domain" })).toBeVisible();
  await expect(page.getByText("HTTP 200")).toBeVisible();
});

test("scraper error path", async ({ page }) => {
  await mockApiError(page, "**/api/scraper/scrape", 500, "Scrape failed");
  await page.goto("/scraper");
  await page.fill("#scraper-url", "https://example.com");
  await page.getByRole("button", { name: "🕷️ Start Scraping →" }).click();
  await expect(page.getByText("⚠ Error:")).toBeVisible();
  await expect(page.getByText("Scrape failed")).toBeVisible();
});
