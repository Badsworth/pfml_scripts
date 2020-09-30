import { fineos } from "../actions/";

function getToClaimPage(): void {
  fineos.loginSavilinx();
  fineos.searchScenario();
  fineos.findClaim();
  fineos.onPage("claims");
}

export function HAP1(): void {
  getToClaimPage();
  fineos.clickAdjudicate();
  fineos.onTab("Paid Benefits");

  // When I click edit
  cy.wait(2000).get('input[type="submit"][value="Edit"]').click();

  // Then I should add weekly wage
  cy.labelled("Average weekly wage").type("{selectall}{backspace}1000");
  cy.get('input[type="submit"][id="p9_un7_editPageSave"]').click();

  fineos.onTab("Evidence");
  fineos.onTab("Certification Periods");

  // Then I should fufill availability request
  cy.get('input[type="submit"][value="Prefill with Requested Absence Periods"]')
    .click()
    .wait(1000);
  cy.get('input[type="submit"][value="Yes"]').click();
  cy.get('input[type="submit"][id="p8_un180_editPageSave"]').click();

  fineos.clickAdjudicate();
  fineos.onTab("Evidence");
  fineos.manageEvidence();
  fineos.validateEvidence("valid");

  // When I highlight ID Proof
  cy.wait(2000).get('.ListRow2 > [width="20%"]').click();

  fineos.manageEvidence();
  fineos.validateEvidence("valid");
  fineos.onTab("Manage Request");

  // Then I click Accept
  cy.get('input[title="Accept Leave Plan"]').click();
  cy.get('input[type="submit"][id="p10_un180_editPageSave"]').click();

  fineos.onPage("claims");

  // Then I should approve Claim
  cy.get('a[title="Approve the Pending Leaving Request"]').dblclick();
  cy.get("#managedLeaveProgressCardWidget").contains("Future Leave");
}

export function HAP2(): void {
  getToClaimPage();
  fineos.onTab("Documents");

  // Then I should confirm "OOS ID form" is not present
  cy.contains("No Records To Display");

  fineos.onTab("Absence Hub");
  fineos.clickAdjudicate();
  fineos.onTab("Evidence");
  fineos.manageEvidence();
  fineos.validateEvidence("valid");

  // When I highlight ID Proof
  cy.wait(2000).get('.ListRow2 > [width="20%"]').click();

  fineos.manageEvidence();
  fineos.validateEvidence("invalid due to missing identity documents");
  fineos.onTab("Manage Request");
  fineos.clickReject();
  fineos.onPage("claims");

  // And claim is rejected
  cy.get('td[title="Rejected"]');

  fineos.clickDeny();
  fineos.denialReason("Insufficient Certification");
  fineos.claimCompletion();
}

export function HAP3(): void {
  getToClaimPage();
  fineos.clickAdjudicate();

  // Given claim is financially ineligible
  cy.get('td[title="Not Met"]');

  fineos.clickReject();
  fineos.onPage("claims");

  // And claim is rejected
  cy.get('td[title="Rejected"]');

  fineos.clickDeny();
  fineos.denialReason("Financially Ineligible");
  fineos.claimCompletion();
}

export function GBR1(): void {
  getToClaimPage();
  fineos.onTab("Documents");

  // Then I should confirm HCP form is not present
  cy.contains("No Records To Display");

  fineos.onTab("Absence Hub");
  fineos.clickAdjudicate();
  fineos.onTab("Evidence");
  fineos.manageEvidence();
  fineos.validateEvidence("invalid due to missing HCP form");
  fineos.onPage("claims");
  fineos.onTab("Tasks");
  fineos.addEvidenceReviewTask();
  fineos.transferToDFML();
  fineos.confirmDFMLTransfer();
}
