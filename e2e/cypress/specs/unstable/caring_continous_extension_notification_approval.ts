import { getNotificationSubject } from "../../actions/email";
import { fineos, portal, fineosPages } from "../../actions";
import { getFineosBaseUrl, getLeaveAdminCredentials } from "../../config";
import { Submission } from "../../../src/types";
import { extractLeavePeriod } from "../../../src/util/claims";
import { assertValidClaim } from "../../../src/util/typeUtils";
import { format, addDays, parse } from "date-fns";

describe("Post-approval (notifications/notices)", { retries: 0 }, () => {
  const credentials: Credentials = {
    username: Cypress.env("E2E_PORTAL_USERNAME"),
    password: Cypress.env("E2E_PORTAL_PASSWORD"),
  };
  const extension = it(
    "Given a fully approved claim, a CSR agent can extend the claim's leave dates",
    { baseUrl: getFineosBaseUrl() },
    () => {
      fineos.before();
      cy.visit("/");
      // Submit a claim via the API, including Employer Response.
      cy.task("generateClaim", "CHAP_ER").then((claim) => {
        cy.stash("claim", claim);
        cy.task("submitClaimToAPI", {
          ...claim,
          credentials,
        }).then((response) => {
          if (!response.fineos_absence_id) {
            throw new Error("Response contained no fineos_absence_id property");
          }
          const [startDate, endDate] = extractLeavePeriod(claim.claim);
          cy.stash("submission", {
            application_id: response.application_id,
            fineos_absence_id: response.fineos_absence_id,
            timestamp_from: Date.now(),
          });
          const newStartDate = format(
            addDays(new Date(endDate), 1),
            "MM/dd/yyyy"
          );
          const newEndDate = format(
            addDays(new Date(endDate), 8),
            "MM/dd/yyyy"
          );
          cy.stash("extensionLeaveDates", [startDate, newEndDate]);
          const claimPage = fineosPages.ClaimPage.visit(
            response.fineos_absence_id
          );
          claimPage.adjudicate((adjudication) => {
            adjudication.evidence((evidence) => {
              for (const document of claim.documents) {
                evidence.receive(document.document_type);
              }
            });
            cy.wait("@ajaxRender");
            cy.wait(150);
            adjudication.certificationPeriods((certificationPeriods) =>
              certificationPeriods.prefill()
            );
            adjudication.acceptLeavePlan();
          });
          claimPage.tasks((task) => {
            task.close("Caring Certification Review");
            task.close("ID Review");
          });
          claimPage.approve();
          claimPage.benefitsExtension((benefitsExtension) =>
            benefitsExtension.extendLeave(newStartDate, newEndDate)
          );
          // Including this visit helps to avoid the "Whoops there is no test to run" message by Cypress.
          cy.visit("/");
          const claimAfterExtension = fineosPages.ClaimPage.visit(
            response.fineos_absence_id
          );
          claimAfterExtension.adjudicate((adjudication) => {
            adjudication.evidence((evidence) => {
              for (const document of claim.documents) {
                evidence.receive(document.document_type);
              }
            });
          });
        });
      });
    }
  );

  it(
    "Leave admin will see leave periods for the claim that reflect the extension",
    { retries: 0 },
    () => {
      cy.dependsOnPreviousPass([extension]);
      portal.before();
      cy.visit("/");
      cy.unstash<DehydratedClaim>("claim").then(({ claim }) => {
        cy.unstash<Submission>("submission").then((submission) => {
          cy.unstash<string[]>("extensionLeaveDates").then(
            ([startDate, endDate]) => {
              assertValidClaim(claim);
              portal.login(getLeaveAdminCredentials(claim.employer_fein));
              portal.selectClaimFromEmployerDashboard(
                submission.fineos_absence_id,
                "--"
              );
              const portalFormatStart = format(new Date(startDate), "M/d/yyyy");
              const portalFormatEnd = format(
                parse(endDate, "MM/dd/yyyy", new Date(endDate)),
                "M/d/yyyy"
              );
              portal.assertLeaveDatesAsLA(portalFormatStart, portalFormatEnd);
            }
          );
        });
      });
    }
  );
  it("As a leave admin, I should receive a notification regarding the time added to the claim", () => {
    cy.dependsOnPreviousPass([extension]);
    cy.unstash<Submission>("submission").then(
      ({ timestamp_from, fineos_absence_id }) => {
        cy.unstash<DehydratedClaim>("claim").then((claim) => {
          const subject = getNotificationSubject(
            `${claim.claim.first_name} ${claim.claim.last_name}`,
            "extension of benefits"
          );
          cy.task<Email[]>(
            "getEmails",
            {
              address: "gqzap.notifications@inbox.testmail.app",
              subject,
              timestamp_from: timestamp_from,
            },
            { timeout: 360000 }
          ).then((emails) => {
            expect(emails[0].html).to.contain(fineos_absence_id);
          });
        });
      }
    );
  });
});
