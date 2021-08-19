import playwright from "playwright-chromium";
import delay from "delay";

/**********
 * These are common actions for using Playwright.
 ***********/

export async function click(
  page: playwright.Page,
  element: playwright.ElementHandle | null
): Promise<void> {
  if (!element) {
    throw new Error(`No element given`);
  }
  await Promise.all([element.click(), page.waitForNavigation()]);
}

export async function labelled(
  page: playwright.Page,
  label: string
): Promise<playwright.ElementHandle> {
  const $label = await page.waitForSelector(`label:text("${label}")`);
  const id = await $label.evaluate((el) => el.getAttribute("for"));
  const input = await page.$(
    `input[name="${id}"],select[name="${id}"],textarea[name="${id}"]`
  );
  if (input !== null) {
    return input;
  }
  throw new Error(`Unable to find input labelled by: ${label}`);
}

export async function contains(
  page: playwright.Page,
  selector: string,
  text: string
): Promise<playwright.ElementHandle> {
  const candidates = await page.$$(selector);
  const checked = [];
  for (const candidate of candidates) {
    const candidateText = await candidate.innerText();
    if (text === candidateText) {
      return candidate;
    }
    checked.push(candidateText);
  }
  throw new Error(
    `Unable to find element with selector: ${selector} and text: ${text}. Found: ${checked.join(
      ", "
    )}`
  );
}

export async function clickTab(
  page: playwright.Page,
  label: string
): Promise<void> {
  await page.click(
    `:is(.TabStrip td.TabOn :text("${label}"), .TabStrip td.TabOff :text("${label}"))`
  );
  await waitForStablePage(page);
  await delay(200);
}

export async function waitForStablePage(page: playwright.Page): Promise<void> {
  // Waits for all known Fineos ajax stuff to complete.
  await Promise.all([
    page.waitForFunction(() => {
      // @ts-ignore - Ignore use of Fineos window properties.
      const requests = window.axGetAjaxQueueManager
        ? // @ts-ignore - Ignore use of Fineos window properties.
          Object.values(window.axGetAjaxQueueManager().requests)
        : [];
      // @ts-ignore - Ignore use of Fineos window properties.
      return requests.filter((r) => r.state === "resolved").length === 0;
    }),
    // @ts-ignore - Ignore use of Fineos window properties.
    page.waitForFunction(() => window.submitted_99 === 0),
    // @ts-ignore - Ignore use of Fineos window properties.
    page.waitForFunction(() => !window.wl_mainButtons_processing),
  ]);
}

export async function gotoCase(
  page: playwright.Page,
  id: string
): Promise<void> {
  await page.click('.menulink a.Link[aria-label="Cases"]');
  await clickTab(page, "Case");
  await labelled(page, "Case Number").then((el) => el.type(id));
  // Uncheck "Search Case Alias".
  await labelled(page, "Search Case Alias").then((el) => el.click());
  await page.click('input[type="submit"][value="Search"]');
  const title = await page
    .waitForSelector(".case_pageheader_title")
    .then((el) => el.innerText());
  if (!(typeof title === "string") || !title.match(id)) {
    throw new Error("Page title should include case ID");
  }
}
