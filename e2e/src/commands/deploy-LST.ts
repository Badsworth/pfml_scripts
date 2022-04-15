import { CommandModule } from "yargs";
import { SystemWideArgs } from "../cli";
import config from "../config";
import { v4 as uuid } from "uuid";
import { spawn as _spawn } from "child_process";
import ArtilleryDeployer, {
  ContainerConfig,
} from "../artillery/ArtilleryDeployer";
import { format } from "date-fns";

/**
 * @Note
 * This command is used to build images and push them to AWS ECR and
 * then running the image via AWS ECS Fargate
 *
 * In order to use AWS CLI you'll need your SSO creds configured -
 * then authenticate (to Docker) to our repo w/this command:
 *
 * AWS_PROFILE=lcm-pfml aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 233259245172.dkr.ecr.us-east-1.amazonaws.com
 *
 * Once authenticated you can use this script to build, tag and push the image to our AWS ECR
 */

type PresetArgs = {
  env: string;
  deploy_type: string;
  containers: number;
  debug: boolean;
  crmTesting: boolean;
} & SystemWideArgs;

const cmd: CommandModule<SystemWideArgs, PresetArgs> = {
  command: "deploy-lst",
  describe: "Creates docker image and triggers LST via AWS fargate",
  builder: (yargs) => {
    return yargs.options({
      env: {
        description: "Sets the env for LST",
        string: true,
        default: "performance",
        choices: ["test", "performance"],
        alias: ["e", "env", "environment"],
      },
      deploy_type: {
        description: "Specifies the type of LST",
        string: true,
        default: "basic",
        choices: ["basic", "full_lst", "noSpikes_lst"],
        alias: ["t", "type"],
      },
      containers: {
        description: "Amount of containers needed for LST",
        num: true,
        default: 1,
        alias: ["c", "cont", "containers"],
      },
      debug: {
        description: "Turn on debug for extra logging",
        boolean: true,
        default: false,
        alias: ["d", "debug"],
      },
      crmTesting: {
        description: "Deploy CRM integration testing",
        boolean: true,
        default: true,
        alias: ["crm"],
      },
    });
  },
  async handler(args) {
    const { env, deploy_type, containers, debug, logger, crmTesting } = args;
    const deployer = await ArtilleryDeployer.createFromConfigParameter(
      "arn:aws:ssm:us-east-1:233259245172:parameter/lst-worker-config",
      {
        // Optional config overrides can be added here in development. Move them into
        // the configuration parameter once you're ready for others to use them.
      }
    );
    const run_id = `${format(new Date(), "MM-dd-yyyy")}-${uuid()}`;
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

    logger.info("Building Docker Image ...\n-----------------------");
    await spawn("docker", cmd_args.build);
    logger.info("Docker Image Build Complete!\n");

    logger.info(
      "Pushing Image to ECR-LST repository...\n-----------------------"
    );
    await spawn("docker", cmd_args.push);
    logger.info(`Image Pushed to ${remote_tag}!`);

    const secretNames = [
      "PORTAL_PASSWORD" as const,
      "FINEOS_PASSWORD" as const,
      "EMPLOYER_PORTAL_PASSWORD" as const,
      "TESTMAIL_APIKEY" as const,
      "FINEOS_USERS" as const,
      "LST_FILE_RANGE" as const,
      "API_SNOW_CLIENT_ID" as const,
      "API_SNOW_CLIENT_SECRET" as const,
    ];
    const environment = secretNames.reduce(
      (env, name) => {
        env[`E2E_${name}`] = config(name);
        return env;
      },
      {
        E2E_ENVIRONMENT: env,
        LST_RUN_ID: run_id,
        E2E_DEBUG: debug ? "true" : "false",
        IS_ECS: "true",
      } as Record<string, string>
    );

    const containerConfigs: ContainerConfig[] = [
      {
        name: "artillery-agent",
        image: remote_tag,
        command: [
          "node_modules/.bin/artillery",
          "run",
          "-e",
          deploy_type,
          "dist/cloud.agents.yml",
        ],
        instances: containers,
        environment,
      },
      {
        name: "artillery-claimant",
        image: remote_tag,
        command: [
          "node_modules/.bin/artillery",
          "run",
          "-e",
          deploy_type,
          "dist/cloud.claimants.yml",
        ],
        instances: containers,
        environment,
      },
    ];
    if (crmTesting) {
      containerConfigs.push({
        name: "artillery-crm",
        image: remote_tag,
        command: [
          "node_modules/.bin/artillery",
          "run",
          "-e",
          deploy_type,
          "dist/cloud.crm.yml",
        ],
        instances: containers,
        environment,
      });
    }
    const result = await deployer.deploy(run_id, containerConfigs);
    logger.info(
      `LST has been triggered...\n\nContainers:${result.containerCount} of ${result.runCount}\n\nCluster:\n------\n${result.cluster}\n\nInflux Dashboard:\n------\n${result.influx}\n\nLogs:\n-----\n${result.cloudwatch}\n\nNew Relic APM:\n-----\n${result.newrelic}\n\n\n`
    );
  },
};

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

const { command, describe, builder, handler } = cmd;
export { command, describe, builder, handler };
