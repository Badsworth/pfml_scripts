import { getFineosBaseUrl } from "@cypress/config";

export function loginSavilinx(): void {
  Cypress.config("baseUrl", getFineosBaseUrl());
}

export function searchScenario(): void {
  cy.visit("/");
  cy.get('a[aria-label="Cases"]').click();
  cy.get('td[keytipnumber="4"]').contains("Case").click();

  /* For Testing (hard coded Claim Number)
   */
  cy.labelled("Case Number").type("NTN-474-ABS-01");
  // cy.unstash("claimNumber2").then((claimNumber) => {
  //   cy.log("**Inside UNSTASH**")
  //   // cy.labelled("Case Number").type(claimNumber as string);
  // });
  cy.get('input[type="submit"][value="Search"]').click();
}

export function findClaim(): void {
  /* For Testing (hard coded Claim Number)
   */
  cy.get("h2 > span").should("contain.text", "NTN-474-ABS-01");
  // cy.unstash("claimNumber").then((claimNumber) => {
  //   cy.get("h2 > span").should("contain.text", claimNumber);
  // });
}

export function onPage(page: string): void {
  let url = "";
  switch (page) {
    case "claims":
      url = "/sharedpages/casemanager/displaycase/displaycasepage";
      break;

    case "dept":
      url = "/sharedpages/workmanager/transfertodeptpage";
      break;
  }
  if (!url) throw new Error(`Page ${page} not found!`);
  cy.url().should("include", url);
}

export function onTab(label: string): void {
  cy.get('td[class="TabOff"]').contains(label).click().wait(2000);
}

export function clickAdjudicate(): void {
  cy.get('input[type="submit"][value="Adjudicate"]').click();
}

export function manageEvidence(): void {
  cy.wait(2000).get('input[type="submit"][value="Manage Evidence"]').click();
}

export function clickReject(): void {
  cy.get('input[title="Reject Leave Plan"]').click();
  cy.get("#footerButtonsBar").find('input[value="OK"]').dblclick();
}

export function clickDeny(): void {
  cy.get('a[title="Deny the Pending Leave Request"]')
    .dblclick({ force: true })
    .wait(150);
  cy.get('span[id="leaveRequestDenialDetailsWidget"]');
}

export function validateEvidence(label: string): void {
  let receipt: string, decision: string, reason: string;
  if (label === "valid") {
    receipt = "Received";
    decision = "Satisfied";
    reason = "Evidence is Approved";
  } else if (label === "invalid due to missing HCP form") {
    receipt = "Not Received";
    decision = "Pending";
    reason = "Missing HCP Form";
  } else if (label === "invalid due to missing identity documents") {
    receipt = "Received";
    decision = "Not Satisfied";
    reason = "Submitted document is not a valid out-of-state ID.";
  } else {
    receipt = "Not Received";
    decision = "Pending";
    reason = "";
  }
  cy.labelled("Evidence Receipt")
    .get('select[id="manageEvidenceResultPopupWidget_un92_evidence-receipt"]')
    .select(receipt);
  cy.labelled("Evidence Decision")
    .get(
      'select[id="manageEvidenceResultPopupWidget_un92_evidence-resulttype"]'
    )
    .select(decision);
  cy.labelled("Evidence Decision Reason").type(reason);
  cy.get('input[type="button"][value="OK"]').click();
  if (label === "invalid due to missing HCP form") {
    cy.get("#p8_un180_editPageSave").click();
  }
}

export function denialReason(reason: string): void {
  cy.get('span[id="leaveRequestDenialDetailsWidget"]')
    .find("select")
    .select(
      reason === "Financially Ineligible"
        ? "Ineligible"
        : "Insufficient Certification"
    );
  let reasonText = "";
  switch (reason) {
    case "Financially Ineligible": {
      reasonText =
        "This leave claim was denied due to financial ineligibility.";
    }
    case "Insufficient Certification": {
      reasonText =
        "This leave claim was denied due to invalid out-of-state ID.";
    }
  }
}

export function claimCompletion(): void {
  cy.get("#completedLeaveCardWidget").contains("Complete");
}

export function addEvidenceReviewTask(): void {
  cy.get("input[type='submit'][title='Add a task to this case']").click({
    force: true,
    timeout: 30000,
  });
  cy.get("#NameSearchWidget")
    .find('input[type="text"]')
    .type("Evidence Review");
  cy.get("#NameSearchWidget").find('input[type="submit"]').click();
  cy.get("#p10_un8_next").click();
  cy.get('td[title="Evidence Review"]').first().click();
  cy.get("input[type='submit'][title='Open this task']").click();
}

export function transferToDFML(): void {
  cy.get('div[title="Transfer"]').dblclick();
  cy.get('a[title="Transfer to Dept"]').dblclick({ force: true });
  cy.url().should("include", "/sharedpages/workmanager/transfertodeptpage");
  cy.get(':nth-child(2) > [title="DFML Ops"]').first().click();
  cy.contains("label", "Description")
    .parentsUntil("tr")
    .get("textarea")
    .type("This claim is missing a Health Care Provider form.");
  cy.get("#p12_un6_editPageSave").click();
}

export function confirmDFMLTransfer(): void {
  cy.get("#PopupContainer").contains("Transferred to DFML Ops");
  cy.get(".popup_buttons").find('input[value="OK"]').click();
  cy.get("#BasicDetailsUsersDeptWidget_un16_Department").should(
    "contain.text",
    "DFML Ops"
  );
}
