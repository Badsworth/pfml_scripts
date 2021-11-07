import { getNotificationSubject } from "../../../actions/email";
import { fineos, portal, email, fineosPages } from "../../../actions";
import { Submission } from "../../../../src/types";
import { extractLeavePeriod } from "../../../../src/util/claims";
import { assertValidClaim } from "../../../../src/util/typeUtils";
import { format, addDays, parse } from "date-fns";
import {waitForAjaxComplete} from "../../../actions/fineos";

describe("Post-approval (notifications/notices)", () => {
  const credentials: Credentials = {
    username: Cypress.env("E2E_PORTAL_USERNAME"),
    password: Cypress.env("E2E_PORTAL_PASSWORD"),
  };

  const submit = it("Given a fully approved claim", () => {
    fineos.before();
    // Submit a claim via the API, including Employer Response.
    cy.task("generateClaim", "CHAP_ER").then((claim) => {
      cy.task("submitClaimToAPI", {
        ...claim,
        credentials,
      }).then((response) => {
        cy.stash("claim", claim);
        cy.stash("submission", {
          application_id: response.application_id,
          fineos_absence_id: response.fineos_absence_id,
          timestamp_from: Date.now(),
        });

        const claimPage = fineosPages.ClaimPage.visit(
          response.fineos_absence_id
        );
        claimPage.triggerNotice("Preliminary Designation");
        fineos.onTab("Absence Hub");
        claimPage.adjudicate((adjudication) => {
          adjudication.evidence((evidence) => {
            // Receive and approve all of the documentation for the claim.
            claim.documents.forEach((document) => {
              evidence.receive(document.document_type);
            });
          });
          adjudication.certificationPeriods((certificationPeriods) =>
            certificationPeriods.prefill()
          );
          adjudication.acceptLeavePlan();
        });
        claimPage.approve();
      });
    });
  });

  const extension = it("Should process an extension", { retries: 0 }, () => {
    cy.dependsOnPreviousPass([submit]);
    fineos.before();
    cy.unstash<Submission>("submission").then((submission) => {
      cy.unstash<DehydratedClaim>("claim").then((claim) => {
        assertValidClaim(claim.claim);
        const [, endDate] = extractLeavePeriod(claim.claim);
        const newStartDate = format(
          addDays(new Date(endDate), 1),
          "MM/dd/yyyy"
        );
        console.log(submission);
        const newEndDate = format(addDays(new Date(endDate), 8), "MM/dd/yyyy");
        cy.stash("extensionLeaveDates", [newStartDate, newEndDate]);

        const claimPage = fineosPages.ClaimPage.visit(
          submission.fineos_absence_id
        );
        claimPage.benefitsExtension((benefitsExtension) =>
          benefitsExtension.extendLeave(newStartDate, newEndDate)
        );
      });
    });
  });

  const approval = it(
    "Should approve extension as CSR rep.",
    { retries: 0 },
    () => {
      cy.dependsOnPreviousPass([extension]);
      fineos.before();
      cy.unstash<Submission>("submission").then((submission) => {
        cy.unstash<DehydratedClaim>("claim").then((claim) => {
          const claimPage = fineosPages.ClaimPage.visit(
            submission.fineos_absence_id
          );
          claimPage.adjudicate((adjudication) => {
            adjudication.evidence((evidence) => {
              // Receive all of the claim documentation.
              claim.documents.forEach((document) => {
                evidence.receive(document.document_type);
              });
            });
            adjudication.certificationPeriods((cert) => cert.prefill());
            adjudication.acceptLeavePlan();
          });
          claimPage.outstandingRequirements((outstandingRequirements) => {
            outstandingRequirements.complete(
              "Received",
              "Complete Employer Confirmation",
              true
            );
          });
          claimPage.approve();
        });
      });
    }
  );
  it(
    "Should display updated leave period fnd status or the claimant",
    { retries: 0 },
    () => {
      cy.dependsOnPreviousPass([approval]);
      portal.before();
      cy.unstash<Submission>("submission").then((submission) => {
        cy.unstash<string[]>("extensionLeaveDates").then(
          ([startDate, endDate]) => {
            const portalFormatStart = format(
              new Date(startDate),
              "MMMM d, yyyy"
            );
            const portalFormatEnd = format(
              parse(endDate, "MM/dd/yyyy", new Date(endDate)),
              "MMMM d, yyyy"
            );
            portal.login(credentials);
            portal.claimantGoToClaimStatus(submission.fineos_absence_id);
            portal.claimantAssertClaimStatus([
              {
                leave: "Care for a Family Member",
                status: "Approved",
              },
            ]);
            cy.findAllByText(/Continuous leave/)
              .eq(1)
              .next()
              .should(
                "contain.text",
                `From ${portalFormatStart} to ${portalFormatEnd}`
              );
          }
        );
      });
    }
  );

  it(
    "Should generate an (Extension) notification for the Leave Administrator",
    { retries: 0 },
    () => {
      cy.dependsOnPreviousPass([extension]);
      cy.unstash<Submission>("submission").then((submission) => {
        const subjectClaimant = getNotificationSubject("extension of benefits");
        email
          .getEmails(
            {
              address: "gqzap.notifications@inbox.testmail.app",
              subjectWildcard: subjectClaimant,
              messageWildcard: submission.fineos_absence_id,
              timestamp_from: submission.timestamp_from,
              debugInfo: { "Fineos Claim ID": submission.fineos_absence_id },
            },
            60000
          )
          .then(() => {
            cy.contains(submission.fineos_absence_id);
          });
      });
    }
  );

  it("Check to see if the O/R buttons are enabled to Complete, Suppress, & Remove", () => {
    cy.dependsOnPreviousPass([submit, extension, approval]);
    fineos.before();
    cy.unstash<Submission>("submission").then((submission) => {
      const claimPage = fineosPages.ClaimPage.visit(
        submission.fineos_absence_id
      );
      claimPage.outstandingRequirements((outstanding_requirement) => {
        outstanding_requirement.add();
        waitForAjaxComplete();
        outstanding_requirement.complete(
          "Received",
          "Complete Employer Confirmation",
          true
        );
        waitForAjaxComplete();
        outstanding_requirement.reopen(true);
        waitForAjaxComplete();
        outstanding_requirement.suppress(
          "Auto-Suppressed",
          "Suppress Employer Confirmation",
          true
        );
        waitForAjaxComplete();
        outstanding_requirement.reopen(true);
        waitForAjaxComplete();
        outstanding_requirement.removeOR(true);
      })
    });
  });
});
