import path from "path";
import util from "util";
import { exec } from "child_process";
import * as Cfg from "./flood/config";
import { prompt } from "enquirer";

const asyncExec = util.promisify(exec);

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

export const convMinToSec = (minutes: string): string =>
  (+minutes * 1000).toString();

(async (): Promise<void> => {
  const response: Record<string, string> = await prompt([
    {
      type: "password",
      name: "token",
      message:
        "Flood API token <https://app.flood.io/account/api> (Leave blank if previously authenticated):",
      initial: await Cfg.floodToken,
      skip: true,
    },
    {
      type: "confirm",
      name: "makeBundle",
      message: "Generate new file bundle?",
      initial: false,
      required: true,
    },
    {
      type: "input",
      name: "files",
      message: "Path to bundled files (`floodBundle.zip` and `index.perf.ts`):",
      initial: path.join(__dirname, "../scripts"),
      required: true,
    },
    {
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
      required: true,
    },
    {
      type: "input",
      name: "project",
      message: "Flood project name:",
      initial: "PFML",
      required: true,
    },
    {
      type: "input",
      name: "name",
      message: "Name of test:",
      initial: `${new Date().toISOString().slice(0, 17).replace(/-|:/g, "")}`,
      required: true,
    },
    {
      type: "numeral",
      name: "threads",
      message: "Number of concurrent users:",
      initial: 1,
      required: true,
    },
    {
      type: "numeral",
      name: "duration",
      message: "Duration (minutes):",
      initial: 15,
      result: (value) => convMinToSec(value),
      required: true,
    },
    {
      type: "numeral",
      name: "rampup",
      message: "Ramp-up (minutes):",
      initial: 0,
      result: (value) => convMinToSec(value),
      required: true,
    },
    {
      type: "select",
      name: "privacy",
      message: "Privacy:",
      choices: [
        { name: "public", message: "Public" },
        { name: "private", message: "Private" },
      ],
      initial: 0,
      skip: true,
    },
    {
      type: "select",
      name: "region",
      message: "Region:",
      choices: [
        { name: "us-east-1", message: "US East (Virginia)" },
        { name: "us-west-1", message: "US West (California)" },
        { name: "us-west-2", message: "US West (Oregon)" },
      ],
      initial: 0,
      required: true,
    },
    {
      type: "select",
      name: "infrastructure",
      message: "Grid type:",
      choices: [
        { name: "demand", message: "On-demand" },
        { name: "hosted", message: "Hosted" },
      ],
      initial: 0,
      skip: true,
    },
    {
      type: "numeral",
      name: "instanceQuantity",
      message: "Grid instance quantity:",
      initial: 1,
      skip: true,
    },
    {
      type: "numeral",
      name: "stopAfter",
      message:
        "Stop grid after N minutes (where N > 0 and N <= 2,880 [48 hours]):",
      initial: 90,
      skip: true,
    },
    {
      type: "select",
      name: "instanceType",
      message: "Grid instance type:",
      choices: ["m5.xlarge"],
      initial: 0,
      skip: true,
    },
    {
      type: "confirm",
      name: "startFlood",
      message: "Are you ready to start your flood?",
    },
  ]);

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
    startFlood,
  } = response;

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
  if (startFlood) {
    const command = `./launchFlood.sh \
      -u "${token}" \
      -l "${tool}" \
      -p "${project}" \
      -n "${name}" \
      -v "${privacy}" \
      -t "${threads}" \
      -m "${rampup}" \
      -d "${duration}" \
      -i "${infrastructure}" \
      -q "${instanceQuantity}" \
      -r "${region}" \
      -y "${instanceType}" \
      -s "${stopAfter}"`;

    const message = `
Flood "${name}" launched on "${project}":
  - Concurrent users: ${threads}
  - Duration: ${+duration / 1000} minute(s)
  - Ramp-up: ${rampup} minute(s)`;

    execScript(files, command, message);
  }
})();
