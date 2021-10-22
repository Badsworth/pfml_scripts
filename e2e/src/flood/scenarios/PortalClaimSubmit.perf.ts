import { StepFunction, TestData, Browser, step, By, ENV } from "@flood/element";
import * as Cfg from "../config";
import * as Util from "../helpers";
import config from "../../config";
import {
  generateCredentials,
  getLeaveAdminCredentials,
} from "../../util/credentials";
import TestMailVerificationFetcher from "../../submission/TestMailVerificationFetcher";
import { fetchJSON, fetchFormData } from "../fetch";
import pRetry from "p-retry";
import type {
  EmployerClaimRequestBody,
  GETEmployersClaimsByFineosAbsenceIdReviewResponse,
} from "../../_api";
import { splitClaimToParts } from "../../util/common";
import assert from "assert";
import { DashboardClaimStatus } from "../../../cypress/actions/portal";

let authToken: string;
let username: string;
let password: string;
let applicationId: string;
let fineosId: string;

export const settings = Cfg.globalElementSettings;
export const scenario: Cfg.LSTScenario = "PortalClaimSubmit";

export const steps: Cfg.StoredStep[] = [
  {
    name: "Register a new account",
    test: async (browser: Browser): Promise<void> => {
      await setFeatureFlags(browser);
      ({ username, password } = generateCredentials());
      await register(browser, username, password);
    },
  },
  {
    name: "Login with new account",
    test: async (browser: Browser): Promise<void> => {
      authToken = await login(browser, username, password);
    },
  },
  {
    name: "Create new application",
    test: createApplication,
  },
  {
    name: "Update application",
    test: async (browser: Browser, data: Cfg.LSTSimClaim): Promise<void> => {
      // Attempt at simulating portal's consequent small patch requests
      const claimParts = getClaimParts(data);
      // Execute all claim steps in queue and in order
      for (const claimPart of claimParts) {
        await updateApplication(
          browser,
          claimPart as Partial<Cfg.LSTSimClaim["claim"]>
        );
        // Prevent unrealistic PATCH request spam
        await browser.wait(1000);
      }
    },
  },
  {
    name: "Submit application",
    test: submitApplication,
  },
  {
    name: "Submit payment preference",
    test: submitPaymentPreference,
  },
  {
    name: "Upload documents",
    test: uploadDocuments,
  },
  {
    name: "Complete application",
    test: completeApplication,
  },
  {
    name: "Leave Admin Login",
    test: async (browser: Browser, data: Cfg.LSTSimClaim): Promise<void> => {
      await (
        await Util.waitForElement(browser, By.visibleText("Log out"))
      ).click();
      const fein = data.claim.employer_fein;
      if (!fein) throw new Error("No FEIN was found on this claim");
      const { username, password } = getLeaveAdminCredentials(fein);
      // Log in on Portal as Leave Admin
      authToken = await login(browser, username, password);
    },
  },
  {
    name: "Leave Admin submits employer response",
    options: { waitTimeout: 300000 },
    test: submitEmployerResponse,
  },
];

export default async (): Promise<void> => {
  TestData.fromJSON<Cfg.LSTSimClaim>(`../data/claims.json`).filter(
    (line) => line.scenario === scenario
  );

  steps.forEach((action) => {
    step(action.name, action.test as StepFunction<unknown>);
  });
};

async function register(browser: Browser, username: string, password: string) {
  // go to registration page
  await browser.visit(`${config("PORTAL_BASEURL")}/create-account/`);
  // fill out the form
  await (await Util.labelled(browser, "Email address")).type(username);
  await (await Util.labelled(browser, "Password")).type(password);
  // submit new user
  await (
    await Util.waitForElement(browser, By.css("button[type='submit']"))
  ).click();

  const fetcher = new TestMailVerificationFetcher(
    config("TESTMAIL_APIKEY"),
    config("TESTMAIL_NAMESPACE")
  );
  const code = await fetcher.getVerificationCodeForUser(username);
  // type code
  await (await Util.labelled(browser, "6-digit code")).type(code);
  // submit code
  await (
    await Util.waitForElement(browser, By.css("button[type='submit']"))
  ).click();
  // wait for successful registration
  await Util.waitForElement(
    browser,
    By.visibleText("Email successfully verified")
  );
}

