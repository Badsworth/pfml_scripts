import { Locator, Browser, By, ElementHandle, Until } from "@flood/element";
import * as Cfg from "./config";
import { getFamilyLeavePlanProp } from "./tasks/ApproveClaim";
import { actions } from "./scenarios/SavilinxAgent.perf";

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

export type TestMailVerificationFetcher = {
  getVerificationCodeForUser: (address: string) => Promise<string>;
  getCodeFromMessage: (message: { html: string }) => string;
  getTagFromAddress: (address: string) => string;
  getCredentials: () => { username: string; password: string };
};

export async function getMailVerifier(
  browser: Browser
): Promise<TestMailVerificationFetcher> {
  const apiKey = await Cfg.config("E2E_TESTMAIL_APIKEY");
  const namespace = await Cfg.config("E2E_TESTMAIL_NAMESPACE");
  const endpoint = "https://api.testmail.app/api/json";
  let tag: string;
  let username: string;
  let password: string;

  if (!apiKey || !namespace) {
    throw new Error(
      "Unable to create Test Mail API client due to missing environment variables."
    );
  }

  async function getVerificationCodeForUser(address: string): Promise<string> {
    const params = {
      apikey: apiKey,
      namespace: namespace,
      tag: getTagFromAddress(address),
      livequery: true,
    };

    const paramsString = Object.entries(params)
      .map(([key, val]) => `${key}=${val}`)
      .join("&");

    let body;
    // Stop trying to find email after 90 seconds
    const getBody = async () =>
      browser.evaluate(
        (baseUrl, query) =>
          new Promise((resolve, reject) => {
            const controller = new AbortController();
            setTimeout(() => controller.abort(), 90000);
            fetch(`${baseUrl}?${query}`, { signal: controller.signal })
              .then((r) => {
                resolve(r.json());
              })
              .catch(reject);
          }),
        endpoint,
        paramsString
      );

    const startTimer = new Date().getTime();
    let endTimer;
    try {
      body = await getBody();
      endTimer = new Date().getTime();
      console.info(`\n\n\nTestmail API: ${endTimer - startTimer}ms\n\n\n`);
    } catch (e) {
      endTimer = new Date().getTime();
      console.info(
        `\n\n\nTestmail API: ${endTimer - startTimer}ms\n${
          e.message
        }\n\n${address}\n${password}\n\n\n`
      );
      throw e;
    }

    if (body.result !== "success") {
      throw new Error(
        `There was an error fetching the verification code: ${body.message}`
      );
    }

    if (!Array.isArray(body.emails) || !(body.emails.length > 0)) {
      throw new Error(`No emails found for this user.`);
    }

    return getCodeFromMessage(body.emails[0]);
  }

  function getCodeFromMessage(message: { html: string }): string {
    const match = message.html.match(/(\d{6})<\/strong>/);
    if (!match) {
      throw new Error(`Unable to parse verification code from message.`);
    }
    return match[1];
  }

  function getTagFromAddress(address: string): string {
    const re = new RegExp(`^${namespace}\.(.*)@inbox\.testmail\.app$`);
    const match = address.match(re);
    if (!match || !(match[1].length > 0)) {
      throw new Error(
        `Oops, this doesn't look like a testmail address: ${address}`
      );
    }
    return match[1];
  }

  const randomOf = (charset: string) =>
    charset[Math.floor(Math.random() * charset.length)];

  function rPassword(length: number) {
    const symbolsSet = "@#$%^&*";
    const lowercaseSet = "abcdefghijklmnopqrstuvwxyz";
    const uppercaseSet = lowercaseSet.toUpperCase();
    const pChars = [];
    for (let i = 0; i < length; i++) {
      pChars.push(
        i % 2 === 0 ? randomOf(uppercaseSet) : randomOf(lowercaseSet)
      );
    }
    pChars.push(randomOf(symbolsSet));
    pChars.push(rNum(999));
    shuffleArray(pChars);
    return pChars.join("");
  }

  /**
   * Durstenfeld shuffle.
   *
   * @see https://stackoverflow.com/a/12646864
   */
  function shuffleArray(array: (string | number)[]) {
    for (let i = array.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [array[i], array[j]] = [array[j], array[i]];
    }
  }

  function rTag(length: number) {
    return Math.random().toString(36).substr(2, length);
  }

  function rNum(max: number) {
    return Math.floor(Math.random() * max) + 1;
  }

  function getCredentials() {
    tag = rTag(8);
    username = `${namespace}.${tag}@inbox.testmail.app`;
    password = rPassword(12);
    return {
      username,
      password,
    };
  }

  return {
    getVerificationCodeForUser,
    getCodeFromMessage,
    getTagFromAddress,
    getCredentials,
  };
}

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
