import {
  Locator,
  Browser,
  By,
  ElementHandle,
  Until,
  BaseLocator,
} from "@flood/element";
import { EvalLocator } from "@flood/element-core/dist/src/page/locators/EvalLocator";
import * as Cfg from "./config";
import { getFamilyLeavePlanProp } from "./tasks/ApproveClaim";
import { actions } from "./scenarios/SavilinxAgent.perf";
import { EvaluateFn } from "puppeteer";

export const formatDate = (d: string | null | undefined): string =>
  new Intl.DateTimeFormat("en-US", {
    month: "2-digit",
    day: "2-digit",
    year: "numeric",
  }).format(new Date(d || ""));

export const labelled = async (
  browser: Browser,
  labelText: string
): Promise<ElementHandle> => {
  const label = By.js(
    (text) =>
      Array.from(document.querySelectorAll("label")).find(
        (label) => label.textContent === text
      ),
    labelText
  );
  const labelEl = await waitForElement(browser, label);
  const inputId = await labelEl.getAttribute("for");
  if (!inputId) {
    throw new Error(
      `Unable to find label with the content: "${labelText}". ${labelEl.toErrorString()}`
    );
  }
  return waitForElement(browser, By.id(inputId));
};

export function byButtonText(text: string): Locator {
  return By.js((text) => {
    // @ts-ignore
    const buttons = [...document.querySelectorAll("button")];
    return buttons.find((button) => button.innerText.match(text));
  }, text);
}

type SelectorEvaluator = EvaluateFn<string | undefined>;
export function byContains(selector: string, text: string): Locator {
  const findMany = (selector: string, text: string) =>
    Array.from(document.querySelectorAll(selector)).filter((candidate) =>
      candidate.textContent?.match(text)
    );
  const findOne = (selector: string, text: string) =>
    Array.from(document.querySelectorAll(selector)).find((candidate) =>
      candidate.textContent?.match(text)
    );

  return new BaseLocator(
    new EvalLocator(
      findOne as SelectorEvaluator,
      findMany as SelectorEvaluator,
      [selector, text]
    ),
    `byContains(${selector}, ${text})`
  );
}

export function byLabelled(labelText: string): Locator {
  const findMany = (text: string) => {
    const results = Array.from(document.querySelectorAll("label"))
      .filter((label) => label.textContent === text)
      .map((label) => {
        const labelFor = label.getAttribute("for");
        if (labelFor !== null) {
          return document.getElementById(labelFor);
        }
      })
      .filter((i) => i);
    return results;
  };
  const findOne = (text: string) => {
    const results = Array.from(document.querySelectorAll("label"))
      .filter((label) => label.textContent === text)
      .map((label) => {
        const labelFor = label.getAttribute("for");
        if (labelFor !== null) {
          return document.getElementById(labelFor);
        }
      })
      .filter((i) => i);
    return results.pop();
  };

  return new BaseLocator(
    new EvalLocator(
      findOne as SelectorEvaluator,
      findMany as SelectorEvaluator,
      [labelText]
    ),
    `By.labelled("${labelText}")`
  );
}

export const waitForElement = async (
  browser: Browser,
  locator: Locator
): Promise<ElementHandle> => {
  await browser.wait(Until.elementIsVisible(locator));
  await browser.focus(locator);
  return browser.findElement(locator);
};

export const maybeFindElement = async (
  browser: Browser,
  locator: Locator,
  retries = 5,
  frequency = 1000
): Promise<ElementHandle | null> => {
  let element: ElementHandle | null = await browser.maybeFindElement(locator);
  if (element) return element;
  for (let i = 0; i < retries; i++) {
    element = await browser.maybeFindElement(locator);
    if (element !== null) break;
    await browser.wait(frequency);
  }
  return element;
};

export const isFinanciallyEligible = async (
  browser: Browser
): Promise<boolean> => {
  // go to the absence hub tab
  const absenceHubTab = await waitForElement(
    browser,
    By.css("[class^='TabO'][keytipnumber='5']")
  );
  await absenceHubTab.click();

  // and verify eligibility before proceeding
  const eligibility = await waitForElement(
    browser,
    getFamilyLeavePlanProp("EligibilityIcon")
  );
  const eligibilityIcon = await eligibility.getAttribute("class");

  return eligibilityIcon === "icon-checkbox";
};

export function assignTasks(
  fineosId: string,
  search = true,
  agent: Cfg.FineosUserType = "SAVILINX"
): Cfg.StoredStep {
  return {
    name: `Assign ${fineosId}'s tasks to ${agent} Agent`,
    test: async (browser: Browser): Promise<void> => {
      if (search) {
        await browser.visit(await Cfg.getFineosBaseUrl());
        // search for particular by id
        const casesMenu = await waitForElement(
          browser,
          By.css("a[aria-label='Cases']")
        );
        await casesMenu.click();
        const caseTab = await waitForElement(
          browser,
          By.css("[keytipnumber='4']")
        );
        await caseTab.click();
        const caseNumberInput = await labelled(browser, "Case Number");
        await browser.type(caseNumberInput, fineosId);
        const searchButton = await waitForElement(
          browser,
          By.css("input[type='submit'][value*='Search']")
        );
        await searchButton.click();
      }
      // go to claim tasks tab
      const tasksTab = await waitForElement(
        browser,
        By.css("[class^='TabO'][keytipnumber='9']")
      );
      await browser.click(tasksTab);
      // assign each task to SAVILINX
      for (const action of actions) {
        const claimTask = await waitForElement(
          browser,
          By.css(`table[id*='TasksForCaseListView'] td[title='${action}']`)
        );
        await browser.click(claimTask);
        const openTask = await waitForElement(
          browser,
          By.css("input[type='submit'][title='Open this task']")
        );
        await browser.click(openTask);

        const transferDropdown = await waitForElement(
          browser,
          By.css("a[aria-label='Transfer']")
        );
        await browser.click(transferDropdown);
        const transferToUser = await waitForElement(
          browser,
          By.css("a[aria-label='Transfer to User']")
        );
        await browser.click(transferToUser);
        // the user tasks are transferred to can be changed
        // under the "title='SAVILINX'" replace SAVILINX with the user you want
        const pickSavilinxAgent = await waitForElement(
          browser,
          By.css(`table[id*='TransferUsersRolesListView'] td[title='${agent}']`)
        );
        await browser.click(pickSavilinxAgent);
        const okButton = await waitForElement(
          browser,
          By.css("input[type='submit'][value='OK']")
        );
        await browser.click(okButton);

        const closePopupButton = await waitForElement(
          browser,
          By.css("input[id*='UserTaskTransferRecord_ok'][value='OK']")
        );
        await browser.click(closePopupButton);
        const closeTaskButton = await waitForElement(
          browser,
          By.css("input[type='submit'][value='Close']")
        );
        await browser.click(closeTaskButton);
      }
    },
  };
}

export async function findClaimOnEmployerDashboard(
  browser: Browser,
  fineosAbsenceId: string
): Promise<void> {
  await (
    await await waitForElement(browser, By.css(".ma__pagination__next"))
  ).click();
  const claimLink = await maybeFindElement(
    browser,
    By.visibleText(fineosAbsenceId)
  );
  /* if the claim link doesn't exist on the second page then go back to the first page.
   this would be the case where there is a high volume of concurrent submissions against a single employer and the claim is no longer on the first page
   */
  if (!claimLink) {
    await (
      await await waitForElement(browser, By.css(".ma__pagination__prev"))
    ).click();
  }
  await (
    await waitForElement(browser, By.visibleText(fineosAbsenceId))
  ).click();
  await browser.waitForNavigation();
}