async function login(
  browser: Browser,
  username: string,
  password: string
): Promise<string> {
  await browser.visit(`${config("PORTAL_BASEURL")}/login`);
  await (await Util.labelled(browser, "Email address")).type(username);
  await (await Util.labelled(browser, "Password")).type(password);
  await (
    await Util.waitForElement(browser, By.css("button[type='submit']"))
  ).click();
  const agreeTerms = await Util.maybeFindElement(
    browser,
    By.visibleText("Agree and continue")
  );
  if (agreeTerms) {
    await agreeTerms.click();
    await browser.waitForNavigation();
  }
  await Util.waitForElement(browser, By.visibleText("Log out"));

  const cookie = (await browser.page.cookies()).find((cookie) => {
    return cookie.name.match(/CognitoIdentityServiceProvider\..*\.accessToken/);
  });
  if (!cookie) {
    throw new Error("Unable to find accessToken cookie");
  }
  return cookie.value;
}

async function submitEmployerResponse(
  browser: Browser,
  data: Cfg.LSTSimClaim
): Promise<void> {
  if (!data.employerResponse) return;
  await (await Util.waitForElement(browser, By.linkText("Dashboard"))).click();
  await filterClaims(browser, "Review by");
  await randomClaimSort(browser); // filter for "Review by" status
  // Randomly Select Search Methods
  switch (randomNumber(2)) {
    case 0:
      await searchAbsenceCaseNumber(browser, fineosId);
      break;
    case 1:
      await searchName(browser, data);
      break;
  }

  console.log("Sort and Search Completed w/o errors!");

  // submit response directly to API
  const employerResponse = data.employerResponse;
  const review = await pRetry(
    async () => {
      const fetchedResponse = await fetchJSON(
        browser,
        authToken,
        `${config("API_BASEURL")}/employers/claims/${fineosId}/review`
      );
      if (fetchedResponse.status_code !== 200) {
        if (
          fetchedResponse.data &&
          fetchedResponse.data.message ===
            "Claim does not exist for given absence ID"
        ) {
          throw new Error(
            `Unable to find claim as leave admin for ${fineosId}.`
          );
        }
        throw new pRetry.AbortError(
          `Hit an unknown error fetching leave admin response`
        );
      }
      return fetchedResponse as GETEmployersClaimsByFineosAbsenceIdReviewResponse;
    },
    { retries: 20, maxRetryTime: 30000 }
  );
  const body = {
    ...employerResponse,
    employer_benefits: [
      ...(review.data?.employer_benefits ?? []),
      ...(employerResponse.employer_benefits ?? []),
    ],
    previous_leaves: [
      ...(review.data?.previous_leaves ?? []),
      ...(employerResponse.previous_leaves ?? []),
    ],
  } as EmployerClaimRequestBody;
  const res = await fetchJSON(
    browser,
    authToken,
    `${config("API_BASEURL")}/employers/claims/${fineosId}/review`,
    {
      method: "PATCH",
      body: JSON.stringify(body),
    }
  );
  if (res.status_code !== 200) {
    throw new Error(
      `Unable to update application: ${JSON.stringify(res, null, 2)}`
    );
  }
  console.log("Submitted employer response");
}

const isNode = !!(typeof process !== "undefined" && process.version);
async function readFile(filename: string): Promise<Buffer> {
  if (!isNode) {
    throw new Error("Cannot load the fs module API outside of Node.");
  }
  let fs;
  fs = await import("fs");
  if (!fs.promises) {
    fs = fs.default;
  }
  if (ENV.FLOOD_LOAD_TEST) {
    filename = `/data/flood/files/${filename}`;
  }
  console.info(`\n\n\nreadFile in "${filename}"\n\n\n`);
  return fs.readFileSync(filename);
}

