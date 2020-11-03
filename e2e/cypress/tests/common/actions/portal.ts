import { SimulationClaim } from "@/simulation/types";
import {
  ApplicationResponse,
  WorkPattern,
  IntermittentLeavePeriods,
  WorkPatternDay,
} from "@/api";
import { inFieldset } from "../actions";

export function onPage(page: string): void {
  cy.url().should("include", `/claims/${page}`);
}

export function submittingClaimType(
  claimType: string,
  employeeType: string
): void {
  cy.task("generateClaim", {
    claimType: claimType,
    employeeType: employeeType,
  }).then((claim?: SimulationClaim) => {
    if (!claim) {
      throw new Error("Claim Was Not Generated");
    }
    cy.log("generated claim", claim.claim);
    cy.wrap(claim.claim).as("application");
  });
}

export function submitClaimDirectlyToAPI(
  scenario: string,
  employeeType: string
): void {
  cy.task("generateClaim", {
    claimType: scenario,
    employeeType: employeeType,
  }).then({ timeout: 40000 }, (claim?: SimulationClaim) => {
    if (!claim) {
      throw new Error("Claim Was Not Generated");
    }
    cy.log("submitting", claim);
    cy.task("submitClaimToAPI", claim)
      .then((responseIds: unknown) => responseIds as ApplicationResponse)
      .then((responseIds) => {
        cy.stash("claimNumber", responseIds.fineos_absence_id);
        cy.log("submitted", responseIds.fineos_absence_id);
        cy.stash("applicationId", responseIds.application_id);
        cy.log("submitted", responseIds.application_id);
      });
  });
}

export function login(credentials: Credentials): void {
  // Alias the credentials for later use.
  cy.wrap(credentials).as("credentials");
  cy.visit("/");
  cy.labelled("Email address").type(credentials.username);
  cy.labelled("Password").typeMasked(credentials.password);
  cy.contains("button", "Log in").click();
  cy.url().should("not.include", "login");
}

export function assertLoggedIn(): void {
  cy.contains("button", "Log out").should("be.visible");
}

export function startClaim(): void {
  cy.get('[href="/claims/start/"]').click();
}

export function agreeToStart(): void {
  cy.contains("button", "I understand and agree").click();
}

export function hasClaimId(): void {
  cy.url().should("include", "claim_id");
}

export function startSubmit(
  credentials: Credentials,
  scenario: string,
  employeeType: string
): void {
  submittingClaimType(scenario, employeeType);
  login(credentials);
  startClaim();
  onPage("start");
  agreeToStart();
  hasClaimId();
  onPage("checklist");
}

export function clickChecklistButton(label: string): void {
  cy.contains(label)
    .parents(".display-flex.border-bottom.border-base-light.padding-y-3")
    .contains("a", "Start")
    .click();
}

export function verifyIdentity(
  application: ApplicationRequestBody,
  leaveType: string
): void {
  if (leaveType === "normal") {
    cy.labelled("First name").type(application.first_name as string);
    cy.labelled("Last name").type(application.last_name as string);
    cy.contains("button", "Save and continue").click();
  }

  cy.labelled("Street address 1").type(
    (application.mailing_address &&
      application.mailing_address.line_1) as string
  );
  cy.labelled("City").type(
    (application.mailing_address && application.mailing_address.city) as string
  );
  cy.labelled("State")
    .get("select")
    .select(
      (application.mailing_address &&
        application.mailing_address.state) as string
    );
  cy.labelled("ZIP").type(
    (application.mailing_address && application.mailing_address.zip) as string
  );

  // Answers the question "Do you get your mail at this address?"
  cy.get(":nth-child(1) > .usa-radio__label").click();

  cy.contains("button", "Save and continue").click();

  cy.contains("fieldset", "What's your birthdate?").within(() => {
    const DOB = new Date(application.date_of_birth as string);

    cy.contains("Month").type(String(DOB.getMonth() + 1) as string);
    cy.contains("Day").type(String(DOB.getUTCDate()) as string);
    cy.contains("Year").type(String(DOB.getUTCFullYear()) as string);
  });
  cy.contains("button", "Save and continue").click();

  cy.contains("Do you have a Massachusetts driver's license or ID card?");
  if (application.has_state_id) {
    cy.contains("Yes").click();
    cy.contains("Enter your license or ID number").type(
      `{selectall}{backspace}${application.mass_id}`
    );
  } else {
    cy.contains("No").click();
  }
  cy.contains("button", "Save and continue").click();

  cy.contains("What's your Social Security Number?").type(
    `{selectall}{backspace}${application.tax_identifier}`
  );
  cy.contains("button", "Save and continue").click();
}

