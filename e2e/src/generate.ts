import * as faker from "faker";
import { BenefitKinds, IncomeSourceTypes } from "./types";
import type {
  Application,
  BenefitKind,
  ReceivedBenefit,
  IncomeSourceType,
  OtherIncomeSource,
} from "./types";

/**
 * This file contains logic to generate applications for business simulations.
 */
export function generateApplication(): Application {
  /**
   * Generates data for `otherBenefits` section of application:
   *   ```
   *     otherBenefits: {
   *       willUseEmployerBenefits,
   *       employerBenefitsUsed,
   *       willReceiveOtherIncome,
   *       otherIncomeSources,
   *       tookLeaveForQualifyingReason,
   *     }
   *   ```
   */
  const willUseEmployerBenefits = faker.random.boolean();
  const employerBenefitsUsed = [] as ReceivedBenefit[];
  if (willUseEmployerBenefits) {
    const count = faker.random.number({ min: 1, max: 5 });
    for (let i = 0; i < count; i++) {
      const kind = faker.random.arrayElement(BenefitKinds) as BenefitKind;
      const receivedBenefit: ReceivedBenefit = {
        kind,
        dateStart: formatDate(faker.date.past(1)),
        dateEnd: formatDate(faker.date.future()),
        amount: faker.random.number({ min: 100 }),
      };
      employerBenefitsUsed.push(receivedBenefit);
    }
  }
  const willReceiveOtherIncome = faker.random.boolean();
  const otherIncomeSources = [] as OtherIncomeSource[];
  if (willReceiveOtherIncome) {
    const count = faker.random.number({ min: 1, max: 5 });
    for (let i = 0; i < count; i++) {
      const type = faker.random.arrayElement(
        IncomeSourceTypes
      ) as IncomeSourceType;
      const otherIncomeSource = {
        type,
        dateStart: formatDate(faker.date.past(1)),
        dateEnd: formatDate(faker.date.future()),
        amount: faker.random.number({ min: 100 }),
      };
      otherIncomeSources.push(otherIncomeSource);
    }
  }
  const tookLeaveForQualifyingReason = faker.random.boolean();

  return {
    // @todo: For now we're submitting applications with a pre-existing user.
    // In the future we will also want to test registration flow.
    email: Cypress.env("CYPRESS_PORTAL_USERNAME"),
    password: Cypress.env("CYPRESS_PORTAL_PASSWORD"),
    firstName: faker.name.firstName(),
    lastName: faker.name.lastName(),
    dob: formatDate(faker.date.past(20)),
    massId: faker.random.alphaNumeric(20),
    idVerification: {
      front: faker.internet.avatar(),
      back: faker.internet.avatar(),
    },
    ssn: faker.phone.phoneNumber("###-##-####"),
    claim: {
      type: "medical",
      dueToPregnancy: faker.random.boolean(),
      providerForm: faker.system.commonFileName("pdf"),
      leave: {
        type: "continuous",
        typeBasedDetails: {
          weeks: 40,
        },
        start: { month: 8, day: 1, year: 2020 },
        end: { month: 9, day: 1, year: 2020 },
      },
    },
    employer: {
      type: "employed",
      fein:
        faker.helpers.replaceSymbolWithNumber("##") +
        "-" +
        faker.helpers.replaceSymbolWithNumber("#######"),
      employerNotified: faker.random.boolean(),
      employerNotificationDate: formatDate(faker.date.past(0)),
    },
    otherBenefits: {
      willUseEmployerBenefits,
      employerBenefitsUsed,
      willReceiveOtherIncome,
      otherIncomeSources,
      tookLeaveForQualifyingReason,
    },
    paymentInfo: {
      type: "ach",
      accountDetails: {
        routingNumber: Number(
          faker.helpers.replaceSymbolWithNumber("!########")
        ),
        accountNumber: Number(
          faker.helpers.replaceSymbolWithNumber("!#######")
        ),
      },
    },
  };
}

function formatDate(date: Date): { month: number; day: number; year: number } {
  return {
    month: date.getMonth() + 1,
    day: date.getDate(),
    year: date.getFullYear(),
  };
}
