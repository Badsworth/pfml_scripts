import {
  Credentials,
  ValidPreviousLeave,
  ValidConcurrentLeave,
  ValidEmployerBenefit,
  ValidOtherIncome,
  FeatureFlags,
} from "../../src/types";
import {
  isNotNull,
  assertIsTypedArray,
  isValidPreviousLeave,
  isValidConcurrentLeave,
  isValidEmployerBenefit,
  isValidOtherIncome,
} from "../../src/util/typeUtils";
import {
  ApplicationResponse,
  IntermittentLeavePeriods,
  PaymentPreference,
  PaymentPreferenceRequestBody,
  ApplicationRequestBody,
  ReducedScheduleLeavePeriods,
  WorkPattern,
  WorkPatternDay,
} from "../../src/api";
import {
  extractDebugInfoFromBody,
  extractDebugInfoFromHeaders,
} from "../../src/errors";
import { config } from "./common";
import { email } from ".";
import { inFieldsetLabelled } from "./common";
import path from "path";
import {
  dateToReviewFormat,
  minutesToHoursAndMinutes,
} from "../../src/util/claims";

/**
 *
 * @param flags set feature flags you want to override from defaults
 * @default {
    pfmlTerriyay: true,
    claimantShowAuth: true,
    claimantShowMedicalLeaveType: true,
    noMaintenance: true,
    employerShowSelfRegistrationForm: true,
    claimantShowOtherLeaveStep: true,
    claimantAuthThroughApi: true,
    employerShowAddOrganization: true,
    employerShowVerifications: true,
    employerShowDashboard: true,
    useNewPlanProofs: config("HAS_FINEOS_SP") === "true",
    showCaringLeaveType: config("HAS_FINEOS_SP") === "true",
  }
 */
