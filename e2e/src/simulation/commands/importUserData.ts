import { CommandModule } from "yargs";
import { SystemWideArgs } from "../../cli";
import fs from "fs";
import SimulationStorage from "../SimulationStorage";
import { SimulationClaim } from "../types";
import { ApplicationRequestBody } from "../../api";

type ImportUserDataArgs = { directory: string } & SystemWideArgs;

const userFields = [
  "first_name",
  "last_name",
  "tax_identifier",
  "employer_fein",
] as const;

const claimDocs = ["MASSID", "HCP"] as const;

const cmd: CommandModule<SystemWideArgs, ImportUserDataArgs> = {
  command: "importUserData",
  describe: "Import users into LST scenario dataset",
  builder: {
    directory: {
      type: "string",
      description: "The directory with existing claim and user data",
      demandOption: true,
      requiresArg: true,
      normalize: true,
      alias: "d",
    },
  },
  async handler(args) {
    args.logger.profile("importUserData");
    const storage = new SimulationStorage(args.directory);
    const claims = await storage.claims();
    const users = await storage.users();

    const HAP1Users = users.filter((u) => u.scenario === "HAP1");
    const HAP3Users = users.filter((u) => u.scenario === "HAP3");
    const GBR1Users = users.filter((u) => u.scenario === "GBR1");

    const getRandomUserFromPool = (
      pool: SimulationClaim[]
    ): Partial<ApplicationRequestBody> => {
      const userData: Partial<ApplicationRequestBody> = {};
      if (pool.length <= 0) {
        return userData;
      }
      const randomClaim = Math.floor(Math.random() * pool.length);
      const randomUser = pool[randomClaim].claim;
      userFields.forEach((field) => {
        userData[field] = randomUser[field];
      });
      return userData;
    };

    // Go through all LST json claims and replace invalid users.
    for (const i in claims) {
      const scenario: SimulationClaim = claims[i];
      if (!scenario.claim.first_name) continue;
      // Find useful data to correlate LST scenarios with BizSim ones.
      let pool: SimulationClaim[] = [];
      const isEligible = !scenario.financiallyIneligible;
      const hasMissingDocs = scenario.documents.length !== claimDocs.length;
      // Find out which pool of users best matches our current scenario.
      if (hasMissingDocs) {
        pool = GBR1Users;
      } else if (isEligible) {
        pool = HAP1Users;
      } else {
        pool = HAP3Users;
      }

      // should we also adjust for?:
      // payment_preferences -> name_to_print_on_check
      // documents -> path
      // replace current user with random user from pool
      claims[i].claim = {
        ...scenario.claim,
        ...getRandomUserFromPool(pool),
        // residential_address: scenario.claim.mailing_address,
        // hours_worked_per_week: scenario.claim.hours_worked_per_week
      };
    }
    // output new LST json file with valid "BizSim" users
    const path = `${args.directory}/claimsValid.json`;
    await fs.promises.writeFile(path, JSON.stringify(claims));

    args.logger.profile("importUserData");
    args.logger.info(
      `Imported user data for ${claims.length} claims into ${path}`
    );
  },
};

const { command, describe, builder, handler } = cmd;

export { command, describe, builder, handler };