export function selectClaimType(application: ApplicationRequestBody): void {
  // Preceeded by - "I am on the claims Checklist page";
  // Preceeded by - "I click on the checklist button called {string}"
  //                with the label "Enter leave details"
  const reason = application.leave_details && application.leave_details.reason;
  const reasonQualifier =
    application.leave_details && application.leave_details.reason_qualifier;
  type ClaimTypePortal = {
    [index: string]: string;
  };
  const claimType: ClaimTypePortal = {
    "Serious Health Condition - Employee":
      "I can’t work due to an illness, injury, or pregnancy.",
    "Child Bonding":
      "I need to bond with my child after birth, adoption, or foster placement.",
    "Care For A Family Member":
      "I need to manage family affairs while a family member is on active duty in the armed forces.",
    "Pregnancy/Maternity":
      "I need to care for a family member who serves in the armed forces.",
  };
  const leaveReason: ClaimTypePortal = {
    Newborn: "Birth",
    Adoption: "Adoption",
    "Foster Care": "Foster placement",
  };
  cy.contains(claimType[reason as string]).click();
  if (reason === "Child Bonding") {
    cy.contains(leaveReason[reasonQualifier as string]).click();
  }
  cy.contains("button", "Save and continue").click();
}

export function answerPregnancyQuestion(
  application: ApplicationRequestBody
): void {
  // if (
  //   application.leave_details?.reason !== "Serious Health Condition - Employee"
  // ) {
  //   throw new Error("Reason besides Serious Health Condition was entered");
  // }
  // Example of selecting a radio button pertaining to a particular question. Scopes the lookup
  // of the "yes" value so we don't select "yes" for the wrong question.
  cy.contains(
    "fieldset",
    "Are you taking medical leave because you are pregnant or recently gave birth?"
  ).within(() => {
    cy.contains(
      application.leave_details?.pregnant_or_recent_birth ? "Yes" : "No"
    ).click();
  });
  cy.contains("button", "Save and continue").click();
}

export function answerContinuousLeaveQuestion(
  application: ApplicationRequestBody
): void {
  if (!application.leave_details) {
    throw new Error("Leave details not provided.");
  }

  const leave = application.leave_details.continuous_leave_periods;

  cy.contains(
    "fieldset",
    "Do you need to take off work completely for a period of time (continuous leave)?"
  ).within(() => {
    cy.get("input[type='radio']").check(
      application.has_continuous_leave_periods?.toString() as string,
      {
        force: true,
      }
    );
  });

  if (application.has_continuous_leave_periods) {
    const startDate = new Date((leave && leave[0].start_date) as string);
    const endDate = new Date((leave && leave[0].end_date) as string);

    onPage("leave-period-continuous");
    completeDateForm(startDate, endDate);
  }
  cy.contains("button", "Save and continue").click();
}

export function answerReducedLeaveQuestion(
  application: ApplicationRequestBody
): void {
  if (!application.leave_details) {
    throw new Error("Leave details not provided.");
  }

  cy.contains(
    "fieldset",
    "Do you need to work a reduced schedule for a period of time (reduced leave schedule)?"
  ).within(() => {
    cy.get("input[type='radio']").check(
      application.has_reduced_schedule_leave_periods?.toString() as string,
      {
        force: true,
      }
    );
  });

  if (application.has_reduced_schedule_leave_periods) {
    const leave = application.leave_details.reduced_schedule_leave_periods;

    const startDate = new Date((leave && leave[0].start_date) as string);
    const endDate = new Date((leave && leave[0].end_date) as string);

    onPage("leave-period-reduced-schedule");
    completeDateForm(startDate, endDate);
  }
  cy.contains("button", "Save and continue").click();
}

