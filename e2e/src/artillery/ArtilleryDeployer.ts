import {
  ECSClient,
  RegisterTaskDefinitionCommand,
  RunTaskCommand,
} from "@aws-sdk/client-ecs";
import { GetParameterCommand, SSMClient } from "@aws-sdk/client-ssm";
import { parse as parseARN } from "@aws-sdk/util-arn-parser";
import { cloudwatchInsights, generateNRAPMLink } from "../util/urls";
import { add } from "date-fns";
import { URL, URLSearchParams } from "url";

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
  influx_url: string;
  influx_token: string;
  influx_organization: string;
  influx_bucket: string;
  sqs_queue: string;
};

type ContainerConfig = {
  name: string;
  image: string;
  command: string[];
  instances: number;
  environment: Record<string, string>;
};
type ContainerConfigWithDefinition = ContainerConfig & {
  taskDefinitionArn: string;
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
    const values = await getParameter(arn);
    this.checkConfig(values);
    return new ArtilleryDeployer({
      ...values,
      ...overrides,
    });
  }

  static checkConfig(config: unknown): asserts config is ECSLSTRunnerConfig {
    // Yeah, this is kind of a weak type check...
    if (
      !config ||
      !(config as ECSLSTRunnerConfig).region ||
      !(config as ECSLSTRunnerConfig).influx_url
    ) {
      throw new Error(`Invalid configuration`);
    }
  }

  constructor(private config: ECSLSTRunnerConfig) {
    this.ecsClient = new ECSClient({ region: config.region });
    this.registry = config.registry;
  }

  async deploy(
    runId: string,
    containers: ContainerConfig[]
  ): Promise<{
    cluster: string;
    cloudwatch: string;
    influx: string;
    newrelic: string;
  }> {
    const configsWithDefinition: ContainerConfigWithDefinition[] = [];
    for (const container of containers) {
      const taskDefinitionArn = await this.createTaskDefinition(
        container.name,
        container.image,
        runId
      );
      configsWithDefinition.push({
        ...container,
        taskDefinitionArn,
      });
    }
    // Now run a task for each configuration.
    for (const container of configsWithDefinition) {
      const containerWithEnvironment = {
        ...container,
        environment: {
          ...container.environment,
          INFLUX_URL: this.config.influx_url,
          INFLUX_TOKEN: this.config.influx_token,
          INFLUX_ORGANIZATION: this.config.influx_organization,
          INFLUX_BUCKET: this.config.influx_bucket,
          CLAIMS_SQS_QUEUE: this.config.sqs_queue,
        },
      };
      await this.runTask(containerWithEnvironment);
    }
    const clusterName = parseARN(this.config.cluster).resource.split("/").pop();
    const start = new Date();
    const end = add(new Date(), { hours: 1.5 });
    return {
      cluster: `https://console.aws.amazon.com/ecs/home?region=us-east-1#/clusters/${clusterName}/tasks`,
      cloudwatch: this.buildCloudwatchURL(runId, start, end),
      influx: this.buildInfluxURL(runId, start, end),
      newrelic: generateNRAPMLink(start, end, "performance"),
    };
  }

  private buildCloudwatchURL(runId: string, start: Date, end: Date): string {
    const query = `fields @timestamp, uid, level, message, @message
    | filter run_id = "${runId}"
    | sort @timestamp desc
    | limit 200`;
    return cloudwatchInsights(
      this.config.region,
      [this.config.logGroup],
      query,
      {
        start,
        end,
        timeType: "ABSOLUTE",
      }
    );
  }

  private buildInfluxURL(runId: string, start: Date, end: Date): string {
    const dashboardUrl = new URL(
      "https://us-east-1-1.aws.cloud2.influxdata.com/orgs/2d104c868dfad878/dashboards/083748d6e50d4000"
    );
    const params = new URLSearchParams({
      "vars[runId]": runId,
      lower: start.toISOString(),
      upper: end.toISOString(),
    });
    dashboardUrl.search = params.toString();
    return dashboardUrl.toString();
  }

  private createTaskDefinition(
    name: string,
    image: string,
    runId: string
  ): Promise<string> {
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
              "awslogs-stream-prefix": `artillery/${runId}/${name}`,
            },
          },
          essential: true,
        },
      ],
      family: name,
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

  private runTask(container: ContainerConfigWithDefinition): Promise<string[]> {
    const command = new RunTaskCommand({
      cluster: this.config.cluster,
      taskDefinition: container.taskDefinitionArn,
      networkConfiguration: {
        awsvpcConfiguration: {
          subnets: this.config.subnets,
          securityGroups: this.config.securityGroups,
          assignPublicIp: "ENABLED",
        },
      },
      launchType: "FARGATE",
      count: container.instances,
      startedBy: "E2E-LST",
      overrides: {
        containerOverrides: [
          {
            name: "worker",
            command: container.command,
            environment: Object.entries(container.environment).map(
              ([name, value]) => ({
                name,
                value,
              })
            ),
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

export async function getParameter(arn: string): Promise<unknown> {
  const name = parseARN(arn).resource.replace(/^parameter/, "");
  const parameterRegion = parseARN(arn).region;
  const ssm = new SSMClient({ region: parameterRegion });
  const response = await ssm.send(
    new GetParameterCommand({
      Name: name,
      WithDecryption: true,
    })
  );
  if (!response.Parameter) throw new Error("Parameter not found");
  if (!response.Parameter.Value) throw new Error("Parameter has no value");
  return { region: parameterRegion, ...JSON.parse(response.Parameter.Value) };
}
