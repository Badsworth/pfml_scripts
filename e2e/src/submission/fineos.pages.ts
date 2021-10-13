import delay from "delay";
import path from "path";
import { Page, chromium } from "playwright-chromium";
import config from "../config";
import { v4 as uuid } from "uuid";
import * as util from "../util/playwright";
import { ClaimStatus, Credentials, FineosTasks } from "../types";

export type FineosBrowserOptions = {
  debug: boolean;
  screenshots?: string;
  credentials?: Credentials;
};
export class Fineos {
  static async withBrowser<T extends unknown>(
    next: (page: Page) => Promise<T>,
    { debug = false, screenshots, credentials }: FineosBrowserOptions
  ): Promise<T> {
    const isSSO = config("ENVIRONMENT") === "uat";
    const browser = await chromium.launch({
      headless: !debug,
      slowMo: debug ? 100 : undefined,
      executablePath: process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH,
    });
    const httpCredentials = isSSO
      ? undefined
      : credentials ?? {
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
        const ssoCredentials = credentials ?? {
          username: config("SSO_USERNAME"),
          password: config("SSO_PASSWORD"),
        };
        await page.fill(
          "input[type='email'][name='loginfmt']",
          ssoCredentials.username
        );
        await page.click("input[value='Next']");
        await page.fill(
          "input[type='password'][name='passwd']",
          ssoCredentials.password
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
  constructor(protected readonly page: Page) {
    this.page = page;
  }
  protected async onTab(...path: string[]): Promise<void> {
    for (const part of path) {
      await util.clickTab(this.page, part);
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
    await this.page.click("#footerButtonsBar input[value='OK']");
  }

  async approve(): Promise<void> {
    await this.page.click("a[title='Approve the Pending Leaving Request']", {
      // This sometimes takes a while. Wait for it to complete.
      timeout: 60000,
    });
    await this.assertClaimStatus("Approved");
  }

  async assertClaimStatus(expected: ClaimStatus): Promise<void> {
    const status = await this.page.textContent(".key-info-bar .status dd");
    if (status !== expected)
      throw new Error(
        `Expected status to be ${expected}, but it was ${status}`
      );
  }

  async deny(): Promise<void> {
    await this.page.click("div[title='Deny the Pending Leave Request']");
    await this.page.selectOption("label:text-is('Denial Reason')", "5");
    await this.page.click('input[type="submit"][value="OK"]', {
      // This sometimes takes a while. Wait for it to complete.
      timeout: 60000,
    });
    await this.assertClaimStatus("Declined");
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
    await this.page.click('input[type="submit"][value="Reject"]');
    await delay(150);
  }

  async acceptLeavePlan(): Promise<void> {
    await this.onTab(`Manage Request`);
    await this.page.click('input[type="submit"][value="Accept"]');
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
    await this.page.click('#PopupContainer input[value="Yes"]');
    await delay(150);
  }
}

export class Evidence extends FineosPage {
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
    const row = `table[id*='evidenceResultListviewWidget'] tr:has-text('${evidenceType}')`;
    await util.selectListTableRow(this.page, row);
    await this.page.click('input[value="Manage Evidence"]');
    await this.page.waitForSelector(".WidgetPanel_PopupWidget");
    await this.page.selectOption('label:text-is("Evidence Receipt")', {
      label: receipt,
    });
    await this.page.selectOption('label:text-is("Evidence Decision")', {
      label: decision,
    });
    await this.page.fill('label:text-is("Evidence Decision Reason")', reason);
    await this.page.click('.WidgetPanel_PopupWidget input[value="OK"]');
    // Wait for the row to update before moving on.
    await this.page.waitForSelector(
      `${row} :nth-child(3):has-text('${receipt}')`
    );
    await this.page.waitForSelector(
      `${row} :nth-child(5):has-text('${decision}')`
    );
  }
}

export class Tasks extends FineosPage {
  constructor(page: Page) {
    super(page);
  }
  async close(task: FineosTasks): Promise<void> {
    await util.clickTab(this.page, "Tasks");
    await util.selectListTableRow(
      this.page,
      `table[id*='TasksForCaseWidget'] tr:has-text('${task}')`
    );
    await this.page.click('input[type="submit"][value="Close"]');
  }
  async open(task: FineosTasks): Promise<void> {
    await Promise.race([
      this.page.waitForNavigation(),
      this.page.click(`input[title="Add a task to this case"][type=submit]`),
    ]);
    await util.labelled(this.page, "Find Work Types Named").then(async (el) => {
      await el.fill(task);
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

type RolesSpec = {
  role: FineosRoles | FineosSecurityGroups;
  supervisorOf: boolean;
  memberOf: boolean;
}[];
export class ConfigPage extends FineosPage {
  constructor(page: Page) {
    super(page);
  }
  static async visit(page: Page): Promise<ConfigPage> {
    await page.click(`a[aria-label='Configuration Studio']`);
    return new ConfigPage(page);
  }
  async setRoles(userId: string, roles: RolesSpec): Promise<void> {
    await this.roles(userId, async (rolePage) => {
      // Can't make this work without the wait.
      // Role selection doesn't work straigh away, and there's no UI indication of when it turns on.
      await this.page.waitForTimeout(2000);
      await rolePage.clearRoles();
      for (const { role, memberOf, supervisorOf } of roles)
        await rolePage.setRole(role, memberOf, supervisorOf);
      // This is a good place to pause if you want to make sure you are assigning the roles correctly.
      // await this.page.pause();
      await rolePage.applyRolesToUser();
    });
  }
  async roles(
    userId: string,
    cb: (page: RolesPage) => Promise<void>
  ): Promise<void> {
    await this.page.click(`text="Company Structure"`);
    await util.clickTab(this.page, "Users");
    await this.page.fill("#UserSearchWidgetOrganizationStructure_un18_userID", userId);
    await this.page.click(`input[title="Search for User"]`);
    await this.page.click(`input[title="Select to edit the user"]`);
    // Lookup the user ID, then navigate to the edit roles page.
    await cb(new RolesPage(this.page));
  }
}

export type FineosRoles =
  | "DFML Program Integrity"
  | "DFML Appeals"
  | "SaviLinx"
  | "Post-Prod Admin(sec)"
  | "DFML IT";
export type FineosSecurityGroups =
  | "DFML Claims Examiners(sec)"
  | "DFML Claims Supervisors(sec)"
  | "DFML Compliance Analyst(sec)"
  | "DFML Compliance Supervisors(sec)"
  | "DFML Appeals Administrator(sec)"
  | "DFML Appeals Examiner I(sec)"
  | "DFML Appeals Examiner II(sec)"
  | "SaviLinx Agents (sec)"
  | "SaviLinx Secured Agents(sec)"
  | "SaviLinx Supervisors(sec)"
  | "DFML IT(sec)"
  | "Post-Prod Admin(sec)";
export class RolesPage extends FineosPage {
  constructor(page: Page) {
    super(page);
  }
  async setRole(
    name: FineosSecurityGroups | FineosRoles,
    member: boolean,
    supervisor: boolean
  ): Promise<void> {
    await this.page.click(
      `a[id^="LinkDepartmentToUserWidget_"][id$="_AvailableDepartments-Name-filter"]`
    );

    await this.page
      .waitForSelector(
        `input[id^="LinkDepartmentToUserWidget"][id$="_AvailableDepartments_Name_textFilter"]`
      )
      .then((filterInput) => filterInput.fill(name));
    await this.page.click(
      `input[id^="LinkDepartmentToUserWidget"][id$="_AvailableDepartments_cmdFilter"]`
    );
    await this.page.click(
      `table[id$="_AvailableDepartments"] tr:has-text("${name}")`
    );

    const setCheckboxState = async (
      selector: string,
      checked: boolean
    ): Promise<void> => {
      await this.page.waitForSelector(selector).then((checkbox) =>
        checkbox.isChecked().then((isChecked) =>
          // If current checkbox state is different from desired - click on it.
          // Have to use this because checkbox selection doesn't reset when linking/unlinking roles
          isChecked === checked ? null : checkbox.click()
        )
      );
    };
    await setCheckboxState(
      `input[type="checkbox"][id^="LinkDepartmentToUserWidget"][id$="_userToDeptMemberCheckbox_CHECKBOX"]`,
      member
    );
    await setCheckboxState(
      `input[type="checkbox"][id^="LinkDepartmentToUserWidget"][id$="_userToDeptSupervisorCheckbox_CHECKBOX"]`,
      supervisor
    );
    await this.page.click(`input[title="Link Department to User"]`);
  }
  async clearRoles(): Promise<void> {
    const checkboxSelector = `input[type="checkbox"][id^="LinkDepartmentToUserWidget"][id$="_LinkedDepartments_MasterMultiSelectCB_CHECKBOX"]`;
    await this.page.click(checkboxSelector);
    await this.page.waitForSelector(
      `table[id^="LinkDepartmentToUserWidget"][id$="_LinkedDepartments"] tr.ListRowSelected`
    );
    const activeRoles = await this.page.$$(
      `table[id^="LinkDepartmentToUserWidget"][id$="_LinkedDepartments"] tr`
    );
    for (const tr of activeRoles) {
      const rowText = await tr.textContent();
      // Don't unlink the Post-prod role by request from @mrossi113
      if (rowText?.includes("Post-Prod Admin(sec)")) {
        tr.$(`input[type="checkbox"]`).then((chbox) => chbox?.click());
      }
    }
    await this.page.click(`input[title="Unlink Department from User"]`);
  }
  async applyRolesToUser(): Promise<void> {
    await this.page.click(`input[title="Select to update the User"]`);
  }
}

export class ClaimantPage extends FineosPage {
  constructor(page: Page) {
    super(page);
  }
  async visit(ssn: string): Promise<ClaimantPage> {
    ssn = ssn.replace(/-/g, "");
    await this.page.click('a[aria-label="Parties"]');
    await this.page.focus("label:text-is('Identification Number')");
    await this.page.type("label:text-is('Identification Number')", ssn);
    await this.page.click('input[type="submit"][value="Search"]', {
      force: true,
    });
    await this.page.click("#footerButtonsBar input[value='OK']");
    return new ClaimantPage(this.page);
  }
}
