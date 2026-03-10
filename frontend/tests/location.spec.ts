import { test, expect } from "@playwright/test";
import { mockJson } from "./helpers";

test("location detect flow", async ({ page }) => {
  await mockJson(page, "**/api/location/me", {
    ip: "1.1.1.1",
    city: "Test City",
    region: "CA",
    country: "US",
    latitude: 37.7,
    longitude: -122.4,
  });
  await page.goto("/location");
  await page.getByRole("button", { name: "📡 Detect Location" }).click();
  await expect(page.getByText("1.1.1.1")).toBeVisible();
  await expect(page.getByText("Test City")).toBeVisible();
});

test("location geocode flow", async ({ page }) => {
  await mockJson(page, "**/api/location/geocode**", {
    results: [
      {
        display_name: "Eiffel Tower, Paris",
        latitude: 48.8584,
        longitude: 2.2945,
        type: "landmark",
        address: { city: "Paris" },
      },
    ],
  });
  await page.goto("/location");
  await page.getByRole("button", { name: "🔍 Search Address" }).click();
  await page.fill("#loc-addr", "Eiffel Tower");
  await page.getByRole("button", { name: "🔍 Search" }).click();
  await expect(page.getByText("Eiffel Tower, Paris")).toBeVisible();
});
