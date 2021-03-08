import puppeteer from "puppeteer";
import delay from "delay";
import * as actions from "../utils";

export async function withFineosBrowser(
  baseUrl: string,
  next: (page: puppeteer.Page) => Promise<void>
): Promise<void> {
  const browser = await puppeteer.launch({
    defaultViewport: { width: 1200, height: 1000 },
    headless: true,
  });
  const page = await browser.newPage();
  await page.goto(baseUrl);
  page.on("dialog", async (dialog) => {
    // When a dialog is detected, attempt to close it. This is usually
    // a "request in progress" thing, and closing it will allow the rest
    // of the claim to proceed.
    await delay(2000);
    await dialog.dismiss().catch(() => {
      //intentional no-op on error.
    });
  });
  try {
    await next(page);
  } finally {
    await browser.close();
  }
}

export async function approveClaim(
  page: puppeteer.Page,
  fineos_absence_id: string
): Promise<void> {
  await actions.gotoCase(page, fineos_absence_id);
  // Start Adjudication.
  await actions.click(
    page,
    await page.waitForSelector('input[type="submit"][value="Adjudicate"]', {
      visible: true,
    })
  );
  await approveDocuments(page);
  await approveCertificationPeriods(page);
  // Complete Adjudication.
  await actions.click(
    page,
    await page.waitForSelector("#footerButtonsBar input[value='OK']")
  );
  // Approve the claim.
  await actions.click(
    page,
    await page.waitForSelector("a[title='Approve the Pending Leaving Request']")
  );
}

async function approveDocuments(page: puppeteer.Page): Promise<void> {
  await actions.clickTab(page, "Evidence");
  while (true) {
    let pendingDocument;
    try {
      pendingDocument = await page.waitForSelector('td[title="Pending"]', {
        timeout: 1000,
      });
    } catch (e) {
      // Break out if there are no pending documents left.
      break;
    }
    await pendingDocument.click();
    await page
      .waitForSelector("input[value='Manage Evidence']")
      .then((el) => el.click());
    await page.waitForSelector(".WidgetPanel_PopupWidget");
    await actions
      .labelled(page, "Evidence Decision")
      .then((el) => el.select("0"));
    await page
      .waitForSelector('.WidgetPanel_PopupWidget input[value="OK"]')
      .then((el) => el.click());
    await page.waitForSelector("#disablingLayer", { hidden: true });
  }
}

async function approveCertificationPeriods(
  page: puppeteer.Page
): Promise<void> {
  await actions.clickTab(page, "Certification Periods");
  await page
    .waitForSelector('input[value="Prefill with Requested Absence Periods"]')
    .then((el) => el.click());
  await actions.click(
    page,
    await page.waitForSelector("#PopupContainer input[value='Yes']")
  );
}
