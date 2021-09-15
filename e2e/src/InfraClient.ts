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

export default class InfraClient {
  //
  private s3Client: S3Client;
  private sfnClient: SFNClient;

  constructor() {
    this.s3Client = new S3Client({
      region: "us-east-1",
    });
    this.sfnClient = new SFNClient({
      region: "us-east-1",
    });
  }

  private getS3UploadParams(filename: string): PutObjectCommandInput {
    const target_env = config("ENVIRONMENT");
    if (target_env === "local")
      throw Error("Cannot upload when targeting 'local' environment");
    const formattedURI = config("DOR_IMPORT_URI").replace(
      "TARGET_ENV",
      target_env
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
        .then(() => console.log(`Completed upload of ${file}`));
    });
    await Promise.all(uploads);
  }

  async runElibible(): Promise<boolean | void> {
    const target_env = config("ENVIRONMENT");
    if (target_env === "local")
      throw Error("Cannot upload when targeting 'local' environment");
    const formattedEtlArn = config("DOR_ETL_ARN").replace(
      "TARGET_ENV",
      target_env
    );
    const { executionArn } = await this.sfnClient.send(
      new StartExecutionCommand({
        stateMachineArn: formattedEtlArn,
      })
    );
    console.log(
      `${chalk.blue(
        "etl execution started"
      )} - waiting on 'load_employers_to_fineos' task completion`
    );
    // wait 2.5 minutes before checking task completion
    await delay(1000 * 60 * 2.5);
    // reduces amount of repeat logs
    let log = true;
    return pRetry(
      async () => {
        log &&
          console.log(
            "Checking for 'load_employers_to_fineos' task completion"
          );
        const logs = await this.sfnClient.send(
          new GetExecutionHistoryCommand({
            executionArn,
          })
        );
        if (!logs.events) return;
        const getStartedEventName = (event: HistoryEvent) => {
          if (event.type === "TaskStateEntered") {
            return event.stateEnteredEventDetails?.name;
          }
        };
        for (const event of logs.events) {
          if (getStartedEventName(event) === "fineos_eligibility_feed_export") {
            console.log(chalk.green("load_employers_to_fineos successful!"));
            return true;
          }
        }
        await delay(1000 * 15);
        log = !log;
        throw new Error(
          "Unable to verify completion of 'load_employers_to_fineos'"
        );
      },
      { retries: 48, maxTimeout: 100, minTimeout: 0 }
    );
  }
}
