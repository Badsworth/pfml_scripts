import { spawn as _spawn } from "child_process";
import config from "../config";
import { v4 as uuid } from "uuid";
import ArtilleryDeployer from "../artillery/ArtilleryDeployer";

/**
 * This command is to be used to build images and push them to AWS ECR and
 * then running the image via AWS ECS Fargate
 *
 * In order to use this command you'll need your SSO creds to use AWS CLI -
 * then authenticate (to Docker) to our repo w/this command:
 *
 * AWS_PROFILE=lcm-pfml aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 233259245172.dkr.ecr.us-east-1.amazonaws.com
 *
 * Once authenticated you can use this script to build, tag and push the image our AWS ECR
 *
 */

(async () => {
  const configARN =
    "arn:aws:ssm:us-east-1:233259245172:parameter/lst-worker-config";

  const deployer = await ArtilleryDeployer.createFromConfigParameter(
    configARN,
    {
      // Optional config overrides can be added here in development. Move them into
      // the configuration parameter once you're ready for others to use them.
    }
  );
  const run_id = uuid();
  const local_tag = `e2e-lst:${run_id}`;
  const remote_tag = `${deployer.registry}:${run_id}`;
  const cmd_args = {
    build: [
      "build",
      "--pull",
      "--rm",
      "-f",
      "Dockerfile",
      "-t",
      local_tag,
      "-t",
      remote_tag,
      ".",
    ],
    push: ["push", remote_tag],
  };

  console.log("Building Docker Image ...\n-----------------------");
  await spawn("docker", cmd_args.build);
  console.log("Docker Image Build Complete!\n");

  console.log(
    "Pushing Image to ECR-LST repository...\n-----------------------"
  );
  await spawn("docker", cmd_args.push);
  console.log(`Image Pushed to ${remote_tag}!`);

  const secretNames = [
    "ENVIRONMENT" as const,
    "PORTAL_PASSWORD" as const,
    "FINEOS_PASSWORD" as const,
    "TESTMAIL_APIKEY" as const,
    "FINEOS_USERS" as const,
  ];
  const environment = secretNames.reduce(
    (env, name) => {
      env[`E2E_${name}`] = config(name);
      return env;
    },
    {
      LST_RUN_ID: run_id,
      E2E_DEBUG: process.env.E2E_DEBUG,
      IS_ECS: "true",
    } as Record<string, string>,
  );

  const result = await deployer.deploy(remote_tag, run_id, environment);
  console.log(
    `LST has been triggered...\n\n\tCluster: ${result.cluster}\n\n\n`
  );
  console.log(`Check AWS Cloudwatch with RUN_ID: ${run_id} for any logs.`);
})().catch((e) => {
  console.error(e);
  process.exit(1);
});

function spawn(command: string, args: string[] = []): Promise<void> {
  return new Promise((resolve, reject) => {
    const child = _spawn(command, args, {
      stdio: "inherit",
    });
    child.on("close", (code) => {
      code === 0 ? resolve() : reject(`Received ${code}`);
    });
    child.on("error", (err) => {
      reject(err);
    });
  });
}
