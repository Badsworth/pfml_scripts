import { Argv } from "yargs";

const command = "newrelic <command>";
const describe = "Perform New Relic tasks.";
const builder = (yargs: Argv): Argv =>
  yargs.commandDir(`${__dirname}/newrelic`, {
    extensions: ["js", "ts"],
  });
const handler = (): void => {
  // Expected no-op.
};

export { command, describe, builder, handler };
