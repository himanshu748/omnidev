import { test, expect, Route } from "@playwright/test";
import { mockJson } from "./helpers";

test("storage list and download flow", async ({ page }) => {
  await mockJson(page, "**/api/storage/buckets", {
    buckets: [{ name: "demo-bucket", creation_date: "2025-01-01T00:00:00Z" }],
  });
  await page.route("**/api/storage/files**", async (route: Route) => {
    if (route.request().method() === "GET") {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          bucket: "demo-bucket",
          prefix: "",
          files: [
            { key: "report.pdf", size: 1024, last_modified: "2025-01-01T00:00:00Z", storage_class: "STANDARD" },
          ],
        }),
      });
      return;
    }
    await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({}) });
  });
  await mockJson(page, "**/api/storage/download**", {
    bucket: "demo-bucket",
    key: "report.pdf",
    presigned_url: "https://example.com/report.pdf",
    expires_in: 3600,
  });
  await page.goto("/storage");
  await expect(page.getByRole("combobox").first()).toHaveValue("demo-bucket");
  await expect(page.getByText("report.pdf")).toBeVisible();
  await page.getByRole("button", { name: "🔗 Link" }).click();
  await expect(page.getByRole("link", { name: "⬇ Open" })).toBeVisible();
});
