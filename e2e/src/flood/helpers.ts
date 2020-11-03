import { Locator, Browser, By, ElementHandle, Until } from "@flood/element";
import { config, StandardDocumentType } from "./config";
import { ClaimDocument } from "../simulation/types";
import { DocumentUploadRequest } from "../api";

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

export const waitForElement = async (
  browser: Browser,
  locator: Locator
): Promise<ElementHandle> => {
  await browser.wait(Until.elementIsVisible(locator));
  await browser.focus(locator);
  return browser.findElement(locator);
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
    By.css("td[id*='EligibilityStatusIcon'] i")
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
      livequery: true,
      timestamp_from: new Date().getTime(),
    };

    const paramsString = Object.entries(params)
      .map(([key, val]) => `${key}=${val}`)
      .join("&");

    // Stop trying to find email after 60 seconds
    const controller = new AbortController();
    setTimeout(() => controller.abort(), 60000);
    const body = await browser.evaluate(
      (baseUrl, query, signal) => {
        return new Promise((resolve, reject) => {
          fetch(`${baseUrl}?${query}`, { signal })
            .then((r) => {
              resolve(r.json());
            })
            .catch(reject);
        });
      },
      endpoint,
      paramsString,
      controller.signal
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

export const getRequestOptions = (
  token: string,
  method: string,
  body?: unknown,
  headers: HeadersInit = {
    "Content-Type": "application/json",
  },
  options?: RequestInit
): RequestInit => ({
  method,
  body: JSON.stringify(body),
  headers: {
    Accept: "application/json",
    Authorization: `Bearer ${token}`,
    "User-Agent": "PFML Load Testing Bot",
    ...headers,
  },
  ...options,
});

export function getDocumentType(document: ClaimDocument): StandardDocumentType {
  if (["MASSID", "OOSID"].includes(document.type)) {
    return "Identification Proof";
  } else {
    return "State Managed Paid Leave Confirmation";
  }
}

export const evalFetch = async (
  browser: Browser,
  url: string,
  options: RequestInit,
  docUpload?: DocumentUploadRequest
): // eslint-disable-next-line @typescript-eslint/no-explicit-any
Promise<any> => {
  return browser.evaluate(
    (
      fUrl: RequestInfo,
      fOpts: RequestInit,
      fDocUpload: DocumentUploadRequest
    ) => {
      return new Promise((resolve, reject) => {
        if (typeof fDocUpload !== "undefined") {
          const body = fDocUpload;
          const fd = new FormData();
          const blobType = "application/pdf";
          fd.append(
            "file",
            // @ts-ignore
            new Blob([new Uint8Array(body.file.data)], { type: blobType }),
            body.name
          );
          fd.append("document_type", body.document_type);
          fd.append("description", body.description as string);
          fd.append("name", body.name as string);
          fOpts.body = fd;
        }
        fetch(fUrl, fOpts)
          .then((r) => r.json())
          .then(resolve)
          .catch(reject);
      });
    },
    url,
    options,
    docUpload
  );
};
