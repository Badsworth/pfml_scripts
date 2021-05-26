import { ApplicationRequestBody, ReducedScheduleLeavePeriods } from "_api";
import { format, addMonths, addDays, startOfWeek, subDays } from "date-fns";
import {
  getCertificationDocumentType,
  getDocumentReviewTaskName,
} from "../../src/util/documents";
import { LeaveReason } from "../../src/types";
import { config } from "./common";
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
  claimType?: "military" | "bonding" | "caring",
  application?: ApplicationRequestBody
): void {
  const clickNext = (timeout?: number) =>
    cy
      .get('#navButtons input[value="Next "]', { timeout })
      .first()
      .click({ force: true });
  cy.contains("span", "Create Notification").click();
  clickNext();
  cy.labelled("Hours worked per week").type(
    `{selectall}{backspace}${application?.hours_worked_per_week}`
  );
  clickNext();
  switch (claimType) {
    case "military":
      cy.contains("div", "Out of work for another reason")
        .prev()
        .find("input")
        .click();
      clickNext();
      cy.labelled("Absence relates to").select("Family");
      wait();
      cy.labelled("Absence reason").select("Military Caregiver", {});
      break;

    case "bonding":
      cy.contains(
        "div",
        "Bonding with a new child (adoption/ foster care/ newborn)"
      )
        .prev()
        .find("input")
        .click();
      clickNext();
      cy.labelled("Qualifier 1").select("Foster Care");
      break;

    case "caring":
      cy.contains("div", "Caring for a family member")
        .prev()
        .find("input")
        .click();
      clickNext();
      cy.labelled("Qualifier 1").select("Serious Health Condition");
      cy.wait("@ajaxRender");
      cy.get("#leaveRequestAbsenceRelationshipsWidget").within(() => {
        cy.labelled("Primary Relationship to Employee").select(
          "Sibling - Brother/Sister"
        );
        cy.wait("@ajaxRender");
        cy.wait(200);
        cy.labelled("Qualifier 1").select("Biological");
      });
      clickNext();
      break;

    default:
      throw new Error("ClaimType not found");
  }
  clickNext(5000);

  const {
    has_continuous_leave_periods,
    has_intermittent_leave_periods,
    has_reduced_schedule_leave_periods,
  } = application as ApplicationRequestBody;

  if (has_continuous_leave_periods) {
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
    cy.get('input[title="Quick Add"]').click();
  }

  if (has_intermittent_leave_periods) {
    cy.contains("div.toggle-guidance-row", "Episodic / leave as needed")
      .find("span.slider")
      .click();
    // @ToDo
    // Implement any actions/flows for episodic
  }

  if (has_reduced_schedule_leave_periods) {
    cy.contains("div.toggle-guidance-row", "Reduced work schedule")
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
    enterReducedWorkHours(
      application?.leave_details
        ?.reduced_schedule_leave_periods as ReducedScheduleLeavePeriods[]
    );
    wait();
    cy.get(
      '#reducedScheduleAbsencePeriodDetailsQuickAddWidget input[value="Add"]'
    ).click();
  }

  clickNext(5000);
  if (application?.work_pattern?.work_pattern_type !== "Rotating") {
    cy.labelled("Work Pattern Type").select(
      application?.work_pattern?.work_pattern_type as string
    );
    wait();
  } else {
    // @Reminder: If needed add more dynamic options such as
    // 3 weeks Rotating (currently not needed)
    cy.labelled("Work Pattern Type").select("2 weeks Rotating");
    wait();
  }
  cy.wait("@ajaxRender");
  cy.wait(200);
  cy.labelled("Standard Work Week").click();
  cy.wait(1000);
  cy.get('input[value="Apply to Calendar"]').click({ force: true });
  clickNext();
  if (claimType === "military") {
    cy.labelled("Military Caregiver Description").type(
      "I am a parent military caregiver."
    );
  }
  clickNext(20000);
  cy.contains("div", "Thank you. Your notification has been submitted.");
  clickNext(20000);
}

export function enterReducedWorkHours(
  leave_details: ReducedScheduleLeavePeriods[]
): void {
  const hrs = (minutes: number | null | undefined) => {
    return minutes ? Math.round(minutes / 60) : 0;
  };
  const weekdayInfo = [
    { hours: hrs(leave_details[0].sunday_off_minutes) },
    { hours: hrs(leave_details[0].monday_off_minutes) },
    { hours: hrs(leave_details[0].tuesday_off_minutes) },
    { hours: hrs(leave_details[0].wednesday_off_minutes) },
    { hours: hrs(leave_details[0].thursday_off_minutes) },
    { hours: hrs(leave_details[0].friday_off_minutes) },
    { hours: hrs(leave_details[0].saturday_off_minutes) },
  ];

  cy.get("input[name*='_hours']").each((input, index) => {
    cy.wrap(input).type(weekdayInfo[index].hours.toString());
  });
}

