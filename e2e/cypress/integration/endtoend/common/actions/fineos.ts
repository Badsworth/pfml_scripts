import { getFineosBaseUrl } from "@cypress/config";

export function loginSavilinx(): void {
  Cypress.config("baseUrl", getFineosBaseUrl());
}

export function searchScenario(): void {
  cy.visit("/");
  cy.get('a[aria-label="Cases"]').click();
  cy.get('td[keytipnumber="4"]').contains("Case").click();

  /* For Testing (hard coded Claim Number)
    cy.labelled("Case Number").type("NTN-528-ABS-01");
   */
  cy.unstash("claimNumber").then((claimNumber) => {
    cy.labelled("Case Number").type(claimNumber as string);
  });
  cy.get('input[type="submit"][value="Search"]').click();
}

export function findClaim(): void {
  /* For Testing (hard coded Claim Number)
    cy.get("h2 > span").should("contain.text", "NTN-528-ABS-01");
   */
  cy.unstash("claimNumber").then((claimNumber) => {
    cy.get("h2 > span").should("contain.text", claimNumber);
  });
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

export function clickBottomWidgetButton(value = "OK"): void {
  cy.get("#PageFooterWidget").within(() => {
    cy.get(`input[value="${value}"]`).click();
  });
}

export function validateEvidence(label: string): void {
  let receipt: string, decision: string, reason: string;
  switch (label) {
    case "valid":
      receipt = "Received";
      decision = "Satisfied";
      reason = "Evidence is Approved";
      break;
    case "invalid due to missing HCP form":
      receipt = "Not Received";
      decision = "Pending";
      reason = "Missing HCP Form";
      break;
    case "invalid due to missing identity documents":
      receipt = "Received";
      decision = "Not Satisfied";
      reason = "Submitted document is not a valid out-of-state ID.";
      break;
    case "invalid due to invalid HCP form":
      receipt = "Received";
      decision = "Not Satisfied";
      reason =
        "Submitted document is not a valid DFML-certified HCP form or FMLA form.";
      break;
    case "invalid due to mismatched ID and SSN":
      receipt = "Received";
      decision = "Not Satisfied";
      reason = "ID does not match SSN.";
      break;
    default:
      throw new Error("Evidence status not set or not recognized.");
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
}

export function denialReason(reason: string): void {
  let reasonText = "";
  switch (reason) {
    case "Ineligible":
      reasonText =
        "This leave claim was denied due to financial ineligibility.";
      break;
    case "Insufficient Certification":
      reasonText =
        "This leave claim was denied due to invalid out-of-state ID.";
      break;
    default:
      throw new Error("Denial reason not set or not recognized.");
  }
  cy.get('span[id="leaveRequestDenialDetailsWidget"]')
    .find("select")
    .select(reason);
  cy.labelled("Notes").type(reasonText);
  cy.get('input[type="submit"][value="OK"]').click();
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
    .type("outstanding document");
  cy.get("#NameSearchWidget").find('input[type="submit"]').click();
  clickBottomWidgetButton("Next");
  cy.get('td[title*="Outstanding Document"]').first().click();
  cy.get("input[type='submit'][title='Open this task']").click();
}

export function transferToDFML(reason: string): void {
  let reasonText: string;
  switch (reason) {
    case "missing HCP form":
      reasonText = "This claim is missing a Health Care Provider form.";
      break;
    case "mismatched ID/SSN":
      reasonText =
        "This claim has a mismatched ID number and Social Security Number.";
      break;
    case "invalid HCP":
      reasonText = "This claim has an invalid Health Care Provider form.";
      break;
    default:
      throw new Error("Provided reason for transfer is not recognized.");
  }

  cy.get('div[title="Transfer"]').dblclick();
  cy.get('a[title="Transfer to Dept"]').dblclick({ force: true });
  cy.url().should("include", "/sharedpages/workmanager/transfertodeptpage");
  cy.get(':nth-child(2) > [title="DFML Ops"]').first().click();
  cy.contains("label", "Description")
    .parentsUntil("tr")
    .get("textarea")
    .type(reasonText);
  clickBottomWidgetButton();
}

export function confirmDFMLTransfer(): void {
  cy.get("#PopupContainer").contains("Transferred to DFML Ops");
  cy.get(".popup_buttons").find('input[value="OK"]').click();
  cy.get("#BasicDetailsUsersDeptWidget_un16_Department").should(
    "contain.text",
    "DFML Ops"
  );
}

export function uploadDocument(
  documentType: string,
  businessType: string
): void {
  const docName = documentType.replace(" ", "_");
  cy.get('input[value="Add"]').click();
  cy.get("table[class='TabStrip']").contains("div", "Search").click();
  cy.labelled("Business Type").type(businessType);
  cy.get("input[value='Search']").click();
  clickBottomWidgetButton();
  cy.get("input[type='file']").attachFile(`./${docName}.pdf`);
  clickBottomWidgetButton();
}

export function findDocument(documentType: string): void {
  let documentCategory: string;
  switch (documentType) {
    case "MA ID":
      documentCategory = "Identification_Proof";
      cy.get(`a[name*=${documentCategory}]`);
      break;
    case "HCP":
      documentCategory = "State_Managed_Paid_Leave_Confirmation";
      cy.get(`a[name*=${documentCategory}]`);
      break;
    default:
      throw new Error("Provided reason for transfer is not recognized.");
  }
}

export function addWeeklyWage(): void {
  cy.labelled("Average weekly wage").type("{selectall}{backspace}1000");
  clickBottomWidgetButton();
}

export function fillAvailability(): void {
  cy.get('input[type="submit"][value="Prefill with Requested Absence Periods"]')
    .click()
    .wait(1000);
  cy.get('input[type="submit"][value="Yes"]').click();
  clickBottomWidgetButton();
}

export function acceptLeavePlan(): void {
  cy.get('input[title="Accept Leave Plan"]').click();
  clickBottomWidgetButton();
}

export function approveClaim(): void {
  // This button turns out to be unclickable without force, because selecting
  // it seems to scroll it out of view. Force works around that.
  cy.get('a[title="Approve the Pending Leaving Request"]').click({
    force: true,
  });
  cy.get(".key-info-bar .status").should("contain.text", "Approved");
}
