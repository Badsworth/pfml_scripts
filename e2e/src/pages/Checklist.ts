import {
  Application,
  MedicalClaim,
  MedicalLeaveContinuous,
  MedicalLeaveReduced,
  MedicalLeaveIntermittent,
} from "../types";
import { lookup } from "./util";

export default class Checklist {
  assertOnChecklist(): this {
    cy.url().should("contain", "/claims/checklist");
    return this;
  }
  clickChecklistButton(label: string): this {
    // @todo: Very brittle selector. Ask for a better one.
    cy.contains(label)
      .parentsUntil(".display-flex.border-bottom.border-base-light.padding-y-4")
      .contains("a", "Start")
      .click();
    return this;
  }
  verifyIdentity(application: Application): this {
    // Starting from the claim checklist.
    this.assertOnChecklist();
    this.clickChecklistButton("Verify your identity");
    if (
      !application.idVerification ||
      !application.idVerification.front ||
      !application.idVerification.back
    ) {
      throw new Error(
        "Missing ID verification. Did you forget to generate it?"
      );
    }

    cy.labelled("First name").type(application.firstName);
    cy.labelled("Last name").type(application.lastName);
    cy.contains("button", "Continue").click();

    cy.contains("fieldset", "What's your birthdate?").within(() => {
      cy.contains("Month").type(application.dob.month.toString());
      cy.contains("Day").type(application.dob.day.toString());
      cy.contains("Year").type(application.dob.year.toString());
    });
    cy.contains("button", "Continue").click();

    cy.contains("Do you have a Massachusetts driver's license or ID card?");
    if (application.massId) {
      cy.contains("Yes").click();
      cy.contains("Enter your license or ID number").type(application.massId);
    } else {
      cy.contains("No").click();
    }
    cy.contains("button", "Continue").click();

    cy.get('input[type="file"]')
      .attachFile(application.idVerification.front)
      .attachFile(application.idVerification.back);
    cy.contains("button", "Continue").click();

    cy.contains("What's your Social Security Number?").type(application.ssn);
    cy.contains("button", "Continue").click();
    return this;
  }
  submitClaim(application: Application): this {
    // Starting from the claim checklist.
    this.assertOnChecklist();
    this.clickChecklistButton("Enter leave details");

    const { claim } = application;

    const claimType = lookup(claim.type, {
      medical: "I can’t work due to an illness, injury, or pregnancy.",
      childBonding: "I need to bond with my child after birth or placement.",
      careForFamilyMember:
        "I need to manage family affairs while a family member is on active duty in the armed forces.",
      pregnancyMaternity:
        "I need to care for a family member who serves in the armed forces.",
    });
    cy.contains(claimType).click();
    cy.contains("button", "Continue").click();

    // Submits data required by specific claim types.
    if (claim.type === "medical") {
      this.submitMedical(application);
    }

    return this;
  }
  /**
   * Medical claim questions.
   */
  submitMedical(application: Application): this {
    const claim = application.claim as MedicalClaim;
    if (!claim.providerForm) {
      throw new Error(
        "Provider form was not specified. Did you forget to generate one in your test?"
      );
    }
    // Example of selecting a radio button pertaining to a particular question. Scopes the lookup
    // of the "yes" value so we don't select "yes" for the wrong question.
    cy.contains(
      "fieldset",
      "Are you pregnant or have you recently given birth?"
    ).within(() => {
      cy.contains(claim.dueToPregnancy ? "Yes" : "No").click();
    });
    cy.contains("button", "Continue").click();
    cy.get('input[type="file"]').attachFile(claim.providerForm);
    cy.contains("button", "Continue").click();
    const leave = lookup(claim.leave.type, {
      continuous: claim.leave as MedicalLeaveContinuous,
      reduced: claim.leave as MedicalLeaveReduced,
      intermittent: claim.leave as MedicalLeaveIntermittent,
    });

    /**
     * Leave details section.
     */
    cy.contains("fieldset", "Which of the following situations apply?").within(
      () => {
        const value = lookup(leave.type, {
          continuous: "Continuous leave",
          reduced: "Reduced leave schedule",
          intermittent: "Intermittent leave",
        });
        cy.contains(value).click();
      }
    );
    // Leave type-based questions.
    switch (leave.type) {
      // Continuous leave questions.
      case "continuous":
        cy.labelled(
          "How many weeks will you need to take continuous leave from work?"
        ).type(leave.typeBasedDetails.weeks.toString());
        cy.contains("button", "Continue").click();
        break;

      // Reduced leave schedule questions.
      case "reduced":
        cy.labelled(
          "How many weeks of a reduced leave schedule do you need?"
        ).type(leave.typeBasedDetails.weeks.toString());
        cy.labelled(
          "How many hours will your work schedule be reduced by each week?"
        ).type(leave.typeBasedDetails.hoursPerWeek.toString());
        cy.contains("button", "Continue").click();

        cy.labelled(
          "On average, how many hours do you work for your employer each week?"
        ).type(leave.typeBasedDetails.averageWeeklyWorkHours.toString());
        cy.contains("button", "Continue").click();
        break;

      // Intermittent leave questions.
      case "intermittent":
        const frequency = lookup(
          leave.typeBasedDetails.frequencyIntervalBasis,
          {
            weeks: {
              radioLabel: "At least once a week",
              inputLabel: "Estimate how many absences per week.",
            },
            months: {
              radioLabel: "At least once a month",
              inputLabel: "Estimate how many absences per month.",
            },
            every6Months: {
              radioLabel: "Irregular over the next 6 months",
              inputLabel: "Estimate how many absences over the next 6 months.",
            },
          }
        );
        cy.contains(
          "fieldset",
          "How often might you need to be absent from work?"
        ).within(() => {
          cy.contains(frequency.radioLabel).click();
        });
        cy.labelled(frequency.inputLabel).type(
          leave.typeBasedDetails.frequency.toString()
        );

        const duration = lookup(leave.typeBasedDetails.durationBasis, {
          days: {
            radioLabel: "At least a day",
            inputLabel: "How many days of work will you miss per absence?",
          },
          hours: {
            radioLabel: "Less than a full work day",
            inputLabel: "How many hours of work will you miss per absence?",
          },
        });
        cy.contains(
          "fieldset",
          "How long will an absence typically last?"
        ).within(() => {
          cy.contains(duration.radioLabel).click();
        });
        cy.labelled(duration.inputLabel).type(
          leave.typeBasedDetails.duration.toString()
        );
        cy.contains("button", "Continue").click();

        cy.labelled(
          "On average, how many hours do you work for your employer each week?"
        ).type(leave.typeBasedDetails.averageWeeklyWorkHours.toString());
        cy.contains("button", "Continue").click();
        break;

      default:
        throw new Error(`Invalid medical leave type.`);
    }

    /**
     * Leave details section (continued).
     */
    cy.contains("fieldset", "When will you first need to take leave?").within(
      () => {
        cy.labelled("Month").type(leave.start.month.toString());
        cy.labelled("Day").type(leave.start.day.toString());
        cy.labelled("Year").type(leave.start.year.toString());
      }
    );
    cy.contains(
      "fieldset",
      "When will your leave end or be re-evaluated?"
    ).within(() => {
      cy.labelled("Month").type(leave.end.month.toString());
      cy.labelled("Day").type(leave.end.day.toString());
      cy.labelled("Year").type(leave.end.year.toString());
    });
    cy.contains("button", "Continue").click();

    return this;
  }

