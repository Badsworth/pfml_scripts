import { LeavePeriods } from "./types";
import { parseISO } from "date-fns";
import puppeteer from "puppeteer";
import { SimulationClaim } from "./simulation/types";
import delay from "delay";

export function extractLeavePeriod(
  claim: SimulationClaim["claim"],
  leaveType: keyof LeavePeriods = "continuous_leave_periods"
): [Date, Date] {
  const period = claim.leave_details?.[leaveType]?.[0];
  if (!period || !period.start_date || !period.end_date) {
    throw new Error("No leave period given");
  }
  return [parseISO(period.start_date), parseISO(period.end_date)];
}

/**********
 * These are common actions for using puppetter
 ***********/

export async function click(
  page: puppeteer.Page,
  element: puppeteer.ElementHandle | null
): Promise<void> {
  if (!element) {
    throw new Error(`No element given`);
  }
  await Promise.all([element.click(), page.waitForNavigation()]);
}

export async function labelled(
  page: puppeteer.Page,
  label: string
): Promise<puppeteer.ElementHandle> {
  const $label = await contains(page, "label", label);
  const id = await $label.evaluate((el) => el.getAttribute("for"));
  const input = await page.$(`input[name="${id}"],select[name="${id}"]`);
  if (input !== null) {
    return input;
  }
  throw new Error(`Unable to find input labelled by: ${label}`);
}

export async function contains(
  page: puppeteer.Page,
  selector: string,
  text: string
): Promise<puppeteer.ElementHandle> {
  const candidates = await page.$$(selector);
  const checked = [];
  for (const candidate of candidates) {
    const candidateText = await candidate
      .getProperty("innerText")
      .then((val) => val.jsonValue());
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
  page: puppeteer.Page,
  label: string
): Promise<void> {
  await page.waitForSelector("td.TabOn");
  const tab = await contains(
    page,
    ".TabStrip td.TabOn, .TabStrip td.TabOff",
    label
  );
  // Remove the TabOn class before we start so we can detect when it has been re-added.
  await tab.evaluate((tab) => {
    tab.classList.remove("TabOn");
  });

  await tab.click();
  await Promise.all([
    // Wait for the page to stabilize.
    waitForStablePage(page),
    // Wait for the tab to have the `TabOn` class added as well.
    page.waitForFunction(
      (label) => {
        const tabs = document.querySelectorAll(".TabStrip td.TabOn");
        return (
          Array.prototype.slice
            .call(tabs)
            .filter((tab) => tab.innerHTML.match(label)).length > 0
        );
      },
      undefined,
      [label]
    ),
  ]);
  await delay(200);
}

async function waitForStablePage(page: puppeteer.Page) {
  // Waits for all known Fineos ajax stuff to complete.
  return Promise.all([
    page.waitForFunction(() => {
      // @ts-ignore - Ignore use of Fineos window properties.
      const requests = Object.values(window.axGetAjaxQueueManager().requests);
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
  page: puppeteer.Page,
  id: string
): Promise<void> {
  await page
    .$(`.menulink a.Link[aria-label="Cases"]`)
    .then((el) => click(page, el));
  await clickTab(page, "Case");
  await labelled(page, "Case Number").then((el) => el.type(id));
  // Uncheck "Search Case Alias".
  await labelled(page, "Search Case Alias").then((el) => el.click());
  await page
    .$('input[type="submit"][value="Search"]')
    .then((el) => click(page, el));
  const title = await page
    .$(".case_pageheader_title")
    .then((el) => el?.getProperty("innerText").then((val) => val.jsonValue()));
  if (!(typeof title === "string") || !title.match(id)) {
    throw new Error("Page title should include case ID");
  }
}

export async function withdrawClaim(page: puppeteer.Page): Promise<void> {
  await page.$('a[aria-label="Withdraw"]').then((el) => click(page, el));
  await page.select("select", "3");
  await page
    .$('input[type="submit"][value="OK"]')
    .then((el) => click(page, el));
}
