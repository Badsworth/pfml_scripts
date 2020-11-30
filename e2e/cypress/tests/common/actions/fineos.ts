import { getFineosBaseUrl } from "../../../config";

export function loginSavilinx(): void {
  Cypress.config("baseUrl", getFineosBaseUrl());
  cy.visit("/");
}

export function visitClaim(claimId: string): void {
  cy.get('a[aria-label="Cases"]').click();
  cy.get('td[keytipnumber="4"]').contains("Case").click();
  cy.labelled("Case Number").type(claimId);
  cy.get('input[type="submit"][value="Search"]').click();
  assertOnClaimPage();
}

export function visitEmployer(fein: string): void {
  fein = fein.replace("-", "");
  cy.get('a[aria-label="Parties"]').click();
  cy.get("input[value*='Organisation']").click();
  cy.contains("td", "Identification Number")
    .next()
    .within(($td) => cy.get("input").type(fein));

  cy.get('input[type="submit"][value="Search"]').click();
  // cy.get('td[title="Adjudication"]').first().click();
  cy.get('input[value="OK"]').last().click();
}

export function confirmPOC(email: string): void {
  cy.get('td[keytipnumber="6"]').contains("Party History").click();
  cy.wait("@ajaxRender");
  cy.contains("span", email);
}

export function commenceIntake(claimId: string): void {
  cy.get('a[aria-label="Cases"]').click();
  cy.get('td[keytipnumber="4"]').contains("Case").click();
  cy.labelled("Case Number").type(claimId);
  cy.get('input[type="submit"][value="Search"]').click();
  cy.contains("Capture the following details in order to commence intake");
}

export function assertOnClaimPage(): void {
  cy.unstash("claimNumber")
    .then((claimNumber) => {
      if (typeof claimNumber === "string") {
        return claimNumber;
      } else {
        throw new Error("Claim number must be a string.");
      }
    })
    .then((claimNumber) => {
      cy.get("[id*='processPhaseEnum']").should("contain.text", "Adjudication");
      cy.get(".case_pageheader_title").contains(claimNumber);
    });
}

export function assertOnClaimantPage(): void {
  cy.unstash("firstName").then((firstName) => {
    cy.unstash("lastName").then((lastName) => {
      cy.contains("h2", firstName + " " + lastName);
    });
  });
}

export function assertAdjudicatingClaim(claimId: string): void {
  cy.contains(".case_pageheader_title", claimId);
  cy.contains(".pageheader_subtitle", "Editing Leave Request");
}

export function assertClaimApprovable(): void {
  assertOnClaimPage();
  // Assert that we have all green checkboxes.
  cy.get(
    "[id*='leavePlanAdjudicationListviewWidgetApplicabilityStatus']"
  ).should("have.text", "Applicable");
  cy.get("[id*='leavePlanAdjudicationListviewWidgetEligibilityStatus']").should(
    "have.text",
    "Met"
  );
  cy.get("[id*='leavePlanAdjudicationListviewWidgetEvidenceStatus']").should(
    "have.text",
    "Satisfied"
  );
  cy.get(
    "[id*='leavePlanAdjudicationListviewWidgetAvailabilityStatus']"
  ).should("have.text", "Time Available");
  cy.get("[id*='leavePlanAdjudicationListviewWidgetRestrictionStatus']").should(
    "have.text",
    "Passed"
  );
  cy.get("[id*='leavePlanAdjudicationListviewWidgetProtocolsStatus']").should(
    "have.text",
    "Passed"
  );
  cy.get("[id*='leavePlanAdjudicationListviewWidgetPlanDecision0']").should(
    "have.text",
    "Undecided"
  );
  // Assert that we can see the approve button.
  cy.contains(".menulink a", "Approve").should("be.visible");
}

export function searchScenario(): void {
  cy.visit("/");
  cy.get('a[aria-label="Cases"]').click();
  cy.get('td[keytipnumber="4"]').contains("Case").click();

  // For Testing (hard coded Claim Number)
  // cy.labelled("Case Number").type("NTN-5390-ABS-01");

  cy.unstash("claimNumber")
    .as("claimNumber")
    .then((claimNumber) => {
      cy.labelled("Case Number").type(claimNumber as string);
    });
  cy.get('input[type="submit"][value="Search"]').click();
}

export function searchClaimant(): void {
  cy.unstash("lastName").then((lastName) => {
    cy.unstash("firstName").then((firstName) => {
      cy.visit("/");
      cy.get('a[aria-label="Parties"]').click();
      cy.get("input[name*='First_Name']").type(firstName as string);
      cy.get("input[name*='Last_Name']").type(lastName as string);
      cy.get('input[type="submit"][value="Search"]').click();
    });
  });
}

export function findClaim(): void {
  // For Testing (hard coded Claim Number)
  // cy.get("h2 > span").should("contain.text", "NTN-5390-ABS-01");

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
  cy.contains(".TabStrip td", label).click().should("have.class", "TabOn");
  // Wait on any in-flight Ajax to complete.
  cy.wait("@ajaxRender");
  // Slight delay after that to allow for the content to be populated.
  cy.wait(200);
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
    case "FOSTER":
      documentCategory = "State_managed_Paid_Leave_Confirmation";
      cy.get(`a[name*=${documentCategory}]`);
      break;
    case "Employer Confirmation":
      documentCategory = "Employer Confirmation of Leave Data";
      cy.get("tr[class='ListRowSelected']").should(
        "contain.text",
        documentCategory
      );
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