export function answerIntermittentLeaveQuestion(
  application: ApplicationRequestBody
): void {
  if (!application.leave_details) {
    throw new Error("Leave details not provided.");
  }

  cy.contains(
    "fieldset",
    "Do you need to take off work at irregular intervals (intermittent leave)?"
  ).within(() => {
    cy.get("input[type='radio']").check(
      application.has_intermittent_leave_periods?.toString() as string,
      {
        force: true,
      }
    );
  });
  if (application.leave_details?.intermittent_leave_periods?.[0]) {
    const leave: IntermittentLeavePeriods | undefined =
      application.leave_details.intermittent_leave_periods[0];
    Object.assign(leave, {
      frequency: 5,
      frequency_interval: 6,
      frequency_interval_basis: "Months",
      duration: 2,
      duration_basis: "Days",
    });

    const startDate = new Date((leave && leave.start_date) as string);
    const endDate = new Date((leave && leave.end_date) as string);
    onPage("leave-period-intermittent");
    completeDateForm(startDate, endDate);
    cy.contains("button", "Save and continue").click();
    completeIntermittentLeaveDetails(leave);
  } else {
    cy.contains("button", "Save and continue").click();
  }
}

export function enterEmployerInfo(application: ApplicationRequestBody): void {
  // Preceeded by - "I am on the claims Checklist page";
  // Preceeded by - "I click on the checklist button called {string}"
  //                with the label "Enter employment information"
  if (application.employment_status === "Employed") {
    cy.labelled(
      "What is your employer's Federal Employer Identification Number (FEIN)?"
    ).type(application.employer_fein as string);
  }
  cy.contains("button", "Save and continue").click();
  if (application.employment_status === "Employed") {
    // @todo: Set to application property once it exists.
    // cy.labelled("On average, how many hours do you work each week?").type("40");
    // cy.contains("button", "Save and continue").click();

    cy.contains(
      "fieldset",
      "Have you told your employer that you are taking leave?"
    ).within(() => {
      cy.contains(
        "label",
        application.leave_details?.employer_notified ? "Yes" : "No"
      ).click();
    });
    if (application.employment_status) {
      cy.contains("fieldset", "When did you tell them?").within(() => {
        const notificationDate = new Date(
          application.leave_details?.employer_notification_date as string
        );
        cy.labelled("Month").type(
          (notificationDate.getMonth() + 1).toString() as string
        );
        cy.labelled("Day").type(
          notificationDate.getUTCDate().toString() as string
        );
        cy.labelled("Year").type(
          notificationDate.getUTCFullYear().toString() as string
        );
      });
    }
    cy.contains("button", "Save and continue").click();
    describeWorkSchedule(application);
  }
}

export function describeWorkSchedule(
  application: ApplicationRequestBody
): void {
  const workScheduleType: WorkPattern["work_pattern_type"] = "Fixed";

  cy.contains("fieldset", "How would you describe your work schedule?").within(
    () => {
      cy.get(`input[value = ${workScheduleType}]`).check({ force: true });
    }
  );
  cy.contains("button", "Save and continue").click();

  if (!application?.work_pattern?.work_pattern_days) {
    throw new Error("Work pattern days must be specified");
  }
  const workSchedule: WorkPatternDay[] =
    application?.work_pattern?.work_pattern_days;

  for (const workDay of workSchedule) {
    if (!workDay?.minutes || !workDay?.day_of_week) {
      throw new Error("Minutes and day of week must be specified");
    }
    if (workDay.minutes % 15 !== 0) {
      throw new Error("Minutes must be multiple of 15");
    }
    const hours = Math.floor(workDay.minutes / 60);
    const minutes = workDay.minutes % 60;
    cy.contains("fieldset", workDay.day_of_week).within(() => {
      cy.labelled("Hours").type(hours.toString());
      cy.labelled("minutes").select(minutes.toString(), {
        force: true,
      });
    });
  }
  cy.contains("button", "Save and continue").click();
}

export function reportOtherBenefits(): void {
  // Preceeded by - "I am on the claims Checklist page";
  // Preceeded by - "I click on the checklist button called {string}"
  //                with the label "Report other leave and benefits"
  cy.contains(
    "fieldset",
    "Will you use any employer-sponsored benefits during your leave?"
  ).within(() => cy.labelled("No").click({ force: true }));
  cy.contains("button", "Save and continue").click();

  cy.contains(
    "fieldset",
    "Will you receive income from any other sources during your leave?"
  ).within(() => cy.labelled("No").click({ force: true }));
  cy.contains("button", "Save and continue").click();

  /* ********** 
    Been removed from flow as 2nd November

    cy.contains(
      "fieldset",
      "Have you taken paid or unpaid leave since"
    ).within(() => cy.labelled("No").click({ force: true }));
    cy.contains("button", "Save and continue").click();
  */
}

