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

  fineos.addWeeklyWage();
  fineos.onTab("Evidence");
  fineos.onTab("Certification Periods");
  fineos.fufillAvailability();
  fineos.clickAdjudicate();
  fineos.onTab("Evidence");
  fineos.manageEvidence();
  fineos.validateEvidence("valid");

  // When I highlight ID Proof
  cy.wait(2000).get('.ListRow2 > [width="20%"]').click();

  fineos.manageEvidence();
  fineos.validateEvidence("valid");
  fineos.onTab("Manage Request");
  fineos.acceptClaim();
  fineos.onPage("claims");
  fineos.approveClaim();
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
  fineos.denialReason("Ineligible");
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
  fineos.transferToDFML("missing HCP form");
  fineos.confirmDFMLTransfer();
}

export function UNH2(): void {
  getToClaimPage();
  fineos.onTab("Documents");

  // Then I should confirm HCP form is not present
  cy.contains("No Records To Display");

  fineos.onTab("Absence Hub");
  fineos.clickAdjudicate();
  fineos.onTab("Evidence");
  fineos.manageEvidence();
  fineos.validateEvidence("invalid due to invalid HCP form");
  fineos.onPage("claims");
  fineos.onTab("Tasks");
  fineos.addEvidenceReviewTask();
  fineos.transferToDFML("invalid HCP");
  fineos.confirmDFMLTransfer();
}

export function UNH3(): void {
  getToClaimPage();
  fineos.onTab("Documents");
  fineos.uploadDocument("MA ID");
  fineos.findDocument("MA ID");
  fineos.onTab("Absence Hub");
  fineos.clickAdjudicate();
  fineos.onTab("Evidence");
  fineos.manageEvidence();
  fineos.validateEvidence("invalid due to mismatched ID and SSN");
  fineos.onTab("Manage Request");
  fineos.clickReject();
  fineos.onPage("claims");

  // And claim is rejected
  cy.get('td[title="Rejected"]');

  fineos.clickDeny();
  fineos.denialReason("Ineligible");
  fineos.claimCompletion();
}
