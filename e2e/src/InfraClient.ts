import { ConfigFunction } from "./config";
import * as path from "path";
import {
  S3Client,
  PutObjectCommandInput,
  ListObjectsV2Command,
  ListObjectsV2CommandOutput,
  ListObjectsV2CommandInput,
} from "@aws-sdk/client-s3";
import { Upload } from "@aws-sdk/lib-storage";
import {
  SFNClient,
  StartExecutionCommand,
  GetExecutionHistoryCommand,
  HistoryEvent,
} from "@aws-sdk/client-sfn";
import { createReadStream } from "fs";
import { URL } from "url";
import delay from "delay";
import pRetry from "p-retry";
import chalk from "chalk";
import { format } from "date-fns";

type SfnEventName =
  | " dor_import "
  | "load_employers_to_fineos"
  | "fineos_eligibility_feed_export"
  | "success";

export default class InfraClient {
  private s3Client: S3Client;
  private sfnClient: SFNClient;

  static create(config: ConfigFunction) {
    return new InfraClient(
      config("ENVIRONMENT"),
      config("DOR_IMPORT_URI"),
      config("DOR_ETL_ARN"),
      config("S3_INTELLIGENCE_TOOL_BUCKET")
    );
  }

  constructor(
    private environment: string,
    private dor_import_uri: string,
    private dor_etl_arn: string,
    private s3_intelligence_tool_bucket: string
  ) {
    this.s3Client = new S3Client({
      region: "us-east-1",
    });
    this.sfnClient = new SFNClient({
      region: "us-east-1",
    });
  }

  private getS3UploadParams(filename: string): PutObjectCommandInput {
    const {
      host: bucket,
      pathname: key,
      protocol,
    } = new URL(this.dor_import_uri);
    if (protocol !== "s3:")
      throw new Error(`Invalid protocol for DOR_IMPORT_URI: ${protocol}`);
    return {
      Bucket: bucket,
      Key: path.join(key.slice(1), path.basename(filename)),
      Body: createReadStream(filename),
    };
  }
  async uploadDORFiles(files: string[]): Promise<void> {
    const uploads = files.map((file) => {
      const upload = new Upload({
        params: this.getS3UploadParams(file),
        client: this.s3Client,
      });
      return upload
        .done()
        .then(() =>
          console.log(
            `${this.environment.toUpperCase()} - Completed upload of ${file}`
          )
        );
    });
    await Promise.all(uploads);
  }

  private async getS3Objects(
    commandInput: ListObjectsV2CommandInput
  ): Promise<ListObjectsV2CommandOutput> {
    return await this.s3Client.send(new ListObjectsV2Command(commandInput));
  }

  async getFineosExtracts(date: Date) {
    const objects = await this.getS3Objects({
      Bucket: this.s3_intelligence_tool_bucket,
      Prefix: `fineos/dataexports/${format(date, "yyyy-MM-dd")}`,
      Delimiter: "/",
    });
    // Ignore non folder types that match - some envs will experience seemingly random .csv files at this level
    if (!objects.CommonPrefixes)
      throw Error(
        `FINEOS extract data for ${format(
          date,
          "yyyy-MM-dd"
        )} not found in S3 bucket "${
          this.s3_intelligence_tool_bucket
        }/fineos/dataexports"`
      );
    // grab objects only in folder for the date's extracts
    const extractFolderPath = objects.CommonPrefixes[0].Prefix as string;
    const [timestamp] = extractFolderPath.split("/").slice(-2, -1);
    const { Contents } = await this.getS3Objects({
      Bucket: this.s3_intelligence_tool_bucket,
      Prefix: extractFolderPath + timestamp,
    });
    return Contents;
  }

  // "exitEvent" determines at which step we want to stop monitoring etl progress
  // i.e if we want to register leave admins, we only need to monitor progress up until "fineos_eligibility_feed_export" begins
  async runDorEtl(
    exitEvent: SfnEventName = "fineos_eligibility_feed_export"
  ): Promise<boolean | void> {
    const { executionArn } = await this.sfnClient.send(
      new StartExecutionCommand({
        stateMachineArn: this.dor_etl_arn,
      })
    );
    console.log(
      `${chalk.blue(
        this.environment.toUpperCase() + " etl execution started"
      )} - waiting on 'load_employers_to_fineos' task completion`
    );
    // wait 3 minutes before checking 'load_employers_to_fineos' completion
    await delay(1000 * 60 * 3);
    // reduces amount of repeat logs
    let log = true;
    return pRetry(
      async () => {
        log &&
          console.log(
            `${chalk.blue(
              this.environment.toUpperCase()
            )} - checking for 'load_employers_to_fineos' task completion`
          );
        const logs = await this.sfnClient.send(
          new GetExecutionHistoryCommand({
            executionArn,
          })
        );
        if (!logs.events) return;
        const getStartedEventName = (event: HistoryEvent) => {
          if (
            event.type === "TaskStateEntered" ||
            event.type === "SucceedStateEntered"
          ) {
            return event.stateEnteredEventDetails?.name;
          }
        };
        for (const event of logs.events) {
          const eventName = getStartedEventName(event);
          if (eventName === "failure_notification") {
            throw new Error(
              `StepFunction has failed: ${JSON.stringify(
                // These properties are always defined for the "failure_notification" event
                JSON.parse(event.stateEnteredEventDetails?.input as string)
                  .task_failure_details,
                null,
                2
              )}`
            );
          }
          if (eventName === exitEvent) {
            if (eventName === "fineos_eligibility_feed_export") {
              console.log(
                chalk.green(
                  `${this.environment.toUpperCase()} load_employers_to_fineos successful!`
                )
              );
            } else {
              console.log(`${exitEvent} event started`);
            }
            return true;
          }
        }
        await delay(1000 * 15);
        log = !log;
        throw new Error(
          "Unable to verify completion of 'load_employers_to_fineos'"
        );
      },
      // Maximum of 20 minutes waiting for task to complete
      { retries: 60, maxTimeout: 100, minTimeout: 0 }
    );
  }
}
