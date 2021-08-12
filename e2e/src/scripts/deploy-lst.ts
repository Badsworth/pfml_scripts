import { spawn as _spawn, SpawnOptions } from "child_process";
import { format } from "date-fns";

type ProcessData = {
  stdout: string[];
  stderr: string[];
  code: number;
};

interface SpawnError {
  command: string;
  args: string[] | undefined;
  options: SpawnOptions | undefined;
  result: ProcessData;
}

/**
 * This command is to be used to build images and push them to AWS ECR.
 *
 * In order to use this command you'll need your SSO creds to use AWS CLI -
 * then authenticate to our repo w/this command:
 *
 * AWS_PROFILE=lcm-pfml aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 233259245172.dkr.ecr.us-east-1.amazonaws.com
 *
 * Once authenticated you can use this script to build, tag and push the image our AWS ECR
 *
 * @todo
 * Complete https://lwd.atlassian.net/browse/PFMLPB-1757
 */

(async () => {
  const image_name = `e2e-lst:${format(new Date(), "t")}`;
  const cmd_args = {
    build: [
      "build",
      "--pull",
      "--rm",
      "-f",
      "Dockerfile",
      "-t",
      `${image_name}`,
      ".",
    ],
    tag: [
      "tag",
      `${image_name}`,
      `233259245172.dkr.ecr.us-east-1.amazonaws.com/${image_name}`,
    ],
    push: [
      "push",
      `233259245172.dkr.ecr.us-east-1.amazonaws.com/${image_name}`,
    ],
  };

  try {
    console.log("Building Docker Image ...");
    await run_command("docker", cmd_args.build);
    console.log("Docker Image Build Complete!\n");

    console.log("Tagging the Docker Image ...");
    await run_command("docker", cmd_args.tag);
    console.log("Image Tag Successful!\n");

    console.log("Pushing Image to ECR-LST repository ...");
    await run_command("docker", cmd_args.push);
    console.log("Image Push Successful!\n");
  } catch (e) {
    throw e;
  }
})().catch((e) => {
  console.error(e);
  process.exit(1);
});

/**
 * spwawn function to handle bash commands
 */
function run_command(
  command: string,
  args?: string[],
  options?: SpawnOptions
): Promise<ProcessData> {
  const spawnArgs = args || ([] as string[]),
    spawnOptions = options || ({} as SpawnOptions);
  return new Promise<ProcessData>((resolve, reject) => {
    const child = _spawn(command, spawnArgs, spawnOptions);
    const result: ProcessData = {
      stdout: [],
      stderr: [],
      code: -1,
    };
    child.stderr?.on("data", (d) => {
      result.stderr.push(d.toString());
    });
    child.stdout?.on("data", (d) => {
      result.stdout.push(d.toString());
    });
    child.on("close", (code) => {
      result.code = code as number;
      return code
        ? reject(makeSpawnErrorFor(result, command, args, options))
        : resolve(result);
    });
  });
}

function makeSpawnErrorFor(
  result: ProcessData,
  command: string,
  args: string[] | undefined,
  options: SpawnOptions | undefined
): SpawnError {
  return {
    result,
    command,
    args,
    options,
  };
}
