import config from "./config";
import * as path from "path";
import { S3Client, PutObjectCommandInput } from "@aws-sdk/client-s3";
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
import { Environment } from "types";

type SfnEventName =
  | " dor_import "
  | "load_employers_to_fineos"
  | "fineos_eligibility_feed_export"
  | "success";

export default class InfraClient {
  private s3Client: S3Client;
  private sfnClient: SFNClient;
  private env: Environment;

  constructor(environment: Environment) {
    this.s3Client = new S3Client({
      region: "us-east-1",
    });
    this.sfnClient = new SFNClient({
      region: "us-east-1",
    });
    this.env = environment;
  }

  private getS3UploadParams(filename: string): PutObjectCommandInput {
    const formattedURI = config("DOR_IMPORT_URI").replace(
      "TARGET_ENV",
      this.env
    );
    const { host: bucket, pathname: key, protocol } = new URL(formattedURI);
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
          console.log(`${this.env.toUpperCase()} - Completed upload of ${file}`)
        );
    });
    await Promise.all(uploads);
  }

  // "exitEvent" determines at which step we want to stop monitoring etl progress
  // i.e if we want to register leave admins, we only need to monitor progress up until "fineos_eligibilty_feed_export" begins
  async runDorEtl(
    exitEvent: SfnEventName = "fineos_eligibility_feed_export"
  ): Promise<boolean | void> {
    const formattedEtlArn = config("DOR_ETL_ARN").replace(
      "TARGET_ENV",
      this.env
    );
    const { executionArn } = await this.sfnClient.send(
      new StartExecutionCommand({
        stateMachineArn: formattedEtlArn,
      })
    );
    console.log(
      `${chalk.blue(
        this.env.toUpperCase() + " etl execution started"
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
              this.env.toUpperCase()
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
                  `${this.env.toUpperCase()} load_employers_to_fineos successful!`
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