export function before(flags?: Partial<FeatureFlags>): void {
  Cypress.config("baseUrl", config("PORTAL_BASEURL"));
  // Set the feature flag necessary to see the portal.
  const defaults: FeatureFlags = {
    pfmlTerriyay: true,
    claimantShowAuth: true,
    claimantShowMedicalLeaveType: true,
    noMaintenance: true,
    employerShowSelfRegistrationForm: true,
    claimantShowOtherLeaveStep: true,
    claimantAuthThroughApi: true,
    employerShowAddOrganization: true,
    employerShowVerifications: true,
    employerShowDashboard: true,
    useNewPlanProofs: true,
    showCaringLeaveType: true,
  };
  cy.setCookie(
    "_ff",
    JSON.stringify(flags ? { ...defaults, ...flags } : defaults),
    { log: true }
  );

  // Setup a route for application submission so we can extract claim ID later.
  cy.intercept({
    method: "POST",
    url: "**/api/v1/applications/*/submit_application",
  }).as("submitClaimResponse");

  cy.intercept(
    /\/api\/v1\/(employers\/claims|applications)\/.*\/documents\/\d+/
  ).as("documentDownload");

  cy.intercept(/\/api\/v1\/claims\?page_offset=\d+$/).as(
    "dashboardDefaultQuery"
  );
  cy.intercept(/\/api\/v1\/claims\?(page_offset=\d+)?&?(order_by)/).as(
    "dashboardClaimQueries"
  );

  deleteDownloadsFolder();
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

/**
 * Delete the downloads folder to mitigate any file conflicts
 */
export function deleteDownloadsFolder(): void {
  cy.task("deleteDownloadFolder", Cypress.config("downloadsFolder"));
}

/**
 * Downloads Legal Notice based on type
 *
 * Also does basic assertion on contents of legal notice doc
 */
export function downloadLegalNotice(claim_id: string): void {
  const downloadsFolder = Cypress.config("downloadsFolder");
  cy.wait("@documentDownload", { timeout: 30000 });
  cy.task("getNoticeFileName", downloadsFolder).then((filename) => {
    expect(
      filename.length,
      "downloads folder should contain only one file"
    ).to.equal(1);
    expect(
      path.extname(filename[0]),
      "Expect file extension to be a PDF"
    ).to.equal(".pdf");
    cy.task("getParsedPDF", path.join(downloadsFolder, filename[0])).then(
      (pdf) => {
        const application_id_from_notice = email.getTextBetween(
          pdf.text,
          "Application ID:",
          "\n"
        );
        expect(
          application_id_from_notice,
          `The claim_id within the legal notice should be: ${application_id_from_notice}`
        ).to.equal(claim_id);
      }
    );
  });
}

export function login(credentials: Credentials): void {
  cy.visit(`${config("PORTAL_BASEURL")}/login`);
  cy.findByLabelText("Email address").type(credentials.username);
  cy.findByLabelText("Password").typeMasked(credentials.password);
  cy.contains("button", "Log in").click({ waitForAnimations: true });
  cy.url().should("not.include", "login");
}

export function logout(): void {
  cy.contains("button", "Log out").click();
  cy.url().should("contain", "/login");
}

export function registerAsClaimant(credentials: Credentials): void {
  cy.visit("/create-account");
  cy.findByLabelText("Email address").type(credentials.username);
  cy.findByLabelText("Password").type(credentials.password);
  cy.contains("button", "Create account").click();
  cy.task("getAuthVerification", credentials.username).then((code) => {
    cy.findByLabelText("6-digit code").type(code as string);
    cy.contains("button", "Submit").click();
  });
}

export function registerAsLeaveAdmin(
  credentials: Credentials,
  fein: string
): void {
  cy.visit("/employers/create-account");
  cy.findByLabelText("Email address").type(credentials.username);
  cy.findByLabelText("Password").type(credentials.password);
  cy.findByLabelText("Employer ID number (EIN)").type(fein);
  cy.contains("button", "Create account").click();
  cy.task("getAuthVerification", credentials.username as string).then(
    (code: string) => {
      cy.findByLabelText("6-digit code").type(code as string);
      cy.contains("button", "Submit").click();
    }
  );
}

export function employerLogin(credentials: Credentials): void {
  cy.findByLabelText("Email address").type(credentials.username);
  cy.findByLabelText("Password").typeMasked(credentials.password);
  cy.contains("button", "Log in").click();
  cy.url().should("not.include", "login");
}

export function assertLoggedIn(): void {
  cy.contains("button", "Log out").should("be.visible");
}

export function startClaim(): void {
  cy.get('[href="/applications/start/"]').click();
  cy.findByText("I understand and agree").click();
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

export function verifyIdentity(application: ApplicationRequestBody): void {
  cy.findByLabelText("First name").type(application.first_name as string);
  cy.findByLabelText("Last name").type(application.last_name as string);
  cy.log("Employer FEIN", application.employer_fein);
  cy.contains("button", "Save and continue").click();

  cy.get("[data-cy='gender-form']").within(() => {
    if (isNotNull(application.gender))
      cy.findByLabelText(application.gender).check();
    cy.contains("button", "Save and continue").click();
  });

  // Added Phone Section behind Feature Flag
  cy.findByLabelText("Phone number").type(
    application.phone?.phone_number as string
  );
  // Answers Number Type
  cy.get(":nth-child(2) > .usa-radio__label").click();
  cy.contains("button", "Save and continue").click();

  cy.findByLabelText("Address").type(
    (application.mailing_address &&
      application.mailing_address.line_1) as string
  );
  cy.findByLabelText("City").type(
    (application.mailing_address && application.mailing_address.city) as string
  );
  cy.findByLabelText("State")
    .get("select")
    .select(
      (application.mailing_address &&
        application.mailing_address.state) as string
    );
  cy.findByLabelText("ZIP").type(
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
  const reasonMap: Record<typeof reason, string | RegExp> = {
    "Serious Health Condition - Employee":
      /I can’t work due to (an|my) illness, injury, or pregnancy./,
    "Child Bonding":
      "I need to bond with my child after birth, adoption, or foster placement.",
    "Pregnancy/Maternity":
      /I can’t work due to (an|my) illness, injury, or pregnancy./,
    "Care for a Family Member": "I need to care for my family member",
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
      cy.findByLabelText("Hours").type(info.hours.toString());
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
    cy.findByLabelText(
      "What is your employer’s Employer Identification Number (EIN)?"
    ).type(application.employer_fein as string);
  }
  cy.contains("button", "Save and continue").click();
  if (application.employment_status === "Employed") {
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
        cy.findByLabelText("Month").type(
          (notificationDate.getMonth() + 1).toString() as string
        );
        cy.findByLabelText("Day").type(
          notificationDate.getUTCDate().toString() as string
        );
        cy.findByLabelText("Year").type(
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
    const [hours, minutes] = minutesToHoursAndMinutes(workDay.minutes);
    cy.contains("fieldset", workDay.day_of_week).within(() => {
      cy.findByLabelText("Hours").type(hours.toString());
      cy.findByLabelText("Minutes").select(minutes.toString(), {
        force: true,
      });
    });
  }
  cy.contains("button", "Save and continue").click();
}

export function addPaymentInfo(
  paymentPreference: PaymentPreferenceRequestBody
): void {
  // Preceeded by - "I am on the claims Checklist page";
  // Preceeded by - "I click on the checklist button called {string}"
  //                with the label "Add payment information"
  const { payment_method, account_number, routing_number, bank_account_type } =
    paymentPreference.payment_preference as PaymentPreference;

  inFieldsetLabelled("How do you want to get your weekly benefit?", () => {
    const paymentInfoLabel: Record<
      NonNullable<PaymentPreference["payment_method"]>,
      string
    > = {
      Debit: "Direct deposit",
      Check: "Paper check",
      "Elec Funds Transfer": "Direct deposit",
    };
    if (payment_method) cy.contains(paymentInfoLabel[payment_method]).click();
  });
  switch (payment_method) {
    case "Debit":
    case "Elec Funds Transfer":
      cy.findByLabelText("Routing number").type(routing_number as string);
      cy.findByLabelText("Account number").type(account_number as string);
      inFieldsetLabelled("Account type", () => {
        cy.get("input[type='radio']").check(bank_account_type as string, {
          force: true,
        });
      });
      break;

    default:
      throw new Error("Unknown payment method");
  }
  cy.findByText("Submit Part 2").click();
}

export function addId(idType: string): void {
  const docName = idType.replace(" ", "_");
  cy.findByLabelText("Choose files").attachFile({
    filePath: `${docName}.pdf`,
    encoding: "binary",
  });
  cy.findByText("Save and continue").click();
}

export function addLeaveDocs(leaveType: string): void {
  cy.findByLabelText("Choose files").attachFile({
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
      inFieldsetLabelled(
        "When did the child arrive in your home through foster care or adoption?",
        () => {
          const DOB = new Date(
            application.leave_details?.child_placement_date as string
          );

          cy.contains("Month").type(String(DOB.getMonth() + 1) as string);
          cy.contains("Day").type(String(DOB.getUTCDate()) as string);
          cy.contains("Year").type(String(DOB.getUTCFullYear()) as string);
        }
      );
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
      // @bc: This label was changed recently: "At least a day" -> "At least one day".
      cy.findByLabelText(/At least (a|one) day/).click({ force: true });
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

export function visitActionRequiredERFormPage(fineosAbsenceId: string): void {
  cy.visit(
    `/employers/applications/new-application/?absence_id=${fineosAbsenceId}`
  );
  cy.contains("Are you the right person to respond to this application?", {
    timeout: 20000,
  });
  cy.contains("Yes").click();
  cy.contains("Agree and submit").click();
}

export function respondToLeaveAdminRequest(
  suspectFraud: boolean,
  gaveNotice: boolean,
  approval: boolean,
  isCaringLeave = false
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
  // caring leave type has an additional question to respond to
  if (isCaringLeave) {
    cy.contains(
      "fieldset",
      "Do you believe the listed relationship is described accurately? (Optional)"
    ).within(() => {
      cy.contains("label", approval ? "Yes" : "No").click();
      cy.wait(150);
    });
    if (!approval) {
      cy.get('textarea[name="relationshipInaccurateReason"]').type(
        "Employee and person receiving care are not related"
      );
    }
  }
  if (suspectFraud || !gaveNotice || !approval) {
    cy.get('textarea[name="comment"]').type(
      "This is a generic explanation of the leave admin's response."
    );
  }

  cy.contains("button", "Submit").click();
  // This step can take a while.
  cy.contains("Thanks for reviewing the application", { timeout: 30000 });
}

export function checkNoticeForLeaveAdmin(
  fineosAbsenceId: string,
  claimantName: string,
  noticeType: string
): void {
  cy.visit(`/employers/applications/status/?absence_id=${fineosAbsenceId}`);

  switch (noticeType) {
    case "approval":
      cy.contains("h1", claimantName, { timeout: 20000 }).should("be.visible");
      cy.findByText("Approval notice (PDF)").should("be.visible").click();
      break;

    case "denial":
      cy.contains("h1", claimantName, { timeout: 20000 }).should("be.visible");
      cy.findByText("Denial notice (PDF)").should("be.visible").click();
      break;

    default:
      throw new Error("Notice Type not Found!");
  }
}

export function confirmEligibleClaimant(): void {
  cy.findByText("I understand and agree").click();
}

export function submitClaimPartOne(application: ApplicationRequestBody): void {
  const reason = application.leave_details?.reason;
  const reasonQualifier = application?.leave_details?.reason_qualifier;

  clickChecklistButton("Verify your identification");
  verifyIdentity(application);
  onPage("checklist");
  clickChecklistButton("Enter employment information");
  enterEmployerInfo(application);

  onPage("checklist");
  clickChecklistButton("Enter leave details");
  selectClaimType(application);

  switch (reason) {
    case "Serious Health Condition - Employee":
    case "Pregnancy/Maternity":
      answerPregnancyQuestion(application);
      break;

    case "Care for a Family Member":
      answerCaringLeaveQuestions(application);
      break;
    default:
      enterBondingDateInfo(application);
      break;
  }

  if (reasonQualifier === "Newborn") answerPregnancyQuestion(application);

  answerContinuousLeaveQuestion(application);
  answerReducedLeaveQuestion(application);
  answerIntermittentLeaveQuestion(application);
  onPage("checklist");
  clickChecklistButton("Report other leave, benefits, and income");
  reportOtherLeavesAndBenefits(application);

  clickChecklistButton("Review and confirm");
  if (reason === "Child Bonding" || reason === "Care for a Family Member") {
    confirmEligibleClaimant();
  }
  onPage("review");
  cy.findByText("Submit Part 1").click();
}

export function answerCaringLeaveQuestions(
  application: ApplicationRequestBody
): void {
  cy.contains("I am caring for my sibling.").click();
  cy.contains("Save and continue").click();
  cy.findByLabelText("First name").type(
    application.leave_details?.caring_leave_metadata
      ?.family_member_first_name as string
  );
  cy.findByLabelText("Last name").type(
    application.leave_details?.caring_leave_metadata
      ?.family_member_first_name as string
  );
  cy.contains("Save and continue").click();
  const familyMemberDOB = new Date(
    application.leave_details?.caring_leave_metadata
      ?.family_member_date_of_birth as string
  );
  cy.findByLabelText("Month").type(
    (familyMemberDOB.getMonth() + 1).toString() as string
  );
  cy.findByLabelText("Day").type(
    familyMemberDOB.getUTCDate().toString() as string
  );
  cy.findByLabelText("Year").type(
    familyMemberDOB.getUTCFullYear().toString() as string
  );
  cy.contains("Save and continue").click();
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
    cy.get('button[type="submit"]').click();
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
    /(Employer has no verification data|Your account can’t be verified yet, because your organization has not made any paid leave contributions. Once this organization pays quarterly taxes, you can verify your account and review applications)/
  );
}
export type DashboardClaimStatus = "Approved" | "Denied" | "Closed" | "--";
export function selectClaimFromEmployerDashboard(
  fineosAbsenceId: string,
  status: DashboardClaimStatus
): void {
  goToEmployerDashboard();
  cy.contains("tr", fineosAbsenceId).should("contain.text", status);
  cy.findByText(fineosAbsenceId).click();
}

export function assertUnverifiedEmployerDashboard(): void {
  cy.contains("Verify your account");
  cy.contains("You have not verified any organizations.");
}

export function goToEmployerDashboard(): void {
  cy.get('a[href="/employers/dashboard/"]').first().click();
}

export function assertLeaveDatesAsLA(startDate: string, endDate: string): void {
  cy.findByText("Leave duration").parent().contains(startDate);
  cy.findByText("Leave duration").parent().contains(endDate);
}
/**
 * Sequentially reports all of the given previous leaves.
 * Assumes browser is navigated to either
 * @param previous_leaves
 */
function reportPreviousLeaves(previous_leaves: ValidPreviousLeave[]): void {
  previous_leaves.forEach((leave, index) => {
    reportPreviousLeave(leave, index);
    // if there are any more leaves to report - click the button
    if (index < previous_leaves.length - 1)
      cy.contains("button", "Add another previous leave").click();
  });
  cy.contains("button", "Save and continue").click();
}

/**
 * Map the leave reasons accepted by API to current text used by the portal.
 */
const leaveReasonMap: Record<ValidPreviousLeave["leave_reason"], string> = {
  "Caring for a family member with a serious health condition":
    "Caring for a family member",
  "An illness or injury": "An illness or injury",
  Pregnancy: "Pregnancy",
  "Bonding with my child after birth or placement":
    "Bonding with my child after birth or placement",
  "Managing family affairs while a family member is on active duty in the armed forces":
    "Managing family affairs while a family member was on active duty in the armed forces",
  "Caring for a family member who serves in the armed forces":
    "Caring for a family member who served in the armed forces",
  Unknown: "",
};

/**
 * Fills out the previous leave form for the given leave.
 * @param leave valid previous leave object
 * @param index the number of the leave being reported
 */
function reportPreviousLeave(leave: ValidPreviousLeave, index: number) {
  inFieldsetLabelled(`Previous leave ${index + 1}`, () => {
    if (leave.type === "other_reason")
      cy.findByLabelText(leaveReasonMap[leave.leave_reason]).click({
        force: true,
      });
    inFieldsetLabelled("Did you take leave from this employer?", () => {
      cy.findByLabelText("Yes").check({ force: true });
    });

    fillDateFieldset(
      "What was the first day of this leave?",
      leave.leave_start_date
    );
    fillDateFieldset(
      "What was the last day of this leave?",
      leave.leave_end_date
    );

    inFieldsetLabelled(
      "How many hours would you normally have worked per week at the time you took this leave?",
      () => {
        const [hours, minutes] = minutesToHoursAndMinutes(
          leave.worked_per_week_minutes
        );
        cy.contains("Hours").type(hours.toString());
        cy.contains("Minutes").type(minutes.toString());
      }
    );

    inFieldsetLabelled(
      "What was the total number of hours you took off?",
      () => {
        if (leave.leave_minutes) {
          const [hours, minutes] = minutesToHoursAndMinutes(
            leave.leave_minutes
          );
          cy.contains("Hours").type(hours.toString());
          cy.contains("Minutes").type(minutes.toString());
        }
      }
    );
  });
}

/**
 * Report Accrued(Concurrent) leave. Must be navigated to the concurrent leave form.
 * @param accruedLeave - concurrent leave object with all the required properties.
 */
function reportAccruedLeave(accruedLeave: ValidConcurrentLeave): void {
  inFieldsetLabelled(
    "Will you use accrued paid leave from this employer?",
    () => {
      cy.findByLabelText(
        accruedLeave.is_for_current_employer ? "Yes" : "No"
      ).check({
        force: true,
      });
    }
  );
  fillDateFieldset(
    "What is the first day of this leave",
    accruedLeave.leave_start_date
  );
  fillDateFieldset(
    "What is the last day of this leave?",
    accruedLeave.leave_end_date
  );
  cy.contains("button", "Save and continue").click();
}

const benefitTypeMap: Record<ValidEmployerBenefit["benefit_type"], string> = {
  "Family or medical leave insurance": "Family or medical leave insurance",
  "Permanent disability insurance": "Permanent disability insurance",
  "Short-term disability insurance": "Temporary disability insurance",
  "Accrued paid leave": "",
  Unknown: "",
};
/**
 * Fills out the employer-sponsored benefits form for a given benefit.
 * @param benefit
 * @param index
 */
function reportEmployerBenefit(benefit: ValidEmployerBenefit, index: number) {
  inFieldsetLabelled(`Benefit ${index + 1}`, () => {
    inFieldsetLabelled("What kind of employer-sponsored benefit is it?", () => {
      cy.findByLabelText(benefitTypeMap[benefit.benefit_type]).click({
        force: true,
      });
    });

    fillDateFieldset(
      "What is the first day of leave from work that this benefit will pay you for?",
      benefit.benefit_start_date
    );

    fillDateFieldset(
      "What is the last day of leave from work that this benefit will pay you for?",
      benefit.benefit_end_date
    );

    inFieldsetLabelled(
      "Does this employer-sponsored benefit fully replace your wages?",
      () => {
        cy.findByLabelText(
          benefit.is_full_salary_continuous ? "Yes" : "No"
        ).click({
          force: true,
        });
      }
    );
  });
}

/**
 * Report employer benefits. Must be navigated to the employer benefits form.
 * @param benefits - array of EmployerBenefit objects with all the required properties.
 */
function reportEmployerBenefits(benefits: ValidEmployerBenefit[]) {
  cy.contains(
    "form",
    // BC for "leave dates for paid leave" -> "leave dates for paid leave from PFML" text change.
    /Tell us about employer-sponsored benefits you will use during your leave dates for paid leave( from PFML)?\./
  ).within(() => {
    benefits.forEach((benefit, index) => {
      reportEmployerBenefit(benefit, index);
      // if there are any more leaves to report - click the button
      if (index < benefits.length - 1)
        cy.contains("button", "Add another benefit").click();
    });
    cy.contains("button", "Save and continue").click();
  });
}

const otherIncomeTypeMap: Record<ValidOtherIncome["income_type"], string> = {
  "Disability benefits under Gov't retirement plan":
    "Disability benefits under a governmental retirement plan",
  "Earnings from another employment/self-employment":
    "Earnings or benefits from another employer, or through self-employment",
  "Jones Act benefits": "Jones Act benefits",
  "Railroad Retirement benefits": "Railroad Retirement benefits",
  "Unemployment Insurance": "Unemployment Insurance",
  "Workers Compensation": "Workers Compensation",
  SSDI: "Social Security Disability Insurance",
};

/**
 * Fills out the other income form for a given income.
 * @param income
 * @param index
 */
function reportOtherIncome(income: ValidOtherIncome, index: number): void {
  inFieldsetLabelled(`Income ${index + 1}`, () => {
    inFieldsetLabelled("What kind of income is it?", () => {
      cy.findByLabelText(otherIncomeTypeMap[income.income_type]).click({
        force: true,
      });
    });

    fillDateFieldset(
      "What is the first day of your leave that this income will pay you for?",
      income.income_start_date
    );
    fillDateFieldset(
      "What is the last day of your leave that this income will pay you for?",
      income.income_end_date
    );

    inFieldsetLabelled("How much will you receive?", () => {
      cy.findByLabelText("Amount").type(`${income.income_amount_dollars}`);

      const frequencyMap: Record<
        ValidOtherIncome["income_amount_frequency"],
        string
      > = {
        "In Total": "All at once",
        "Per Day": "Daily",
        "Per Week": "Weekly",
        "Per Month": "Monthly",
      };

      cy.findByLabelText("Frequency").select(
        frequencyMap[income.income_amount_frequency]
      );
    });
  });
}

/**
 * Report other incomes. Must be navigated to the other incomes form.
 * @param other_incomes - array of OtherIncome objects with all the required properties.
 */
("Tell us about your other sources of income during your leave dates for paid leave from PFML.");
function reportOtherIncomes(other_incomes: ValidOtherIncome[]): void {
  cy.contains(
    "form",
    // BC for "leave dates for paid leave" -> "leave dates for paid leave from PFML" text change.
    /Tell us about your other sources of income during your leave dates for paid leave( from PFML)?\./
  ).within(() => {
    other_incomes.forEach((income, index) => {
      reportOtherIncome(income, index);
      // if there are any more leaves to report - click the button
      if (index < other_incomes.length - 1)
        cy.contains("button", "Add another income").click();
    });
    cy.contains("button", "Save and continue").click();
  });
}

/**
 * Report all of the leaves and benefits within the claim.
 * Assumes starting at the first page of reporting other leaves & benefits.
 * @param claim
 */
function reportOtherLeavesAndBenefits(claim: ApplicationRequestBody): void {
  const { previous_leaves_other_reason, previous_leaves_same_reason } = claim;
  //Tell us about your previous leave.
  cy.contains("Save and continue").click();

  // Same reason leaves are reported separately
  // Did you take other leave for the same reason as in current application?
  cy.url().should("include", "previous-leaves-same-reason");
  if (previous_leaves_same_reason?.length) {
    assertIsTypedArray(previous_leaves_same_reason, isValidPreviousLeave);

    cy.findByLabelText("Yes").click({ force: true });
    cy.contains("button", "Save and continue").click();

    reportPreviousLeaves(previous_leaves_same_reason);
  } else {
    cy.findByLabelText("No").click({ force: true });
    cy.contains("button", "Save and continue").click();
  }

  // Did you take other leave for a reason different from current application?
  cy.url().should("include", "previous-leaves-other-reason");
  if (previous_leaves_other_reason?.length) {
    assertIsTypedArray(previous_leaves_other_reason, isValidPreviousLeave);

    cy.findByLabelText("Yes").click({ force: true });
    cy.contains("button", "Save and continue").click();

    reportPreviousLeaves(previous_leaves_other_reason);
  } else {
    cy.findByLabelText("No").click({ force: true });
    cy.contains("button", "Save and continue").click();
  }

  cy.contains(
    "form",
    // @bc: This title was changed: "... your PFML leave." -> "... your paid leave from PFML."
    /Tell us about the accrued paid leave you'll use during your (paid|PFML) (leave.|leave from PFML.)/
  ).submit();

  cy.contains(
    "form",
    "Will you use any employer-sponsored accrued paid leave during your paid leave from PFML?"
  )
    .within(() => {
      cy.findByLabelText(claim.concurrent_leave ? "Yes" : "No").check({
        force: true,
      });
    })
    .submit();
  if (isValidConcurrentLeave(claim.concurrent_leave))
    reportAccruedLeave(claim.concurrent_leave);

  cy.contains(
    "form",
    "Tell us about other benefits and income you will use during your paid leave from PFML."
  ).submit();

  cy.contains(
    "form",
    "Will you use any employer-sponsored benefits from this employer during your paid leave from PFML?"
  ).within(() => {
    cy.findByLabelText(claim.employer_benefits ? "Yes" : "No").click({
      force: true,
    });
    cy.contains("Save and continue").click();
  });

  if (claim.employer_benefits?.length) {
    assertIsTypedArray(claim.employer_benefits, isValidEmployerBenefit);
    reportEmployerBenefits(claim.employer_benefits);
  }

  cy.contains(
    "form",
    "Will you receive income from any other sources during your leave dates for paid leave?"
  ).within(() => {
    cy.findByLabelText(claim.other_incomes ? "Yes" : "No", {
      exact: false,
    }).click({
      force: true,
    });
    cy.contains("Save and continue").click();
  });

  // Tell us about your other sources of income during your leave dates for paid leave.
  if (claim.other_incomes?.length) {
    assertIsTypedArray(claim.other_incomes, isValidOtherIncome);
    reportOtherIncomes(claim.other_incomes);
  }
}

/**
 * Fills date fieldset component within the portal.
 * @param caption Fieldset caption
 * @param date in the format of yyyy-mm-dd
 * @example
 * fillDateFieldset("What was the first day of this leave?", "2021-01-17")
 */
export function fillDateFieldset(caption: string, date: string): void {
  const [year, month, day] = date.split("-");
  inFieldsetLabelled(caption, () => {
    cy.contains("Month").type(month);
    cy.contains("Day").type(day);
    cy.contains("Year").type(year);
  });
}
type UploadAdditonalDocumentOptions =
  | "Massachusetts driver’s license or ID"
  | "Different identification documentation"
  | "Certification";

export function uploadAdditionalDocument(
  fineosClaimId: string,
  type: UploadAdditonalDocumentOptions,
  docName: string
): void {
  cy.contains("article", fineosClaimId).within(() => {
    cy.contains("Upload additional documents").click();
  });
  cy.contains("label", type).click();
  cy.contains("button", "Save and continue").click();
  if (type !== "Certification") {
    addId(docName);
  } else {
    addLeaveDocs(docName);
  }
  cy.contains("You successfully submitted your documents");
}

/**
 * @note Following section is related to claim amendments & review by Leave Admins
 * All of the functions assume you are navigated to the claim review page.
 */

const leaveAdminLeaveResponMap: Record<
  ValidPreviousLeave["leave_reason"],
  string
> = {
  "An illness or injury": "An illness or injury",
  "Bonding with my child after birth or placement":
    "Bonding with their child after birth or placement",
  "Caring for a family member who serves in the armed forces":
    "Caring for a family member who served in the armed forces",
  "Caring for a family member with a serious health condition":
    "Caring for a family member",
  "Managing family affairs while a family member is on active duty in the armed forces":
    "Managing family affairs while a family member was on active duty in the armed forces",
  Pregnancy: "Pregnancy",
  Unknown: "",
};

export function amendWorkingHours(amendedHours: number): void {
  cy.findByText("Weekly hours worked")
    .parent()
    .parent()
    .findByText("Amend")
    .click();
  cy.findByLabelText(
    "On average, how many hours does the employee work each week?"
  ).type(`{selectAll}{backspace}${amendedHours}`);
}

/**
 * In the LA review screen we find the needed leave by the combination of it's dates & leave reason
 */
type LeaveIdentifier = Pick<
  ValidPreviousLeave,
  "leave_start_date" | "leave_end_date" | "leave_reason"
>;
/**
 * Finds a past leave and amends it with given information.
 * @param identifier Leave dates and leave reason in an object.
 * @param amendments Full data of the amended leave, think of PUT instead of PATCH.
 */
export function amendPreviousLeave(
  identifier: LeaveIdentifier,
  amendedLeave: ValidPreviousLeave
): void {
  // Setup the regex template
  // There's no unqiue identifier for listed leaves, so we have to use a combination of dates and reason.
  const template = `${dateToReviewFormat(
    identifier.leave_start_date
  )}.*${dateToReviewFormat(identifier.leave_end_date)}.*${
    leaveAdminLeaveResponMap[identifier.leave_reason]
  }`;
  const selector = new RegExp(template);
  cy.contains("tr", selector).findByText("Amend").click();
  // The next table row will now contain the amendment form.
  cy.contains("tr", selector)
    .next()
    .within(() => fillPreviousLeaveData(amendedLeave));
}

export function addPreviousLeave(leave: ValidPreviousLeave): void {
  cy.findByText("Add another previous leave").click();
  // The table's second to last row will be the new leave form.
  // The last row is the "Add another previous leave" button
  cy.contains("tbody", "Add a new previous leave")
    .children()
    .eq(-2)
    .within(() => {
      fillPreviousLeaveData(leave);
    });
}

export function assertPreviousLeave(leave: ValidPreviousLeave): void {
  const template = `${dateToReviewFormat(
    leave.leave_start_date
  )}.*${dateToReviewFormat(leave.leave_end_date)}.*${
    leaveAdminLeaveResponMap[leave.leave_reason]
  }`;
  const selector = new RegExp(template);

  cy.contains("table", "Leave type").within(() => {
    cy.contains("tr", selector).should(($tr) => {
      expect($tr.html()).to.match(selector);
    });
  });
}

function fillPreviousLeaveData(leave: ValidPreviousLeave): void {
  const isForSameReason = leave.type === "same_reason";
  // Select leave type
  inFieldsetLabelled(
    "Was this leave for the same reason as their paid leave request?",
    () => cy.findByText(isForSameReason ? "Yes" : "No").click()
  );
  // Select leave reason if needed
  if (!isForSameReason)
    inFieldsetLabelled("Why did this employee need to take leave?", () =>
      cy.findByText(`${leaveAdminLeaveResponMap[leave.leave_reason]}`).click()
    );
  // Fill start date
  fillDateFieldset(
    "When did the employee's leave start?",
    leave.leave_start_date
  );
  // Fill end date
  fillDateFieldset("When did the employee's leave end?", leave.leave_end_date);
}

export function assertEmployerBenefit(benefit: ValidEmployerBenefit): void {
  const template = `${dateToReviewFormat(
    benefit.benefit_start_date
  )}.*${dateToReviewFormat(benefit.benefit_end_date)}.*${benefit.benefit_type}`;
  const selector = new RegExp(template);
  cy.contains("table", "Benefit type").within(($table) => {
    expect($table.html()).to.match(selector);
  });
}

export function addEmployerBenefit(benefit: ValidEmployerBenefit): void {
  // BC: Add a benefit -> Add an employer-sponsored benefit.
  cy.findByText(
    /(Add a benefit|Add an(other)? employer-sponsored benefit)/
  ).click();
  // The table's second to last row will be the new benefit form.
  // The last row is the "Add another previous leave" button
  cy.contains("tbody", "Add an employer-sponsored benefit")
    .children()
    .eq(-2)
    .within(() => {
      fillEmployerBenefitData(benefit);
    });
}

export function amendLegacyBenefit(
  identifier: Pick<
    ValidEmployerBenefit,
    "benefit_start_date" | "benefit_end_date" | "benefit_type"
  >,
  amendedBenefit: ValidEmployerBenefit
): void {
  // Setup the regex template
  // There's no unqiue identifier for listed leaves, so we have to use a combination of dates and reason.
  const template = `${dateToReviewFormat(
    identifier.benefit_start_date
  )}.*${dateToReviewFormat(identifier.benefit_end_date)}.*${
    benefitTypeMap[amendedBenefit.benefit_type]
  }`;
  const selector = new RegExp(template);
  cy.contains("tr", selector).findByText("Amend").click();
  // The next table row will now contain the amendment form.
  cy.contains("tr", selector)
    .next()
    .within(() => {
      fillDateFieldset(
        "What is the first day of leave from work that this benefit will pay your employee for?",
        amendedBenefit.benefit_start_date
      );
      fillDateFieldset(
        "What is the last day of leave from work that this benefit will pay your employee for?",
        amendedBenefit.benefit_end_date
      );
      inFieldsetLabelled("How much will your employee receive?", () => {
        cy.findByLabelText("Amount").type(
          `{selectAll}{backspace}${amendedBenefit.benefit_amount_dollars}`
        );

        /**
         * @todo
         * Check if other selects in LA and claimant portals also
         * have the 'value' attribute of their options match the API types.
         * If so - it may make sense to create a custom comman for this and get rid of some of those maps.
         */
        const frequencyMap: Record<
          ValidEmployerBenefit["benefit_amount_frequency"],
          string
        > = {
          "Per Day": "Daily",
          "Per Week": "Weekly",
          "Per Month": "Monthly",
          "In Total": "All at once",
          Unknown: "Unknown",
        };
        cy.findByLabelText("Frequency").select(
          frequencyMap[amendedBenefit.benefit_amount_frequency]
        );
      });
    });
}

export function amendEmployerBenefit(
  identifier: Pick<
    ValidEmployerBenefit,
    "benefit_start_date" | "benefit_end_date" | "benefit_type"
  >,
  amendedBenefit: ValidEmployerBenefit
): void {
  // Setup the regex template
  // There's no unqiue identifier for listed leaves, so we have to use a combination of dates and reason.
  const template = `${dateToReviewFormat(
    identifier.benefit_start_date
  )}.*${dateToReviewFormat(identifier.benefit_end_date)}.*${
    benefitTypeMap[amendedBenefit.benefit_type]
  }`;
  const selector = new RegExp(template);
  cy.contains("tr", selector).findByText("Amend").click();
  // The next table row will now contain the amendment form.
  cy.contains("tr", selector)
    .next()
    .within(() => {
      fillEmployerBenefitData(amendedBenefit);
    });
}

function fillEmployerBenefitData(benefit: ValidEmployerBenefit): void {
  inFieldsetLabelled("What kind of employer-sponsored benefit is it?", () =>
    cy.findByText(benefitTypeMap[benefit.benefit_type]).click()
  );
  fillDateFieldset(
    "What is the first day of leave from work that this benefit will pay your employee for?",
    benefit.benefit_start_date
  );
  fillDateFieldset(
    "What is the last day of leave from work that this benefit will pay your employee for?",
    benefit.benefit_end_date
  );
  const isSalaryReplacement = benefit.is_full_salary_continuous;
  inFieldsetLabelled(
    "Does this employer-sponsored benefit fully replace your employee's wages?",
    () => cy.findByText(isSalaryReplacement ? "Yes" : "No").click()
  );
  if (!isSalaryReplacement)
    inFieldsetLabelled("How much will your employee receive?", () => {
      cy.findByLabelText("Amount").type(
        `{selectAll}{backspace}${benefit.benefit_amount_dollars}`
      );

      /**
       * @todo
       * Check if other selects in LA and claimant portals also
       * have the 'value' attribute of their options match the API types.
       * If so - it may make sense to create a custom comman for this and get rid of some of those maps.
       */
      const frequencyMap: Record<
        ValidEmployerBenefit["benefit_amount_frequency"],
        string
      > = {
        "Per Day": "Daily",
        "Per Week": "Weekly",
        "Per Month": "Monthly",
        "In Total": "All at once",
        Unknown: "Unknown",
      };
      cy.findByLabelText("Frequency").select(
        frequencyMap[benefit.benefit_amount_frequency]
      );
    });
}

export function addConcurrentLeave(leave: ValidConcurrentLeave): void {
  cy.findByText(/Add (a concurrent|an accrued paid) leave/).click();
  cy.contains("tr", "Add an accrued paid leave").within(() => {
    fillDateFieldset("When did the leave begin?", leave.leave_start_date);
    fillDateFieldset("When did the leave end?", leave.leave_end_date);
  });
}

export function assertConcurrentLeave(leave: ValidConcurrentLeave): void {
  const template = `${dateToReviewFormat(
    leave.leave_start_date
  )}.*${dateToReviewFormat(leave.leave_end_date)}`;
  const selector = new RegExp(template);

  cy.findByText("Concurrent accrued paid leave")
    .next()
    .next()
    .should(($table) => {
      expect($table.html()).to.match(selector);
    });
}

/**
 * Assert leave type of the claim during the review.
 * @param leaveType expand the type as needed
 */
export function assertLeaveType(leaveType: "Active duty"): void {
  cy.findByText("Leave type", { selector: "h3" })
    .next()
    .should("contain.text", leaveType);
}

type FilterOptions = {
  status?: {
    [key in DashboardClaimStatus]?: true;
  };
};
/**Filter claims by given parameters
 * @example
 * portal.filterLADashboardBy({
 *   status: {
 *     Closed: true,
 *     Denied: true,
 *   },
 * }); //Shows claims with status of 'Closed' & 'Denied'
 */
export function filterLADashboardBy(filters: FilterOptions): void {
  cy.get('button[aria-controls="filters"]')
    .invoke("text")
    .then((text) => {
      if (text.includes("Show filters"))
        cy.findByText("Show filters", { exact: false }).click();
    });
  cy.findByText("Hide filters").should("be.visible");
  const { status } = filters;
  if (status) {
    cy.get("#filters fieldset").within(() => {
      for (const key of Object.keys(status))
        cy.findByLabelText(key).click({ force: true });
    });
  }
  cy.findByText("Apply filters").should("not.be.disabled").click();
  cy.get('span[role="progressbar"]').should("be.visible");
  cy.contains("table", "Employer ID number").should("be.visible");
  // cy.wait("@dashboardClaimQueries");
}
/**Looks if dashboard is empty */
function checkDashboardIsEmpty() {
  return cy
    .contains("table", "Employer ID number")
    .find("tbody tr")
    .then(($tr) => {
      return $tr.text() === "No applications on file";
    });
}
/**Asserts that all claims visible on the page have a status */
export function assertClaimsHaveStatus(status: DashboardClaimStatus): void {
  checkDashboardIsEmpty().then((hasNoClaims) => {
    // Make sure it passes if there are no claims with that status.
    if (hasNoClaims) return;
    cy.contains("table", "Employer ID number")
      .find('tbody tr td[data-label="Status"]')
      .each((el) => {
        expect(el).to.contain.text(status);
      });
  });
}

export function clearFilters(): void {
  cy.get('button[aria-controls="filters"]')
    .invoke("text")
    .then((text) => {
      if (text.includes("Show filters"))
        cy.findByText("Show filters", { exact: false }).click();
      cy.findByText("Reset all filters").click();
      cy.get('span[role="progressbar"]').should("be.visible");
      cy.contains("table", "Employer ID number").should("be.visible");
      cy.wait("@dashboardDefaultQuery");
    });
}

/**Sorts claims on the dashboard*/
export function sortClaims(by: "new" | "old" | "name_asc" | "name_desc"): void {
  const sortValuesMap = {
    new: {
      value: "created_at,descending",
      query: "order_by=created_at&order_direction=descending",
    },
    old: {
      value: "created_at,ascending",
      query: "order_by=created_at&order_direction=ascending",
    },
    name_asc: {
      value: "employee,ascending",
      query: "order_by=employee&order_direction=ascending",
    },
    name_desc: {
      value: "employee,descending",
      query: "order_by=employee&order_direction=descending",
    },
  };
  cy.findByLabelText("Sort").then((el) => {
    if (el.val() === sortValuesMap[by].value) return;
    cy.wrap(el).select(sortValuesMap[by].value);
    cy.get('span[role="progressbar"]').should("be.visible");
    cy.wait("@dashboardClaimQueries")
      .its("request.url")
      .should("include", sortValuesMap[by].query);
  });
}