export function confirmInfo(): void {
  // Usually preceeded by - "I am on the claims Review page"
  cy.await();
  cy.contains("Submit Part 1").click();

  cy.wait("@submitClaimResponse").then((xhr) => {
    const responseBody = xhr.response.body as Cypress.ObjectLike;
    cy.stash("claimNumber", responseBody.data.fineos_absence_id);
    cy.log("submitted", responseBody.data.fineos_absence_id);
    cy.stash("applicationId", responseBody.data.application_id);
    cy.log("submitted", responseBody.data.application_id);
  });
}

export function addPaymentInfo(application: ApplicationRequestBody): void {
  // Preceeded by - "I am on the claims Checklist page";
  // Preceeded by - "I click on the checklist button called {string}"
  //                with the label "Add payment information"
  const payMethod =
    application.payment_preferences &&
    application.payment_preferences[0].payment_method;
  const accountDetails =
    application.payment_preferences &&
    application.payment_preferences[0].account_details;

  cy.contains("fieldset", "How do you want to get your weekly benefit?").within(
    () => {
      const paymentInfoLabel = {
        ACH: "Direct deposit",
        Check: "Paper check",
        "Gift Card": "Gift Card",
      };
      cy.contains(
        paymentInfoLabel[payMethod as "ACH" | "Check" | "Gift Card"]
      ).click();
    }
  );
  switch (payMethod) {
    case "ACH":
      cy.labelled("Routing number").type(
        accountDetails?.routing_number as string
      );
      cy.labelled("Account number").type(
        accountDetails?.account_number as string
      );
      inFieldset("Account type", () => {
        cy.get("input[type='radio']").check(
          accountDetails?.account_type as string,
          {
            force: true,
          }
        );
      });
      break;

    case "Check":
      /* Currently has been removed from Portal (may return)

        cy.labelled("Street address 1").type(
          application.residential_address?.line_1 as string
        );
        cy.labelled("City").type(application.residential_address?.city as string);
        cy.labelled("State").type(
          application.residential_address?.state as string
        );
        cy.labelled("ZIP Code").type(
          application.residential_address?.zip as string
        );
      */
      break;

    default:
      throw new Error("Unknown payment method");
  }
  cy.contains("button", "Save and continue").click();
}

export function addId(idType: string): void {
  const docName = idType.replace(" ", "_");
  cy.labelled("Choose a file").attachFile(`${docName}.pdf`);
  cy.contains("button", "Save and continue").click();
}

export function addLeaveDocs(leaveType: string): void {
  cy.labelled("Choose a file").attachFile(`${leaveType}.pdf`);
  cy.contains("button", "Save and continue").click();
}

export function enterBondingDateInfo(
  application: ApplicationRequestBody
): void {
  const dateType =
    application.leave_details && application.leave_details.reason_qualifier;
  switch (dateType) {
    case "Newborn":
      cy.contains("fieldset", "When was your child born?").within(() => {
        const DOB = new Date(
          application.leave_details?.child_birth_date as string
        );

        cy.contains("Month").type(String(DOB.getMonth() + 1) as string);
        cy.contains("Day").type(String(DOB.getUTCDate()) as string);
        cy.contains("Year").type(String(DOB.getUTCFullYear()) as string);
      });
      break;

    case "Foster Care":
      cy.contains(
        "fieldset",
        "When did the child arrive in your home through foster care or adoption?"
      ).within(() => {
        const DOB = new Date(
          application.leave_details?.child_placement_date as string
        );

        cy.contains("Month").type(String(DOB.getMonth() + 1) as string);
        cy.contains("Day").type(String(DOB.getUTCDate()) as string);
        cy.contains("Year").type(String(DOB.getUTCFullYear()) as string);
      });
      break;

    default:
      throw new Error("Unknown Reason Qualifier");
  }
  cy.contains("button", "Save and continue").click();
}

export function reviewAndSubmit(): void {
  cy.contains("Review and submit application").click({ force: true });
}

export function confirmSubmit(): void {
  // Usually preceeded by - "I am on the claims Confirm page"
  cy.contains("Submit application").click();
  cy.url({ timeout: 20000 }).should("include", "/claims/success");
}

export function goToDashboard(): void {
  cy.contains("Return to applications").click();
}

export function confirmClaimSubmissionSucces(): void {
  cy.url().should("include", "/claims/success");
}

