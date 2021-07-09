import { CommandModule } from "yargs";
import { SystemWideArgs } from "../../cli";
import ClaimPool from "../../generation/Claim";
import { submit, postSubmit } from "../../scripts/util";
import ClaimSubmissionTracker from "../../submission/ClaimStateTracker";
import SubmittedClaimIndex from "../../submission/writers/SubmittedClaimIndex";
import path from "path";

import dataDirectory from "../../generation/DataDirectory";

type SubmissionArgs = {
  claimDirectory: string;
  concurrency?: number;
  cooldownMode?: boolean;
  errorLimit?: number;
} & SystemWideArgs;

const cmd: CommandModule<SystemWideArgs, SubmissionArgs> = {
  command: "submit <claimDirectory>",
  describe: "Registers a new leave admin account for a given employer.",
  builder: (yargs) => {
    return yargs
      .positional("claimDirectory", {
        type: "string",
        description: "Directory that contains claim pool to be submitted",
        demandOption: true,
      })
      .options({
        concurrency: {
          description: "Concurrent amount of claim submissions",
          number: true,
          default: 3,
          alias: "cc",
        },
        cooldownMode: {
          description: "Delay claim submission after 3 consecutive errors",
          boolean: true,
          default: false,
          alias: "cooldown",
        },
        errorLimit: {
          description: "Amount of consecutive errors before exiting program",
          number: true,
        },
      });
  },
  async handler(args) {
    try {
      const storage = dataDirectory(
        args.claimDirectory,
        path.join(__dirname, "..", "..", "..")
      );
      const tracker = new ClaimSubmissionTracker(storage.state);
      const claimPool: ClaimPool = await ClaimPool.load(
        storage.claims,
        storage.documents
      );

      args.logger.info(
        `Claim submission beginning with a concurrency of ${args.concurrency}`
      );
      args.cooldownMode &&
        args.logger.info(`Claim submission will run in cooldown mode`);

      await submit(claimPool, tracker, postSubmit, args.concurrency);
      await SubmittedClaimIndex.write(
        path.join(storage.dir, "submitted.csv"),
        await ClaimPool.load(storage.claims, storage.documents),
        tracker
      );

      const used = process.memoryUsage().heapUsed / 1024 / 1024;
      console.log(
        `The script uses approximately ${Math.round(used * 100) / 100} MB`
      );
    } catch (e) {
      if (e.code !== "ENOENT") console.log(e);
      else console.log(`Invalid path to claim directory: ${e.path}`);
      process.exit(1);
    }
  },
};

const { command, describe, builder, handler } = cmd;
export { command, describe, builder, handler };
