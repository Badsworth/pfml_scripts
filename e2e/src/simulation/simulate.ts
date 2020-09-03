import faker from "faker";
import {
  SimulationClaim,
  SimulationGenerator,
  SimulationExecutor,
  ClaimDocument,
  SimulationGeneratorOpts,
} from "./types";
import { Employer } from "./dor";
import employers from "./fixtures/employerPool";
import { ApplicationRequestBody } from "../api";
import { generateHCP, generateIDFront, generateIDBack } from "./documents";
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
};

export function scenario(config: ScenarioOpts): SimulationGenerator {
  return async (opts) => {
    const hasMassId =
      config.residence === "MA-proofed" || config.residence === "MA-unproofed";
    const endDate = soon(faker.random.number(365), "2021-02-01");
    const startDate = faker.date.between(new Date(2021, 0), endDate);
    const notificationDate = faker.date.recent(60);
    // Pulls random FEIN from employerPool fixture.
    const employer_fein =
      employers[Math.floor(Math.random() * employers.length)].fein;

    const claim: ApplicationRequestBody = {
      // These fields are brought directly over from the employee record.
      employment_status: "Employed",
      first_name: faker.name.firstName(),
      last_name: faker.name.lastName(),
      employee_ssn: faker.phone.phoneNumber("###-##-####"),
      employer_fein,
      date_of_birth: fmt(faker.date.past(45)),
      has_state_id: hasMassId,
      mass_id: hasMassId ? faker.phone.phoneNumber("#########") : null,
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
        employer_notification_date: fmt(notificationDate),
        employer_notified: true,
        intermittent_leave_periods: [],
        reason: "Serious Health Condition - Employee",
        reduced_schedule_leave_periods: [],
      },
      payment_preferences: [],
    };

    // Generate the necessary documents for the claim.
    const documents: ClaimDocument[] = [];
    const hcpPath = `${claim.employee_ssn}.hcp.pdf`;
    const idFrontPath = `${claim.employee_ssn}.id-front.pdf`;
    const idBackPath = `${claim.employee_ssn}.id-back.pdf`;

    // Flag for Missing Doc HCP
    if (!config.missingDocs || !config.missingDocs.includes("HCP")) {
      await generateHCP(claim, path.join(opts.documentDirectory, hcpPath));
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
        path.join(opts.documentDirectory, idFrontPath)
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
      claim,
      documents,
      financiallyIneligible: !!config.financiallyIneligible,
    };
  };
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

type GenerateOpts = SimulationGeneratorOpts & {
  count: number;
};

/**
 * This is the top level object we interact with from CLI scripts.
 *
 * It knows how to generate a batch of claims as well as execute them. It will be created
 * in the pilot* files and loaded and invoked in our CLI scripts. The generate() output
 * will be captured into JSON, DOR, and RMV files, then we'll read the JSON file back in
 * in the CLI script and call execute() with the claims.
 */
export class Simulation {
  private generator: SimulationGenerator;
  private executor: SimulationExecutor;

  constructor(generator: SimulationGenerator, executor: SimulationExecutor) {
    this.generator = generator;
    this.executor = executor;
  }

  // Generate N claims, probably by invoking a SimulationGenerator. Return an iterable
  // object containing SimulationClaim objects, which will be saved to JSON file on disk
  // by the calling code.
  generate(opts: GenerateOpts): AsyncIterable<SimulationClaim> {
    const generator = this.generator;
    return (async function* () {
      for (let i = 0; i < opts.count; i++) {
        yield generator(opts);
      }
    })();
  }

  /**
   * Execute all claims in the passed iterable.
   */
  async execute(claims: Iterable<SimulationClaim>): Promise<void> {
    for (const claim of claims) {
      await this.executor(claim);
    }
  }
}
