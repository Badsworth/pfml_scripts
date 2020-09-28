import faker from "faker";
import { SimulationGenerator, ClaimDocument } from "./types";
import { Employer } from "./dor";
import employers from "./fixtures/employerPool";
import { ApplicationRequestBody } from "../api";
import { generateHCP, generateIDFront, generateIDBack } from "./documents";
import add from "date-fns/add";
import path from "path";

export function chance(
  config: [number, SimulationGenerator][]
): SimulationGenerator {
  // Build up a "roulette wheel" consisting of array indices from this.generators.
  // Each generator gets N slices, where N = the generator's probability.
  // Slices are combined to form the final wheel.
  const wheel = config.reduce((partialWheel, [probability], i) => {
    const slices = new Array(probability).fill(i);
    return partialWheel.concat(slices);
  }, [] as number[]);

  return async function (opts) {
    // Pick a slice from the wheel.
    const sliceIdx = Math.floor(Math.random() * wheel.length);
    const generator = config[wheel[sliceIdx]][1];
    return generator(opts);
  };
}

type Doc = "HCP" | "ID";
export type ScenarioOpts = {
  residence: "MA-proofed" | "MA-unproofed" | "OOS";
  financiallyIneligible?: boolean;
  employerExempt?: boolean;
  employerPool?: Employer[];
  invalidHCP?: boolean;
  gaveAppropriateNotice?: boolean;
  missingDocs?: Doc[];
  mailedDocs?: Doc[];
  skipSubmitClaim?: boolean;
  shortNotice?: boolean;
};

export function scenario(
  name: string,
  config: ScenarioOpts
): SimulationGenerator {
  return async (opts) => {
    const hasMassId =
      config.residence === "MA-proofed" || config.residence === "MA-unproofed";

    const [startDate, endDate] = generateLeaveDates();
    const notificationDate = generateNotificationDate(
      startDate,
      !!config.shortNotice
    );

    // Pulls random FEIN from employerPool fixture.
    const employer_fein =
      employers[Math.floor(Math.random() * employers.length)].fein;
    const first_name = faker.name.firstName();
    const last_name = faker.name.lastName();

    const claim: ApplicationRequestBody = {
      // These fields are brought directly over from the employee record.
      employment_status: "Employed",
      occupation: "Administrative",
      first_name: first_name,
      last_name: last_name,
      tax_identifier: faker.phone.phoneNumber("###-##-####"),
      employer_fein,
      date_of_birth: fmt(generateBirthDate()),
      has_state_id: hasMassId,
      mass_id: hasMassId ? generateMassID() : null,
      mailing_address: {
        city: faker.address.city(),
        line_1: faker.address.streetAddress(),
        state: faker.address.stateAbbr(),
        zip: faker.address.zipCode(),
      },
      leave_details: {
        continuous_leave_periods: [
          {
            start_date: fmt(startDate),
            end_date: fmt(endDate),
            is_estimated: true,
          },
        ],
        pregnant_or_recent_birth: false,
        employer_notification_date: fmt(notificationDate),
        employer_notified: true,
        reason: "Serious Health Condition - Employee",
        reason_qualifier: "Serious Health Condition",
      },
      payment_preferences: [
        {
          payment_method: "Check",
          is_default: true,
          cheque_details: {
            name_to_print_on_check: `${first_name} ${last_name}`,
          },
        },
      ],
    };

    // Generate the necessary documents for the claim.
    const documents: ClaimDocument[] = [];
    const hcpPath = `${claim.tax_identifier}.hcp.pdf`;
    const idFrontPath = `${claim.tax_identifier}.id-front.pdf`;
    const idBackPath = `${claim.tax_identifier}.id-back.pdf`;

    // Flag for Missing Doc HCP
    if (!config.missingDocs || !config.missingDocs.includes("HCP")) {
      // Includes flag for invalid HCP in call to `generateHCP()`.
      await generateHCP(
        claim,
        path.join(opts.documentDirectory, hcpPath),
        !!config.invalidHCP
      );
      documents.push({
        type: "HCP",
        path: hcpPath,
        submittedManually:
          config.mailedDocs && config.mailedDocs.includes("HCP") ? true : false,
      });
    }
    // Flag for Missing Doc ID
    if (!config.missingDocs || !config.missingDocs.includes("ID")) {
      await generateIDFront(
        claim,
        path.join(opts.documentDirectory, idFrontPath),
        // Specifies UNH scn involving mismatched ID/SSN.
        config.residence === "MA-unproofed"
      );
      await generateIDBack(
        claim,
        path.join(opts.documentDirectory, idBackPath)
      );

      documents.push({
        type: "ID-front",
        path: idFrontPath,
      });
      documents.push({
        type: "ID-back",
        path: idBackPath,
      });
    }

    return {
      scenario: name,
      claim,
      documents,
      financiallyIneligible: !!config.financiallyIneligible,
      // Flag for skipSubmitClaim.
      skipSubmitClaim: !!config.skipSubmitClaim,
    };
  };
}

// Generate a Mass ID string.
function generateMassID(): string {
  return faker.random.arrayElement([
    faker.phone.phoneNumber("S########"),
    faker.phone.phoneNumber("SA#######"),
  ]);
}

// Generate start and end dates for a leave request, not to exceed 20 weeks, and with a minimum
// start date of 2021-01-01.
function generateLeaveDates(): [Date, Date] {
  const startDate = soon(182, "2021-01-01");
  const endDate = add(startDate, {
    weeks: faker.random.number({ min: 1, max: 19 }),
  });
  return [startDate, endDate];
}

// Generate an employer notification date based on the claim start date.
// Optionally, generate a "short notice" date.
function generateNotificationDate(startDate: Date, shortNotice: boolean) {
  return add(startDate, {
    days: shortNotice ? -1 : -60,
  });
}

// Generate a birthdate > 65 years ago and < 18 years ago.
function generateBirthDate(): Date {
  return faker.date.between(
    add(new Date(), { years: -65 }),
    add(new Date(), { years: -18 })
  );
}

// Replacement for faker.date.soon(), which is slated to be released in the future.
function soon(days: number, refDate?: string): Date {
  let date = new Date();
  if (typeof refDate !== "undefined") {
    date = new Date(Date.parse(refDate));
  }

  const range = {
    min: 1000,
    max: (days || 1) * 24 * 3600 * 1000,
  };

  let future = date.getTime();
  future += faker.random.number(range); // some time from now to N days later, in milliseconds
  date.setTime(future);

  return date;
}

function fmt(date: Date): string {
  return `${date.getFullYear()}-${(date.getMonth() + 1)
    .toString()
    .padStart(2, "0")}-${date.getDate().toString().padStart(2, "0")}`;
}
