import { getFineosBaseUrl } from "../../../config";
import { formatDateString } from "../util";
import { format, addMonths, addDays, subDays } from "date-fns";
import { Submission } from "types";

export function loginSavilinx(): void {
  Cypress.config("baseUrl", getFineosBaseUrl());
  cy.visit("/");
}

export function visitClaim(claimId: string): void {
  cy.get('a[aria-label="Cases"]').click();
  cy.get('td[keytipnumber="4"]').contains("Case").click();
  cy.labelled("Case Number").type(claimId);
  cy.labelled("Case Type").select("Absence Case");
  cy.get('input[type="submit"][value="Search"]').click();
  assertOnClaimPage(claimId);
}

export function visitEmployer(fein: string): void {
  fein = fein.replace("-", "");
  cy.get('a[aria-label="Parties"]').click();
  cy.get("input[value*='Organisation']").click();
  cy.contains("td", "Identification Number")
    .next()
    .within(() => cy.get("input").type(fein));

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

export function denyClaim(reason: string): void {
  cy.get("input[type='submit'][value='Adjudicate']").click();
  cy.wait("@ajaxRender");
  cy.wait(200);
  cy.get("input[type='submit'][value='Reject']").click({ force: true });
  clickBottomWidgetButton("OK");

  cy.get('a[title="Deny the Pending Leave Request"]').click();
  cy.get('span[id="leaveRequestDenialDetailsWidget"]')
    .find("select")
    .select(reason);
  cy.get('input[type="submit"][value="OK"]').click();
  cy.get(".absenceProgressSummaryTitle").should("contain.text", "Completed");
  cy.wait("@ajaxRender");
  cy.wait(200);
}

export function assertOnClaimPage(claimNumber: string): void {
  cy.get("[id*='processPhaseEnum']").should("contain.text", "Adjudication");
  cy.get(".case_pageheader_title").contains(claimNumber);
}

export function assertOnClaimantPage(
  firstName: string,
  lastName: string
): void {
  cy.contains("h2", `${firstName} ${lastName}`);
}

export function assertAdjudicatingClaim(claimId: string): void {
  cy.contains(".case_pageheader_title", claimId);
  cy.contains(".pageheader_subtitle", "Editing Leave Request");
}

export function assertClaimFinancialEligibility(expectMet: boolean): void {
  cy.get("[id*=leavePlanAdjudicationListviewWidgetEligibilityStatus").should(
    "have.text",
    expectMet ? "Met" : "Not Met"
  );
}

export function assertClaimApprovable(): void {
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

export function searchScenario(claimNumber: string): void {
  cy.get('a[aria-label="Cases"]').click();
  cy.get('td[keytipnumber="4"]').contains("Case").click();
  cy.labelled("Case Number").type(claimNumber);
  cy.get('input[type="submit"][value="Search"]').click();
}

export function findClaim(claimNumber: string): void {
  cy.get("h2 > span").should("contain.text", claimNumber);
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
    cy.get(`input[value="${value}"]`).click({ force: true });
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
  let reasonSelection = "";
  switch (reason) {
    case "Financial Ineligibility":
      reasonSelection = "Claimant wages failed 30x rule";
      break;
    case "Insufficient Certification":
      reasonSelection = "ID documents fail requirements";
      break;
    default:
      throw new Error("Denial reason not set or not recognized.");
  }
  cy.get('span[id="leaveRequestDenialDetailsWidget"]')
    .find("select")
    .select(reasonSelection);
  cy.get('input[type="submit"][value="OK"]').click();
}

export function changeLeaveStart(startDate: Date): void {
  onTab("Request Information");
  cy.get("input[type='submit'][value='Edit']").click();
  cy.get("input[value='Yes']").click();
  cy.get(".popup-container").within(() => {
    const formattedDate = format(startDate, "MM/dd/yyyy");
    cy.labelled("Absence start date").type(
      `{selectall}{backspace}${formattedDate}{enter}`
    );
    cy.labelled(
      "Last day worked"
    ).type(`{selectall}{backspace}${formattedDate}{enter}`, { force: true });
    cy.get("input[type='button'][value='OK']").click();
  });
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

export function findEmployerResponse(employerResponseComment: string): void {
  cy.contains("a", "Employer Response to Leave Request").click();
  cy.contains("textarea", employerResponseComment);
}

export function assertClaimHasLeaveAdminResponse(approval: boolean): void {
  if (approval) {
    cy.contains(
      "a[id^=nextActionsWidget]",
      `Employer Approval Received`
    ).click();
  } else {
    cy.contains(
      "a[id^=nextActionsWidget]",
      `Employer Conflict Reported`
    ).click();
  }
}

// @todo: This seems like it's doing a lot - is this really the whole claim workflow?
// If so, we might want to name it submitClaim() to align with portal/API.
export function createNotification(
  startDate: Date,
  endDate: Date,
  claimType?: string
): void {
  cy.contains("span", "Create Notification").click();
  cy.get("span[id='nextContainer']").first().find("input").click();
  cy.labelled("Hours worked per week").type(`{selectall}{backspace}40`);
  cy.get("span[id='nextContainer']").first().find("input").click();
  if (claimType === "military care leave") {
    cy.contains("div", "Out of work for another reason")
      .prev()
      .find("input")
      .click();
    cy.get("span[id='nextContainer']").first().find("input").click();
    cy.labelled("Absence relates to").select("Family");
    cy.wait(1000);
    cy.labelled("Absence reason").select("Military Caregiver");
  } else {
    cy.contains(
      "div",
      "Bonding with a new child (adoption/ foster care/ newborn)"
    )
      .prev()
      .find("input")
      .click();
    cy.get("span[id='nextContainer']").first().find("input").click();
    cy.labelled("Qualifier 1").select("Foster Care");
  }

  cy.get("span[id='nextContainer']")
    .first()
    .find("input")
    .click()
    .wait("@ajaxRender");
  cy.contains("div", "One or more fixed time off periods")
    .prev()
    .find("input[type='checkbox'][id*='continuousTimeToggle_CHECKBOX']")
    .click({ force: true });
  cy.get("span[id='nextContainer']").first().find("input").click();
  cy.labelled("Absence status").select("Estimated");

  cy.labelled("Absence start date").type(
    `${formatDateString(startDate)}{enter}`
  );
  cy.wait(1000);
  cy.labelled("Absence end date").type(`${formatDateString(endDate)}{enter}`, {
    force: true,
  });
  cy.wait(1000);
  cy.get(
    "input[type='button'][id*='AddTimeOffAbsencePeriod'][value='Add']"
  ).click();
  cy.wait("@ajaxRender");
  cy.wait(200);
  cy.wait("@ajaxRender");
  cy.get("span[id='nextContainer']")
    .first()
    .find("input")
    .click()
    .wait("@ajaxRender");
  cy.get("span[id='nextContainer']")
    .first()
    .find("input")
    .click()
    .wait("@ajaxRender");
  if (claimType === "military care leave") {
    cy.labelled("Military Caregiver Description").type(
      "I am a parent military caregiver."
    );
  }
  cy.get("span[id='nextContainer']")
    .first()
    .find("input")
    .click()
    .wait("@ajaxRender");
  cy.contains("div", "Thank you. Your notification has been submitted.");
  cy.get("span[id='nextContainer']").first().find("input").click();
}

export function additionalEvidenceRequest(claimNumber: string): void {
  assertOnClaimPage(claimNumber as string);
  cy.get("input[type='submit'][value='Adjudicate']").click();
  onTab("Evidence");
  cy.get("input[type='submit'][value='Additional Information']").click();
  cy.get(
    "input[name*='healthcareProviderInformationIncompleteBoolean_CHECKBOX']"
  ).click();
  cy.get("input[name*='healthcareProviderInformationIncompleteText']").type(
    "Wrote Physician requesting revised page 1."
  );
  cy.get("textarea[name*='missingInformationBox']").type(
    "Please resubmit page 1 of the Healthcare Provider form to verify the claimant's demographic information.  The page provided is missing information.  Thank you."
  );
  clickBottomWidgetButton("OK");
  cy.wait("@ajaxRender");
  cy.wait(200);
  clickBottomWidgetButton("OK");
  cy.wait(200);
  // cy.wait(90000);
  // onTab("Documents");
  // cy.get("tbody").within(() => {
  //   cy.get("td > a[title='Request for more Information']").should(
  //     "contain.text",
  //     "Request for more Information"
  //   );
  // });
}

export function checkStatus(
  claimNumber: string,
  section: string,
  status: string
): void {
  assertAdjudicatingClaim(claimNumber);
  onTab("Manage Request");
  cy.get(".divListviewGrid .ListTable tr").should("have.length", 1);
  cy.get(
    `.divListviewGrid .ListTable td[id*='ListviewWidget${section}Status0']`
  ).should("have.text", status);
}

export function checkTask(): void {
  onTab("Task");
  cy.get(`.divListviewGrid .ListTable td[title='Certification Review']`).should(
    "have.text",
    "Certification Review"
  );
  cy.get(`.divListviewGrid .ListTable td[title='ID Review']`).should(
    "have.text",
    "ID Review"
  );
  onTab("Absence Hub");
}

export function markEvidence(
  claimNumber: string,
  claimType: string,
  evidenceType: string
): void {
  assertAdjudicatingClaim(claimNumber);
  onTab("Evidence");
  cy.contains(".ListTable td", evidenceType).click();
  cy.get("input[type='submit'][value='Manage Evidence']").click();
  cy.wait("@ajaxRender");
  cy.wait(200);
  // Focus inside popup.
  cy.get(".WidgetPanel_PopupWidget").within(() => {
    if (claimType === "BGBM1") {
      cy.labelled("Evidence Receipt").select("Received");
    }
    cy.labelled("Evidence Decision").select("Satisfied");
    cy.labelled("Evidence Decision Reason").type(
      "{selectall}{backspace}Evidence has been reviewed and approved"
    );
    cy.get("input[type='button'][value='OK']").click();
    // Wait till modal has fully closed before moving on.
    cy.get("#disablingLayer").should("not.exist");
  });
}

export function fillAbsencePeriod(claimNumber: string): void {
  assertAdjudicatingClaim(claimNumber);
  onTab("Evidence");
  onTab("Certification Periods");
  cy.get("input[value='Prefill with Requested Absence Periods']").click();
  cy.get("#PopupContainer").within(() => {
    cy.get("input[value='Yes']").click();
  });
}

export function claimAdjudicationFlow(
  claimNumber: string,
  ERresponse = false
): void {
  visitClaim(claimNumber);
  if (ERresponse) {
    assertClaimHasLeaveAdminResponse(true);
    clickBottomWidgetButton("Close");
  }
  assertOnClaimPage(claimNumber);
  checkTask();
  cy.get("input[type='submit'][value='Adjudicate']").click();
  checkStatus(claimNumber, "Eligibility", "Met");
  markEvidence(claimNumber, "MHAP1", "State managed Paid Leave Confirmation");
  markEvidence(claimNumber, "MHAP1", "Identification Proof");
  checkStatus(claimNumber, "Evidence", "Satisfied");
  fillAbsencePeriod(claimNumber);
  checkStatus(claimNumber, "Availability", "Time Available");
  // Complete Adjudication
  assertAdjudicatingClaim(claimNumber);
  clickBottomWidgetButton("OK");
  assertClaimApprovable();
  // Approve Claim
  if (ERresponse) {
    approveClaim();
  }
  cy.wait(2000);
}

export function claimAdjudicationMailedDoc(claimNumber: string): void {
  visitClaim(claimNumber);
  assertOnClaimPage(claimNumber);
  onTab("Documents");
  uploadDocument("HCP", "State Managed");
  onTab("Absence Hub");
  cy.get('input[type="submit"][value="Adjudicate"]').click();
  markEvidence(claimNumber, "BGBM1", "State managed Paid Leave Confirmation");
  markEvidence(claimNumber, "BGBM1", "Identification Proof");
  checkStatus(claimNumber, "Evidence", "Satisfied");
  fillAbsencePeriod(claimNumber);
  checkStatus(claimNumber, "Availability", "Time Available");
  // Complete Adjudication
  assertAdjudicatingClaim(claimNumber);
  clickBottomWidgetButton("OK");
  assertClaimApprovable();
}

export function addBondingLeaveFlow(timeStamp: Date): void {
  cy.get('a[aria-label="Add Time"]').click({ force: true });
  cy.get('input[type="radio"][value*="another_reason_id"]').click();
  cy.get('input[type="submit"][title="Add Time Off Period"]').click();
  cy.wait("@ajaxRender");
  cy.wait(200);
  cy.get(".popup-container").within(() => {
    cy.labelled("Absence status").select("Known");
    cy.wait("@ajaxRender");
    cy.wait(200);
    const startDate = addMonths(timeStamp, 2);
    const startDateFormatted = format(startDate, "MM/dd/yyyy");
    const endDateFormatted = format(addDays(startDate, 2), "MM/dd/yyyy");

    cy.labelled("Absence start date").type(
      `{selectall}{backspace}${startDateFormatted}{enter}`
    );
    cy.wait("@ajaxRender");
    cy.wait(200);
    cy.labelled("Absence end date").type(
      `{selectall}{backspace}${endDateFormatted}{enter}`
    );
    cy.wait("@ajaxRender");
    cy.wait(200);
    cy.get("input[type='checkbox'][id*='startDateAllDay_CHECKBOX']").click();
    cy.get("input[type='checkbox'][id*='endDateAllDay_CHECKBOX']").click();
    cy.get("input[type='submit'][value='OK']").click();
  });
  clickBottomWidgetButton("Next");
  cy.wait("@ajaxRender");
  cy.wait(200);
  // Work Pattern
  cy.get("input[type='checkbox'][id*='standardWorkWeek_CHECKBOX']").click();
  cy.labelled("Pattern Status").select("Known");
  clickBottomWidgetButton("Next");
  cy.wait("@ajaxRender");
  cy.wait(200);
  // Complete Details
  cy.labelled("Primary Relationship to Employee").select("Child");
  cy.wait("@ajaxRender");
  cy.wait(200);
  cy.wait("@ajaxRender");
  cy.wait(200);
  cy.labelled("Qualifier 1").select("Biological");
  clickBottomWidgetButton("Next");
  // Additional Info
  clickBottomWidgetButton("Next");
  // Wrap up
  clickBottomWidgetButton("OK");
  // Assert bonding leave request was added
  cy.get("[id*='processPhaseEnum']").should("contain.text", "Adjudication");
  cy.get("[id*='requestedLeaveCardWidget']").should(
    "contain.text",
    "Pending leave"
  );
  cy.get(".absencePeriodDescription").should(
    "contain.text",
    "Fixed time off for Child Bonding"
  );
  cy.wait(1000);
}

export function searchClaimantSSN(ssn: string): void {
  ssn = ssn.replace(/-/g, "");
  cy.get('a[aria-label="Parties"]').click();
  cy.contains("td", "Identification Number")
    .next()
    .within(() => cy.get("input").type(ssn));

  cy.get('input[type="submit"][value="Search"]').click();
}

export function uploadIDdoc(claimNumber: string): void {
  visitClaim(claimNumber);
  onTab("Documents");
  uploadDocument("MA ID", "Identification Proof");
  findDocument("MA ID");
  cy.wait(200);
}

export function findOtherLeaveEForm(claimNumber: string): void {
  visitClaim(claimNumber);
  onTab("Documents");
  cy.contains("a", "Other Leaves");
  cy.wait(200);
}

export function checkPaymentPreference(simClaim: SimulationClaim): void {
  const { claim, paymentPreference } = simClaim;
  searchClaimantSSN(claim.tax_identifier as string);
  clickBottomWidgetButton("OK");
  onTab("Payment Preferences");
  cy.contains("td", "Yes").click();
  cy.wait("@ajaxRender");
  cy.wait(200);
  cy.get('input[type="submit"][value="View"]').click();
  cy.wait("@ajaxRender");
  cy.wait(200);

  // Check Name
  cy.get('span[id*="accountName"]').should(
    "contain",
    `${claim.first_name} ${claim.last_name}`
  );

  // Check Payment Preference
  cy.contains(
    "span",
    paymentPreference.payment_preference?.payment_method as string
  ).should("be.visible");
  cy.contains(
    "span",
    paymentPreference.payment_preference?.account_number as string
  ).should("be.visible");
  cy.contains(
    "span",
    paymentPreference.payment_preference?.bank_account_type as string
  ).should("be.visible");
  cy.contains(
    "span",
    paymentPreference.payment_preference?.routing_number as string
  ).should("be.visible");

  // Check Address
  cy.contains("span", claim.mailing_address?.line_1 as string).should(
    "be.visible"
  );
  cy.contains("span", claim.mailing_address?.city as string).should(
    "be.visible"
  );
  cy.contains("tr > td > span", claim.mailing_address?.state as string).should(
    "be.visible"
  );
  cy.contains("span", claim.mailing_address?.zip as string).should(
    "be.visible"
  );
  cy.wait(2000);
}

export function modifyDates(submission: Submission): void {
  visitClaim(submission.fineos_absence_id);
  cy.get('.date-wrapper span[id*="leaveStartDate"]')
    .invoke("text")
    .as("previousStartDate");

  cy.get("input[type='submit'][value='Adjudicate']").click();
  cy.get<string>("@previousStartDate").then((dateString) => {
    const newStartDate = subDays(new Date(dateString), 1);
    changeLeaveStart(newStartDate);
    cy.wrap(newStartDate).as("newStartDate");
  });

  clickBottomWidgetButton("OK");
  cy.get<Date>("@newStartDate").then((date) => {
    cy.get('.date-wrapper span[id*="leaveStartDate"]').should(
      "have.text",
      format(date, "MM/dd/yyyy")
    );
  });
  cy.wait(2000);
}

export function confirmRMVStatus(RMVStatus: string): void {
  let statusText = "";
  switch (RMVStatus) {
    case "valid":
      statusText = "Verification check passed";
      cy.get("div[id*='identificationStatus']").should(
        "contain.text",
        statusText
      );
      break;

    case "invalid":
    case "fraud":
      statusText =
        "Verification failed because no record could be found for given ID information";
      cy.get("div[id*='identificationStatus']").should(
        "contain.text",
        statusText
      );
      break;

    case "mismatch":
      statusText = "Verification failed because ID number mismatch";
      cy.get("div[id*='identificationStatus']").should(
        "contain.text",
        statusText
      );
      break;

    default:
      throw new Error("RMV Status Type not found!");
  }
}
