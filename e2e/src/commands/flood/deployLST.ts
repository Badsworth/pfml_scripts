/* eslint-disable @typescript-eslint/explicit-module-boundary-types */
import fs from "fs";
import path from "path";
import util from "util";
import fetch from "node-fetch";
import FormData from "form-data";
import { CommandModule } from "yargs";
import { v4 as uuid } from "uuid";
import { prompt } from "enquirer";
import { exec } from "child_process";
import { SystemWideArgs } from "../../cli";
import * as Cfg from "../../flood/config";

type DeployLSTArgs = {
  token: string;
  tool: string;
  project: string;
  name: string;
  privacy: string;
  threads: number;
  rampup: number;
  duration: number;
  infrastructure: string;
  instanceQuantity: number;
  region: string;
  instanceType: string;
  stopAfter: number;
  startFlood: boolean;
} & SystemWideArgs;

type PromptRes = Record<string, string>;
type PromptParams = Parameters<typeof prompt>;

interface Choice {
  name: string;
  message?: string;
  value?: string;
  hint?: string;
  disabled?: boolean | string;
}

export type LSTDataConfig = {
  scenario: Cfg.LSTScenario;
  chance: number;
  eligible?: number;
  type?: Cfg.ClaimType;
};

const cmd: CommandModule<SystemWideArgs, DeployLSTArgs> = {
  command: "deployLST",
  describe: "Builds and deploys a bundle to run in Flood.io",
  builder: {
    token: {
      alias: "u",
      string: true,
      desc: "Flood API token <https://app.flood.io/account/api>",
    },
    tool: { alias: "l", string: true, desc: "Testing tool to use" },
    project: { alias: "p", string: true, desc: "Flood project name" },
    name: { alias: "n", string: true, desc: "Name of test" },
    privacy: { alias: "v", string: true, desc: "Privacy" },
    threads: {
      alias: "t",
      number: true,
      desc: "Number of concurrent users",
    },
    rampup: { alias: "m", number: true, desc: "Ramp-up (minutes)" },
    duration: { alias: "d", number: true, desc: "Duration (minutes)" },
    infrastructure: { alias: "i", string: true, desc: "Grid type" },
    instanceQuantity: {
      alias: "q",
      number: true,
      desc: "Grid instance quantity",
    },
    region: { alias: "r", string: true, desc: "Region" },
    instanceType: { alias: "y", string: true, desc: "Grid instance type" },
    stopAfter: {
      alias: "s",
      number: true,
      desc: "Stop grid after N minutes (where N > 0 and N <= 2,880 [48 hours])",
    },
    startFlood: { boolean: true },
  },
  async handler(args) {
    // Flood LST deployment unique identifier for file structures
    const deploymentId = uuid().split("-")[0];
    args.logger.profile(`deployLST ${deploymentId}`);
    // Skips the prompt if this script is called with arguments
    const autoPrompt = async (...args: PromptParams): Promise<PromptRes> => {
      if ("token" in args) {
        return args as PromptRes;
      } else {
        return prompt(...args);
      }
    };
    // Hold configuration of newly generated claims.json
    const newDataConfig: LSTDataConfig[] = [];

    const builds = path.join(__dirname, "../../../scripts");
    // Asks whether we need new test data
    const { createNewTestData }: PromptRes = await autoPrompt(
      prompts.createNewTestData
    );
    let assignedChance = 0;
    if (createNewTestData) {
      console.info("Entering data generation...");
      // While we have free space on the test file
      while (assignedChance < 100) {
        // Prompt which scenario to run and it's frequency
        const { scenario, chance }: PromptRes = await autoPrompt([
          prompts.scenario(newDataConfig),
          prompts.chance(assignedChance),
        ]);
        // if we're using a claim submission scenario,
        // we can control the ammount of eligible/ineligible employees,
        let eligible = 100;
        if (scenario.includes("ClaimSubmit")) {
          const genClaims = await autoPrompt(prompts.eligible);
          eligible = parseFloat(genClaims.eligible);
        }
        // Builds the new test data configuration
        const dataConfig: LSTDataConfig = {
          scenario: scenario as Cfg.LSTScenario,
          chance: parseFloat(chance),
          eligible,
        };
        // Add it to the global config for the data generation script
        newDataConfig.push(dataConfig);
        // The scenario occupied a certain percentage of the test file
        assignedChance += dataConfig.chance;
      }
      // Finds out how much data we need and where to put it
      const { dataOutput, numRecords }: PromptRes = await autoPrompt([
        prompts.numRecords,
        prompts.dataOutput(deploymentId),
      ]);
      // Runs the data generation script
      await execScript(
        `npm run cli -- simulation generate -f ./src/simulation/scenarios/controlLST.ts -d ./src/flood/data/${dataOutput} -n "${numRecords}" -G "${escape(
          JSON.stringify(newDataConfig)
        )}"`
      );
    }
    // Builds a new LST bundle
    const buildOutput = `${builds}\\${deploymentId}`;
    await execScript(
      `npm run flood:build -- -f "${deploymentId}"`,
      `LST successfully built in "${buildOutput}"!`
    );
    // Asks for all needed info to launch/deploy a flood
    const flood: PromptRes = await autoPrompt([
      prompts.token(await Cfg.floodToken),
      prompts.tool,
      prompts.project,
      prompts.name,
      prompts.threads,
      prompts.duration,
      prompts.rampup,
      prompts.privacy,
      prompts.region,
      prompts.infrastructure,
      prompts.instanceQuantity,
      prompts.instanceType,
      prompts.stopAfter,
      prompts.startFlood,
    ]);

    // Launches flood via cURL script.
    if (flood.startFlood) {
      const message = `Flood "${flood.name}" launched on "${
        flood.project
      }": \n\t- Concurrent users: ${flood.threads} \n\t- Duration: ${
        +flood.duration / 60
      } minute(s) \n\t- Ramp-up: ${flood.rampup} minute(s)`;

      const formData = new FormData();
      const floodData: PromptRes = {
        "flood[tool]": flood.tool,
        "flood[project]": flood.project,
        "flood[name]": flood.name,
        "flood[privacy_flag]": flood.privacy,
        "flood[tag_list]": "LST",
        "flood[threads]": flood.threads,
        "flood[rampup]": flood.rampup,
        "flood[duration]": flood.duration,
        "flood[grids][][region]": flood.region,
        "flood[grids][][infrastructure]": flood.infrastructure,
        "flood[grids][][instance_quantity]": flood.instanceQuantity,
        "flood[grids][][instance_type]": flood.instanceType,
        "flood[grids][][stop_after]": flood.stopAfter,
      };
      for (const k in floodData) {
        formData.append(k, floodData[k]);
      }
      formData.append(
        "flood_files[]",
        fs.createReadStream(`${buildOutput}\\index.perf.ts`),
        { contentType: "text/vnd.typescript" }
      );
      formData.append(
        "flood_files[]",
        fs.createReadStream(`${buildOutput}\\floodBundle.zip`),
        { contentType: "application/zip" }
      );

      const FloodIO = await fetch("https://api.flood.io/floods", {
        method: "POST",
        headers: {
          Authorization:
            "Basic " + Buffer.from(`${flood.token}:`).toString("base64"),
        },
        body: formData,
      });
      if (FloodIO.status < 400) {
        console.log(message, FloodIO.status, FloodIO.statusText);
        args.logger.info("Done!");
      } else {
        args.logger.error("Deployment failed:");
        console.log(FloodIO);
      }
    }
    args.logger.profile("deployLST");
  },
};

