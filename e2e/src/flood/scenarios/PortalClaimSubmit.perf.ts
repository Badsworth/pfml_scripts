import { StepFunction, TestData, Browser, step, By, ENV } from "@flood/element";
import * as Cfg from "../config";
import * as Util from "../helpers";
import { fetchFormData, fetchJSON } from "../fetch";

let authToken: string;
let newAccount: { username: string; password: string };
let applicationId: string;
let fineosId: string;

export const settings = Cfg.globalElementSettings;
export const scenario: Cfg.LSTScenario = "PortalClaimSubmit";

export const steps: Cfg.StoredStep[] = [
  {
    name: "Register a new account",
    test: async (browser: Browser): Promise<void> => {
      await setFeatureFlags(browser);
      const emailVerifier = await Util.getMailVerifier(browser);
      newAccount = emailVerifier.getCredentials();
      await register(
        browser,
        emailVerifier,
        newAccount.username,
        newAccount.password
      );
    },
  },
  {
    name: "Login with new account",
    test: async (browser: Browser): Promise<void> => {
      authToken = await login(
        browser,
        newAccount.username,
        newAccount.password
      );
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
    name: "Upload documents",
    test: uploadDocuments,
  },
  {
    name: "Complete application",
    test: completeApplication,
  },
  {
    name: "Point of Contact fills employer response",
    options: { waitTimeout: 300000 },
    test: async (browser: Browser, data: Cfg.LSTSimClaim): Promise<void> => {
      if (data.employerResponse?.employer_decision !== "Approve") return;
      const employerResponseStep = employerResponse(fineosId);
      console.info(employerResponseStep.name);
      await employerResponseStep.test(browser, data);
    },
  },
  {
    name: "Assign tasks to specific Agent",
    test: async (browser: Browser, data: Cfg.LSTSimClaim): Promise<void> => {
      // we don't want to run this step on a real Flood
      if (!ENV.FLOOD_LOAD_TEST) {
        const assignTasksStep = Util.assignTasks(fineosId);
        console.info(assignTasksStep.name);
        await assignTasksStep.test(browser, data);
      }
    },
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

async function register(
  browser: Browser,
  verifier: Util.TestMailVerificationFetcher,
  username: string,
  password: string
) {
  // go to registration page
  await browser.visit(`${await Cfg.PortalBaseUrl}/create-account/`);
  // fill out the form
  await (await Util.labelled(browser, "Email address")).type(username);
  await (await Util.labelled(browser, "Password")).type(password);
  // submit new user
  await (
    await Util.waitForElement(browser, By.css("button[type='submit']"))
  ).click();

  const code = await verifier.getVerificationCodeForUser(username);
  if (code.length === 0)
    throw new Error("Couldn't getVerificationCodeForUser email!");
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
  await browser.visit(`${await Cfg.PortalBaseUrl}/login`);
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

function employerResponse(fineosId: string): Cfg.StoredStep {
  return {
    name: `Point of Contact responds to "${fineosId}"`,
    test: async (browser: Browser, data: Cfg.LSTSimClaim): Promise<void> => {
      await setFeatureFlags(browser);
      let error;
      for (let i = 0; i < 6; i++) {
        await (
          await Util.waitForElement(browser, By.visibleText("Log out"))
        ).click();
        // Log in on Portal as Leave Admin
        authToken = await login(
          browser,
          `gqzap.lst-employer.${data.claim.employer_fein?.replace(
            "-",
            ""
          )}@inbox.testmail.app`,
          await Cfg.config("E2E_EMPLOYER_PORTAL_PASSWORD")
        );
        // Review submited application via direct link on Portal
        await browser.visit(
          `${await Cfg.PortalBaseUrl}/employers/applications/new-application/?absence_id=${fineosId}`
        );
        error = await Util.maybeFindElement(
          browser,
          By.visibleText("An error occurred")
        );
        if (error) {
          // Waits 20 seconds for FINEOS to catch up.
          // Will wait 120 seconds total over entire For loop.
          await browser.wait(20000);
        } else {
          break;
        }
      }

      // Are you the right person? true | false
      await (
        await Util.waitForElement(
          browser,
          By.css("[name='hasReviewerVerified'][value='true'] + label")
        )
      ).click();
      // Click "Agree and submit" button
      await (
        await Util.waitForElement(browser, By.visibleText("Agree and submit"))
      ).click();
      await browser.waitForNavigation();
      // Suspect of fraud? Yes | No
      const isSus = Math.random() * 100 <= 5;
      await (
        await Util.waitForElement(
          browser,
          By.css(`[name='isFraud'][value='${isSus ? "Yes" : "No"}'] + label`)
        )
      ).click();
      // Given 30 days notice? Yes | No
      const employerNotified = data.claim.leave_details?.employer_notified;
      await (
        await Util.waitForElement(
          browser,
          By.css(
            `[name='employeeNotice'][value='${
              employerNotified ? "Yes" : "No"
            }'] + label`
          )
        )
      ).click();
      // Leave request response? Approve | Deny
      const isApproved = !isSus && employerNotified;
      await (
        await Util.waitForElement(
          browser,
          By.css(
            `[name='employerDecision'][value="${
              isApproved ? "Approve" : "Deny"
            }"] + label`
          )
        )
      ).click();
      // Any concerns? true | false
      await (
        await Util.waitForElement(
          browser,
          By.css("[name='shouldShowCommentBox'][value='false'] + label")
        )
      ).click();
      // Provides required comment as needed.
      if (!isApproved) {
        await (
          await Util.waitForElement(browser, By.css('textarea[name="comment"]'))
        ).type("PFML - Denied for LST purposes");
      }
      // Click "Submit"
      await (
        await Util.waitForElement(browser, By.css("button[type='submit']"))
      ).click();
      await browser.waitForNavigation();
      // Check if review was successful
      await Util.waitForElement(
        browser,
        By.visibleText("Thanks for reviewing the application")
      );
      await Util.waitForElement(browser, By.visibleText(fineosId));
      // @todo?: Possibly check back on fineos claim if employer response showed up
    },
  };
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
      claimantShowAuth: true,
      claimantAuthThroughApi: true,
    }),
    url: await Cfg.PortalBaseUrl,
  });
}

