import { inFieldset, portal } from "./actions";
import { Then } from "cypress-cucumber-preprocessor/steps";
import { CypressStepThis, TestType } from "@/types";
import { lookup, getLeaveType } from "./util";
import { fineos, scenarios } from "./actions";

const scenarioFunctions: Record<TestType, () => void> = scenarios;

Then("I should be logged in", () => portal.assertLoggedIn());

Then("I should see a success page confirming my claim submission", function () {
  cy.url({ timeout: 20000 }).should("include", "/claims/success");
});

Then("I should be able to return to the portal dashboard", function () {
  cy.contains("Return to dashboard").click();
  cy.url().should("equal", `${Cypress.config().baseUrl}/`);
});

/**
 * Assert the data matches previously filled info
 */
Then("I should see any previously entered data", function (
  this: CypressStepThis
): void {
  if (!this.application) {
    throw new Error("Application has not been set");
  }
  const { application } = this;
  cy.get('input[name="first_name"]').should(
    "have.value",
    application.first_name
  );
  cy.get('input[name="last_name"]').should("have.value", application.last_name);
  cy.contains("button", "Save and continue").click();
});

/**
 * Find claim in Fineos.
 *
 * @param claimId The Claim ID, as reported from the portal.
 */
Then("I should find their claim", function () {
  // Fetch the claimId from the previous step, then use it in submission to Fineos.
  cy.unstash("claimId").then((claimId) => {
    if (typeof claimId !== "string") {
      throw new Error("Invalid Claim ID from previous test.");
    }
    // cy.get(`[title="PFML API ${claimId}"]`).click();
    cy.get(`[title="Adjudication"]`).click();
    // For now, we're stopping at asserting that the claim made it to Fineos.
  });
});

/* Review Page */
Then("I should have confirmed that information is correct", function (): void {
  // Usually preceeded by - "I am on the claims Review page"
  cy.await();
  cy.contains("Submit Part 1").click();

  cy.wait("@submitClaimResponse").then((xhr) => {
    const responseBody = xhr.response.body as Cypress.ObjectLike;
    cy.stash("claimNumber", responseBody.data.fineos_absence_id);
  });
});

/* Confirm Page */
Then(
  "I should have agreed and successfully submitted the claim",
  function (): void {
    // Usually preceeded by - "I am on the claims Confirm page"
    cy.contains("Submit application").click();
    cy.url({ timeout: 20000 }).should("include", "/claims/success");
  }
);

/* Checklist Page's reviewAndSubmit */
Then("I should review and submit the application", function (): void {
  // Usually preceeded by - "I am on the claims Checklist page"
  cy.contains("Review and submit application").click();
});

/* Checklist page */
// submitClaim
Then("I start submitting the claim", function (this: CypressStepThis): void {
  // Preceeded by - "I am on the claims Checklist page";
  // Preceeded by - "I click on the checklist button called {string}"
  //                with the label "Enter leave details"
  if (!this.application) {
    throw new Error("Application has not been set");
  }
  const { application } = this;
  const reason = application.leave_details && application.leave_details.reason;
  type ClaimTypePortal = {
    [index: string]: string;
  };
  const claimType: ClaimTypePortal = {
    "Serious Health Condition - Employee":
      "I can’t work due to an illness, injury, or pregnancy.",
    "Child Bonding": "I need to bond with my child after birth or placement.",
    "Care For A Family Member":
      "I need to manage family affairs while a family member is on active duty in the armed forces.",
    "Pregnancy/Maternity":
      "I need to care for a family member who serves in the armed forces.",
  };
  cy.contains(claimType[reason as string]).click();
  cy.contains("button", "Save and continue").click();

  // Submits data required by specific claim types.
  /* Usually followed by - "I finish submitting the claim based on its type" */
});

