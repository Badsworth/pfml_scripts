import { getNotificationSubject } from "../../actions/email";
import { fineos, portal, email, fineosPages } from "../../actions";
import { Submission } from "../../../src/types";
import { extractLeavePeriod } from "../../../src/util/claims";
import { assertValidClaim } from "../../../src/util/typeUtils";
import { format, addDays, parse } from "date-fns";

describe("Post-approval (notifications/notices)", () => {
  const submit = it("Given a fully approved claim", () => {
    fineos.before();
    // Submit a claim via the API, including Employer Response.
    cy.task("generateClaim", "CHAP_ER").then((claim) => {
      cy.stash("claim", claim);
      cy.task("submitClaimToAPI", claim).then((response) => {
        cy.stash("submission", {
          application_id: response.application_id,
          fineos_absence_id: response.fineos_absence_id,
          timestamp_from: Date.now(),
        });

        const claimPage = fineosPages.ClaimPage.visit(
          response.fineos_absence_id
        );
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
        claimPage.triggerNotice("Preliminary Designation");
      });
    });
  });

  const extension = it("Agent extends the claim", () => {
    cy.dependsOnPreviousPass([submit]);
    fineos.before();
    cy.unstash<DehydratedClaim>("claim").then(({ claim, documents }) => {
      cy.unstash<Submission>("submission").then(({ fineos_absence_id }) => {
        const [startDate, endDate] = extractLeavePeriod(claim);
        const newStartDate = format(
          addDays(new Date(endDate), 1),
          "MM/dd/yyyy"
        );
        const newEndDate = format(addDays(new Date(endDate), 8), "MM/dd/yyyy");
        cy.stash("extensionLeaveDates", [startDate, newEndDate]);

        const claimPage = fineosPages.ClaimPage.visit(fineos_absence_id);
        claimPage.benefitsExtension((benefitsExtension) =>
          benefitsExtension.extendLeave(newStartDate, newEndDate)
        );
        claimPage.adjudicate((adjudication) => {
          adjudication.evidence((evidence) => {
            for (const document of documents) {
              evidence.receive(document.document_type);
            }
          });
        });
      });
    });
  });

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
              portal.loginLeaveAdmin(claim.employer_fein);
              portal.selectClaimFromEmployerDashboard(
                submission.fineos_absence_id
              );
              const portalFormatStart = format(new Date(startDate), "M/d/yyyy");
              const portalFormatEnd = format(
                parse(endDate, "MM/dd/yyyy", new Date(endDate)),
                "M/d/yyyy"
              );
              // This introduces some backward compatibility until we figure out the differences in ERI trigger
              // between defferent envs. @see https://lwd.atlassian.net/browse/PFMLPB-1736
              // Wait till the redirects are over and we are viewing the claim.
              cy.url().should("not.include", "dashboard");
              cy.contains(`${claim.first_name} ${claim.last_name}`);
              // Check by url if we can review the claim
              cy.contains(
                "Are you the right person to respond to this application?"
              );
              cy.contains("Yes").click();
              cy.contains("Agree and submit").click();
              cy.findByText(
                // There's a strange unicode hyphen at this place.
                /This is your employe(.*)s expected leave schedule/
              )
                .next()
                .should(
                  "contain.text",
                  `${portalFormatStart} to ${portalFormatEnd}`
                );
              portal.respondToLeaveAdminRequest(false, true, false);
            }
          );
        });
      });
    }
  );
  it(
    "As a leave admin, I should receive a notification regarding the time added to the claim",
    { retries: 0 },
    () => {
      cy.dependsOnPreviousPass([extension]);
      cy.unstash<Submission>("submission").then((submission) => {
        cy.unstash<DehydratedClaim>("claim").then(({ claim }) => {
          const subjectClaimant = getNotificationSubject(
            `${claim.first_name} ${claim.last_name}`,
            "extension of benefits"
          );
          email
            .getEmails(
              {
                address: "gqzap.notifications@inbox.testmail.app",
                subject: subjectClaimant,
                messageWildcard: submission.fineos_absence_id,
                timestamp_from: submission.timestamp_from,
                debugInfo: { "Fineos Claim ID": submission.fineos_absence_id },
              },
              70000
            )
            .then(() => {
              cy.contains(submission.fineos_absence_id);
            });
        });
      });
    }
  );
});
