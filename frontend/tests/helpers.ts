import { Page, Route } from "@playwright/test";

export async function mockJson(
  page: Page,
  url: string | RegExp,
  body: unknown,
  status = 200
) {
  await page.route(url, async (route: Route) => {
    await route.fulfill({
      status,
      contentType: "application/json",
      body: JSON.stringify(body),
    });
  });
}

export async function mockApiError(
  page: Page,
  url: string | RegExp,
  status = 500,
  detail = "Server error"
) {
  await page.route(url, async (route: Route) => {
    await route.fulfill({
      status,
      contentType: "application/json",
      body: JSON.stringify({ detail }),
    });
  });
}
