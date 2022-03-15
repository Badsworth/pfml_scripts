import { CommandModule } from "yargs";
import { DatasetArgs } from "../dataset";
import InfraClient from "../../InfraClient";
import assert from "assert";

const cmd: CommandModule<DatasetArgs, DatasetArgs> = {
  command: "upload",
  describe: "Uploads DOR files and runs the ETL process.",
  async handler(args) {
    const dorFiles = await args.storage.getDORFiles();
    assert(
      dorFiles.length === 2,
      `${dorFiles.length} DOR files detected - expected 2`
    );

    const infra = InfraClient.create(args.config);
    args.logger.info(`Uploading ${dorFiles.join(",")} to ${args.environment}`);
    await infra.uploadDORFiles(dorFiles);
    args.logger.info(`Finished uploading DOR files.`);
    args.logger.info(`Running DOR ETL for ${args.environment}`);
    await infra.runDorEtl();
    args.logger.info(`Completed DOR ETL.`);
  },
};

const { command, describe, builder, handler } = cmd;
export { command, describe, builder, handler };
