import yargs, { Argv } from "yargs";
import { config as dotenv } from "dotenv";
import winston from "winston";

dotenv();

export type SystemWideArgs = {
  verbose: boolean;
  logger: winston.Logger;
};

/**
 * This is the top level CLI script.
 *
 * Commands can be added here to be made available.
 */
(yargs as Argv<SystemWideArgs>)
  .middleware((argv) => {
    // Add a logger, which we'll use in the commands.
    argv.logger = winston.createLogger({
      level: argv.verbose ? "debug" : "info",
      format: winston.format.combine(
        winston.format.colorize(),
        winston.format.simple()
      ),
      transports: new winston.transports.Console(),
    });
  })
  .commandDir(`${__dirname}/commands`, {
    extensions: ["js", "ts"],
  })
  .option("verbose", {
    type: "boolean",
  })
  .demandCommand()
  .help().argv;
