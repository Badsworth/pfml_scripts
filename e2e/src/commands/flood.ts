import { Argv } from "yargs";

const command = "flood <command>";
const describe = "Manage load-and-stress testing on Flood.io";
const builder = (yargs: Argv): Argv =>
  yargs.commandDir(`${__dirname}/flood`, {
    extensions: ["js", "ts"],
  });
const handler = (): void => {
  // Expected no-op.
};

export { command, describe, builder, handler };
