import playwright, { chromium, Page } from "playwright-chromium";
import delay from "delay";
import * as actions from "../util/playwright";
import config from "../config";
import path from "path";
import { v4 as uuid } from "uuid";
import { GeneratedClaim } from "../generation/Claim";
import { getDocumentReviewTaskName } from "../util/documents";

export type Tasks =
  | "ID Review"
  | "Certification Review"
  | "Employer Approval Received";

export async function withFineosBrowser<T extends unknown>(
  next: (page: Page) => Promise<T>,
  debug = false,
  screenshots?: string
): Promise<T> {
  const isSSO = config("ENVIRONMENT") === "uat";
  const browser = await chromium.launch({
    headless: !debug,
  });
  const httpCredentials = isSSO
    ? undefined
    : {
        username: config("FINEOS_USERNAME"),
        password: config("FINEOS_PASSWORD"),
      };
  const page = await browser.newPage({
    viewport: { width: 1200, height: 1000 },
    httpCredentials,
  });
  page.on("dialog", async (dialog) => {
    await delay(2000);
    await dialog.dismiss().catch(() => {
      //intentional no-op on error.
    });
  });

  const debugError = async (e: Error) => {
    // If we're in debug mode, pause the page wherever the error was thrown.
    if (debug) {
      console.error(
        "Caught error - holding browser window open for debugging.",
        e
      );
      await page.pause();
    }
    if (screenshots) {
      const filename = path.join(screenshots, `${uuid()}.jpg`);
      await page
        .screenshot({
          fullPage: true,
          path: filename,
        })
        .then(() => console.log(`Saved screenshot of error to ${filename}`))
        .catch((err) =>
          console.error("An error was caught during screenshot capture", err)
        );
    }
    return Promise.reject(e);
  };
  const start = async () => {
    // We have to wait for network idle here because the SAML redirect happens via JS, which is only triggered after
    // the initial load. So we can't determine whether we've been redirect to SSO unless we wait for network activity
    // to stop.
    await page.goto(config("FINEOS_BASEURL"));

    if (isSSO) {
      await page.fill(
        "input[type='email'][name='loginfmt']",
        config("SSO_USERNAME")
      );
      await page.click("input[value='Next']");
      await page.fill(
        "input[type='password'][name='passwd']",
        config("SSO_PASSWORD")
      );
      await page.click("input[value='Sign in']");
      // Sometimes we end up with a "Do you want to stay logged in" question.
      // This seems inconsistent, so we only look for it if we haven't already found ourselves
      // in Fineos.
      if (/login\.microsoftonline\.com/.test(page.url())) {
        await page.click("input[value='No']");
      }
    }
    await page.waitForSelector("body.PageBody");
    return page;
  };

  return start()
    .then(next)
    .catch(debugError)
    .finally(async () => {
      // Note: For whatever reason, we get sporadic crashes when calling browser.close() without page.close().
      // This sporadic crash is characterized by an ERR_IPC_CHANNEL_CLOSED error. We believe the issue is similar
      // to https://github.com/microsoft/playwright/issues/5327.
      await page.close();
      await browser.close();
    });
}

export async function approveClaim(
  page: playwright.Page,
  claim: GeneratedClaim,
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

  // Close all of the documentation review tasks.
  for (const document of claim.documents) {
    await closeTask(page, getDocumentReviewTaskName(document.document_type));
  }
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
  claim: GeneratedClaim,
  fineos_absence_id: string
): Promise<void> {
  await actions.gotoCase(page, fineos_absence_id);
  await page.click('input[type="submit"][value="Adjudicate"]');
  await approveDocuments(page);
  await approveCertificationPeriods(page);
  await page.click("#footerButtonsBar input[value='OK']");
  // Close all of the documentation review tasks.
  for (const document of claim.documents) {
    await closeTask(page, getDocumentReviewTaskName(document.document_type));
  }

  if (claim.employerResponse?.has_amendments) {
    await closeTask(page, "Employer Conflict Reported");
    if (claim.employerResponse.concurrent_leave)
      await addTask(
        page,
        "Escalate employer reported accrued paid leave (PTO)"
      );
    if (claim.employerResponse.previous_leaves.length)
      await addTask(page, "Escalate employer reported past leave");
    if (claim.employerResponse.employer_benefits.length)
      await addTask(page, "Escalate Employer Reported Other Income");
  } else if (claim.employerResponse?.employer_decision === "Approve") {
    await closeTask(page, "Employer Approval Received");
  }
}

export async function closeTask(
  page: playwright.Page,
  task: string
): Promise<void> {
  await actions.clickTab(page, "Tasks");
  await Promise.race([
    page.waitForNavigation(),
    page.click(`td[title="${task}"]`),
  ]);
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
  await Promise.all([
    page.waitForNavigation(),
    actions.clickTab(page, "Manage Request"),
  ]);
  await Promise.all([
    page.waitForNavigation(),
    page.click('input[type="submit"][value="Accept"]'),
  ]);
  await delay(150);
}

export async function addTask(
  page: playwright.Page,
  taskName:
    | "Escalate Employer Reported Other Income"
    | "Escalate employer reported past leave"
    | "Escalate employer reported accrued paid leave (PTO)"
    | "Escalate Employer Reported Fraud"
): Promise<void> {
  await page.click(`input[title="Add a task to this case"][type=submit]`);
  await page.waitForNavigation();
  // Search for the task type
  await actions.labelled(page, `Find Work Types Named`).then(async (el) => {
    await el.type(`${taskName}`);
    await el.press("Enter");
  });
  // Create task
  await page.click(`td[title="${taskName}"]`);
  await page.click("#footerButtonsBar input[value='Next']");
  await page.waitForNavigation();
}