export function additionalEvidenceRequest(claimNumber: string): void {
  assertClaimStatus("Adjudication");
  assertAbsenceCaseNumber(claimNumber as string);
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
  evidenceType: string,
  receipt = "Received",
  decision = "Satisfied",
  reason = "Evidence has been reviewed and approved"
): void {
  onTab("Evidence");
  cy.contains(".ListTable td", evidenceType).click();
  cy.get("input[type='submit'][value='Manage Evidence']").click();
  // Focus inside popup. Note: There should be no need for an explicit wait here because
  // Cypress will not move on until the popup has been rendered.
  cy.get(".WidgetPanel_PopupWidget").within(() => {
    cy.labelled("Evidence Receipt").select(receipt);
    cy.labelled("Evidence Decision").select(decision);
    cy.labelled("Evidence Decision Reason").type(
      `{selectall}{backspace}${reason}`
    );
    cy.get("input[type='button'][value='OK']").click();
    // Wait till modal has fully closed before moving on.
    cy.get("#disablingLayer").should("not.exist");
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

export function intermittentFillAbsencePeriod(claimNumber: string): void {
  assertAdjudicatingClaim(claimNumber);
  onTab("Evidence");
  onTab("Certification Periods");
  cy.get("input[value='Prefill with Requested Absence Periods']").click();
  cy.get("#PopupContainer").within(() => {
    cy.get("input[value='Yes']").click();
  });
  cy.get("#certificationEpisodicLeaveEntitlementWidget").within(() => {
    cy.get("input[name*=episodeDuration]").focus().type("{selectall}5").blur();
    // Wait until the entitlement widget becomes detached from the DOM. At this point, we're in the middle
    // of a rerender, and we just need to wait a little additional time for the render to complete.
    cy.root()
      .should(($el) => !Cypress.dom.isAttached($el))
      .wait(250);
  });
  // This has to be reselected because #certificationEpisodicLeaveEntitlementWidget
  // is removed and rerendered after episode duration is selected.
  cy.get(
    "#certificationEpisodicLeaveEntitlementWidget input[type='button'][value='Apply']"
  ).click();
  cy.get("#PopupContainer").within(() => {
    cy.get("input[value='Yes']").click();
  });
}

export function claimAdjudicationFlow(
  claimNumber: string,
  reason: LeaveReason,
  ERresponse = false
): void {
  const docType = getCertificationDocumentType(
    reason,
    config("HAS_FINEOS_SP") === "true"
  );

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
  markEvidence(
    getCertificationDocumentType(reason, config("HAS_FINEOS_SP") === "true")
  );
  markEvidence("Identification Proof");
  checkStatus(claimNumber, "Evidence", "Satisfied");
  intermittentFillAbsencePeriod(claimNumber);
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
  const documentType = getCertificationDocumentType(
    reason,
    config("HAS_FINEOS_SP") === "true"
  );
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

export function reviewMailedDocumentsWithTasks(
  claimNumber: string,
  reason: LeaveReason,
  uploadedIDProof = true,
  approveDocs = true
): void {
  visitClaim(claimNumber);
  assertClaimStatus("Adjudication");
  onTab("Documents");
  if (uploadedIDProof) {
    assertHasDocument("Identification Proof");
  } else {
    uploadDocument("MA_ID", "Identification proof");
    onTab("Documents");
    assertHasDocument("Identification Proof");
  }
  const documentType = getCertificationDocumentType(
    reason,
    config("HAS_FINEOS_SP") === "true"
  );
  cy.wait(150);
  uploadDocument("HCP", documentType);
  onTab("Documents");
  cy.wait(150);
  assertHasDocument(documentType);
  onTab("Absence Hub");
  openDocTasks();
  onTab("Absence Hub");
  cy.get('input[type="submit"][value="Adjudicate"]').click();
  const evidenceDecision = approveDocs ? "Satisfied" : "Not Satisfied";
  const evidenceReason = !approveDocs
    ? "Evidence has been reviewed and denied"
    : undefined;
  markEvidence(documentType, undefined, evidenceDecision, evidenceReason);
  cy.wait(150);
  markEvidence(
    "Identification Proof",
    undefined,
    evidenceDecision,
    evidenceReason
  );
  checkStatus(claimNumber, "Evidence", evidenceDecision);
  clickBottomWidgetButton();

  for (const task of ["ID Review", "Caring Certification Review"]) {
    closeTask(task);
  }
}

export function openDocTasks(): void {
  openTask("ID Review");
  // replace Caring with argument of Leave Type
  openTask("Caring Certification Review");
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
  cy.wait(150);
  cy.get('input[type="submit"][value="Close"]').click();
  cy.wait(150);
}
export function claimExtensionAdjudicationFlow(claimNumber: string): void {
  visitClaim(claimNumber);
  cy.get("input[type='submit'][value='Adjudicate']").click();
  markEvidence("State managed Paid Leave Confirmation");
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
