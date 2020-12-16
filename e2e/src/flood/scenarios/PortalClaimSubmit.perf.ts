import { StepFunction, TestData, Browser, step, By, ENV } from "@flood/element";
import { DocumentUploadRequest } from "../../api";
import { FineosUserType } from "../../simulation/types";
import { checkApprovalReadiness } from "../tasks/ApproveClaim";
import * as Conf from "../config";
import * as Util from "../helpers";

let authToken: string;
let applicationId: string;
let fineosId: string;

export const settings = Conf.globalElementSettings;
export const scenario: Conf.LSTScenario = "PortalClaimSubmit";
export const steps = [
  {
    name: "Register and login",
    test: async (browser: Browser): Promise<void> => {
      await setFeatureFlags(browser);
      const emailVerifier = await Util.getMailVerifier(browser);
      const { username, password } = emailVerifier.getCredentials();
      await register(browser, emailVerifier, username, password);
      authToken = await login(browser, username, password);
    },
  },
  {
    name: "Create, Update and Submit new application",
    test: async (browser: Browser, data: Conf.LSTSimClaim): Promise<void> => {
      const { claim, documents } = data;
      const { leave_details } = claim;
      // Attempt at simulating portal's consequent small patch requests
      const claimParts: (Partial<Conf.LSTSimClaim["claim"]> | string)[] = [
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
      ];
      // Execute all claim steps in queue and in order
      for (const claimPart of claimParts) {
        let reqOptions: RequestInit;
        let res;
        if (typeof claimPart === "string") {
          switch (claimPart) {
            // request to create application
            case "create":
              reqOptions = Util.getRequestOptions(authToken, "POST");
              res = await Util.evalFetch(
                browser,
                `${await Conf.APIBaseUrl}/applications`,
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
              reqOptions = Util.getRequestOptions(authToken, "POST");
              res = await Util.evalFetch(
                browser,
                `${await Conf.APIBaseUrl}/applications/${applicationId}/submit_application`,
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
                reqOptions = Util.getRequestOptions(authToken, "POST", {}, {});
                const docBody: DocumentUploadRequest = {
                  document_type: Util.getDocumentType(document),
                  description: "LST - Direct to API",
                  file: await readFile(Conf.documentUrl),
                  mark_evidence_received: true,
                  name: `${document.type}.pdf`,
                };
                res = await Util.evalFetch(
                  browser,
                  `${await Conf.APIBaseUrl}/applications/${applicationId}/documents`,
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
              reqOptions = Util.getRequestOptions(authToken, "POST");
              res = await Util.evalFetch(
                browser,
                `${await Conf.APIBaseUrl}/applications/${applicationId}/complete_application`,
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
            default:
              break;
          }
        } else {
          reqOptions = Util.getRequestOptions(authToken, "PATCH", claimPart);
          res = await Util.evalFetch(
            browser,
            `${await Conf.APIBaseUrl}/applications/${applicationId}`,
            reqOptions
          );
          if (res.status_code !== 200) {
            throw new Error(
              `Unable to update application: ${JSON.stringify(res, null, 2)}`
            );
          }
          console.info("Updated application", res.status_code);
        }
        await Util.waitForRealTimeSim(browser, data, 1 / claimParts.length);
      }
    },
  },
  {
    name: "Verify that Outstanding Requirement was generated",
    test: async (browser: Browser, data: Conf.LSTSimClaim): Promise<void> => {
      const receiveDocumentsStep = receiveDocuments(fineosId);
      console.info(receiveDocumentsStep.name);
      await receiveDocumentsStep.test(browser, data);
    },
  },
  {
    name: "Fill employer response as point of contact",
    test: async (browser: Browser, data: Conf.LSTSimClaim): Promise<void> => {
      const employerResponseStep = employerResponse(fineosId);
      console.info(employerResponseStep.name);
      await employerResponseStep.test(browser, data);
    },
  },
  {
    name: "Assign tasks to specific Agent",
    test: async (browser: Browser, data: Conf.LSTSimClaim): Promise<void> => {
      if (!ENV.FLOOD_LOAD_TEST) {
        const assignTasksStep = Util.assignTasks(fineosId);
        console.info(assignTasksStep.name);
        await assignTasksStep.test(browser, data);
      }
    },
  },
];

async function register(
  browser: Browser,
  verifier: Util.TestMailVerificationFetcher,
  username: string,
  password: string
) {
  // go to registration page
  await browser.visit(`${await Conf.PortalBaseUrl}/create-account/`);
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
  await browser.visit(`${await Conf.PortalBaseUrl}/login`);
  await (await Util.labelled(browser, "Email address")).type(username);
  await (await Util.labelled(browser, "Password")).type(password);
  await (
    await Util.waitForElement(browser, By.css("button[type='submit']"))
  ).click();
  await browser.waitForNavigation();
  const agreeTerms = await browser.maybeFindElement(
    By.visibleText("Agree and continue")
  );
  if (agreeTerms) {
    agreeTerms.click();
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

function receiveDocuments(
  fineosId: string,
  search = true,
  agent: FineosUserType = "SAVILINX"
): Conf.StoredStep {
  return {
    name: `Receive ${fineosId}'s documents as ${agent} Agent`,
    test: async (browser: Browser, data: Conf.LSTSimClaim): Promise<void> => {
      if (search) {
        await browser.visit(await Conf.getFineosBaseUrl(agent));
        await browser.setViewport({ width: 1920, height: 1080 });
        // search for particular by id
        const casesMenu = await Util.waitForElement(
          browser,
          By.css("a[aria-label='Cases']")
        );
        await casesMenu.click();
        const caseTab = await Util.waitForElement(
          browser,
          By.css("[keytipnumber='4']")
        );
        await caseTab.click();
        const caseNumberInput = await Util.labelled(browser, "Case Number");
        await browser.type(caseNumberInput, fineosId);
        const searchButton = await Util.waitForElement(
          browser,
          By.css("input[type='submit'][value*='Search']")
        );
        await searchButton.click();
        await browser.waitForNavigation();
      }
      // Checks claim approval readiness and receive documents.
      await checkApprovalReadiness().test(browser, data);
      // Checks whether Employer Response has been requested.
      const outstandingRequirementsTab = await Util.waitForElement(
        browser,
        By.visibleText("Outstanding Requirements")
      );
      await browser.click(outstandingRequirementsTab);
      try {
        await Util.waitForElement(
          browser,
          By.css("tr td[title='Employer Confirmation of Leave Data']")
        );
      } catch (e) {
        // workaround from ER Demo - adds ER manually
        console.info("\nImplementing Employer Response workaround\n");
        const addButton = await Util.waitForElement(
          browser,
          By.visibleText("Add")
        );
        await addButton.click();
        const categorySelect = await Util.labelled(
          browser,
          "Selected category"
        );
        await browser.selectByText(categorySelect, "Employer Confirmation");
        const typeSelect = await Util.labelled(browser, "Selected type");
        await browser.selectByText(
          typeSelect,
          "Employer Confirmation of Leave Data"
        );
        let okButton = await Util.waitForElement(
          browser,
          By.css("input[type='submit'][value='Ok']")
        );
        await browser.click(okButton);
        okButton = await Util.waitForElement(
          browser,
          By.css("#footerButtonsBar input[type='submit'][value='OK']")
        );
      }
    },
  };
}

function employerResponse(fineosId: string): Conf.StoredStep {
  return {
    name: `Point of Contact responds to "${fineosId}"`,
    test: async (browser: Browser, data: Conf.LSTSimClaim): Promise<void> => {
      await setFeatureFlags(browser);
      // Log in on Portal as Leave Admin
      authToken = await login(
        browser,
        await Conf.config("E2E_EMPLOYER_PORTAL_USERNAME"),
        await Conf.config("E2E_EMPLOYER_PORTAL_PASSWORD")
      );

      // Review submited application via direct link on Portal
      await browser.visit(
        `${await Conf.PortalBaseUrl}/employers/applications/new-application/?absence_id=${fineosId}`
      );

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

export default (): void => {
  TestData.fromJSON<Conf.LSTSimClaim>(
    `../${Conf.dataBaseUrl}/claims.json`
  ).filter((line) => line.scenario === scenario);

  steps.forEach((action) => {
    step(action.name, action.test as StepFunction<unknown>);
  });
};

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
    }),
    url: await Conf.PortalBaseUrl,
  });
}
