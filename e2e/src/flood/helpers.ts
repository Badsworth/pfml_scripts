import { Locator, Browser, By, ElementHandle, Until } from "@flood/element";
import { config } from "./config";

export const formatDate = (d: string | null | undefined): string => {
  const notificationDate = new Date(d || "");
  const notifDate = {
    day: notificationDate.getDate().toString().padStart(2, "0"),
    month: (notificationDate.getMonth() + 1).toString().padStart(2, "0"),
    year: notificationDate.getFullYear(),
  };
  const notifDateStr = `${notifDate.month}/${notifDate.day}/${notifDate.year}`;
  return notifDateStr;
};

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

export const waitForElement = async (
  browser: Browser,
  locator: Locator
): Promise<ElementHandle> => {
  await browser.wait(Until.elementIsVisible(locator));
  await browser.focus(locator);
  return browser.findElement(locator);
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
  const apiKey = await config("E2E_TESTMAIL_APIKEY");
  const namespace = await config("E2E_TESTMAIL_NAMESPACE");
  const endpoint = "https://api.testmail.app/api/json";
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
    };

    const paramsString = Object.entries(params)
      .map(([key, val]) => `${key}=${val}`)
      .join("&");

    const body = await browser.evaluate(
      (baseUrl, query) => {
        return new Promise((resolve, reject) => {
          fetch(`${baseUrl}?${query}`)
            .then((r) => {
              resolve(r.json());
            })
            .catch(reject);
        });
      },
      endpoint,
      paramsString
    );

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

  function rStr(length: number) {
    return Array(length)
      .fill("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz")
      .map((x) => x[Math.floor(Math.random() * x.length)])
      .join("");
  }

  function rStrWithNums(length: number) {
    return Math.random().toString(36).substr(2, length);
  }

  function rNum(max: number) {
    return Math.floor(Math.random() * max) + 1;
  }

  function getCredentials() {
    const tag = rStrWithNums(8);
    return {
      username: `${namespace}.${tag}@inbox.testmail.app`,
      password: rStr(10) + rNum(999),
    };
  }

  return {
    getVerificationCodeForUser,
    getCodeFromMessage,
    getTagFromAddress,
    getCredentials,
  };
}