export function viewClaim(): void {
  cy.unstash("applicationId").then((applicationId) => {
    cy.visit(`/claims/checklist/?claim_id=${applicationId}`);
    cy.url().should("include", `/claims/checklist/?claim_id=${applicationId}`);
  });
}

export function goToIdUploadPage(): void {
  cy.unstash("applicationId").then((applicationId) => {
    cy.visit(`/claims/upload-id/?claim_id=${applicationId}`);
  });
}

export function goToCertificationUploadPage(): void {
  cy.unstash("applicationId").then((applicationId) => {
    cy.visit(`/claims/certification-id/?claim_id=${applicationId}`);
  });
}

export function completeDateForm(startDate: Date, endDate: Date): void {
  cy.contains("fieldset", "First day of leave").within(() => {
    cy.contains("Month").type(String(startDate.getMonth() + 1) as string);
    cy.contains("Day").type(String(startDate.getUTCDate()) as string);
    cy.contains("Year").type(String(startDate.getUTCFullYear()) as string);
  });
  cy.contains("fieldset", "Last day of leave").within(() => {
    cy.contains("Month").type(String(endDate.getMonth() + 1) as string);
    cy.contains("Day").type(String(endDate.getUTCDate()) as string);
    cy.contains("Year").type(String(endDate.getUTCFullYear()) as string);
  });
}

export function completeIntermittentLeaveDetails(
  leave: IntermittentLeavePeriods
): void {
  cy.contains(
    "fieldset",
    "How often might you need to be absent from work?"
  ).within(() => {
    const label = "Irregular over the next 6 months";
    if (leave.frequency_interval_basis !== "Months") {
      throw new Error("Frequency interval should be Months");
    }
    cy.labelled(label).click({ force: true });
  });
  if (!leave.frequency) {
    throw new Error("Frequency must be specified");
  }
  cy.get(
    "input[name='leave_details.intermittent_leave_periods[0].frequency']"
  ).type(leave.frequency.toString());

  cy.contains("fieldset", "How long will an absence typically last?").within(
    () => {
      if (leave.duration_basis !== "Days") {
        throw new Error("Duration basis should be Days");
      }
      cy.labelled("At least a day").click({ force: true });
    }
  );
  if (!leave.duration) {
    throw new Error("Frequency must be specified");
  }
  cy.get(
    "input[name='leave_details.intermittent_leave_periods[0].duration']"
  ).type(leave.duration.toString());

  cy.contains("button", "Save and continue").click();
}

export function confirmEligibleParent(): void {
  cy.contains("button", "I understand and agree").click();
}

export function submitClaimPartOne(application: ApplicationRequestBody): void {
  const reason = application.leave_details && application.leave_details.reason;
  const reasonQualifier =
    application.leave_details && application.leave_details.reason_qualifier;

  clickChecklistButton("Verify your identity");
  verifyIdentity(application, "normal");
  onPage("checklist");
  clickChecklistButton("Enter employment information");
  enterEmployerInfo(application);
  onPage("checklist");
  clickChecklistButton("Enter leave details");
  selectClaimType(application);
  enterBondingDateInfo(application);
  if (reasonQualifier === "Newborn") {
    answerPregnancyQuestion(application);
  }
  answerContinuousLeaveQuestion(application);
  answerReducedLeaveQuestion(application);
  answerIntermittentLeaveQuestion(application);
  onPage("checklist");
  clickChecklistButton("Report other leave, income, and benefits");
  reportOtherBenefits();
  onPage("checklist");
  clickChecklistButton("Review and confirm");
  if (reason === "Child Bonding") {
    confirmEligibleParent();
  }
  onPage("review");
  confirmInfo();
}

export function submitClaimPortal(application: ApplicationRequestBody): void {
  submitClaimPartOne(application);
  addPaymentInfo(application);
  onPage("checklist");
  clickChecklistButton("Upload identity document");
  addId("MA ID");
  onPage("checklist");
  clickChecklistButton("Upload leave certification documents");
  onPage("checklist");
  reviewAndSubmit();
  onPage("review");
  confirmSubmit();
  goToDashboard();
}

// Given I am on the claims "checklist" page
// When I click on the checklist button called "Upload leave certification documents"
// Then I add my leave certification documents
// Given I am on the claims "checklist" page
// Then I should review and submit the application
// Given I am on the claims "review" page
// Then I should have agreed and successfully submitted the claim
// And I should be able to return to the portal dashboard
