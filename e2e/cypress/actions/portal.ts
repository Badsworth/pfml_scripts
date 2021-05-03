import { Credentials } from "../../src/types";
import {
  ApplicationResponse,
  WorkPattern,
  IntermittentLeavePeriods,
  WorkPatternDay,
  ReducedScheduleLeavePeriods,
  PaymentPreference,
  PaymentPreferenceRequestBody,
} from "../../src/api";
import { inFieldset } from "./common";
import {
  extractDebugInfoFromBody,
  extractDebugInfoFromHeaders,
} from "../../src/errors";

export function before(): void {
  // Set the feature flag necessary to see the portal.
  cy.setCookie(
    "_ff",
    JSON.stringify({
      pfmlTerriyay: true,
      claimantShowAuth: true,
      claimantShowMedicalLeaveType: true,
      noMaintenance: true,
      employerShowSelfRegistrationForm: true,
      claimantShowOtherLeaveStep: false,
      claimantAuthThroughApi: true,
      employerShowAddOrganization: true,
      employerShowVerifications: true,
      employerShowDashboard: true,
    }),
    { log: true }
  );

  cy.on("uncaught:exception", (e) => {
    if (e.message.match(/Cannot set property 'status' of undefined/)) {
      return false;
    }
    return true;
  });

  // Setup a route for application submission so we can extract claim ID later.
  cy.intercept({
    method: "POST",
    url: "**/api/v1/applications/*/submit_application",
  }).as("submitClaimResponse");

  // Block new-relic.js outright due to issues with Cypress networking code.
  // Without this block, test retries on the portal error out due to fetch() errors.
  cy.intercept("**/new-relic.js", (req) => {
    req.reply("console.log('Fake New Relic script loaded');");
  });
}

export function onPage(page: string): void {
  cy.url().should("include", `/applications/${page}`);
}

export function submitClaimDirectlyToAPI(scenario: string): void {
  cy.task("generateClaim", scenario).then({ timeout: 40000 }, (claim) => {
    cy.log("submitting", claim);
    cy.task("submitClaimToAPI", claim)
      .then((responseData: unknown) => responseData as ApplicationResponse)
      .then((responseData) => {
        cy.stashLog("claimNumber", responseData.fineos_absence_id);
        cy.stashLog("applicationId", responseData.application_id);
        cy.stashLog("firstName", responseData.first_name);
        cy.stashLog("lastName", responseData.last_name);
      });
  });
}

/**
 * Waits for the claim submission response to come from the API.
 *
 * If an error is received during submission, it enriches the error with additional metadata.
 */
export function waitForClaimSubmission(): Cypress.Chainable<{
  fineos_absence_id: string;
  application_id: string;
}> {
  return cy.wait("@submitClaimResponse").then((xhr) => {
    if (xhr.error) {
      throw new Error(`Error while waiting for claim submission: ${xhr.error}`);
    }
    if (!xhr.response) {
      throw new Error(
        "No response received while waiting for claim submission."
      );
    }

    if (xhr.response.statusCode < 200 || xhr.response.statusCode > 299) {
      const debugInfo: Record<string, string> = {
        ...extractDebugInfoFromHeaders(xhr.response?.headers ?? {}),
        ...extractDebugInfoFromBody(xhr.response?.body),
      };
      const debugInfoString = Object.entries(debugInfo)
        .map(([key, value]) => `${key}: ${value}`)
        .join("\n");
      throw new Error(
        `Application submission failed: ${xhr.request.url} - ${xhr.response.statusMessage} (${xhr.response.statusCode}\n\nDebug Information\n------------------\n${debugInfoString}`
      );
    }

    const body =
      typeof xhr.response.body === "string"
        ? JSON.parse(xhr.response.body)
        : xhr.response.body;

    if (!body.data.fineos_absence_id || !body.data.application_id) {
      throw new Error(
        `Submission response is missing required properties: ${JSON.stringify(
          body
        )}`
      );
    }

    return cy.wrap(
      {
        fineos_absence_id: body.data.fineos_absence_id,
        application_id: body.data.application_id,
      },
      { log: false }
    );
  });
}

