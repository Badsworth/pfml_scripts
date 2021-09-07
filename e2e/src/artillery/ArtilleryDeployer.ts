import {
  ECSClient,
  RegisterTaskDefinitionCommand,
  RunTaskCommand,
} from "@aws-sdk/client-ecs";
import { GetParameterCommand, SSMClient } from "@aws-sdk/client-ssm";
import { parse as parseARN } from "@aws-sdk/util-arn-parser";

type ECSLSTRunnerConfig = {
  region: string;
  cluster: string;
  logGroup: string;
  taskRoleArn: string;
  executionRoleArn: string;
  subnets: string[];
  securityGroups: string[];
  registry: string;
  cpu?: string;
  memory?: string;
};

/**
 * This class deploys artillery to an AWS account.
 *
 * The account must have already been set up with an ECR registry, ECS cluster, and some roles.
 */
export default class ArtilleryDeployer {
  private ecsClient: ECSClient;
  public readonly registry: string;

  /**
   * Creates a new runner instance by pulling the configuration from an SSM Parameter Store parameter.
   *
   * This parameter should contain a JSON object with the configuration values from above.
   */
  static async createFromConfigParameter(
    arn: string,
    overrides?: Partial<ECSLSTRunnerConfig>
  ): Promise<ArtilleryDeployer> {
    const name = parseARN(arn).resource.replace(/^parameter/, "");
    const parameterRegion = parseARN(arn).region;
    const ssm = new SSMClient({ region: parameterRegion });
    const response = await ssm.send(
      new GetParameterCommand({
        Name: name,
      })
    );
    if (!response.Parameter) throw new Error("Parameter not found");
    if (!response.Parameter.Value) throw new Error("Parameter has no value");
    const values = JSON.parse(response.Parameter.Value);
    return new ArtilleryDeployer({
      region: parameterRegion,
      ...values,
      ...overrides,
    });
  }

  constructor(private config: ECSLSTRunnerConfig) {
    this.ecsClient = new ECSClient({ region: config.region });
    this.registry = config.registry;
  }

  async deploy(
    image: string,
    runId: string,
    environment: Record<string, string>
  ): Promise<{ cluster: string }> {
    const taskDefinitionArn = await this.createTaskDefinition(image, runId);
    await this.runTask(taskDefinitionArn, environment);
    const clusterName = parseARN(this.config.cluster).resource.split("/").pop();
    return {
      cluster: `https://console.aws.amazon.com/ecs/home?region=us-east-1#/clusters/${clusterName}/tasks`,
    };
  }

  private createTaskDefinition(image: string, runId: string): Promise<string> {
    const definition = new RegisterTaskDefinitionCommand({
      containerDefinitions: [
        {
          name: "worker",
          image,
          logConfiguration: {
            logDriver: "awslogs",
            options: {
              "awslogs-group": this.config.logGroup,
              "awslogs-region": this.config.region,
              // Put the run ID in the log stream so we can group the log data for a single run together.
              "awslogs-stream-prefix": `artillery/${runId}`,
            },
          },
          essential: true,
        },
      ],
      family: "lst-worker",
      taskRoleArn: this.config.taskRoleArn,
      executionRoleArn: this.config.executionRoleArn,
      networkMode: "awsvpc",
      requiresCompatibilities: ["FARGATE"],
      cpu: this.config.cpu ?? "2048",
      memory: this.config.memory ?? "4096",
    });
    return this.ecsClient.send(definition).then((response) => {
      if (!response.taskDefinition) {
        throw new Error(`No task definition was received`);
      }
      if (!response.taskDefinition.taskDefinitionArn) {
        throw new Error("No task definition ARN was received");
      }
      return response.taskDefinition.taskDefinitionArn;
    });
  }
  private runTask(
    taskDefinition: string,
    environment: Record<string, string>
  ): Promise<string[]> {
    const command = new RunTaskCommand({
      cluster: this.config.cluster,
      taskDefinition: taskDefinition,
      networkConfiguration: {
        awsvpcConfiguration: {
          subnets: this.config.subnets,
          securityGroups: this.config.securityGroups,
          assignPublicIp: "ENABLED",
        },
      },
      launchType: "FARGATE",
      count: 1,
      startedBy: "E2E-LST",
      overrides: {
        containerOverrides: [
          {
            name: "worker",
            environment: Object.entries(environment).map(([name, value]) => ({
              name,
              value,
            })),
          },
        ],
      },
    });

    return this.ecsClient.send(command).then((response) => {
      if (response.failures && response.failures.length > 0) {
        throw new Error(
          `Received failures in starting tasks: ${response.failures
            .map((failure) => failure.reason)
            .join(", ")}`
        );
      }
      if (!response.tasks) {
        throw new Error("No tasks were started");
      }
      return response.tasks.map((task) => {
        if (!task.taskArn) {
          throw new Error(`Task was received without an ARN.`);
        }
        return task.taskArn;
      });
    });
  }
}