Then("I have my identity verified {string}", function (
  this: CypressStepThis,
  label: string
): void {
  if (!this.application) {
    throw new Error("Application has not been set");
  }
  const { application } = this;
  // Preceeded by - "I am on the claims Checklist page";
  // Preceeded by - "I click on the checklist button called {string}"
  //                with the label "Verify your identity"

  /***** Portal is currenlty NOT handling document submission

  if (
    !application.idVerification ||
    !application.idVerification.front ||
    !application.idVerification.back
  ) {
    throw new Error("Missing ID verification. Did you forget to generate it?");
  }

  *****/

  if (label === "normal") {
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

  // Input was removed from portal at some point
  // If it reappears, generate the PDF here and upload.
  // cy.get('input[type="file"]')
  //  .attachFile(application.idVerification.front)
  //  .attachFile(application.idVerification.back);
  // cy.contains("button", "Save and continue").click();
});

Then("I finish submitting the claim based on its type", function (
  this: CypressStepThis
) {
  if (!this.application) {
    throw new Error("Application has not been set");
  }
  const { application } = this;
  if (
    application.leave_details?.reason !== "Serious Health Condition - Employee"
  ) {
    throw new Error("Test");
  }
  // Example of selecting a radio button pertaining to a particular question. Scopes the lookup
  // of the "yes" value so we don't select "yes" for the wrong question.
  cy.contains(
    "fieldset",
    "Are you pregnant or have you recently given birth?"
  ).within(() => {
    cy.contains(
      application.leave_details?.pregnant_or_recent_birth ? "Yes" : "No"
    ).click();
  });
  cy.contains("button", "Save and continue").click();

  // Input was removed from portal at some point. If it gets reinstated, generate it here and upload.
  // if (!claim.providerForm) {
  //   throw new Error(
  //     "Provider form was not specified. Did you forget to generate one in your test?"
  //   );
  // }
  // cy.get('input[type="file"]').attachFile(claim.providerForm);
  // cy.contains("button", "Save and continue").click();

  const leaveType = getLeaveType(application.leave_details);

  const leave = lookup(leaveType, {
    continuous: application.leave_details.continuous_leave_periods,
    reduced: application.leave_details.reduced_schedule_leave_periods,
    intermittent: application.leave_details.intermittent_leave_periods,
  });

  const continuousLeaveButtonValue: string =
    leaveType === "continuous" ? "true" : "false";

  cy.contains(
    "fieldset",
    "Do you need to take off work completely for a period of time (continuous leave)?"
  ).within(() => {
    cy.get("input[type='radio']").check(continuousLeaveButtonValue, {
      force: true,
    });
  });
  /**
   * Leave details section.
   */

  // Leave type-based questions.
  switch (leaveType) {
    /**
     * Continuous leave questions.
     */
    case "continuous":
      const startDate = new Date((leave && leave[0].start_date) as string);
      const endDate = new Date((leave && leave[0].end_date) as string);

      /* Currently Been Removed from Portal
        const weeks = getWeeks(application.leave_details)?.toString();
        cy.labelled(
          "How many weeks will you need to take continuous leave from work?"
        ).type(weeks as string);
        cy.contains("button", "Save and continue").click();
      */

      // Continous Leave details section (continued).
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
      cy.contains("button", "Save and continue").click();
      break;

    /**
     * Reduced leave schedule questions.
     */
    // case "reduced":
    //   cy.labelled(
    //     "How many weeks of a reduced leave schedule do you need?"
    //   ).type(leave.typeBasedDetails.weeks.toString());
    //   cy.labelled(
    //     "How many hours will your work schedule be reduced by each week?"
    //   ).type(leave.typeBasedDetails.hoursPerWeek.toString());
    //   cy.contains("button", "Save and continue").click();

    // // Reduced leave questions continued ...
    //   cy.labelled(
    //     "On average, how many hours do you work for your employer each week?"
    //   ).type(leave.typeBasedDetails.averageWeeklyWorkHours.toString());
    //   cy.contains("button", "Save and continue").click();
    //   break;

    /**
     * Intermittent leave questions.
     */
    // case "intermittent":
    //   const frequency = lookup(leave.typeBasedDetails.frequencyIntervalBasis, {
    //     weeks: {
    //       radioLabel: "At least once a week",
    //       inputLabel: "Estimate how many absences per week.",
    //     },
    //     months: {
    //       radioLabel: "At least once a month",
    //       inputLabel: "Estimate how many absences per month.",
    //     },
    //     every6Months: {
    //       radioLabel: "Irregular over the next 6 months",
    //       inputLabel: "Estimate how many absences over the next 6 months.",
    //     },
    //   });
    //   cy.contains(
    //     "fieldset",
    //     "How often might you need to be absent from work?"
    //   ).within(() => {
    //     cy.contains(frequency.radioLabel).click();
    //   });
    //   cy.labelled(frequency.inputLabel).type(
    //     leave.typeBasedDetails.frequency.toString()
    //   );

    //   const duration = lookup(leave.typeBasedDetails.durationBasis, {
    //     days: {
    //       radioLabel: "At least a day",
    //       inputLabel: "How many days of work will you miss per absence?",
    //     },
    //     hours: {
    //       radioLabel: "Less than a full work day",
    //       inputLabel: "How many hours of work will you miss per absence?",
    //     },
    //   });
    //   cy.contains(
    //     "fieldset",
    //     "How long will an absence typically last?"
    //   ).within(() => {
    //     cy.contains(duration.radioLabel).click();
    //   });
    //   cy.labelled(duration.inputLabel).type(
    //     leave.typeBasedDetails.duration.toString()
    //   );
    //   cy.contains("button", "Save and continue").click();

    //   // Reduced leave questions continued ...
    //   cy.labelled(
    //     "On average, how many hours do you work for your employer each week?"
    //   ).type(leave.typeBasedDetails.averageWeeklyWorkHours.toString());
    //   cy.contains("button", "Save and continue").click();
    //   break;

    default:
      throw new Error(`Invalid medical leave type.`);
  }
});

// enterEmployerInfo
Then("I enter employer info", function (this: CypressStepThis): void {
  // Preceeded by - "I am on the claims Checklist page";
  // Preceeded by - "I click on the checklist button called {string}"
  //                with the label "Enter employment information"
  if (!this.application) {
    throw new Error("Application has not been set");
  }
  const { application } = this;

  cy.contains("fieldset", "What is your employment status?").within(() => {
    const choice = lookup(
      application.employment_status as
        | "Employed"
        | "Unemployed"
        | "Self-Employed",
      {
        Employed: "I'm employed in Massachusetts",
        Unemployed: "I'm unemployed",
        "Self-Employed": "I'm self-employed",
      }
    );
    cy.contains("label", choice).click({ force: true });
  });
  if (application.employment_status === "Employed") {
    cy.labelled(
      "What is your employer's Federal Employer Identification Number (FEIN)?"
    ).type(application.employer_fein as string);
  }
  cy.contains("button", "Save and continue").click();
  if (application.employment_status === "Employed") {
    // @todo: Set to application property once it exists.
    cy.labelled("On average, how many hours do you work each week?").type("40");
    cy.contains("button", "Save and continue").click();

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
        const notifcationDate = new Date(
          application.leave_details?.employer_notification_date as string
        );
        cy.labelled("Month").type(
          (notifcationDate.getMonth() + 1).toString() as string
        );
        cy.labelled("Day").type(
          notifcationDate.getUTCDate().toString() as string
        );
        cy.labelled("Year").type(
          notifcationDate.getUTCFullYear().toString() as string
        );
      });
    }
    cy.contains("button", "Save and continue").click();
  }
});