export function login(credentials: Credentials): void {
  cy.visit(`${Cypress.env("E2E_PORTAL_BASEURL")}/login`);
  cy.labelled("Email address").type(credentials.username);
  cy.labelled("Password").typeMasked(credentials.password);
  cy.contains("button", "Log in").click({ waitForAnimations: true });
  cy.url().should("not.include", "login");
}

export function logout(): void {
  cy.contains("button", "Log out").click();
  cy.url().should("contain", "/login");
}

export function registerAsClaimant(credentials: Credentials): void {
  cy.visit("/create-account");
  cy.labelled("Email address").type(credentials.username);
  cy.labelled("Password").type(credentials.password);
  cy.contains("button", "Create account").click();
  cy.task("getAuthVerification", credentials.username).then((code) => {
    cy.labelled("6-digit code").type(code as string);
    cy.contains("button", "Submit").click();
  });
}

export function registerAsLeaveAdmin(
  credentials: Credentials,
  fein: string
): void {
  cy.visit("/employers/create-account");
  cy.labelled("Email address").type(credentials.username);
  cy.labelled("Password").type(credentials.password);
  cy.labelled("Employer ID number").type(fein);
  cy.contains("button", "Create account").click();
  cy.task("getAuthVerification", credentials.username as string).then(
    (code: string) => {
      cy.labelled("6-digit code").type(code as string);
      cy.contains("button", "Submit").click();
    }
  );
}

export function employerLogin(credentials: Credentials): void {
  cy.labelled("Email address").type(credentials.username);
  cy.labelled("Password").typeMasked(credentials.password);
  cy.contains("button", "Log in").click();
  cy.url().should("not.include", "login");
}

export function assertLoggedIn(): void {
  cy.contains("button", "Log out").should("be.visible");
}

export function startClaim(): void {
  cy.get('[href="/applications/start/"]').click();
  cy.contains("button", "I understand and agree").click();
  cy.location({ timeout: 30000 }).should((location) => {
    expect(location.pathname, "Expect to be on the checklist page").to.equal(
      "/applications/checklist/"
    );
    expect(location.search, "Expect to have a claim ID").to.include("claim_id");
  });
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
    cy.log("Employer FEIN", application.employer_fein);
    cy.contains("button", "Save and continue").click();
  }

  // Added Phone Section behind Feature Flag
  cy.labelled("Phone number").type(application.phone?.phone_number as string);
  // Answers Number Type
  cy.get(":nth-child(2) > .usa-radio__label").click();
  cy.contains("button", "Save and continue").click();

  cy.labelled("Address").type(
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

  cy.contains("fieldset", "What’s your date of birth?").within(() => {
    const DOB = new Date(application.date_of_birth as string);

    cy.contains("Month").type(String(DOB.getMonth() + 1) as string);
    cy.contains("Day").type(String(DOB.getUTCDate()) as string);
    cy.contains("Year").type(String(DOB.getUTCFullYear()) as string);
  });
  cy.contains("button", "Save and continue").click();

  cy.contains("Do you have a Massachusetts driver’s license or ID card?");
  if (application.has_state_id) {
    cy.contains("Yes").click();
    cy.contains("Enter your license or ID number").type(
      `{selectall}{backspace}${application.mass_id}`
    );
  } else {
    cy.contains("No").click();
  }
  cy.contains("button", "Save and continue").click();

  cy.contains("What’s your Social Security Number?").type(
    `{selectall}{backspace}${application.tax_identifier}`
  );
  cy.contains("button", "Save and continue").click();
}

