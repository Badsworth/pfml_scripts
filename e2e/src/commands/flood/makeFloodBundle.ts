import fs from "fs";
import path from "path";
import { Options, CommandModule } from "yargs";
import { prompt } from "enquirer";
import { SystemWideArgs } from "../../cli";
import { factory as EnvFactory, E2ELSTConfig } from "../../config";
import { LSTScenario } from "../../flood/config";
import * as Util from "./common";
import generateLSTData from "../../scripts/generateLSTData";

type BundleLSTArgs = Util.BundleLST & SystemWideArgs;

export const CLIArgs: Record<keyof Util.BundleLST, Options> = {
  bundleDir: {
    alias: "d",
    string: true,
    desc: "Directory name to store the new bundle",
    default: Util.deploymentId,
  },
  env: { string: true },
  token: { string: true },
  speed: { number: true },
  generateData: { boolean: true },
  numRecords: { number: true },
  scenario: { string: true },
  chance: { number: true },
  eligible: { number: true },
};

const cmd: CommandModule<SystemWideArgs, BundleLSTArgs> = {
  command: "bundle",
  describe: "Builds an LST bundle to run in Flood.io",
  builder: CLIArgs,
  async handler(args) {
    args.logger.profile("bundle");
    await prepareBundle(args);
    await makeBundle(args);
    args.logger.profile("bundle");
  },
};

export const { command, describe, builder, handler } = cmd;

export async function makeBundle(args: BundleLSTArgs): Promise<void> {
  args.logger.info("Bundling...");
  await Util.runCommand(`${Util.bundlerShell} -d "${args.bundleDir}"`, true);
  args.logger.info(
    `Bundled successfully. Check ${path.join(Util.scriptsDir, args.bundleDir)}`
  );
}

export async function prepareBundle(
  args: BundleLSTArgs
): Promise<Record<string, string>> {
  Util.setBuildDir(args.bundleDir);
  // Holds configuration of newly generated claims.json
  const newDataConfig: Util.LSTDataConfig[] = [];
  // Asks for target environment and whether we need new test data
  const prompts = Util.bundlerPrompts(args);
  const { bundleDir } = args;
  const { env, speed, generateData }: Util.PromptRes = await prompt([
    prompts.env,
    prompts.speed,
    prompts.generateData,
  ]);
  // Holds new environment vars
  const newEnvConfig: Partial<E2ELSTConfig> = {
    SIMULATION_SPEED: speed,
    FLOOD_DATA_BASEURL: `data/${bundleDir}`,
  };

  let assignedChance = 0;
  if (generateData) {
    // Finds out how much data we need and where to put it
    const { numRecords }: Util.PromptRes = await prompt([prompts.numRecords]);
    // While we have free space on the test file
    while (assignedChance < 100) {
      // Prompt which scenario to run and it's frequency
      const { scenario, chance }: Util.PromptRes = await prompt([
        prompts.scenario,
        prompts.chance(assignedChance),
      ]);
      // if we're using a claim submission scenario,
      // we can control the ammount of eligible/ineligible employees,
      let eligible = "100";
      if (scenario.includes("ClaimSubmit")) {
        ({ eligible } = await prompt([prompts.eligible]));
      }
      // Builds the new test data configuration
      const dataConfig: Util.LSTDataConfig = {
        scenario: scenario as LSTScenario,
        chance: parseFloat(chance),
        eligible: parseFloat(eligible),
      };
      // Add it to the global config for the data generation script
      newDataConfig.push(dataConfig);
      // The scenario occupied a certain percentage of the test file
      assignedChance += dataConfig.chance;
    }
    // Runs the data generation script
    args.logger.info("Generating test data...");

    // Generate LST data
    await generateLSTData(env, bundleDir, parseInt(numRecords), newDataConfig);

    // Log deployment details
    await Util.logDeployment("Generated new data:", {
      deploymentId: Util.deploymentId,
      bundleDir,
      numRecords,
      newDataConfig,
    });
  }
  // Recreate local env.json with new configurations
  args.logger.info("Generating environment json...");
  const newEnvVars = getEnvJson(env, newEnvConfig);
  await fs.promises.writeFile(
    Util.envJson,
    JSON.stringify(newEnvVars, null, 2)
  );
  await Util.logDeployment("Environment variables:", newEnvVars);
  args.logger.info("Generated local env.json for flood bundle!");
  return newEnvVars;
}

export const requiredLSTEnvVars: (keyof E2ELSTConfig)[] = [
  "FLOOD_API_TOKEN",
  "FLOOD_DATA_BASEURL",
  "SIMULATION_SPEED",
  "PORTAL_BASEURL",
  "API_BASEURL",
  "FINEOS_BASEURL",
  "PORTAL_USERNAME",
  "PORTAL_PASSWORD",
  "FINEOS_USERNAME",
  "FINEOS_PASSWORD",
  "FINEOS_USERS",
  "EMPLOYER_PORTAL_PASSWORD",
  "TESTMAIL_NAMESPACE",
  "TESTMAIL_APIKEY",
];

export const getEnvJson = (
  environment: string,
  override?: Partial<E2ELSTConfig>
): Record<string, string> => {
  const config = EnvFactory(environment);
  let allEnvVars: Partial<E2ELSTConfig> = {};
  for (const env of requiredLSTEnvVars) {
    allEnvVars[env] = config(env);
  }
  allEnvVars = { ...allEnvVars, ...override };
  return Object.entries(allEnvVars).reduce((t, [k, v]) => {
    t[`E2E_${k}`] = v as string;
    return t;
  }, {} as Record<string, string>);
};
