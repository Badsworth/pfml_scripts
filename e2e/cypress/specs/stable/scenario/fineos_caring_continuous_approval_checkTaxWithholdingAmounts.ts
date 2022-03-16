import { fineos, fineosPages } from "../../../actions";
import { assertValidClaim } from "../../../../src/util/typeUtils";
import { Submission } from "../../../../src/types";
import * as faker from "faker";
import { add, format } from "date-fns";
import { config } from "../../../actions/common";

describe("Approve claim created in Fineos, then check Tax Withholding deductions (SIT/FIT)", () => {
  const fineosSubmission =
    it("Given a fully approved claim created in Fineos", () => {
      fineos.before();
      cy.task("generateClaim", "CARE_TAXES").then((claim) => {
        cy.stash("claim", claim);
        assertValidClaim(claim.claim);
        const customer = fineosPages.ClaimantPage.visit(
          claim.claim.tax_identifier
        );
        customer.addAddress({
          city: faker.address.city(),
          state: "MA",
          zip: faker.address.zipCode(),
          line_1: faker.address.streetAddress(),
        });
        if (config("HAS_APRIL_UPGRADE") === "true") {
          customer.editPersonalIdentification(
            {
              date_of_birth: format(
                faker.date.between(
                  add(new Date(), { years: -65 }),
                  add(new Date(), { years: -18 })
                ),
                "MM/dd/yyyy"
              ),
            },
            true
          );
        } else {
          customer.editPersonalIdentification(
            {
              date_of_birth: format(
                faker.date.between(
                  add(new Date(), { years: -65 }),
                  add(new Date(), { years: -18 })
                ),
                "MM/dd/yyyy"
              ),
            },
            false
          );
        }
        customer
          .createNotification(claim.claim, claim.is_withholding_tax)
          .then((fineos_absence_id) => {
            cy.log(fineos_absence_id);
            cy.stash("submission", {
              fineos_absence_id: fineos_absence_id,
              timestamp_from: Date.now(),
            });
            const claimPage = fineosPages.ClaimPage.visit(fineos_absence_id)
              .documents((docs) => {
                claim.documents.forEach((document) =>
                  docs
                    .uploadDocument(document.document_type)
                    .assertDocumentUploads(document.document_type)
                );
              })
              .adjudicate((adjudication) => {
                adjudication
                  .evidence((evidence) =>
                    claim.documents.forEach(({ document_type }) =>
                      evidence.receive(document_type)
                    )
                  )
                  .certificationPeriods((certificaitonPeriods) =>
                    certificaitonPeriods.prefill()
                  );
              })
              .outstandingRequirements((outstandingRequirements) =>
                outstandingRequirements.complete(
                  "Received",
                  "Complete Employer Confirmation",
                  true
                )
              );
            if (config("HAS_APRIL_UPGRADE") === "true") {
              claimPage.approve("Approved", true);
            } else {
              claimPage.approve("Approved", false);
            }
          });
      });
    });

  const payments = it(
    "Should calculate the proper withholding amounts for SIT/FIT",
    { retries: 0 },
    () => {
      cy.dependsOnPreviousPass([fineosSubmission]);
      fineos.before();
      cy.unstash<Submission>("submission").then(({ fineos_absence_id }) => {
        fineosPages.ClaimPage.visit(fineos_absence_id).paidLeave(
          (paidLeavePage) => {
            paidLeavePage.assertAmountsPending([
              { net_payment_amount: 196.15 },
              { net_payment_amount: 23.08 },
              { net_payment_amount: 11.54 },
            ]);
          }
        );
      });
    }
  );

  it("SIT/FIT opt-in cannot be modified once payments are generated", () => {
    cy.dependsOnPreviousPass([payments]);
    fineos.before();
    cy.unstash<Submission>("submission").then((submission) => {
      const claimPage = fineosPages.ClaimPage.visit(
        submission.fineos_absence_id
      );
      if (config("HAS_APRIL_UPGRADE") === "true") {
        claimPage.reviewClaim(true);
        claimPage.adjudicateUpgrade((adjudicationPage) => {
          adjudicationPage.paidBenefits((paidBenefitsPage) => {
            paidBenefitsPage.assertSitFitOptIn(true);
            paidBenefitsPage.edit();
            cy.get(
              'input[type="checkbox"][name$="SITFITOptIn_CHECKBOX"]'
            ).should("be.disabled");
            fineos.clickBottomWidgetButton("Cancel");
          });
          adjudicationPage.acceptLeavePlan();
        });
        claimPage.approve("Approved", true);
      } else {
        claimPage.reviewClaim(false);
        claimPage.adjudicate((adjudicationPage) => {
          adjudicationPage.editPlanDecision("Undecided");
          adjudicationPage.paidBenefits((paidBenefitsPage) => {
            paidBenefitsPage.assertSitFitOptIn(true);
            paidBenefitsPage.edit();
            cy.get(
              'input[type="checkbox"][name$="SITFITOptIn_CHECKBOX"]'
            ).should("be.disabled");
            fineos.clickBottomWidgetButton("Cancel");
          });
          adjudicationPage.acceptLeavePlan(); // restore claim to it's approved status
        });
        claimPage.approve("Approved", false);
      }
    });
  });
});