export function selectClaimType(application: ApplicationRequestBody): void {
  // Preceeded by - "I am on the claims Checklist page";
  // Preceeded by - "I click on the checklist button called {string}"
  //                with the label "Enter leave details"
  const reason = application.leave_details?.reason;
  const reasonQualifier = application.leave_details?.reason_qualifier;
  if (!reason) {
    throw new Error("Claim is missing reason or reason qualifier");
  }
  const reasonMap: Record<typeof reason, string> = {
    "Serious Health Condition - Employee":
      "I can’t work due to an illness, injury, or pregnancy.",
    "Child Bonding":
      "I need to bond with my child after birth, adoption, or foster placement.",
    "Pregnancy/Maternity":
      "I can’t work due to an illness, injury, or pregnancy.",
  };
  cy.contains(reasonMap[reason]).click();
  if (reasonQualifier) {
    const reasonQualifierMap: Record<typeof reasonQualifier, string> = {
      Newborn: "Birth",
      Adoption: "Adoption",
      "Foster Care": "Foster placement",
    };
    if (!(reasonQualifier in reasonQualifierMap)) {
      throw new Error(`Unknown reason qualifier: ${reasonQualifier}`);
    }
    cy.contains(reasonQualifierMap[reasonQualifier]).click();
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
    onPage("leave-period-continuous");
    completeDateForm(leave?.[0]?.start_date, leave?.[0]?.end_date);
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
    "Do you need to work fewer hours than usual for a period of time (reduced leave schedule)?"
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
    onPage("leave-period-reduced-schedule");
    completeDateForm(leave?.[0]?.start_date, leave?.[0]?.end_date);
    cy.contains("button", "Save and continue").click();
    enterReducedWorkHours(leave as ReducedScheduleLeavePeriods[]);
  } else {
    cy.contains("button", "Save and continue").click();
  }
}