// reportOtherBenefits
Then("I report other benefits", function (this: CypressStepThis): void {
  // Preceeded by - "I am on the claims Checklist page";
  // Preceeded by - "I click on the checklist button called {string}"
  //                with the label "Report other leave and benefits"
  if (!this.application) {
    throw new Error("Application has not been set");
  }

  cy.contains(
    "fieldset",
    "Will you use any employer-sponsored benefits during your leave?"
  ).within(() => cy.labelled("No").click());
  cy.contains("button", "Save and continue").click();

  cy.contains(
    "fieldset",
    "Will you receive income from any other sources during your leave?"
  ).within(() => cy.labelled("No").click());
  cy.contains("button", "Save and continue").click();

  cy.contains(
    "fieldset",
    "Have you taken paid or unpaid leave since"
  ).within(() => cy.labelled("No").click());
  cy.contains("button", "Save and continue").click();

  // const { extract properties once added to ApplicationRequest } = application.;

  /* Will be used for when "otherBenefits" becomes availble
     on the API ApplicatinRequestBody

    if (willUseEmployerBenefits) {
      const lastBenefit = employerBenefitsUsed.length - 1;
      employerBenefitsUsed.forEach((benefit, index) => {
        const benefitKindLabel = lookup(benefit.kind, {
          accrued: "Accrued paid Leave",
          stDis: "Short-term disability insurance",
          permDis: "Permanent disability insurance",
          pfml: "Family or medical leave insurance",
        });
        cy.contains("fieldset", `Benefit ${index + 1}`).within(() => {
          cy.labelled(benefitKindLabel).click();
          cy.contains(
            "fieldset",
            "When will you start using the benefit?"
          ).within(() => {
            cy.labelled("Month").type(benefit.dateStart.month.toString());
            cy.labelled("Day").type(benefit.dateStart.day.toString());
            cy.labelled("Year").type(benefit.dateStart.year.toString());
          });
          cy.contains("fieldset", "When will you stop using the benefit?").within(
            () => {
              cy.labelled("Month").type(benefit.dateEnd.month.toString());
              cy.labelled("Day").type(benefit.dateEnd.day.toString());
              cy.labelled("Year").type(benefit.dateEnd.year.toString());
            }
          );
        });
        if (index !== lastBenefit) {
          cy.contains("button", "Add another benefit").click();
        }
      });
      cy.contains("button", "Save and continue").click();
    }
  */

  /* Will be used for when "otherBenefits" becomes availble
    on the API ApplicatinRequestBody

    if (willReceiveOtherIncome) {
      const lastIncomeSource = otherIncomeSources.length - 1;
      otherIncomeSources.forEach((incomeSource, index) => {
        const incomeSourceTypeLabel = lookup(incomeSource.type, {
          workersComp: "Workers Compensation",
          unemployment: "Unemployment Insurance",
          ssdi: "Social Security Disability Insurance",
          govRetDis: "Disability benefits under a governmental retirement plan",
          jonesAct: "Jones Act benefits",
          rrRet: "Railroad Retirement benefits",
          otherEmp: "Earnings from another employer",
          selfEmp: "Earnings from self-employment",
        });
        cy.contains("fieldset", `Income ${index + 1}`).within(() => {
          cy.labelled(incomeSourceTypeLabel).click();
          cy.contains(
            "fieldset",
            "When will you start receiving this income?"
          ).within(() => {
            cy.labelled("Month").type(incomeSource.dateStart.month.toString());
            cy.labelled("Day").type(incomeSource.dateStart.day.toString());
            cy.labelled("Year").type(incomeSource.dateStart.year.toString());
          });
          cy.contains(
            "fieldset",
            "When will you stop receiving this income?"
          ).within(() => {
            cy.labelled("Month").type(incomeSource.dateEnd.month.toString());
            cy.labelled("Day").type(incomeSource.dateEnd.day.toString());
            cy.labelled("Year").type(incomeSource.dateEnd.year.toString());
          });
        });
        if (index !== lastIncomeSource) {
          cy.contains("button", "Add another income").click();
        }
      });
      cy.contains("button", "Save and continue").click();
    }
  */
});

