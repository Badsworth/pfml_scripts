import { StepFunction, TestData, Browser, step, By } from "@flood/element";
import { DocumentUploadRequest } from "../../api";
import {
  globalElementSettings as settings,
  PortalBaseUrl,
  APIBaseUrl,
  dataBaseUrl,
  LSTSimClaim,
  LSTScenario,
  config,
} from "../config";
import {
  labelled,
  waitForElement,
  waitForRealTimeSim,
  getRequestOptions,
  getDocumentType,
  evalFetch,
} from "../helpers";
import fs from "fs";

let authToken: string;
let applicationId: string;

const pdfDocument = fs.readFileSync(
  "src/flood/data/pilot3/documents/219-45-4343.MASSID.pdf"
);

export { settings };
export const scenario: LSTScenario = "PortalClaimSubmit";
export const steps = [
  {
    name: "Login in Portal",
    test: async (browser: Browser): Promise<void> => {
      // Fetch an auth token by performing a browser-based login.
      await browser.page.setCookie({
        name: "_ff",
        value: JSON.stringify({
          pfmlTerriyay: true,
        }),
        url: await PortalBaseUrl,
      });
      await browser.visit(await PortalBaseUrl);
      await (await labelled(browser, "Email address")).type(
        await config("E2E_PORTAL_USERNAME")
      );
      await (await labelled(browser, "Password")).type(
        await config("E2E_PORTAL_PASSWORD")
      );
      await (
        await waitForElement(browser, By.css("button[type='submit']"))
      ).click();
      await waitForElement(browser, By.visibleText("Log out"));
      const cookie = (await browser.page.cookies()).find((cookie) => {
        return cookie.name.match(
          /CognitoIdentityServiceProvider\..*\.accessToken/
        );
      });
      if (!cookie) {
        throw new Error("Unable to find accessToken cookie");
      }
      authToken = cookie.value;
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
        // { temp: { has_employer_benefits: false } },
        // { temp: { has_other_incomes: false } },
        // { temp: { has_previous_leaves: false } },
        "submit",
        {
          payment_preferences: claim.payment_preferences,
        },
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
              reqOptions = getRequestOptions(authToken, "POST");
              res = await evalFetch(
                browser,
                `${await APIBaseUrl}/applications`,
                reqOptions
              );
              if (!res.data || !res.data.application_id) {
                throw new Error(
                  `Unable to create application: ${JSON.stringify(res)}`
                );
              }
              applicationId = res.data.application_id;
              console.info("Created application", { authToken, applicationId });
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
                  `Unable to submit application: ${JSON.stringify(res)}`
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
                  file: pdfDocument,
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
                    `Unable to upload document: ${JSON.stringify(res)}`
                  );
                }
                console.info("Uploaded document", res);
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
                  `Unable to complete application: ${JSON.stringify(res)}`
                );
              }
              console.info("Completed application", res.status_code);
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
              `Unable to update application: ${JSON.stringify(res)}`
            );
          }
          console.info("Updated application", res.status_code);
        }
        await waitForRealTimeSim(browser, data, 1 / steps.length);
      }
    },
  },
];

export default (): void => {
  TestData.fromJSON<LSTSimClaim>(`../${dataBaseUrl}/claims.json`).filter(
    (line) => line.scenario === scenario
  );
  steps.forEach((action) => {
    step(action.name, action.test as StepFunction<unknown>);
  });
};