export function enterReducedWorkHours(
  leave?: ReducedScheduleLeavePeriods[]
): void {
  if (!leave) {
    throw new Error(
      "Unable to enter reduced work hours - leave was not defined"
    );
  }
  const hrs = (minutes: number | null | undefined) => {
    return minutes ? Math.round(minutes / 60) : 0;
  };
  const weekdayInfo = [
    { day: "Sunday", hours: hrs(leave[0].sunday_off_minutes) },
    { day: "Monday", hours: hrs(leave[0].monday_off_minutes) },
    { day: "Tuesday", hours: hrs(leave[0].tuesday_off_minutes) },
    { day: "Wednesday", hours: hrs(leave[0].wednesday_off_minutes) },
    { day: "Thursday", hours: hrs(leave[0].thursday_off_minutes) },
    { day: "Friday", hours: hrs(leave[0].friday_off_minutes) },
    { day: "Saturday", hours: hrs(leave[0].saturday_off_minutes) },
  ];

  for (const info of weekdayInfo) {
    cy.contains("fieldset", info.day).within(() => {
      cy.labelled("Hours").type(info.hours.toString());
    });
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
    "Do you need to take off work in uneven blocks of time (intermittent leave)?"
  ).within(() => {
    cy.get("input[type='radio']").check(
      application.has_intermittent_leave_periods?.toString() as string,
      {
        force: true,
      }
    );
  });
  const leave = application.leave_details?.intermittent_leave_periods?.[0];
  if (leave) {
    onPage("leave-period-intermittent");
    completeDateForm(leave.start_date, leave.end_date);
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
      "What is your employer’s Employer Identification Number (EIN)?"
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
    if (!(typeof workDay?.minutes === "number") || !workDay?.day_of_week) {
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
  cy.contains("Submit Part 1").click();
}

export function reportOtherLeave(
  application: ApplicationRequestBody,
  otherLeave: boolean
): void {
  clickChecklistButton("Report other leave, income, and benefits");
  cy.contains("No").click();
  cy.contains("button", "Save and continue").click();
  cy.contains("legend", "Will you receive income from any other sources");

  if (otherLeave) {
    cy.contains("Yes").click();
    cy.contains("button", "Save and continue").click();
    cy.contains("h2", "Tell us about your other sources of income");
    cy.contains("Workers Compensation").click();
    if (
      application.leave_details &&
      application.leave_details.continuous_leave_periods
    ) {
      const leave = application.leave_details.continuous_leave_periods;
      const startDate = leave?.[0]?.start_date;
      const endDate = leave?.[0]?.end_date;
      if (!startDate || !endDate) {
        throw new Error("Unable to fill in empty dates.");
      }

      const [startYear, startMonth, startDay] = startDate.split("-");
      const [endYear, endMonth, endDay] = endDate.split("-");
      cy.contains(
        "fieldset",
        "When will you start receiving this income?"
      ).within(() => {
        cy.contains("Month").type(startMonth);
        cy.contains("Day").type(startDay);
        cy.contains("Year").type(startYear);
      });
      cy.contains(
        "fieldset",
        "When will you stop receiving this income?"
      ).within(() => {
        cy.contains("Month").type(endMonth);
        cy.contains("Day").type(endDay);
        cy.contains("Year").type(endYear);
      });
      cy.contains("button", "Save and continue").click();
      cy.contains("Yes").click();
      cy.contains("button", "Save and continue").click();
      cy.contains("h2", "Tell us about previous paid or unpaid leave");
      cy.contains("Yes").click();
      cy.contains("An illness or injury").click();
      cy.contains("fieldset", "When did your leave begin?").within(() => {
        cy.contains("Month").type("1");
        cy.contains("Day").type("1");
        cy.contains("Year").type("2021");
      });
      cy.contains("fieldset", "When did your leave end?").within(() => {
        cy.contains("Month").type("1");
        cy.contains("Day").type("2");
        cy.contains("Year").type("2021");
      });
      cy.contains("button", "Save and continue").click();
    }
  } else {
    cy.contains("No").click();
    cy.contains("button", "Save and continue").click();
    cy.contains("legend", "Have you taken paid or unpaid leave");
    cy.contains("No").click();
    cy.contains("button", "Save and continue").click();
  }
}

// Payment Section Currently Removed
// @Todo: Once this prop has been added back to ApplicationRequestBody

export function addPaymentInfo(
  paymentPreference: PaymentPreferenceRequestBody
): void {
  // Preceeded by - "I am on the claims Checklist page";
  // Preceeded by - "I click on the checklist button called {string}"
  //                with the label "Add payment information"
  const {
    payment_method,
    account_number,
    routing_number,
    bank_account_type,
  } = paymentPreference.payment_preference as PaymentPreference;

  cy.contains("fieldset", "How do you want to get your weekly benefit?").within(
    () => {
      const paymentInfoLabel = {
        Debit: "Direct deposit",
        Check: "Paper check",
        "Elec Funds Transfer": "Direct deposit",
      };
      cy.contains(
        paymentInfoLabel[
          payment_method as "Debit" | "Check" | "Elec Funds Transfer"
        ]
      ).click();
    }
  );
  switch (payment_method) {
    case "Debit":
    case "Elec Funds Transfer":
      cy.labelled("Routing number").type(routing_number as string);
      cy.labelled("Account number").type(account_number as string);
      inFieldset("Account type", () => {
        cy.get("input[type='radio']").check(bank_account_type as string, {
          force: true,
        });
      });
      break;

    default:
      throw new Error("Unknown payment method");
  }
  cy.contains("button", "Submit Part 2").click();
}

export function addId(idType: string): void {
  const docName = idType.replace(" ", "_");
  cy.labelled("Choose files").attachFile({
    filePath: `${docName}.pdf`,
    encoding: "binary",
  });
  cy.contains("button", "Save and continue").click();
}

export function addLeaveDocs(leaveType: string): void {
  cy.labelled("Choose files").attachFile({
    filePath: `${leaveType}.pdf`,
    encoding: "binary",
  });
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
    case "Adoption":
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
      throw new Error(`Unknown Reason Qualifier ${dateType}`);
  }
  cy.contains("button", "Save and continue").click();
}

export function reviewAndSubmit(): void {
  cy.contains("Review and submit application").click({ force: true });
}

export function confirmSubmit(): void {
  // Usually preceeded by - "I am on the claims Confirm page"
  cy.contains("Submit application").click();
  cy.url({ timeout: 20000 }).should("include", "/applications/success");
}

export function goToDashboardFromApplicationsPage(): void {
  cy.contains("Start a new application", {
    timeout: 15000, // Dashboard can take awhile to load due to the number of claims the E2E user has
  }).click();
}

export function goToDashboardFromSuccessPage(): void {
  cy.contains("Return to applications").click();
}

export function confirmClaimSubmissionSucces(): void {
  cy.url().should("include", "/applications/success");
}

export function viewClaim(applicationId: string): void {
  cy.visit(`/applications/checklist/?claim_id=${applicationId}`);
  cy.url().should(
    "include",
    `/applications/checklist/?claim_id=${applicationId}`
  );
}

export function goToUploadCertificationPage(applicationId: string): void {
  cy.visit(`/applications/upload-certification/?claim_id=${applicationId}`);
}

export function completeDateForm(
  startDate?: string | null,
  endDate?: string | null
): void {
  if (!startDate || !endDate) {
    throw new Error("Unable to fill in empty dates.");
  }

  const [startYear, startMonth, startDay] = startDate.split("-");
  const [endYear, endMonth, endDay] = endDate.split("-");
  cy.contains("fieldset", "First day of leave").within(() => {
    cy.contains("Month").type(startMonth);
    cy.contains("Day").type(startDay);
    cy.contains("Year").type(startYear);
  });
  cy.contains("fieldset", "Last day of leave").within(() => {
    cy.contains("Month").type(endMonth);
    cy.contains("Day").type(endDay);
    cy.contains("Year").type(endYear);
  });
}

export function completeIntermittentLeaveDetails(
  leave: IntermittentLeavePeriods
): void {
  cy.contains("fieldset", "How often might you need").within(() => {
    cy.get(
      `input[name='leave_details.intermittent_leave_periods[0].frequency_interval_basis'][value="${leave.frequency_interval_basis}"]`
    ).click({ force: true });
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

export function checkHoursPerWeekLeaveAdmin(hwpw: number): void {
  cy.get("#employer-review-form").should((textArea) => {
    expect(
      textArea,
      `Hours worked per week should be: ${hwpw} hours`
    ).contain.text(String(hwpw));
  });
}

export function vistActionRequiredERFormPage(fineosAbsenceId: string): void {
  cy.visit(
    `/employers/applications/new-application/?absence_id=${fineosAbsenceId}`
  );
  cy.contains("Are you the right person to respond to this application?");
  cy.contains("Yes").click();
  cy.contains("Agree and submit").click();
}

export function respondToLeaveAdminRequest(
  suspectFraud: boolean,
  gaveNotice: boolean,
  approval: boolean
): void {
  cy.contains(
    "fieldset",
    "Do you have any reason to suspect this is fraud?"
  ).within(() => {
    cy.contains("label", suspectFraud ? "Yes (explain below)" : "No").click();
  });
  cy.contains(
    "fieldset",
    "Did the employee give you at least 30 days notice about their leave?"
  ).within(() => {
    cy.contains("label", gaveNotice ? "Yes" : "No (explain below)").click();
  });
  cy.contains(
    "fieldset",
    "Have you approved or denied this leave request?"
  ).within(() => {
    cy.contains("label", approval ? "Approve" : "Deny (explain below)").click();
  });
  if (suspectFraud || !gaveNotice || !approval) {
    cy.get('textarea[name="comment"]').type(
      "This is a generic explanation of the leave admin's response."
    );
  }
  cy.contains("button", "Submit").click();
  cy.contains("Thanks for reviewing the application");
}

export function checkNoticeForLeaveAdmin(
  fineosAbsenceId: string,
  claimantName: string,
  noticeType: string
): void {
  cy.visit(`/employers/applications/status/?absence_id=${fineosAbsenceId}`);

  switch (noticeType) {
    case "approval":
      cy.contains("h1", claimantName).should("be.visible");
      cy.contains("a", "Approval notice").should("be.visible");
      break;

    case "denial":
      cy.contains("h1", claimantName).should("be.visible");
      cy.contains("a", "Denial notice").should("be.visible");
      break;

    case "request for info":
      cy.contains("h1", claimantName).should("be.visible");
      cy.contains("a", "Request for more information").should("be.visible");
      break;

    default:
      throw new Error("Notice Type not Found!");
  }
}

export function confirmEligibleParent(): void {
  cy.contains("button", "I understand and agree").click();
}

export function submitClaimPartOne(application: ApplicationRequestBody): void {
  const reason = application.leave_details && application.leave_details.reason;
  const reasonQualifier =
    application.leave_details && application.leave_details.reason_qualifier;

  clickChecklistButton("Verify your identification");
  verifyIdentity(application, "normal");
  onPage("checklist");
  clickChecklistButton("Enter employment information");
  enterEmployerInfo(application);
  onPage("checklist");
  clickChecklistButton("Enter leave details");
  selectClaimType(application);
  if (
    reason === "Serious Health Condition - Employee" ||
    reason === "Pregnancy/Maternity"
  ) {
    answerPregnancyQuestion(application);
  } else {
    enterBondingDateInfo(application);
  }
  if (reasonQualifier === "Newborn") {
    answerPregnancyQuestion(application);
  }
  answerContinuousLeaveQuestion(application);
  answerReducedLeaveQuestion(application);
  answerIntermittentLeaveQuestion(application);
  onPage("checklist");
  // @Reminder - This section is currenlty being removed
  // Will return once development work is complete
  // reportOtherLeave(application, otherLeave);
  clickChecklistButton("Review and confirm");
  if (reason === "Child Bonding") {
    confirmEligibleParent();
  }
  onPage("review");
  confirmInfo();
}

export function submitPartsTwoThreeNoLeaveCert(
  paymentPreference: PaymentPreferenceRequestBody
): void {
  clickChecklistButton("Add payment information");
  addPaymentInfo(paymentPreference);
  onPage("checklist");
  clickChecklistButton("Upload identification document");
  addId("MA ID");
  cy.wait(1000);
}

export function submitClaimPartsTwoThree(
  application: ApplicationRequestBody,
  paymentPreference: PaymentPreferenceRequestBody
): void {
  const reason = application.leave_details && application.leave_details.reason;
  clickChecklistButton("Add payment information");
  addPaymentInfo(paymentPreference);
  onPage("checklist");
  clickChecklistButton("Upload identification document");
  addId("MA ID");
  onPage("checklist");
  clickChecklistButton("Upload leave certification documents");
  addLeaveDocs(
    reason === "Serious Health Condition - Employee" ? "HCP" : "FOSTER"
  );
  onPage("checklist");
  reviewAndSubmit();
  onPage("review");
  confirmSubmit();
  goToDashboardFromSuccessPage();
  cy.wait(3000);
}

export function verifyLeaveAdmin(withholding: number): void {
  cy.get('a[href="/employers/organizations"]').first().click();
  cy.get('a[href^="/employers/organizations/verify-contributions"]')
    .last()
    .click();
  cy.get('input[id="InputText1"]').type(withholding.toString());
  cy.get('button[type="submit"').click();
  cy.contains("h1", "Thanks for verifying your paid leave contributions");
  cy.contains("p", "Your account has been verified");
  cy.contains("button", "Continue").click();
  cy.get('a[href^="/employers/organizations/verify-contributions"]').should(
    "not.exist"
  );
}

/**
 * Register a leave admin for an additional organization.
 */
export function addOrganization(fein: string, withholding: number): void {
  cy.get('a[href="/employers/organizations/add-organization/"').click();
  cy.get('input[name="ein"]').type(fein);
  cy.get('button[type="submit"').click();
  if (withholding !== 0) {
    cy.get('input[name="withholdingAmount"]').type(withholding.toString());
    cy.get('button[type="submit"').click();
    cy.contains("h1", "Thanks for verifying your paid leave contributions");
    cy.contains("p", "Your account has been verified");
    cy.contains("button", "Continue").click();
    cy.get('a[href^="/employers/organizations/verify-contributions"]').should(
      "not.exist"
    );
  } else {
    assertZeroWithholdings();
  }
}

/**
 * Assertion for error message when adding employer with zero contributions.
 */
export function assertZeroWithholdings(): void {
  cy.contains(
    "p",
    "Your account can’t be verified yet, because your organization has not made any paid leave contributions. Once this organization pays quarterly taxes, you can verify your account and review applications. "
  );
}

export function selectClaimFromEmployerDashboard(
  fineosAbsenceId: string,
  status: "Approved" | "Denied" | "Closed" | "--"
): void {
  cy.get('a[href="/employers/dashboard"]').first().click();

  cy.get("tr")
    .contains(fineosAbsenceId)
    .parent()
    .parent()
    .contains('td[data-label="Status"]', status);
  // TODO: once ALL environments include links to the applications, we should uncomment and make an assertion that the link exists
  // .siblings()
  // .contains(
  //   `a[href="/employers/applications/new-application?absence_id=${fineosAbsenceId}"]`
  // )
}

export function assertUnverifiedEmployerDashboard(): void {
  cy.contains("Verify your account");
  cy.contains("You have not verified any organizations.");
}

export function goToEmployerDashboard(): void {
  cy.get('a[href="/employers/dashboard/"]').first().click();
}
