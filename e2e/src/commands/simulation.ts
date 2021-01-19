import { Argv } from "yargs";

const command = "simulation <command>";
const describe = "Manage business simulation";
const builder = (yargs: Argv): Argv =>
  yargs.commandDir(`${__dirname}/simulation`, {
    extensions: ["js", "ts"],
  });
const handler = (): void => {
  // Expected no-op.
};

export { command, describe, builder, handler };