const { command, describe, builder, handler } = cmd;

export { command, describe, builder, handler };

export const prompts = {
  createNewTestData: {
    type: "confirm",
    name: "createNewTestData",
    message: "Generate new test data?",
    initial: false,
    required: true,
  },
  scenario: (chosenScenarios: LSTDataConfig[]) => ({
    type: "select",
    name: "scenario",
    message: "Which scenario?",
    choices: scenarioChoices.reduce((choices, choice) => {
      if (!chosenScenarios.find((v) => v.scenario === choice.name)) {
        choices.push(choice as Choice);
      }
      return choices;
    }, [] as Choice[]),
    initial: 0,
    required: true,
  }),
  chance: (occupied: number) => ({
    type: "numeral",
    name: "chance",
    message: `With a frequency of (max. ${100 - occupied}%)?`,
    min: 0.01,
    max: 100 - occupied,
    initial: 100 - occupied,
    required: true,
  }),
  eligible: {
    type: "numeral",
    name: "eligible",
    message: "Employee eligibility rate (max. 100%)?",
    min: 1,
    max: 100,
    initial: 100,
    required: true,
  },
  numRecords: {
    type: "numeral",
    name: "numRecords",
    message: "How many records are needed?",
    min: 10,
    max: 10000,
    initial: 10,
    required: true,
  },
  dataOutput: (id: string) => ({
    type: "input",
    name: "dataOutput",
    message: "What is the destination folder?",
    initial: id,
    required: true,
  }),
  token: (token: string) => ({
    type: "input",
    name: "token",
    message: "Flood API Key:",
    initial: token,
    required: true,
    skip: true,
  }),
  tool: {
    type: "select",
    name: "tool",
    message: "Testing tool to use:",
    choices: [
      { name: "flood-chrome", message: "Flood Chrome" },
      { name: "jmeter", message: "JMeter" },
      { name: "gatling", message: "Gatling" },
      { name: "java-selenium-chrome", message: "Selenium Chrome" },
      { name: "java-selenium-firefox", message: "Selenium Firefox" },
    ],
    initial: 0,
    skip: true,
  },
  project: {
    type: "input",
    name: "project",
    message: "Flood project name:",
    initial: "PFML",
    skip: true,
  },
  name: {
    type: "input",
    name: "name",
    message: "Name of test:",
    initial: `${new Date().toISOString().slice(0, 17).replace(/-|:/g, "")}`,
    required: true,
  },
  threads: {
    type: "numeral",
    name: "threads",
    message: "Number of concurrent users?",
    min: 1,
    max: 500,
    initial: 1,
    required: true,
  },
  duration: {
    type: "numeral",
    name: "duration",
    message: "Duration (in minutes)?",
    min: 15,
    max: 180,
    initial: 15,
    result: minutesToSecs,
    required: true,
  },
  rampup: {
    type: "numeral",
    name: "rampup",
    message: "Ramp-up (in minutes)?",
    min: 0,
    max: 180,
    initial: 0,
    result: minutesToSecs,
    required: true,
  },
  privacy: {
    type: "select",
    name: "privacy",
    message: "Privacy?",
    choices: [
      { name: "public", message: "Public" },
      { name: "private", message: "Private" },
    ],
    initial: 0,
    skip: true,
  },
  region: {
    type: "select",
    name: "region",
    message: "Region?",
    choices: [
      { name: "us-east-1", message: "US East (Virginia)" },
      { name: "us-west-1", message: "US West (California)" },
      { name: "us-west-2", message: "US West (Oregon)" },
    ],
    initial: 0,
    required: true,
  },
  infrastructure: {
    type: "select",
    name: "infrastructure",
    message: "Grid type?",
    choices: [
      { name: "demand", message: "On-demand" },
      { name: "hosted", message: "Hosted" },
    ],
    initial: 0,
    skip: true,
  },
  instanceQuantity: {
    type: "numeral",
    name: "instanceQuantity",
    message: "Grid instance quantity?",
    initial: 1,
    skip: true,
  },
  instanceType: {
    type: "input",
    name: "instanceType",
    message: "Grid instance type?",
    initial: "m5.xlarge",
    skip: true,
  },
  stopAfter: {
    type: "numeral",
    name: "stopAfter",
    message: "Stop grid (in minutes)?",
    min: 0,
    max: 2880,
    initial: 180,
    skip: true,
  },
  startFlood: {
    type: "confirm",
    name: "startFlood",
    message: "Are you ready to start your flood?",
  },
};

export function minutesToSecs(minutes: string): string {
  return (+minutes * 60).toString();
}

export const scenarioChoices = [
  {
    name: "PortalClaimSubmit",
    message: "Portal claim submission",
  },
  {
    name: "FineosClaimSubmit",
    message: "Fineos claim submission",
  },
  {
    name: "LeaveAdminSelfRegistration",
    message: "Leave Admin Self Registration",
  },
  { name: "SavilinxAgent", message: "Savilinx Agent" },
  { name: "DFMLOpsAgent", message: "DFMLOps Agent" },
];

const asyncExec = util.promisify(exec);

export const execScript = async (
  command: string,
  message?: string,
  dirname?: string
): Promise<void> => {
  const { stderr, stdout } = await asyncExec(
    `${dirname ? `cd ${dirname} && ` : ""}${command}`
  );
  if (stderr) {
    console.log(`stderr: ${stderr}`);
  } else {
    console.log(stdout);
    if (message) console.log(message);
  }
};