function getClaimParts(
  data: Cfg.LSTSimClaim
): Partial<Cfg.LSTSimClaim["claim"]>[] {
  const { claim } = data;
  const { leave_details } = claim;
  return [
    {
      first_name: claim.first_name,
      middle_name: null,
      last_name: claim.last_name,
    },
    {
      has_mailing_address: claim.has_mailing_address,
      residential_address: claim.residential_address,
      mailing_address: claim.mailing_address,
    },
    {
      date_of_birth: claim.date_of_birth,
    },
    {
      has_state_id: claim.has_state_id,
      mass_id: claim.mass_id,
    },
    {
      tax_identifier: claim.tax_identifier,
    },
    {
      employment_status: claim.employment_status,
      employer_fein: claim.employer_fein,
    },
    {
      leave_details: {
        employer_notified: leave_details?.employer_notified,
        employer_notification_date: leave_details?.employer_notification_date,
      },
    },
    {
      work_pattern: {
        work_pattern_type: claim.work_pattern?.work_pattern_type,
      },
    },
    {
      hours_worked_per_week: claim.hours_worked_per_week,
      work_pattern: {
        work_pattern_days: claim.work_pattern?.work_pattern_days,
      },
    },
    {
      leave_details: {
        reason: leave_details?.reason,
        reason_qualifier: leave_details?.reason_qualifier,
      },
    },
    {
      leave_details: {
        child_birth_date: leave_details?.child_birth_date,
        child_placement_date: leave_details?.child_placement_date,
        pregnant_or_recent_birth: leave_details?.pregnant_or_recent_birth,
      },
    },
    {
      has_continuous_leave_periods: claim.has_continuous_leave_periods,
      leave_details: {
        continuous_leave_periods: leave_details?.continuous_leave_periods,
      },
    },
    {
      has_reduced_schedule_leave_periods:
        claim.has_reduced_schedule_leave_periods,
    },
    {
      has_intermittent_leave_periods: claim.has_intermittent_leave_periods,
    },
    {
      phone: {
        int_code: "1",
        phone_number: "844-781-3163",
        phone_type: "Cell",
      },
    },
    // { temp: { has_employer_benefits: false } },
    // { temp: { has_other_incomes: false } },
    // { temp: { has_previous_leaves: false } },
    // {
    //   payment_preferences: claim.payment_preferences,
    // },
  ];
}

async function createApplication(browser: Browser): Promise<void> {
  const res = await fetchJSON(
    browser,
    authToken,
    `${await Cfg.APIBaseUrl}/applications`,
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
    `${await Cfg.APIBaseUrl}/applications/${applicationId}`,
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
    `${await Cfg.APIBaseUrl}/applications/${applicationId}/submit_application`,
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
      `${await Cfg.APIBaseUrl}/applications/${applicationId}/documents`,
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
    `${await Cfg.APIBaseUrl}/applications/${applicationId}/complete_application`,
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