async function setFeatureFlags(browser: Browser): Promise<void> {
  return browser.page.setCookie({
    name: "_ff",
    value: JSON.stringify({
      pfmlTerriyay: true,
      employerShowDashboardSort: true,
      employerShowDashboardSearch: true,
      employerShowReviewByStatus: true,
    }),
    url: config("PORTAL_BASEURL"),
  });
}

function getClaimParts(
  data: Cfg.LSTSimClaim
): Partial<Cfg.LSTSimClaim["claim"]>[] {
  const { claim } = data;
  return splitClaimToParts(claim);
}

async function createApplication(browser: Browser): Promise<void> {
  const res = await fetchJSON(
    browser,
    authToken,
    `${config("API_BASEURL")}/applications`,
    {
      method: "POST",
    }
  );

  if (!res.data || !res.data.application_id) {
    throw new Error(
      `Unable to create application: ${JSON.stringify(res, null, 2)}`
    );
  }
  applicationId = res.data.application_id;
  console.info("Created application", res.status_code);
}

async function updateApplication(
  browser: Browser,
  claimPart: Partial<Cfg.LSTSimClaim["claim"]>
): Promise<void> {
  const res = await fetchJSON(
    browser,
    authToken,
    `${config("API_BASEURL")}/applications/${applicationId}`,
    {
      method: "PATCH",
      body: JSON.stringify(claimPart),
    }
  );
  if (res.status_code !== 200) {
    throw new Error(
      `Unable to update application: ${JSON.stringify(res, null, 2)}`
    );
  }
  console.info("Updated application", res.status_code);
}

async function submitApplication(browser: Browser): Promise<void> {
  const res = await fetchJSON(
    browser,
    authToken,
    `${config("API_BASEURL")}/applications/${applicationId}/submit_application`,
    {
      method: "POST",
    }
  );
  if (res.status_code !== 201) {
    throw new Error(
      `Unable to submit application: ${JSON.stringify(res, null, 2)}`
    );
  }
  console.info("Submitted application", res.status_code);
}

async function submitPaymentPreference(browser: Browser): Promise<void> {
  const res = await fetchJSON(
    browser,
    authToken,
    `${config(
      "API_BASEURL"
    )}/applications/${applicationId}/submit_payment_preference`,
    {
      method: "POST",
      body: JSON.stringify({
        payment_preference: {
          payment_method: "Elec Funds Transfer",
          routing_number: "011401533",
          account_number: "5555555555",
          bank_account_type: "Checking",
        },
      }),
    }
  );
  if (res.status_code !== 201) {
    throw new Error(
      `Unable to submit application: ${JSON.stringify(res, null, 2)}`
    );
  }
  console.info("Payment preferences updated", res.status_code);
}

async function uploadDocuments(
  browser: Browser,
  data: Cfg.LSTSimClaim
): Promise<void> {
  for (const document of data.documents) {
    const data = await readFile("forms/hcp-real.pdf");
    const name = `${document.document_type}.pdf`;
    const res = await fetchFormData(
      browser,
      authToken,
      {
        document_type: document.document_type,
        description: `LST - Direct to API - ${document.document_type}`,
        file: { data, name, type: "application/pdf" },
        name,
      },
      `${config("API_BASEURL")}/applications/${applicationId}/documents`,
      {
        method: "POST",
      }
    );
    if (res.status_code !== 200) {
      throw new Error(
        `Unable to upload document: ${JSON.stringify(res, null, 2)}`
      );
    }
    console.info("Uploaded document", res.status_code);
    await browser.wait(1000);
  }
}

async function completeApplication(browser: Browser): Promise<void> {
  const res = await fetchJSON(
    browser,
    authToken,
    `${config(
      "API_BASEURL"
    )}/applications/${applicationId}/complete_application`,
    {
      method: "POST",
    }
  );
  if (res.status_code !== 200) {
    throw new Error(
      `Unable to complete application: ${JSON.stringify(res, null, 2)}`
    );
  }
  fineosId = res.data.fineos_absence_id;
  console.info("Completed application", {
    application_id: res.data.application_id,
    fineos_absence_id: res.data.fineos_absence_id,
  });
}

