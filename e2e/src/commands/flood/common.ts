import fs from "fs";
import path from "path";
import util from "util";
import { exec } from "child_process";
import { LSTScenario } from "../../flood/config";
import configs from "../../../config.json";

export const presetNames = [
  "base",
  "basePlus",
  "basePlusSpikes",
  "leaveAdmin",
] as const;
export type PresetName = typeof presetNames[number];
export type Presets = {
  // Uses "mapped type" for key definition.
  // @see https://www.typescriptlang.org/docs/handbook/2/mapped-types.html
  [Property in PresetName]: DeployLST[];
};

export const environmentNames = Object.keys(configs);
export type EnvironmentName = typeof environmentNames[number];

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
let buildDir = path.join(scriptsDir, deploymentId);
let docsDir = path.join(buildDir, "bundleInfo.md");
export const envJson = path.resolve("./src/flood/data", "env.json");

export function setBuildDir(folder: string): string {
  if (folder.length > 0) {
    buildDir = path.join(scriptsDir, folder);
    docsDir = path.join(buildDir, "bundleInfo.md");
  }
  return buildDir;
}

export function minutesToSecs(minutes: string): string {
  return (+minutes * 60).toString();
}

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
  token: string;
  env?: string;
  speed?: number;
  generateData?: boolean;
  numRecords?: number;
  scenario?: string;
  chance?: number;
  eligible?: number;
};

export type DeployLST = {
  startAfter?: number;
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

/*
 * Bug: Enquirer's initial values do not apply to "choice" questions/prompts
 * and it will default to whatever is the first option everytime instead.
 * We can go around this by limiting the choices to one, when it is in args
 */
export const getChoiceIndexByName = (
  choices: Choice[],
  name: string
): number | null => {
  const index = choices.findIndex((element) => element.name === name);
  return index !== -1 ? index : null;
};

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

// eslint-disable-next-line @typescript-eslint/explicit-module-boundary-types
export const bundlerPrompts = (args: BundleLST) => ({
  env: {
    type: "input",
    name: "env",
    message: "Target environment?",
    initial: args.env || "performance",
    required: true,
    skip: "env" in args,
  },
  speed: {
    type: "numeral",
    name: "speed",
    message: "Simulation speed (higher means slower)?",
    min: 0,
    max: 2,
    initial: args.speed || 0.1,
    required: true,
    skip: "speed" in args,
  },
  generateData: {
    type: "confirm",
    name: "generateData",
    message: "Generate new test data?",
    initial: args.generateData,
    required: true,
    skip: !!args.generateData,
  },
  scenario: {
    type: "select",
    name: "scenario",
    message: "Scenario?",
    choices: args.scenario
      ? [scenarioChoices.find((s) => s.name === args.scenario)]
      : scenarioChoices,
    initial: getChoiceIndexByName(
      scenarioChoices,
      args.scenario || "PortalClaimSubmit"
    ),
    required: true,
    skip: !!args.scenario,
  },
  chance: (occupied: number) => ({
    type: "numeral",
    name: "chance",
    message: `With a frequency of (max. ${100 - occupied}%)?`,
    min: 0.01,
    max: 100 - occupied,
    initial: args.chance || 100 - occupied,
    required: true,
    skip: "chance" in args,
  }),
  eligible: {
    type: "numeral",
    name: "eligible",
    message: "Employee eligibility rate (max. 100%)?",
    min: 1,
    max: 100,
    initial: args.eligible || 100,
    required: true,
    skip: "eligible" in args,
  },
  numRecords: {
    type: "numeral",
    name: "numRecords",
    message: "How many records?",
    min: 10,
    max: 10000,
    initial: args.numRecords || 10,
    required: true,
    skip: "numRecords" in args,
  },
  bundleDir: {
    type: "input",
    name: "bundleDir",
    message: "Destination folder?",
    initial: deploymentId,
    skip: true,
  },
});

export const toolChoices: Choice[] = [
  { name: "flood-chrome", message: "Flood Chrome" },
  { name: "jmeter", message: "JMeter" },
  { name: "gatling", message: "Gatling" },
  { name: "java-selenium-chrome", message: "Selenium Chrome" },
  { name: "java-selenium-firefox", message: "Selenium Firefox" },
];

export const privacyChoices: Choice[] = [
  { name: "public", message: "Public" },
  { name: "private", message: "Private" },
];

export const regionChoices: Choice[] = [
  { name: "us-east-1", message: "US East (Virginia)" },
  { name: "us-west-1", message: "US West (California)" },
  { name: "us-west-2", message: "US West (Oregon)" },
];

export const infrastructureChoices: Choice[] = [
  { name: "demand", message: "On-demand" },
  { name: "hosted", message: "Hosted" },
];

// eslint-disable-next-line @typescript-eslint/explicit-module-boundary-types
export const deployPrompts = (args: DeployLST) => ({
  tool: {
    type: "select",
    name: "tool",
    message: "Testing tool?",
    choices: args.tool
      ? [toolChoices.find((s) => s.name === args.tool)]
      : toolChoices,
    initial: getChoiceIndexByName(toolChoices, args.tool || "flood-chrome"),
    skip: !!args.tool,
  },
  project: {
    type: "input",
    name: "project",
    message: "Project's name?",
    initial: args.project || "PFML",
    skip: true,
  },
  name: {
    type: "input",
    name: "name",
    message: "Test's name?",
    initial: args.name || deploymentId,
    required: true,
    skip: !!args.name,
  },
  threads: {
    type: "numeral",
    name: "threads",
    message: "How many concurrent users?",
    min: 1,
    max: 500,
    initial: args.threads || 1,
    required: true,
    skip: !!args.threads,
  },
  duration: {
    type: "numeral",
    name: "duration",
    message: "Duration (in minutes)?",
    min: 15,
    max: 180,
    initial: args.duration || 15,
    result: minutesToSecs,
    required: true,
    skip: "duration" in args,
  },
  rampup: {
    type: "numeral",
    name: "rampup",
    message: "Ramp-up (in minutes)?",
    min: 0,
    max: 180,
    initial: args.rampup || 0,
    result: minutesToSecs,
    required: true,
    skip: "rampup" in args,
  },
  privacy: {
    type: "select",
    name: "privacy",
    message: "Privacy?",
    choices: args.privacy
      ? [privacyChoices.find((s) => s.name === args.privacy)]
      : privacyChoices,
    initial: getChoiceIndexByName(privacyChoices, args.privacy || "public"),
    skip: !!args.privacy,
  },
  region: {
    type: "select",
    name: "region",
    message: "Region?",
    choices: args.region
      ? [regionChoices.find((s) => s.name === args.region)]
      : regionChoices,
    initial: getChoiceIndexByName(regionChoices, args.region || "us-east-1"),
    required: true,
    skip: !!args.region,
  },
  infrastructure: {
    type: "select",
    name: "infrastructure",
    message: "Grid type?",
    choices: args.infrastructure
      ? [infrastructureChoices.find((s) => s.name === args.infrastructure)]
      : infrastructureChoices,
    initial: getChoiceIndexByName(
      infrastructureChoices,
      args.infrastructure || "demand"
    ),
    skip: !!args.infrastructure,
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
    initial: args.startFlood,
    skip: !!args.startFlood,
  },
});
