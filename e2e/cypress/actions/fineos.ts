import { DocumentUploadRequest, ReducedScheduleLeavePeriods } from "_api";
import { format, addMonths, addDays, startOfWeek, subDays } from "date-fns";
import {
  getCertificationDocumentType,
  getDocumentReviewTaskName,
} from "../../src/util/documents";
import { config } from "./common";
import { LeaveReason } from "../../src/generation/Claim";
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
    // Filter out any cookies that will fail to be set. Those are ones where secure: false
    // and sameSite: "None"
    const noSecure = deserializedCookies.filter(
      (cookie) => !(!cookie.secure && cookie.sameSite === "None")
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
    if (
      e.message.match(
        /Cannot (set|read) property ('status'|'range') of undefined/
      )
    ) {
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
  cy.intercept(/\/(util\/errorpage\.jsp|outofdatedataerror\.jsp)/, (req) => {
    req.reply(
      "A fatal Fineos error was thrown at this point. We've blocked the rendering of this page to prevent test crashes"
    );
  });

  // Set up a route we can listen to wait on ajax rendering to complete.
  cy.intercept(
    /(ajax\/pagerender\.jsp|sharedpages\/ajax\/listviewpagerender\.jsp|AJAXRequestHandler\.do)/
  ).as("ajaxRender");

  if (config("ENVIRONMENT") === "uat") {
    SSO();
  }
}

export function visitClaim(claimId: string): void {
  cy.get('a[aria-label="Cases"]').click();
  onTab("Case");
  cy.labelled("Case Number").type(claimId);
  cy.labelled("Case Type").select("Absence Case");
  cy.get('input[type="submit"][value="Search"]').click();
  assertAbsenceCaseNumber(claimId);
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

export function reviewClaim(): void {
  cy.contains("td", "Approved").click();
  cy.get('input[title="Review a Leave Request"').click();
  cy.wait("@ajaxRender");
}

/**
 * Called from the claim page, asserts that the claim status is an expected value.
 */
export function assertClaimStatus(expected: string): void {
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
export function assertHasTask(name: string): void {
  cy.get("table[id*='TasksForCaseWidget']").should((table) => {
    expect(table, `Expected to find a "${name}" task`).to.have.descendants(
      `tr td:nth-child(6)[title="${name}"]`
    );
  });
}

export function assertHasDocument(name: string): void {
  cy.get("table[id*='DocumentsForCaseListviewWidget']").should((table) => {
    expect(table, `Expected to find a "${name}" document`).to.have.descendants(
      `a:contains("${name}")`
    );
  });
}

/**
 * Called from the claim page, asserts Absence Case is the expected value.
 */
export function assertAbsenceCaseNumber(claimNumber: string): void {
  cy.get(".case_pageheader_title").should((statusElement) => {
    expect(
      statusElement,
      `Absence Case ID should be: ${claimNumber}`
    ).to.contain.text(claimNumber);
  });
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
export function onTab(label: string): void {
  cy.contains(".TabStrip td", label).then((tab) => {
    if (tab.hasClass("TabOn")) {
      return; // We're already on the correct tab.
    }
    cy.wrap(tab).click().should("have.class", "TabOn");
    waitForAjaxComplete();
  });
}

/**
 * Helper to wait for ajax-y actions to complete before proceeding.
 *
 * Note: Please do not add explicit waits here. This function should be fast -
 * it will be called often. Try to find a better way to determine if we can move
 * on with processing (element detection).
 */
export function wait(): void {
  cy.wait("@ajaxRender");
  // cy.get("#disablingLayer").should("not.be.visible");
  cy.root()
    .should(($el) => {
      expect(Cypress.dom.isAttached($el)).to.be.true;
    })
    .closest(`html`)
    .should(($el) => {
      expect(Cypress.dom.isAttached($el)).to.be.true;
    })
    .find(`#disablingLayer`)
    .should(($el) => {
      expect(Cypress.dom.isAttached($el)).to.be.true;
    })
    .should("not.be.visible");
}

export function waitForAjaxComplete(): void {
  cy.window()
    .invoke("axGetAjaxQueueManager")
    .should((q) => {
      const inFlight = Object.values(q.requests).filter(
        // @ts-ignore - ignore uses of Fineos internal window properties.
        (req) => req.state() !== "resolved"
      );
      expect(inFlight, "In-flight Ajax requests should be 0").to.have.length(0);
    });
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
  onTab("Search");
  cy.labelled("Business Type").type(businessType);
  cy.get("input[value='Search']").click();
  clickBottomWidgetButton();
  cy.get("input[type='file']").attachFile(`./${docName}.pdf`);
  clickBottomWidgetButton();
}

export function approveClaim(): void {
  // This button turns out to be unclickable without force, because selecting
  // it seems to scroll it out of view. Force works around that.
  cy.get('a[title="Approve the Pending Leaving Request"]').click({
    force: true,
  });
  assertClaimStatus("Approved");
}

export function withdrawClaim(): void {
  cy.get('a[title="Withdraw the Pending Leave Request"').click({
    force: true,
  });
  cy.get("#leaveRequestWithdrawPopupWidget_PopupWidgetWrapper").within(() => {
    cy.findByLabelText("Withdrawal Reason").select("Employee Withdrawal");
    cy.findByText("OK").click({ force: true });
  });
  assertClaimStatus("Closed");
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

export function enterReducedWorkHours(
  leave_details: ReducedScheduleLeavePeriods
): void {
  const hrs = (minutes: number | null | undefined) => {
    return minutes ? Math.round(minutes / 60) : 0;
  };
  const weekdayInfo = [
    { hours: hrs(leave_details.sunday_off_minutes) },
    { hours: hrs(leave_details.monday_off_minutes) },
    { hours: hrs(leave_details.tuesday_off_minutes) },
    { hours: hrs(leave_details.wednesday_off_minutes) },
    { hours: hrs(leave_details.thursday_off_minutes) },
    { hours: hrs(leave_details.friday_off_minutes) },
    { hours: hrs(leave_details.saturday_off_minutes) },
  ];

  cy.get("input[name*='_hours']").each((input, index) => {
    cy.wrap(input).type(weekdayInfo[index].hours.toString());
  });
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
  evidenceType: string,
  receipt = "Received",
  decision = "Satisfied",
  reason = "Evidence has been reviewed and approved"
): void {
  onTab("Evidence");
  cy.contains(".ListTable td", evidenceType).click({ force: true });
  cy.get("input[type='submit'][value='Manage Evidence']").click({
    force: true,
  });
  // Focus inside popup. Note: There should be no need for an explicit wait here because
  // Cypress will not move on until the popup has been rendered.
  cy.get(".WidgetPanel_PopupWidget").within(() => {
    cy.labelled("Evidence Receipt").select(receipt);
    cy.labelled("Evidence Decision").select(decision);
    cy.labelled("Evidence Decision Reason").type(
      `{selectall}{backspace}${reason}`
    );
    cy.get("input[type='button'][value='OK']").click({ force: true });
  });
  // Wait until the table has updated with the new status before we attempt to move on.
  cy.contains(".ListTable tr", evidenceType).should((row) => {
    expect(row.find("td:nth-child(3)")).to.contain.text(receipt);
    expect(row.find("td:nth-child(5)")).to.contain.text(decision);
  });
}

export function fillAbsencePeriod(claimNumber: string): void {
  assertAdjudicatingClaim(claimNumber);
  onTab("Evidence");
  cy.wait(2000);
  onTab("Certification Periods");
  cy.get("input[value='Prefill with Requested Absence Periods']").click();
  cy.get("#PopupContainer input[value='Yes']").click();
}

export function claimAdjudicationFlow(
  claimNumber: string,
  reason: LeaveReason,
  ERresponse = false
): void {
  const docType = getCertificationDocumentType(reason);

  visitClaim(claimNumber);
  assertClaimStatus("Adjudication");
  onTab("Tasks");
  assertHasTask(getDocumentReviewTaskName(docType));
  assertHasTask("ID Review");
  if (ERresponse) {
    assertHasTask("Employer Approval Received");
  }
  onTab("Absence Hub");
  assertPlanStatus("Applicability", "Applicable");
  assertPlanStatus("Eligibility", "Met");
  cy.get("input[type='submit'][value='Adjudicate']").click();
  markEvidence(docType);
  markEvidence("Identification Proof");
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

export function intermittentClaimAdjudicationFlow(
  claimNumber: string,
  reason: LeaveReason,
  ERresponse = false
): void {
  visitClaim(claimNumber);
  if (ERresponse) {
    assertClaimHasLeaveAdminResponse(true);
    clickBottomWidgetButton("Close");
  }
  assertClaimStatus("Adjudication");
  cy.get("input[type='submit'][value='Adjudicate']").click();
  checkStatus(claimNumber, "Eligibility", "Met");
  markEvidence(getCertificationDocumentType(reason));
  markEvidence("Identification Proof");
  checkStatus(claimNumber, "Evidence", "Satisfied");
  fillAbsencePeriod(claimNumber);
  onTab("Manage Request");
  cy.wait(500);
  cy.get("input[type='submit'][value='Accept']").click();
  cy.wait(500);
  checkStatus(claimNumber, "Availability", "As Certified");
  // Complete Adjudication
  assertAdjudicatingClaim(claimNumber);
  clickBottomWidgetButton("OK");
  // Approve Claim
  if (ERresponse) {
    approveClaim();
  }
  wait();
}

// This is being used for Sally hours to allow us to see payment being made.
export function submitIntermittentActualHours(
  timeSpanHoursStart: string,
  timeSpanHoursEnd: string
): void {
  cy.contains("span[class='LinkText']", "Record Actual").click({ force: true });
  wait();
  cy.contains("tbody", "Episodic").click();
  cy.contains("input", "Record Actual").click();
  cy.get(".popup-container").within(() => {
    cy.wait("@ajaxRender");
    // Wait for focus to be captured on the "Last Day Worked" field. This happens automatically, and only occurs
    // when the popup is ready for interaction. Annoyingly, it gets captured 2x on render, forcing us to wait as well.
    cy.labelled("Last Day Worked").should("have.focus").wait(250);

    const mostRecentSunday = startOfWeek(new Date());
    const startDate = subDays(mostRecentSunday, 13);
    const startDateFormatted = format(startDate, "MM/dd/yyyy");
    const endDateFormatted = format(addDays(startDate, 4), "MM/dd/yyyy");

    cy.labelled("Absence start date")
      .focus()
      .type(`{selectall}{backspace}${startDateFormatted}`)
      .blur()
      // Wait for this element to be detached, then rerendered after being blurred.
      .should(($el) => Cypress.dom.isDetached($el))
      .wait(100);

    cy.labelled("Absence end date")
      .focus()
      // @bc: During a debug session there was a odd failure
      // this wait helps prevent typing in wrong field
      .wait(1000)
      .type(`{selectall}{backspace}${endDateFormatted}`)
      .blur()
      // Wait for this element to be detached, then rerendered after being blurred.
      .should(($el) => Cypress.dom.isDetached($el))
      .wait(100);

    cy.get(
      "input[name*='timeOffAbsencePeriodDetailsWidget_un26_timeSpanHoursStartDate']"
    ).type(`{selectall}{backspace}${timeSpanHoursStart}`);
    cy.get(
      "input[name*='timeOffAbsencePeriodDetailsWidget_un26_timeSpanHoursEndDate']"
    ).type(`{selectall}{backspace}${timeSpanHoursEnd}`);
    cy.get("input[type='submit'][value='OK']").click();
  });
  cy.get("#nextPreviousButtons").within(() => {
    cy.get("input[value*='Next ']").click({ force: true });
  });
  cy.contains("td", "Time off period").click({ force: true });
  wait();
  cy.get("select[name*='reportedBy']").select("Employee");
  wait();
  cy.get("select[name*='receivedVia']").select("Phone");
  wait();
  cy.get("select[name*='managerAccepted']").select("Yes");
  cy.get("input[name*='applyActualTime']").click();
  cy.contains("td", "Time off period").click({ force: true });
  cy.get("#nextPreviousButtons").within(() => {
    cy.get("input[value*='Next ']").click({ force: true });
  });
}

export function mailedDocumentMarkEvidenceRecieved(
  claimNumber: string,
  reason: LeaveReason
): void {
  visitClaim(claimNumber);
  assertClaimStatus("Adjudication");
  onTab("Documents");
  assertHasDocument("Identification Proof");
  const documentType = getCertificationDocumentType(reason);
  uploadDocument("HCP", documentType);
  onTab("Documents");
  assertHasDocument(documentType);
  onTab("Absence Hub");
  cy.get('input[type="submit"][value="Adjudicate"]').click();
  markEvidence(documentType);
  markEvidence("Identification Proof");
  checkStatus(claimNumber, "Evidence", "Satisfied");
  clickBottomWidgetButton();
}

/**
 *Assumes that the ID and certification documents have not been uploaded to the case.
 *The function will upload both ID documents and certification document into fineos.
 *The certfication review and identification proof tasks are both opened and then closed after marking the evidence.
 */
export function reviewMailedDocumentsWithTasks(
  claimNumber: string,
  reason: LeaveReason,
  taskName: string,
  approveDocs = true
): void {
  visitClaim(claimNumber);
  assertClaimStatus("Adjudication");
  onTab("Documents");
  uploadDocument("MA_ID", "Identification proof");
  onTab("Documents");
  assertHasDocument("Identification Proof");
  const documentType = getCertificationDocumentType(reason);
  uploadDocument("HCP", documentType);
  onTab("Documents");
  cy.wait(150);
  assertHasDocument(documentType);
  onTab("Absence Hub");
  openDocTasks(taskName);
  onTab("Absence Hub");
  cy.get('input[type="submit"][value="Adjudicate"]').click();
  const evidenceDecision = approveDocs ? "Satisfied" : "Not Satisfied";
  const evidenceReason = !approveDocs
    ? "Evidence has been reviewed and denied"
    : undefined;
  markEvidence(documentType, undefined, evidenceDecision, evidenceReason);
  markEvidence(
    "Identification Proof",
    undefined,
    evidenceDecision,
    evidenceReason
  );
  checkStatus(claimNumber, "Evidence", evidenceDecision);
  clickBottomWidgetButton();
  for (const task of ["ID Review", taskName]) {
    closeTask(task);
  }
}

export function openDocTasks(taskName: string): void {
  openTask("ID Review");
  openTask(taskName);
}

export function openTask(taskName: string): void {
  onTab("Tasks");
  cy.get('input[type="submit"][value="Add"]').click({ force: true });
  cy.get('span[id="NameSearchWidget"]').within(() => {
    cy.get('input[type="text"]').type(taskName);
    cy.contains("input", "Find").click();
    cy.wait("@ajaxRender");
    cy.wait(250);
  });
  cy.get('span[id="footerButtonsBar"]').within(() => {
    cy.contains("Next").click();
  });
}

export function closeTask(task: string): void {
  onTab("Tasks");
  cy.wait("@ajaxRender");
  cy.wait(150);
  cy.get(`td[title="${task}"]`).click();
  cy.get('input[type="submit"][value="Close"]').click();
}

export function claimExtensionAdjudicationFlow(
  claimNumber: string,
  reason: LeaveReason
): void {
  visitClaim(claimNumber);
  cy.get("input[type='submit'][value='Adjudicate']").click();
  markEvidence(getCertificationDocumentType(reason));
  markEvidence("Identification Proof");
  checkStatus(claimNumber, "Evidence", "Satisfied");
}

export function checkHoursWorkedPerWeek(
  claimNumber: string,
  hours_worked_per_week: number
): void {
  visitClaim(claimNumber);
  assertClaimStatus("Adjudication");
  cy.get('input[type="submit"][value="Adjudicate"]').click();
  onTab("Request Information");
  wait();
  cy.contains(".TabStrip td", "Employment Information").click();
  wait();
  cy.labelled("Hours worked per week").should((input) => {
    expect(
      input,
      `Hours worked per week should be: ${hours_worked_per_week} hours`
    )
      .attr("value")
      .equal(String(hours_worked_per_week));
  });
  clickBottomWidgetButton("OK");
}

export function claimAddTimeAfterApproval(
  claimNumber: string,
  endDate: Date
): void {
  // Adds a leave extension/transition to a claim.
  // This is not the same as updating a claim to adjust the time.
  const newStartDateFormatted = format(
    addDays(new Date(endDate), 1),
    "MM/dd/yyyy"
  );
  const newEndDateFormatted = format(
    addDays(new Date(endDate), 8),
    "MM/dd/yyyy"
  );

  visitClaim(claimNumber);
  onTab("Absence Hub");

  cy.get("a[title='Register a Leave Extension or Transition']").click({
    force: true,
    timeout: 30000,
  });

  onTab("Capture Additional Time");
  cy.get(".header-title").contains("Capture Additional Time");
  cy.wait(500);
  cy.wait("@ajaxRender");

  // This assumes the claim is continuos
  cy.get("input[title='Add Time Off Period']").click();
  cy.wait(500);
  cy.wait("@ajaxRender");
  cy.labelled("Absence status").select("Known");
  cy.get("input[id='timeOffAbsencePeriodDetailsWidget_un19_startDate']").type(
    `{selectall}{backspace}${newStartDateFormatted}{enter}`
  );
  cy.get("input[id='timeOffAbsencePeriodDetailsWidget_un19_endDate']").type(
    `{selectall}{backspace}${newEndDateFormatted}{enter}`
  );

  cy.get(
    "input[name='timeOffAbsencePeriodDetailsWidget_un19_startDateAllDay_CHECKBOX']"
  ).click();
  cy.get(
    "input[name='timeOffAbsencePeriodDetailsWidget_un19_endDateAllDay_CHECKBOX']"
  ).click();
  cy.get("input[title='OK']").click();

  clickBottomWidgetButton("Next");
  cy.wait(500);
  clickBottomWidgetButton("Next");
  cy.wait(500);
  clickBottomWidgetButton("Next");
  cy.wait(500);
  clickBottomWidgetButton("Next");
  cy.wait(500);
  clickBottomWidgetButton("OK");
  cy.wait(1000);
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

export function getIntermittentPaymentAmount(): Cypress.Chainable<string> {
  cy.contains("Absence Paid Leave Case").click();
  wait();
  onTab("Financials");
  onTab("Payment History");
  return cy
    .get(
      '#PaymentHistoryDetailsListviewWidget td[id*="PaymentHistoryDetailsListviewWidget_un46_PaymentHistoryDetailsListviewNetPaymentAmount0"]'
    )
    .invoke("text");
}

export function triggerNoticeRelease(docType: string): void {
  onTab("Task");
  onTab("Processes");
  cy.contains(".TreeNodeElement", docType).click({
    force: true,
  });
  cy.get('input[type="submit"][value="Properties"]').click();
  cy.get('input[type="submit"][value="Continue"]').click();
  cy.contains(".TreeNodeContainer", docType, {
    timeout: 20000,
  })
    .find("input[type='checkbox']")
    .should("be.checked");
}

/**
 * Adding a  Historical Absence case, assumes being navigated to `Absence Hub` tab on the Claim page.
 */
export function addHistoricalAbsenceCase(): void {
  cy.contains("Options").click();
  cy.contains("Add Historical Absence").click();
  cy.findByLabelText("Absence relates to").select("Employee");
  waitForAjaxComplete();
  cy.findByLabelText("Absence Reason").select(
    "Serious Health Condition - Employee"
  );
  waitForAjaxComplete();
  cy.findByLabelText("Qualifier 1").select("Not Work Related");
  waitForAjaxComplete();
  cy.findByLabelText("Qualifier 2").select("Sickness");
  waitForAjaxComplete();
  cy.contains("div", "timeOffHistoricalAbsencePeriodsListviewWidget")
    .find("input")
    .click();
  const mostRecentSunday = startOfWeek(new Date());
  const startDate = subDays(mostRecentSunday, 13);
  const startDateFormatted = format(startDate, "MM/dd/yyyy");
  const endDateFormatted = format(addDays(startDate, 4), "MM/dd/yyyy");
  // Fill in end date
  cy.findByLabelText("End Date").type(
    `{selectall}{backspace}${endDateFormatted}{enter}`
  );
  wait();
  cy.wait(200);
  // Fill start date
  cy.findByLabelText("Start Date").type(
    `{selectall}{backspace}${startDateFormatted}{enter}`
  );
  wait();
  cy.wait(200);
  // First all day checkbox
  cy.get(
    'span[id^="historicalTimeOffAbsencePeriodDetailsWidget"][id$="startDateAllDay_WRAPPER"]'
  ).click();
  wait();
  cy.wait(200);
  // Second all day checkbox
  cy.get(
    'span[id^="historicalTimeOffAbsencePeriodDetailsWidget"][id$="endDateAllDay_WRAPPER"]'
  ).click();
  wait();
  cy.wait(200);

  // Click on Okay to exit popup window
  cy.get(
    'input[id^="addHistoricalTimeOffAbsencePeriodPopupWidget"][id$="okButtonBean"]'
  ).click({ force: true });
  // Select Leave Plan
  cy.contains("div", "historicalAbsenceSelectedLeavePlansListViewWidget")
    .find("input")
    .click();
  wait();
  cy.get(
    "input[name='historicalCasePlanSelectionListviewWidget_un0_Checkbox_RowId_0_CHECKBOX']"
  ).click();
  clickBottomWidgetButton();
  clickBottomWidgetButton();
  // Click on Claimaints name to view their cases
  cy.get(
    'a[id="com.fineos.frontoffice.casemanager.casekeyinformation.CaseKeyInfoBar_un8_KeyInfoBarLink_0"]'
  ).click();
  onTab("Cases");
  cy.get(".ListRowSelected > td").should(($td) => {
    expect($td.eq(4)).to.contain("Absence Historical Case");
  });
  cy.get('input[title="Open"]').click();
}

/**
 * Assumes that current page is the amounts pending tab in a paid leave case.
 * Function will assert that the processing date and period end date are equal
 */
export function assertMatchingPaymentDates(): void {
  cy.get('#amountspendingtabWidget td[id*="processing_date0"]')
    .invoke("text")
    .then((processingDate) => {
      cy.get('#amountspendingtabWidget td[id*="period_end_date0"]')
        .invoke("text")
        .should("eq", processingDate);
    });
}

/**
 * Takes document type and returns fixture file name.
 * @param document_type document type as specified in the `claim.documents`
 * @returns name of the fixture file, see `e2e/cypress/fixtures`
 */
export function getFixtureDocumentName(
  document_type: DocumentUploadRequest["document_type"]
): string {
  switch (document_type) {
    case "Driver's License Mass":
    case "Identification Proof":
    case "Passport":
      return "MA_ID" as const;
    case "Driver's License Other State":
      return "OOS_ID" as const;
    case "Own serious health condition form":
      return "HCP" as const;
    case "Child bonding evidence form":
      return "FOSTER" as const;
    case "Certification Form":
      return "ADOPTION" as const;

    default:
      return "HCP" as const;
  }
}