async function searchAbsenceCaseNumber(
  browser: Browser,
  claimID: string
): Promise<void> {
  await (
    await Util.labelled(browser, "Search for employee name or application ID")
  ).type(claimID);
  await (
    await Util.waitForElement(browser, By.css('button[type="submit"]'))
  ).click();
  await Util.waitForElement(browser, By.linkText(claimID)).then(async (el) => {
    assert.strictEqual(await el.text(), claimID);
  });
  await browser
    .findElements(By.css("table.usa-table > tbody > tr"))
    .then(async (el) => {
      assert.strictEqual(el.length, 1);
    });
}

async function searchName(
  browser: Browser,
  data: Cfg.LSTSimClaim
): Promise<void> {
  const { claim } = data;
  const { first_name, last_name } = claim;
  const full_name = `${first_name} ${last_name}`;

  switch (randomNumber(3)) {
    // First Name Only
    case 0:
      await (
        await Util.labelled(
          browser,
          "Search for employee name or application ID"
        )
      ).type(first_name as string);
      await (
        await Util.waitForElement(browser, By.css('button[type="submit"]'))
      ).click();
      await Util.waitForElement(
        browser,
        By.partialLinkText(first_name as string)
      );
      await browser
        .findElements(By.css("table.usa-table > tbody > tr"))
        .then(async (el) => {
          assert.ok(
            el.length >= 1,
            "Expect there to be at least 1 or more rows"
          );
        });
      break;
    // First and Last Name
    case 1:
      await (
        await Util.labelled(
          browser,
          "Search for employee name or application ID"
        )
      ).type(full_name);
      await (
        await Util.waitForElement(browser, By.css('button[type="submit"]'))
      ).click();
      await Util.waitForElement(browser, By.linkText(full_name));
      await browser
        .findElements(By.css("table.usa-table > tbody > tr"))
        .then(async (el) => {
          assert.ok(
            el.length >= 1,
            "Expect there to be at least 1 or more rows"
          );
        });
      break;
    // Last name only
    case 2:
      await (
        await Util.labelled(
          browser,
          "Search for employee name or application ID"
        )
      ).type(last_name as string);
      await (
        await Util.waitForElement(browser, By.css('button[type="submit"]'))
      ).click();
      await Util.waitForElement(
        browser,
        By.partialLinkText(last_name as string)
      );
      await browser
        .findElements(By.css("table.usa-table > tbody > tr"))
        .then(async (el) => {
          assert.ok(
            el.length >= 1,
            "Expect there to be at least 1 or more rows"
          );
        });
      break;
  }
}

async function randomClaimSort(browser: Browser): Promise<void> {
  const sorts = [
    "Oldest applications",
    "Last name – A to Z",
    "Last name – Z to A",
    "Newest applications",
    "Status",
  ] as const;
  const randomIndex = randomNumber(sorts.length);
  await Util.waitForElement(browser, Util.byLabelled("Sort"));
  await (await Util.labelled(browser, "Sort")).click();
  await browser.selectByText(
    By.nameAttr("orderAndDirection"),
    sorts[randomIndex]
  );
}

function randomNumber(n: number): number {
  return Math.floor(Math.random() * n);
}

/**
 * Applies a single filter by status. Checks the results, clears filters.
 * @param status
 */
async function filterClaims(browser: Browser, status: DashboardClaimStatus) {
  // find filters button
  await browser
    .findElement(By.css('button[aria-controls="filters"]'))
    .then((button) => button.click());
  // Select the right filter
  await Util.waitForElement(browser, Util.byContains("label", status)).then(
    (el) => el.click()
  );
  // Apply filters
  await browser
    .findElement(By.visibleText("Apply filters"))
    .then((el) => el.click());
  // Check results
  await browser
    .findElements(By.css("table.usa-table > tbody > tr"))
    .then(async (rows) => {
      for (const row of rows) {
        const text = await row.text();
        console.log(text);
        assert.ok(
          text.includes(status),
          `Expected all rows to have status: ${status}`
        );
      }
    });
  // Disable filter
  await browser
    .findElement(Util.byButtonText(status))
    .then((button) => button.click());
}
