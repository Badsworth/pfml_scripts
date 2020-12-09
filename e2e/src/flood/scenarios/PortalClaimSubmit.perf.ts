import { StepFunction, TestData, Browser, step, By, ENV } from "@flood/element";
import { DocumentUploadRequest } from "../../api";
import {
  globalElementSettings as settings,
  PortalBaseUrl,
  APIBaseUrl,
  dataBaseUrl,
  documentUrl,
  LSTSimClaim,
  LSTScenario,
} from "../config";
import {
  labelled,
  readFile,
  evalFetch,
  assignTasks,
  waitForElement,
  waitForRealTimeSim,
  getDocumentType,
  getRequestOptions,
  getMailVerifier,
  TestMailVerificationFetcher,
} from "../helpers";

let authToken: string;
let applicationId: string;
let fineosId: string;

export { settings };
export const scenario: LSTScenario = "PortalClaimSubmit";
export const steps = [
  {
    name: "Register and login",
    test: async (browser: Browser): Promise<void> => {
      await setFeatureFlags(browser);
      const emailVerifier = await getMailVerifier(browser);
      const { username, password } = await emailVerifier.getCredentials();
      authToken = await registerAndLogin(
        browser,
        emailVerifier,
        username,
        password
      );
    },
  },
  {
    name: "Create, Update and Submit new application",
    test: async (browser: Browser, data: LSTSimClaim): Promise<void> => {
      const { claim, documents } = data;
      const { leave_details } = claim;
      // Attempt at simulating portal's consequent small patch requests
      const claimParts: (Partial<LSTSimClaim["claim"]> | string)[] = [
        "create",
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
            employer_notification_date:
              leave_details?.employer_notification_date,
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
        "submit",
        // {
        //   payment_preferences: claim.payment_preferences,
        // },
        "documents",
        "complete",
        "assignTasks",
      ];
      // Execute all claim steps in queue and in order
      for (const claimPart of claimParts) {
        let reqOptions: RequestInit;
        let res;
        if (typeof claimPart === "string") {
          switch (claimPart) {
            // request to create application
            case "create":
              reqOptions = getRequestOptions(authToken, "POST");
              res = await evalFetch(
                browser,
                `${await APIBaseUrl}/applications`,
                reqOptions
              );
              if (!res.data || !res.data.application_id) {
                throw new Error(
                  `Unable to create application: ${JSON.stringify(
                    res,
                    null,
                    2
                  )}`
                );
              }
              applicationId = res.data.application_id;
              console.info("Created application", res.status_code);
              break;
            // request to submit application
            case "submit":
              reqOptions = getRequestOptions(authToken, "POST");
              res = await evalFetch(
                browser,
                `${await APIBaseUrl}/applications/${applicationId}/submit_application`,
                reqOptions
              );
              if (res.status_code !== 201) {
                throw new Error(
                  `Unable to submit application: ${JSON.stringify(
                    res,
                    null,
                    2
                  )}`
                );
              }
              console.info("Submitted application", res.status_code);
              break;
            // request to upload application documents
            case "documents":
              for (const document of documents) {
                // important: body & headers need to be empty objects
                reqOptions = getRequestOptions(authToken, "POST", {}, {});
                const docBody: DocumentUploadRequest = {
                  document_type: getDocumentType(document),
                  description: "LST - Direct to API",
                  file: await readFile(documentUrl),
                  mark_evidence_received: true,
                  name: `${document.type}.pdf`,
                };
                res = await evalFetch(
                  browser,
                  `${await APIBaseUrl}/applications/${applicationId}/documents`,
                  reqOptions,
                  docBody
                );
                if (res.status_code !== 200) {
                  throw new Error(
                    `Unable to upload document: ${JSON.stringify(res, null, 2)}`
                  );
                }
                console.info("Uploaded document", res.status_code);
                await browser.wait(1000);
              }
              break;
            case "complete":
              reqOptions = getRequestOptions(authToken, "POST");
              res = await evalFetch(
                browser,
                `${await APIBaseUrl}/applications/${applicationId}/complete_application`,
                reqOptions
              );
              if (res.status_code !== 200) {
                throw new Error(
                  `Unable to complete application: ${JSON.stringify(
                    res,
                    null,
                    2
                  )}`
                );
              }
              fineosId = res.data.fineos_absence_id;
              console.info("Completed application", {
                application_id: res.data.application_id,
                fineos_absence_id: res.data.fineos_absence_id,
              });
              break;
            case "assignTasks":
              if (!ENV.FLOOD_LOAD_TEST) {
                const assignTasksStep = assignTasks(fineosId);
                console.info(assignTasksStep.name);
                await assignTasksStep.test(browser, data);
              }
              break;
            default:
              break;
          }
        } else {
          reqOptions = getRequestOptions(authToken, "PATCH", claimPart);
          res = await evalFetch(
            browser,
            `${await APIBaseUrl}/applications/${applicationId}`,
            reqOptions
          );
          if (res.status_code !== 200) {
            throw new Error(
              `Unable to update application: ${JSON.stringify(res, null, 2)}`
            );
          }
          console.info("Updated application", res.status_code);
        }
        await waitForRealTimeSim(browser, data, 1 / claimParts.length);
      }
    },
  },
];

async function registerAndLogin(
  browser: Browser,
  verifier: TestMailVerificationFetcher,
  username: string,
  password: string
) {
  // go to registration page
  await browser.visit(`${await PortalBaseUrl}/create-account/`);
  // fill out the form
  await (await labelled(browser, "Email address")).type(username);
  await (await labelled(browser, "Password")).type(password);
  // submit new user
  await (
    await waitForElement(browser, By.css("button[type='submit']"))
  ).click();

  const code = await verifier.getVerificationCodeForUser(username);
  if (code.length === 0)
    throw new Error("Couldn't getVerificationCodeForUser email!");
  // type code
  await (await labelled(browser, "6-digit code")).type(code);
  // submit code
  await (
    await waitForElement(browser, By.css("button[type='submit']"))
  ).click();
  // wait for successful registration
  await waitForElement(browser, By.visibleText("Email successfully verified"));

  await browser.visit(`${await PortalBaseUrl}/login`);
  await (await labelled(browser, "Email address")).type(username);
  await (await labelled(browser, "Password")).type(password);
  await (
    await waitForElement(browser, By.css("button[type='submit']"))
  ).click();
  await (
    await waitForElement(browser, By.visibleText("Agree and continue"))
  ).click();
  await waitForElement(browser, By.visibleText("Log out"));

  const cookie = (await browser.page.cookies()).find((cookie) => {
    return cookie.name.match(/CognitoIdentityServiceProvider\..*\.accessToken/);
  });
  if (!cookie) {
    throw new Error("Unable to find accessToken cookie");
  }
  return cookie.value;
}

async function setFeatureFlags(browser: Browser) {
  await browser.page.setCookie({
    name: "_ff",
    value: JSON.stringify({
      pfmlTerriyay: true,
      claimantShowAuth: true,
    }),
    url: await PortalBaseUrl,
  });
}

export default (): void => {
  TestData.fromJSON<LSTSimClaim>(`../${dataBaseUrl}/claims.json`).filter(
    (line) => line.scenario === scenario
  );
  steps.forEach((action) => {
    step(action.name, action.test as StepFunction<unknown>);
  });
};
