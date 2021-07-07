import { portal, fineos, fineosPages } from "../../actions";
import { getFineosBaseUrl, getLeaveAdminCredentials } from "../../config";
import {
  Submission,
  ValidEmployerBenefit,
  ValidOtherIncome,
} from "../../../src/types";
import { assertValidClaim } from "../../../src/util/typeUtils";
import { getSubmissionFromApiResponse } from "../../../src/util/claims";
import { generateEmployerBenefits } from "../../../src/generation/EmployerBenefits";
import { clickBottomWidgetButton } from "../../actions/fineos";
import { generateOtherIncomes } from "../../../src/generation/OtherIncomes";
import { config } from "../../actions/common";
(config("FINEOS_HAS_UPDATED_EFORMS") === "true" ? xdescribe : describe)(
  "Legacy employer benefit",
  () => {
    const claimSubmission = it("Given a submitted claim", () => {
      cy.task("generateClaim", "BHAP1").then((claim) => {
        cy.task("submitClaimToAPI", claim).then((response) => {
          cy.stash("claim", claim);
          cy.stash("submission", getSubmissionFromApiResponse(response));
          assertValidClaim(claim.claim);
          cy.stash("benefits", [
            ...generateEmployerBenefits(
              [
                {
                  benefit_amount_dollars: 100,
                  benefit_amount_frequency: "Per Week",
                  benefit_type: "Family or medical leave insurance",
                },
                {
                  benefit_amount_dollars: 200,
                  benefit_amount_frequency: "Per Month",
                  benefit_type: "Permanent disability insurance",
                },
              ],
              claim.claim.leave_details
            ),
            ...generateOtherIncomes(
              [
                {
                  income_amount_dollars: 300,
                  income_amount_frequency: "Per Day",
                  income_type: "SSDI",
                },
              ],
              claim.claim.leave_details
            ),
          ]);
        });
      });
    });
    const reportBenefits = it(
      "Claimant can contact the call center & report an employer benefit",
      { baseUrl: getFineosBaseUrl() },
      () => {
        cy.dependsOnPreviousPass([claimSubmission]);
        fineos.before();
        cy.visit("/");
        cy.unstash<DehydratedClaim>("claim").then(({ claim, documents }) => {
          cy.unstash<Submission>("submission").then((submission) => {
            cy.unstash<ValidEmployerBenefit[]>("benefits").then((benefits) => {
              assertValidClaim(claim);
              fineosPages.ClaimPage.visit(submission.fineos_absence_id)
                .documents((docsPage) => {
                  docsPage.submitLegacyEmployerBenefits(benefits);
                })
                .adjudicate((adjudication) => {
                  adjudication.evidence((evidencePage) =>
                    documents.forEach(({ document_type }) =>
                      evidencePage.receive(document_type)
                    )
                  );
                });
            });
          });
        });
      }
    );
    const benefitAmendment = it("LA can view and amend the reported benefits", () => {
      portal.before({ claimantShowOtherLeaveStep: false });
      cy.dependsOnPreviousPass([claimSubmission, reportBenefits]);
      cy.unstash<DehydratedClaim>("claim").then(({ claim }) => {
        cy.unstash<Submission>("submission").then((submission) => {
          cy.unstash<
            [ValidEmployerBenefit, ValidEmployerBenefit, ValidOtherIncome]
          >("benefits").then((benefits) => {
            assertValidClaim(claim);
            portal.login(getLeaveAdminCredentials(claim.employer_fein));
            portal.visitActionRequiredERFormPage(submission.fineos_absence_id);
            const [benefit1, benefit2, nonERBenefit] = benefits;
            // Check we have the employer benefits from fineos
            portal.assertEmployerBenefit(benefit1);
            portal.assertEmployerBenefit(benefit2);
            // Assert the non employer benefit is not here
            cy.contains("table", "Benefit type").within(($table) => {
              expect($table.html()).not.to.contain(nonERBenefit.income_type);
            });
            // Amend the benefit amount.
            portal.amendLegacyBenefit(benefit1, {
              ...benefit1,
              benefit_amount_dollars: 500,
            });
            portal.amendLegacyBenefit(benefit2, {
              ...benefit2,
              benefit_amount_dollars: 600,
            });
            // Approve the claim
            portal.respondToLeaveAdminRequest(false, true, true, false);
          });
        });
      });
    });
    it(
      "Agent can see employer response amendments",
      { baseUrl: getFineosBaseUrl() },
      () => {
        cy.dependsOnPreviousPass([
          claimSubmission,
          reportBenefits,
          benefitAmendment,
        ]);
        fineos.before();
        cy.visit("/");
        cy.unstash<DehydratedClaim>("claim").then(({ claim }) => {
          cy.unstash<Submission>("submission").then((submission) => {
            cy.unstash<
              [ValidEmployerBenefit, ValidEmployerBenefit, ValidOtherIncome]
            >("benefits").then(() => {
              assertValidClaim(claim);
              fineosPages.ClaimPage.visit(
                submission.fineos_absence_id
              ).documents((docsPage) => {
                // Check the employer response is there.
                docsPage.assertDocumentExists(
                  `Employer Response to Leave Request`
                );
                cy.findByText(`Employer Response to Leave Request`).click();
                cy.wait(200);
                // Check the amendment is there.
                cy.findByDisplayValue("500.00").should("be.visible");
                cy.findByDisplayValue("600.00").should("be.visible");

                clickBottomWidgetButton();
              });
            });
          });
        });
      }
    );
  }
);