// addPaymentInfo
Then("I add payment info", function (this: CypressStepThis): void {
  // Preceeded by - "I am on the claims Checklist page";
  // Preceeded by - "I click on the checklist button called {string}"
  //                with the label "Add payment information"
  if (!this.application) {
    throw new Error("Application has not been set");
  }
  const { application } = this;
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
        Check: "Debit card",
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
      break;

    default:
      throw new Error("Unknown payment method");
  }
  cy.contains("button", "Save and continue").click();
});

Then("I should add weekly wage", function (): void {
  fineos.addWeeklyWage();
});

Then("I should fufill availability request", function (): void {
  fineos.fillAvailability();
});

Then("I should confirm evidence is {string}", function (label: string): void {
  fineos.validateEvidence(label);
});

Then("I click Accept", function (): void {
  fineos.acceptLeavePlan();
});

Then("I should approve claim", function (): void {
  fineos.approveClaim();
});

Then("I should confirm {string} is not present", function (): void {
  cy.contains("No Records To Display");
});

Then("I check financial eligibility", function (): void {
  cy.get('td[title="Not Met"]');
});

Then("I click Reject", function (): void {
  fineos.clickReject();
});

Then("I should confirm task assigned to DFML Ops", function (): void {
  fineos.confirmDFMLTransfer();
});

Then("I add {string} as reason in notes", function (reason: string): void {
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

  cy.get('span[id="leaveRequestDenialDetailsWidget"]')
    .find("textarea")
    .type(reasonText);
  cy.get("div[class='popup-footer']").find("input[title='OK']").click();
});

Then("I should confirm claim has been completed", function (): void {
  fineos.claimCompletion();
});

Then("I should adjudicate the {string} claim properly in Fineos", function (
  scenario: string
): void {
  scenarioFunctions[scenario as TestType]();
});

Then("I should transfer task to DMFL due to {string}", function (
  label: string
): void {
  fineos.transferToDFML(label);
});

Then("I should find the {string} document", function (label: string): void {
  fineos.findDocument(label);
});
