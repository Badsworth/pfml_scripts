import { Application } from "./types";
import {
  ChecklistPage,
  LoginPage,
  ReviewPage,
  ConfirmPage,
  SuccessPage,
} from "./pages";

/**
 * This file contains flows for various End to End actions.
 *
 * We keep the flows here so they can be shared between E2E and business simulation tests.
 * Most of the logic and selectors will ultimately be extracted into page classes though.
 */

const dummySubmit = () => {
  // Intentional no-op.
};
/**
 * Submits
 * @param application
 */
export function submitClaim(
  application: Application,
  setApplicationId: (id: string) => void = dummySubmit
): void {
  new LoginPage().login(application);
  cy.contains("button", "Create an application").click();
  new ChecklistPage()
    .verifyIdentity(application)
    .submitClaim(application)
    .enterEmployerInfo(application)
    .reportOtherBenefits(application)
    .addPaymentInfo(application)
    .reviewAndSubmit();
  new ReviewPage().confirmInfo();
  new ConfirmPage().agreeAndSubmit();
  cy.url()
    .then((url) => {
      // Extract the Claim ID from the URL and stash it.
      const appId = new URL(url).searchParams.get("claim_id");
      if (appId) {
        setApplicationId(appId);
      }
    })
    .as("applicationId");
  new SuccessPage().returnToDashboard();
}

/**
 * Validates a claim as a CSR user.
 * @param application
 * @param claimId The Claim ID, as reported from the portal.
 */
export function searchForClaimInFineos(
  application: Application,
  claimId: string
): void {
  // @todo: We'll want to move this into page classes when we have more complex Fineos operations
  // to do. For now, it's just roughed in here.
  cy.visit("/");
  cy.get('a[aria-label="Parties"]').click();
  cy.labelled("Identification Number").type(
    application.ssn.split("-").join("")
  );
  cy.get('input[type="submit"][value="Search"]').click();
  cy.contains("table.WidgetPanel", "Person Search Results").within(() => {
    cy.contains(".ListTable tr", `xxxxx${application.ssn.slice(-4)}`).click();
  });
  cy.contains('input[type="submit"]', "OK").click();
  cy.contains(".TabStrip td", "Cases").click({ force: true });
  cy.get(`[title="PFML API ${claimId}"]`).click();
  cy.contains('input[type="submit"]', "Open").click();
  cy.contains(".TabStrip td", "Leave Details").click();

  // For now, we're stopping at asserting that the claim made it to Fineos.
}

export function register(
  application: Pick<Application, "email" | "password">
): void {
  new LoginPage().register(application);
}