  enterEmployerInfo(application: Application): this {
    this.assertOnChecklist();
    this.clickChecklistButton("Enter employment information");

    const { employer } = application;
    cy.contains("fieldset", "What is your employment status?").within(() => {
      const choice = lookup(employer.type, {
        employed: "I'm employed in Massachusetts",
        unemployed: "I'm unemployed",
        selfEmployed: "I'm self-employed",
      });
      cy.contains("label", choice).click({ force: true });
    });
    if (employer.type === "employed") {
      cy.labelled(
        "What is your employer's Federal Employer Identification Number (FEIN)?"
      ).type(employer.fein);
    }
    cy.contains("button", "Continue").click();

    if (employer.type === "employed") {
      cy.contains(
        "fieldset",
        "Have you told your employer that you are taking leave?"
      ).within(() => {
        cy.contains("label", employer.employerNotified ? "Yes" : "No").click();
      });
      if (employer.employerNotified) {
        cy.contains("fieldset", "When did you tell them?").within(() => {
          cy.labelled("Month").type(
            employer.employerNotificationDate.month.toString()
          );
          cy.labelled("Day").type(
            employer.employerNotificationDate.day.toString()
          );
          cy.labelled("Year").type(
            employer.employerNotificationDate.year.toString()
          );
        });
      }
      cy.contains("button", "Continue").click();
    }
    return this;
  }

