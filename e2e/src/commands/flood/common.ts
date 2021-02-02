import fs from "fs";
import path from "path";
import util from "util";
import { exec } from "child_process";
import { LSTScenario } from "../../flood/config";

const asyncExec = util.promisify(exec);

export const runCommand = async (
  command: string,
  showLogs = false
): Promise<void> => {
  const { stderr, stdout } = await asyncExec(command);
  if (stderr)
    throw new Error(`Failed to run command "${command}":\n${stderr}\n`);
  if (showLogs) console.log(stdout);
};

export const deploymentId = new Date()
  .toISOString()
  .slice(0, 19)
  .replace(/-|:/g, "");

export const scriptsDir = path.resolve("./scripts");
export const bundlerShell = path.join(scriptsDir, "makeFloodBundle.sh");
export const buildDir = path.join(scriptsDir, deploymentId);
export const docsDir = path.join(buildDir, "bundleInfo.md");
export const envJson = path.resolve("./src/flood/data", "env.json");

export const logDeployment = async (
  title: string,
  data?: Record<string, unknown>
): Promise<void> => {
  if (!fs.existsSync(buildDir)) {
    await fs.promises.mkdir(buildDir);
  }
  return fs.promises.appendFile(
    docsDir,
    `${title}\n${
      data ? `\n\`\`\`json\n${JSON.stringify(data, null, 2)}\n\`\`\`\n` : ""
    }`
  );
};

export type LSTDataConfig = {
  scenario: LSTScenario;
  chance: number;
  eligible?: number;
  // type?: Cfg.ClaimType;
};

export type PromptRes = Record<string, string>;
interface Choice {
  name: string;
  message?: string;
  value?: string;
  hint?: string;
  disabled?: boolean | string;
}

export type BundleLST = {
  bundleDir: string;
  env?: string;
  speed?: number;
  generateData?: boolean;
  numRecords?: number;
  scenario?: string;
  chance?: number;
  eligible?: number;
};

export type DeployLST = {
  startFlood?: boolean;
  tool?: string;
  project?: string;
  name: string;
  threads: number;
  duration: number;
  rampup: number;
  privacy?: string;
  region: string;
  infrastructure?: string;
  instanceQuantity?: number;
  instanceType?: string;
  stopAfter?: number;
} & BundleLST;

// type PromptOptions = Record<string, unknown> | ((...args: any) => Record<string, unknown>);
// type BundlerPrompts = Record<keyof BundleLST, PromptOptions>
// type DeployPrompts = Record<keyof DeployLST, PromptOptions>

// eslint-disable-next-line @typescript-eslint/explicit-module-boundary-types
export const bundlerPrompts = (args: BundleLST) => ({
  env: {
    type: "select",
    name: "env",
    message: "Target environment?",
    choices: [
      { name: "test", message: "Test" },
      { name: "stage", message: "Stage" },
      { name: "performance", message: "Performance" },
      { name: "training", message: "Training" },
    ],
    initial: 2,
    required: true,
    skip: !!args.env,
  },
  speed: {
    type: "numeral",
    name: "speed",
    message: "Simulation speed (higher means slower)?",
    min: 0,
    max: 2,
    initial: args.speed || 1,
    required: true,
    skip: !!args.speed,
  },
  generateData: {
    type: "confirm",
    name: "generateData",
    message: "Generate new test data?",
    initial: false,
    required: true,
    skip: !!args.generateData,
  },
  scenario: (chosenScenarios: LSTDataConfig[]) => ({
    type: "select",
    name: "scenario",
    message: "Scenario?",
    // todo: optimize
    choices: scenarioChoices.reduce((choices, choice) => {
      if (!chosenScenarios.find((v) => v.scenario === choice.name)) {
        choices.push(choice);
      }
      return choices;
    }, [] as Choice[]),
    initial: 0,
    required: true,
    skip: !!args.scenario,
  }),
  chance: (occupied: number) => ({
    type: "numeral",
    name: "chance",
    message: `With a frequency of (max. ${100 - occupied}%)?`,
    min: 0.01,
    max: 100 - occupied,
    initial: 100 - occupied,
    required: true,
    skip: !!args.chance,
  }),
  eligible: {
    type: "numeral",
    name: "eligible",
    message: "Employee eligibility rate (max. 100%)?",
    min: 1,
    max: 100,
    initial: 100,
    required: true,
    skip: !!args.eligible,
  },
  numRecords: {
    type: "numeral",
    name: "numRecords",
    message: "How many records?",
    min: 10,
    max: 10000,
    initial: 10,
    required: true,
    skip: !!args.numRecords,
  },
  bundleDir: {
    type: "input",
    name: "bundleDir",
    message: "Destination folder?",
    initial: deploymentId,
    skip: true,
  },
});

// eslint-disable-next-line @typescript-eslint/explicit-module-boundary-types
export const deployPrompts = (args: DeployLST) => ({
  tool: {
    type: "select",
    name: "tool",
    message: "Testing tool?",
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
    message: "Project's name?",
    initial: "PFML",
    skip: true,
  },
  name: {
    type: "input",
    name: "name",
    message: "Test's name?",
    initial: deploymentId,
    required: true,
    skip: !!args.name,
  },
  threads: {
    type: "numeral",
    name: "threads",
    message: "How many concurrent users?",
    min: 1,
    max: 500,
    initial: 1,
    required: true,
    skip: !!args.threads,
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
    skip: !!args.duration,
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
    skip: !!args.rampup,
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
    skip: !!args.region,
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
    message: "Do you want to deploy this bundle to flood?",
    initial: false,
    skip: !!args.startFlood,
  },
});

export function minutesToSecs(minutes: string): string {
  return (+minutes * 60).toString();
}

export const scenarioChoices: Choice[] = [
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
