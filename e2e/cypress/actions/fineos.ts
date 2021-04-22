import { format, addMonths, addDays } from "date-fns";

/**
 * This function is used to fetch and set the proper cookies for access Fineos UAT
 *
 * Note: Only used for UAT enviornment
 */
function SSO(): void {
  cy.clearCookies();
  // Perform SSO login in a task. We can't visit other domains in Cypress.
  cy.task("completeSSOLoginFineos").then((cookiesJson) => {
    const deserializedCookies: Record<string, string>[] = JSON.parse(
      cookiesJson
    );
    // There's no way we can stop the redirection from Fineos -> SSO login.
    // What we _can_ do is set the login cookies so that when that request is made,
    // it bounces back immediately with a HTTP redirect instead of showing the login page.
    const noSecure = deserializedCookies.filter((cookie) =>
      cookie.domain.match(/login\.microsoftonline/)
    );
    for (const cookie_info of noSecure) {
      cy.setCookie(cookie_info.name, cookie_info.value, cookie_info);
    }
  });
}

export function before(): void {
  // Suppress known application errors in Fineos.
  cy.on("uncaught:exception", (e) => {
    if (
      e.message.match(
        /(#.(CaseOwnershipSummaryPanelElement|CaseParticipantsSummaryPanelElement)|panelsdrilldown|startHeartbeatMonitorForPage)/
      )
    ) {
      return false;
    }
    if (e.message.match(/Cannot set property 'status' of undefined/)) {
      return false;
    }
    return true;
  });
  // Block new-relic.js outright due to issues with Cypress networking code.
  // Without this block, test retries on the portal error out due to fetch() errors.
  cy.intercept("https://js-agent.newrelic.com/*", (req) => {
    req.reply("console.log('Fake New Relic script loaded');");
  });

  // Fineos error pages have been found to cause test crashes when rendered. This is very hard to debug, as Cypress
  // crashes with no warning and removes the entire run history, so when a Fineos error page is detected, we instead
  // throw an error.
  cy.intercept(/\/util\/errorpage.jsp/, (req) => {
    req.reply(
      "A fatal Fineos error was thrown at this point. We've blocked the rendering of this page to prevent test crashes"
    );
  });

  // Set up a route we can listen to wait on ajax rendering to complete.
  cy.intercept(
    /(ajax\/pagerender\.jsp|sharedpages\/ajax\/listviewpagerender\.jsp|AJAXRequestHandler\.do)/
  ).as("ajaxRender");

  if (Cypress.env("E2E_ENVIRONMENT") === "uat") {
    SSO();
  }
}

export function visitClaim(claimId: string): void {
  cy.get('a[aria-label="Cases"]').click();
  onTab("Case");
  cy.labelled("Case Number").type(claimId);
  cy.labelled("Case Type").select("Absence Case");
  cy.get('input[type="submit"][value="Search"]').click();
  assertOnClaimPage(claimId);
}

export function denyClaim(reason: string): void {
  cy.get("input[type='submit'][value='Adjudicate']").click();
  // Make sure the page is fully loaded by waiting for the leave plan to show up.
  cy.get("table[id*='selectedLeavePlans'] tr").should("have.length", 1).click();
  cy.get("input[type='submit'][value='Reject']").click();
  clickBottomWidgetButton("OK");

  cy.get('a[title="Deny the Pending Leave Request"]').click();
  cy.get('span[id="leaveRequestDenialDetailsWidget"]')
    .find("select")
    .select(reason);
  cy.get('input[type="submit"][value="OK"]').click();
  assertClaimStatus("Declined");
}

/**
 * Called from the claim page, asserts that the claim status is an expected value.
 */
function assertClaimStatus(expected: string) {
  cy.get(".key-info-bar .status dd").should((statusElement) => {
    expect(statusElement, `Absence case should be ${expected}`).to.contain.text(
      expected
    );
  });
}

/**
 * Called from the claim page or the manage request page, asserts that the claim's eligibility, applicability,
 * eligibility, etc matches a known state.
 */
export function assertPlanStatus(
  section: string,
  expectedStatus: string
): void {
  cy.get(
    `.divListviewGrid .ListTable td[id*='ListviewWidget${section}Status0']`
  ).should((element) => {
    expect(
      element,
      `Expected claim's "${section}" to be "${expectedStatus}"`
    ).to.have.text(expectedStatus);
  });
}

/**
 * Called from the tasks page, asserts that a particular task is found.
 * @param name
 */
function assertHasTask(name: string) {
  cy.get("table[id*='TasksForCaseWidget']").should((table) => {
    expect(table, `Expected to find a "${name}" task`).to.have.descendants(
      `tr td:nth-child(6)[title="${name}"]`
    );
  });
}

function assertHasDocument(name: string) {
  cy.get("table[id*='DocumentsForCaseListviewWidget']").should((table) => {
    expect(table, `Expected to find a "${name}" document`).to.have.descendants(
      `a:contains("${name}")`
    );
  });
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

/**
 * Helper to switch to a particular tab.
 */
function onTab(label: string): void {
  cy.contains(".TabStrip td", label).click().should("have.class", "TabOn");
  // Wait on any in-flight Ajax to complete, then add a very slight delay for rendering to occur.
  cy.wait("@ajaxRender").wait(50);
}

/**
 * Helper to wait for ajax-y actions to complete before proceeding.
 *
 * Note: Please do not add explicit waits here. This function should be fast -
 * it will be called often. Try to find a better way to determine if we can move
 * on with processing (element detection).
 */
function wait() {
  cy.wait("@ajaxRender");
  cy.get("#disablingLayer").should("not.be.visible");
}

export function clickBottomWidgetButton(value = "OK"): void {
  cy.get(`#PageFooterWidget input[value="${value}"]`).click({ force: true });
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
      cy.get(`a[name*=${documentCategory}]`).should(
        "contain.text",
        "Identification Proof"
      );
      break;
    case "HCP":
    case "FOSTER":
      documentCategory = "State_managed_Paid_Leave_Confirmation";
      cy.get(`a[name*=${documentCategory}]`).should(
        "contain.text",
        "State managed Paid Leave Confirmation"
      );
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

export function approveClaim(): void {
  // This button turns out to be unclickable without force, because selecting
  // it seems to scroll it out of view. Force works around that.
  cy.get('a[title="Approve the Pending Leaving Request"]').click({
    force: true,
  });
  assertClaimStatus("Approved");
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

/*
 * This work-flow is submitting a full bonding/military claim
 * directly into Fineos.
 *
 * Note: named createNotification based on the name of the button
 * in Fineos that starts this workflow
 */
export function createNotification(
  startDate: Date,
  endDate: Date,
  claimType?: string,
  hours_worked_per_week?: number
): void {
  const clickNext = (timeout?: number) =>
    cy.get('#navButtons input[value="Next "]', { timeout }).first().click();
  cy.contains("span", "Create Notification").click();
  clickNext();
  cy.labelled("Hours worked per week").type(
    `{selectall}{backspace}${hours_worked_per_week}`
  );
  clickNext();
  // @todo: Make claim type dynamic.
  if (claimType === "military care leave") {
    cy.contains("div", "Out of work for another reason")
      .prev()
      .find("input")
      .click();
    clickNext();
    cy.labelled("Absence relates to").select("Family");
    wait();
    cy.labelled("Absence reason").select("Military Caregiver", {});
  } else {
    cy.contains(
      "div",
      "Bonding with a new child (adoption/ foster care/ newborn)"
    )
      .prev()
      .find("input")
      .click();
    clickNext();
    cy.labelled("Qualifier 1").select("Foster Care");
  }

  clickNext(5000);
  cy.contains("div.toggle-guidance-row", "One or more fixed time off periods")
    .find("span.slider")
    .click();

  clickNext();
  cy.labelled("Absence status").select("Estimated");

  wait();
  cy.labelled("Absence start date").type(
    `${format(startDate, "MM/dd/yyyy")}{enter}`
  );
  wait();
  cy.labelled("Absence end date").type(
    `${format(endDate, "MM/dd/yyyy")}{enter}`
  );
  wait();
  cy.get(
    '#timeOffAbsencePeriodDetailsQuickAddWidget input[value="Add"]'
  ).click();

  clickNext(5000);
  cy.labelled("Work Pattern Type").select("Fixed");
  wait();

  cy.labelled("Standard Work Week").click();
  clickNext();
  if (claimType === "military care leave") {
    cy.labelled("Military Caregiver Description").type(
      "I am a parent military caregiver."
    );
  }
  clickNext(20000);
  cy.contains("div", "Thank you. Your notification has been submitted.");
  clickNext(20000);
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

export function markEvidence(
  claimNumber: string,
  claimType: string,
  evidenceType: string
): void {
  assertAdjudicatingClaim(claimNumber);
  onTab("Evidence");
  cy.contains(".ListTable td", evidenceType).click();
  cy.get("input[type='submit'][value='Manage Evidence']").click();
  // Focus inside popup. Note: There should be no need for an explicit wait here because
  // Cypress will not move on until the popup has been rendered.
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
  cy.get("#PopupContainer input[value='Yes']").click();
}

export function claimAdjudicationFlow(
  claimNumber: string,
  ERresponse = false
): void {
  visitClaim(claimNumber);
  onTab("Tasks");
  assertHasTask("Certification Review");
  assertHasTask("ID Review");
  if (ERresponse) {
    assertHasTask("Employer Approval Received");
  }
  onTab("Absence Hub");
  assertPlanStatus("Applicability", "Applicable");
  assertPlanStatus("Eligibility", "Met");
  cy.get("input[type='submit'][value='Adjudicate']").click();
  markEvidence(claimNumber, "MHAP1", "State managed Paid Leave Confirmation");
  markEvidence(claimNumber, "MHAP1", "Identification Proof");
  fillAbsencePeriod(claimNumber);
  onTab("Manage Request");
  assertPlanStatus("Evidence", "Satisfied");
  assertPlanStatus("Availability", "Time Available");
  assertPlanStatus("Restriction", "Passed");
  assertPlanStatus("Protocols", "Passed");
  clickBottomWidgetButton("OK");

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
  // Assert ID Doc is present
  findDocument("MA ID");
  uploadDocument("HCP", "State Managed");
  onTab("Documents");
  findDocument("HCP");
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
  assertPlanStatus("Applicability", "Applicable");
  assertPlanStatus("Eligibility", "Met");
  assertPlanStatus("Evidence", "Satisfied");
  assertPlanStatus("Availability", "Time Available");
  assertPlanStatus("Restriction", "Passed");
  assertPlanStatus("Protocols", "Passed");
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

export function findOtherLeaveEForm(claimNumber: string): void {
  visitClaim(claimNumber);
  onTab("Documents");
  assertHasDocument("Other Leaves");
  cy.wait(200);
}

export function checkPaymentPreference(simClaim: DehydratedClaim): void {
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

export function getPaymentAmount(): Cypress.Chainable<string> {
  cy.contains("Absence Paid Leave Case").click();
  cy.wait("@ajaxRender");
  onTab("Financials");
  onTab("Payment History");
  onTab("Amounts Pending");
  return cy
    .get('#amountspendingtabWidget td[id*="benefit_amount_money0"]')
    .invoke("text");
}

export function triggerNoticeRelease(docType: string): void {
  onTab("Task");
  onTab("Processes");
  cy.contains(".TreeNodeElement", "SOM Generate Legal Notice").click({
    force: true,
  });
  cy.get('input[type="submit"][value="Properties"]').click();
  cy.get('input[type="submit"][value="Continue"]').click();
  cy.contains(".TreeNodeContainer", "SOM Generate Legal Notice", {
    timeout: 20000,
  })
    .find("input[type='checkbox']")
    .should("be.checked");
  onTab("Documents");
  assertHasDocument(docType);
}
