import { spawn as _spawn, SpawnOptions } from "child_process";
import { format } from "date-fns";
import aws from "aws-sdk";

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

  console.log("Creating Task Definition...\n");
  aws.config.update({ region: "us-east-1" });
  const ecs = new aws.ECS();
  const task_def_options: aws.ECS.RegisterTaskDefinitionRequest = {
    containerDefinitions: [
      {
        name: "e2e-lst-container",
        image: `233259245172.dkr.ecr.us-east-1.amazonaws.com/${image_name}`,
        logConfiguration: {
          logDriver: "awslogs",
          options: {
            "awslogs-group": "e2e-lst-logs",
            "awslogs-region": "us-east-1",
            "awslogs-stream-prefix": "artillery-logs-test-max",
          },
        },
        essential: true,
      },
    ],
    family: "e2e-lst-task-8",
    taskRoleArn: "arn:aws:iam::233259245172:role/execute-task-main",
    executionRoleArn: "arn:aws:iam::233259245172:role/execute-task-main",
    networkMode: "awsvpc",
    requiresCompatibilities: ["FARGATE"],
    cpu: "2048",
    memory: "4096",
  };

  const task_def = await ecs.registerTaskDefinition(task_def_options).promise();

  console.log(
    `Task Definition: '${task_def.taskDefinition?.family}' created ...\nwith status: ${task_def.taskDefinition?.status}\n`
  );

  console.log("Running tasks ...\n");

  const network_config: aws.ECS.NetworkConfiguration = {
    awsvpcConfiguration: {
      subnets: ["subnet-0c18406a", "subnet-26157917", "subnet-d081699c"],
      securityGroups: ["sg-9be41784"],
      assignPublicIp: "ENABLED",
    },
  };

  const task_results = await ecs
    .runTask({
      cluster: "arn:aws:ecs:us-east-1:233259245172:cluster/e2e-lst-cluster",
      group: task_def.taskDefinition?.family,
      taskDefinition: task_def.taskDefinition?.taskDefinitionArn as string,
      networkConfiguration: network_config,
      launchType: "FARGATE",
      count: 1,
      startedBy: "E2E-LST",
    })
    .promise();

  if (!task_results.tasks) {
    throw new Error("No task can be started!");
  }
  console.log(
    `Task has been triggered and last status is: ${task_results.tasks[0].lastStatus}\nCheck AWS Cloudwatch for any logs.`
  );
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
