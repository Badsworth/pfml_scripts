import delay from "delay";
import path from "path";
import { Page, chromium } from "playwright-chromium";
import config from "../config";
import { v4 as uuid } from "uuid";
import * as util from "../util/playwright";
import { ClaimStatus, FineosTasks } from "../types";

export class Fineos {
  static async withBrowser<T extends unknown>(
    next: (page: Page) => Promise<T>,
    debug = false,
    screenshots?: string
  ): Promise<T> {
    const isSSO = config("ENVIRONMENT") === "uat";
    const browser = await chromium.launch({
      headless: !debug,
      slowMo: debug ? 100 : undefined,
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
}

/**
 * Base class which makes sure the page object is internally accesible without defining an explicit dependency.
 * So far it seems like there's no reason to specify it here, as page object will be accessible from Fineos.withBrowser scope anyway.
 */
abstract class FineosPage {
  protected readonly page: Page;
  constructor(page: Page) {
    this.page = page;
  }
  protected async onTab(...path: string[]): Promise<void> {
    for (const part of path) {
      await util.clickTab(this.page, part);
      // await this.page.waitForNavigation();
      // await Promise.all([
      //   this.page.waitForNavigation(),
      //   util.clickTab(this.page, part),
      // ]);
      await delay(150);
    }
  }
}

type FineosPageCallback<T extends FineosPage> = (
  fineosPage: T
) => Promise<void>;

export class Claim extends FineosPage {
  constructor(page: Page) {
    super(page);
  }
  static async visit(page: Page, id: string): Promise<Claim> {
    await util.gotoCase(page, id);
    return new Claim(page);
  }
  async tasks(cb: FineosPageCallback<Tasks>): Promise<void> {
    await this.onTab(`Tasks`);
    await cb(new Tasks(this.page));
    await this.onTab(`Absence Hub`);
  }
  async adjudicate(cb: FineosPageCallback<Adjudication>): Promise<void> {
    await this.page.click('input[type="submit"][value="Adjudicate"]');
    await cb(new Adjudication(this.page));
    await Promise.all([
      this.page.waitForNavigation(),
      this.page.click("#footerButtonsBar input[value='OK']"),
    ]);
  }

  async approve(): Promise<void> {
    await Promise.all([
      this.page.waitForNavigation(),
      this.page.click("a[title='Approve the Pending Leaving Request']"),
    ]);
    await this.assertClaimStatus("Approved");
  }

  async assertClaimStatus(expected: ClaimStatus): Promise<void> {
    const status = await this.page
      .waitForSelector(`.key-info-bar .status dd`)
      .then(async (el) => el.innerText());
    if (status !== expected)
      throw new Error(
        `Expected status to be ${expected}, but it was ${status}`
      );
  }

  async deny(): Promise<void> {
    await this.page.click("div[title='Deny the Pending Leave Request']");
    await util
      .labelled(this.page, "Denial Reason")
      .then((el) => el.selectOption("5"));
    await Promise.all([
      this.page.waitForNavigation(),
      this.page.click('input[type="submit"][value="OK"]'),
    ]);
    await this.assertClaimStatus("Completed");
  }
}

class Adjudication extends FineosPage {
  constructor(page: Page) {
    super(page);
  }
  async evidence(cb: FineosPageCallback<Evidence>): Promise<void> {
    await this.onTab("Evidence");
    await cb(new Evidence(this.page));
  }
  async certificationPeriods(
    cb: FineosPageCallback<CertificationPeriods>
  ): Promise<void> {
    await this.onTab("Evidence", "Certification Periods");
    await cb(new CertificationPeriods(this.page));
  }

  async denyLeavePlan(): Promise<void> {
    await this.onTab(`Manage Request`);
    await Promise.all([
      this.page.waitForNavigation(),
      this.page.click('input[type="submit"][value="Reject"]'),
    ]);
    await delay(150);
  }

  async acceptLeavePlan(): Promise<void> {
    await this.onTab(`Manage Request`);
    await Promise.all([
      this.page.waitForNavigation(),
      this.page.click('input[type="submit"][value="Accept"]'),
    ]);
    await delay(150);
  }
}

export class CertificationPeriods extends FineosPage {
  constructor(page: Page) {
    super(page);
  }
  async prefill(): Promise<void> {
    await this.page.click(
      'input[value="Prefill with Requested Absence Periods"]'
    );
    await Promise.all([
      this.page.waitForNavigation(),
      this.page.click('#PopupContainer input[value="Yes"]'),
    ]);
    await delay(150);
  }
}

export class Evidence extends FineosPage {
  constructor(page: Page) {
    super(page);
  }
  async receive(
    evidenceType: string,
    receipt: "Pending" | "Received" | "Not Received" = "Received",
    decision:
      | "Pending"
      | "Satisfied"
      | "Not Satisfied"
      | "Waived" = "Satisfied",
    reason = "Evidence has been reviewed and approved"
  ): Promise<void> {
    await this.page.click(`td[title="${evidenceType}"]`, { timeout: 1000 });
    await this.page.click('input[value="Manage Evidence"]');
    await this.page.waitForSelector(".WidgetPanel_PopupWidget");
    await util
      .labelled(this.page, "Evidence Receipt")
      .then((el) => el.selectOption({ label: receipt }));
    await util
      .labelled(this.page, "Evidence Decision")
      .then((el) => el.selectOption({ label: decision }));
    await util
      .labelled(this.page, "Evidence Decision Reason")
      .then((el) => el.fill(""));
    await util
      .labelled(this.page, "Evidence Decision Reason")
      .then((el) => el.fill(reason));
    await this.page.click('.WidgetPanel_PopupWidget input[value="OK"]');
    await this.page.waitForSelector(".WidgetPanel_PopupWidget", {
      state: "hidden",
    });
    await this.page
      .waitForSelector("#disablingLayer")
      .then((el) => el.waitForElementState("hidden"));
    await delay(150);
  }
}

export class Tasks extends FineosPage {
  constructor(page: Page) {
    super(page);
  }
  async close(task: FineosTasks): Promise<void> {
    await util.clickTab(this.page, "Tasks");
    await Promise.race([
      this.page.waitForNavigation(),
      this.page.click(`td[title="${task}"]`),
    ]);
    await Promise.race([
      this.page.waitForNavigation(),
      this.page.click('input[type="submit"][value="Close"]'),
    ]);
    await delay(150);
  }

  async open(task: FineosTasks): Promise<void> {
    await util.clickTab(this.page, "Tasks");
    await Promise.race([
      this.page.waitForNavigation(),
      this.page.click(`input[title="Add a task to this case"][type=submit]`),
    ]);
    await util.labelled(this.page, "Find Work Types Named").then(async (el) => {
      await el.type(`${task}`);
      await el.press("Enter");
    });
    await Promise.race([
      this.page.waitForNavigation(),
      this.page.click('td[title="${taskName}"]'),
    ]);
    await Promise.race([
      this.page.waitForNavigation(),
      this.page.click("#footerButtonsBar input[value='Next']"),
    ]);
  }
}
