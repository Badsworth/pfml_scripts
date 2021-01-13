import path from "path";
import util from "util";
import { exec } from "child_process";
import yargsInteractive, { OptionData } from "yargs-interactive";
import * as Cfg from "./flood/config";

const asyncExec = util.promisify(exec);

type FloodOptions = {
  [key: string]:
    | OptionData
    | {
        default: boolean;
        validate?: (input: unknown) => Promise<boolean>;
      };
};

const getOptions = async (): Promise<FloodOptions> => ({
  interactive: { default: true },
  token: {
    type: "password",
    describe:
      "Flood API token <https://app.flood.io/account/api> (Leave blank if previously authenticated):",
    default: (await Cfg.floodToken) || undefined,
    prompt: "if-empty",
  },
  makeBundle: {
    type: "confirm",
    describe: "Generate new file bundle?",
    default: true,
    prompt: "always",
  },
  files: {
    type: "input",
    describe: "Path to bundled files (`floodBundle.zip` and `index.perf.ts`):",
    default: path.join(__dirname, "../scripts"),
    prompt: "if-empty",
  },
  tool: {
    type: "list",
    describe: "Testing tool to use:",
    choices: [
      "flood-chrome",
      "jmeter",
      "gatling",
      "java-selenium-chrome",
      "java-selenium-firefox",
    ],
    default: "flood-chrome",
    prompt: "if-empty",
  },
  project: {
    type: "input",
    describe: "Flood project name:",
    default: "PFML",
    prompt: "if-no-arg",
  },
  name: {
    type: "input",
    describe: "Name of test:",
    // Requires value since no default is being provided.
    validate: (input) => new Promise((resolve) => resolve(!!input)),
    prompt: "if-no-arg",
  },
  threads: {
    type: "number",
    describe: "Number of concurrent users:",
    default: 1,
    prompt: "if-no-arg",
  },
  duration: {
    type: "number",
    describe: "Duration (minutes):",
    default: 15,
    prompt: "if-no-arg",
  },
  rampup: {
    type: "number",
    describe: "Ramp-up (minutes):",
    default: 0,
    prompt: "if-no-arg",
  },
  privacy: {
    type: "list",
    describe: "Privacy:",
    choices: ["public", "private"],
    default: "public",
    prompt: "if-empty",
  },
  region: {
    type: "list",
    describe: "Region:",
    choices: ["us-east-1", "us-west-1", "us-west-2"],
    default: "us-east-1",
    prompt: "if-no-arg",
  },
  infrastructure: {
    type: "list",
    describe: "On-demand or hosted grid:",
    choices: ["demand", "hosted"],
    default: "demand",
    prompt: "if-empty",
  },
  instanceQuantity: {
    type: "number",
    describe: "Grid instance quantity:",
    default: 1,
    prompt: "if-empty",
  },
  stopAfter: {
    type: "number",
    describe:
      "Stop grid after N minutes (where N > 0 and N <= 2,880 [48 hours]):",
    default: 60,
    prompt: "if-empty",
  },
  instanceType: {
    type: "input",
    describe: "Grid instance type:",
    default: "m5.xlarge",
    prompt: "if-empty",
  },
  start: {
    type: "confirm",
    describe: "Are you ready to start your flood?",
    prompt: "always",
  },
});

export const execScript = async (
  dirname: string,
  command: string,
  message: string
): Promise<void> => {
  const { stderr } = await asyncExec(`cd ${dirname} && ${command}`);
  if (stderr) {
    console.log(`stderr: ${stderr}`);
  } else {
    console.log(message);
  }
};

(async (): Promise<void> => {
  const options = await getOptions();
  const {
    token,
    makeBundle,
    files,
    tool,
    project,
    name,
    threads,
    duration,
    rampup,
    privacy,
    region,
    infrastructure,
    instanceQuantity,
    stopAfter,
    instanceType,
  } = await yargsInteractive()
    .usage("$0 <command> [args]")
    .interactive(options);

  // Rebuilds flood file bundle if requested.
  if (makeBundle) {
    execScript(
      files,
      "./makeFloodBundle.sh",
      `
Rebuilt the following files in ${files}:
  - index.perf.ts
  - floodBundle.zip`
    );
  }

  // Launches flood via cURL script.
  const command = `./launchFlood.sh \
    -u "${token}" \
    -l "${tool}" \
    -p "${project}" \
    -n "${name}" \
    -v "${privacy}" \
    -t "${threads}" \
    -m "${rampup}" \
    -d "${+duration * 1000}" \
    -i "${infrastructure}" \
    -q "${instanceQuantity}" \
    -r "${region}" \
    -y "${instanceType}" \
    -s "${stopAfter}"`;
  const message = `
Flood "${name}" launched on "${project}":
  - Concurrent users: ${threads}
  - Duration: ${duration}
  - Ramp-up: ${rampup}`;
  execScript(files, command, message);
})();
