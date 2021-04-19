import playwright, { chromium, Page } from "playwright-chromium";
import delay from "delay";
import * as actions from "../util/playwright";

export type Tasks =
  | "ID Review"
  | "Certification Review"
  | "Employer Approval Received";

export async function withFineosBrowser(
  baseUrl: string,
  next: (page: Page) => Promise<void>,
  debug = false
): Promise<void> {
  const browser = await chromium.launch({
    headless: !debug,
  });
  const page = await browser.newPage({
    viewport: { width: 1200, height: 1000 },
  });
  await page.goto(baseUrl);
  page.on("dialog", async (dialog) => {
    await delay(2000);
    await dialog.dismiss().catch(() => {
      //intentional no-op on error.
    });
  });

  try {
    await next(page).catch(async (e) => {
      // When in debug mode, hold the browser window open for 100 seconds for debugging purposes.
      if (debug) {
        console.log(
          "Caught error - holding browser window open for debugging.",
          e
        );
        await delay(100000);
      }
      throw e;
    });
  } finally {
    await browser.close();
  }
}

export async function approveClaim(
  page: playwright.Page,
  fineos_absence_id: string
): Promise<void> {
  await actions.gotoCase(page, fineos_absence_id);
  // Start Adjudication.
  await page.click('input[type="submit"][value="Adjudicate"]');
  await approveDocuments(page);
  await approveCertificationPeriods(page);
  await approvePlanEligibility(page);
  // Complete Adjudication.
  await Promise.all([
    page.waitForNavigation(),
    page.click("#footerButtonsBar input[value='OK']"),
  ]);

  await closeTask(page, "ID Review");
  await closeTask(page, "Certification Review");
  await closeTask(page, "Employer Approval Received");
  await actions.clickTab(page, "Absence Hub");

  // Approve the claim.
  await Promise.all([
    page.waitForNavigation(),
    page.click("a[title='Approve the Pending Leaving Request']"),
  ]);
  await delay(150);
  await expectClaimState(page, "Approved");
}

export async function denyClaim(
  page: playwright.Page,
  fineos_absence_id: string
): Promise<void> {
  await actions.gotoCase(page, fineos_absence_id);
  await page.click('input[type="submit"][value="Adjudicate"]');
  await page.click('input[type="submit"][value="Reject"]');
  await page.click("#footerButtonsBar input[value='OK']");
  await page.click("div[title='Deny the Pending Leave Request']");
  await actions
    .labelled(page, "Denial Reason")
    .then((el) => el.selectOption("5"));
  await Promise.all([
    page.waitForNavigation(),
    page.click('input[type="submit"][value="OK"]'),
  ]);
  await expectClaimState(page, "Declined");
}

async function expectClaimState(page: playwright.Page, expected: string) {
  const status = await page
    .waitForSelector(".key-info-bar .status dd")
    .then((e) => e.innerText());
  if (status !== expected) {
    throw new Error(`Expected status to be ${expected}, but it was ${status}`);
  }
}

export async function closeDocuments(
  page: playwright.Page,
  fineos_absence_id: string
): Promise<void> {
  await actions.gotoCase(page, fineos_absence_id);
  await page.click('input[type="submit"][value="Adjudicate"]');
  await approveDocuments(page);
  await page.click("#footerButtonsBar input[value='OK']");
  await closeTask(page, "ID Review");
  await closeTask(page, "Certification Review");
}

export async function closeTask(
  page: playwright.Page,
  task: Tasks
): Promise<void> {
  await actions.clickTab(page, "Tasks");
  await Promise.race([
    page.waitForNavigation(),
    page.click(`td[title="${task}"]`),
  ]);
  // await actions.click(page, await page.waitForSelector(`td[title="${task}"]`));
  await actions.waitForStablePage(page);
  await page.waitForTimeout(150);
  await Promise.race([
    page.waitForNavigation(),
    page.click('input[type="submit"][value="Close"]'),
  ]);
  await delay(150);
}

async function approveDocuments(page: playwright.Page): Promise<void> {
  await actions.clickTab(page, "Evidence");
  while (true) {
    try {
      await page.click('td[title="Pending"]', { timeout: 1000 });
    } catch (e) {
      // Exit now if we weren't able to find any documents.
      if (e.name === "TimeoutError") {
        break;
      }
      throw e;
    }
    await page.click('input[value="Manage Evidence"]');
    await page.waitForSelector(".WidgetPanel_PopupWidget");
    await actions
      .labelled(page, "Evidence Decision")
      .then((el) => el.selectOption("0"));
    await page.click('.WidgetPanel_PopupWidget input[value="OK"]');
    await page
      .waitForSelector("#disablingLayer")
      .then((el) => el.waitForElementState("hidden"));
  }
  await delay(150);
}

async function approveCertificationPeriods(
  page: playwright.Page
): Promise<void> {
  await actions.clickTab(page, "Certification Periods");
  await page.click('input[value="Prefill with Requested Absence Periods"]');
  await Promise.all([
    page.waitForNavigation(),
    page.click('#PopupContainer input[value="Yes"]'),
  ]);
  await delay(150);
}

async function approvePlanEligibility(page: playwright.Page): Promise<void> {
  await actions.clickTab(page, "Manage Request");
  await Promise.all([
    page.waitForNavigation(),
    page.click('input[value="Accept"]'),
  ]);
  await delay(150);
}