  reportOtherBenefits(application: Application): this {
    this.assertOnChecklist();
    this.clickChecklistButton("Report other leave and benefits");

    const {
      willUseEmployerBenefits,
      employerBenefitsUsed = [],
      willReceiveOtherIncome,
      otherIncomeSources = [],
      tookLeaveForQualifyingReason,
    } = application.otherBenefits;

    cy.contains(
      "fieldset",
      "Will you use any employer-sponsored benefits during your leave?"
    ).within(() => cy.labelled(willUseEmployerBenefits ? "Yes" : "No").click());
    cy.contains("button", "Continue").click();
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
          cy.contains(
            "fieldset",
            "When will you stop using the benefit?"
          ).within(() => {
            cy.labelled("Month").type(benefit.dateEnd.month.toString());
            cy.labelled("Day").type(benefit.dateEnd.day.toString());
            cy.labelled("Year").type(benefit.dateEnd.year.toString());
          });
        });
        if (index !== lastBenefit) {
          cy.contains("button", "Add another benefit").click();
        }
      });
      cy.contains("button", "Continue").click();
    }

    cy.contains(
      "fieldset",
      "Will you receive income from any other sources during your leave?"
    ).within(() => cy.labelled(willReceiveOtherIncome ? "Yes" : "No").click());
    cy.contains("button", "Continue").click();
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
      cy.contains("button", "Continue").click();
    }

    cy.contains(
      "fieldset",
      "Have you taken paid or unpaid leave since"
    ).within(() =>
      cy.labelled(tookLeaveForQualifyingReason ? "Yes" : "No").click()
    );
    cy.contains("button", "Continue").click();

    return this;
  }

  addPaymentInfo(application: Application): this {
    this.assertOnChecklist();
    this.clickChecklistButton("Add payment information");

    const { paymentInfo } = application;

    cy.contains(
      "fieldset",
      "How do you want to get your weekly benefit?"
    ).within(() => {
      const paymentInfoLabel = lookup(paymentInfo.type, {
        ach: "Direct deposit",
        debit: "Debit card",
      });
      cy.contains(paymentInfoLabel).click();
    });
    switch (paymentInfo.type) {
      case "ach":
        cy.labelled("Routing number").type(
          paymentInfo.accountDetails.routingNumber.toString()
        );
        cy.labelled("Account number").type(
          paymentInfo.accountDetails.accountNumber.toString()
        );
        break;

      case "debit":
        cy.labelled("Street address 1").type(
          paymentInfo.destinationAddress.line1
        );
        cy.labelled("Street address 2 (optional)").type(
          paymentInfo.destinationAddress.line2
        );
        cy.labelled("City").type(paymentInfo.destinationAddress.city);
        cy.labelled("State").type(paymentInfo.destinationAddress.state);
        cy.labelled("ZIP Code").type(
          paymentInfo.destinationAddress.zip.toString()
        );
        break;

      default:
        throw new Error("Unknown payment method");
    }
    cy.contains("button", "Continue").click();

    return this;
  }

  reviewAndSubmit(): this {
    this.assertOnChecklist();
    cy.contains("Review and submit application").click();
    return this;
  }
}
