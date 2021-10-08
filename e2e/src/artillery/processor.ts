import { EventEmitter } from "events";
import ArtilleryPFMLInteractor from "./ArtilleryInteractor";
import { createLogger, format, Logger, transports } from "winston";
import { getDataFromClaim } from "./util";
import { hostname } from "os";
import {
  SQSClient,
  SendMessageCommand,
  ReceiveMessageCommand,
  DeleteMessageCommand,
} from "@aws-sdk/client-sqs";

const { combine, printf, json, colorize } = format;

const localFormat = printf((info) => {
  const { level, message, ..._info } = info;
  if (Object.keys(_info).length === 0) {
    return `${info.level}: ${info.message}`;
  } else {
    return `${info.level}: ${info.message}\n${JSON.stringify(
      { ..._info },
      null,
      2
    )}`;
  }
});
const localLogFormat = combine(colorize(), localFormat);

const logger = createLogger({
  level: process.env.E2E_DEBUG === "true" ? "debug" : "info",
  format: process.env.IS_ECS === "true" ? json() : localLogFormat,
  transports: new transports.Console(),
  defaultMeta: {
    run_id: process.env.LST_RUN_ID,
    instance_id: process.env.LST_INSTANCE_ID ?? hostname(),
    type: "log",
  },
});

type ArtilleryContext = {
  [k: string]: unknown;
  _uid: number;
};
const interactor = new ArtilleryPFMLInteractor();

type ProcessorCB = (
  context: ArtilleryContext,
  ee: EventEmitter,
  logger: Logger
) => Promise<void>;

/**
 * Wraps an async function in a way that allows it to work with artillery, and adds logging.
 */
function wrap(fn: ProcessorCB) {
  return async (context: ArtilleryContext, ee: EventEmitter, done: DoneCB) => {
    const child = logger.child({ uid: context._uid });
    try {
      await fn(context, ee, child);
      done();
    } catch (e) {
      child.error(e.message);
      done(e);
    }
  };
}

/**
 * Wraps a top level callback in a timer that invokes the request/response events.
 */
async function timeRequest<R extends unknown>(
  context: ArtilleryContext,
  ee: EventEmitter,
  fn: () => Promise<R>
): Promise<R> {
  const startedAt = process.hrtime.bigint();
  ee.emit("request");
  const ret = await fn();
  const endedAt = process.hrtime.bigint();
  // Convert to milliseconds.
  const deltaMs = Math.round(Number(endedAt - startedAt) / 1000000);
  ee.emit("response", deltaMs, 200, context._uid);
  return ret;
}

type DoneCB = (err?: Error) => void;

const sqs = new SQSClient({ region: "us-east-1" });

/**
 * Exported handler for a simple submission immediately followed by adjudication.
 */
export const submitAndAdjudicate = wrap(
  async (_context: ArtilleryContext, ee: EventEmitter, logger: Logger) => {
    const claim = await interactor.generateClaim(
      ee,
      "LSTBHAP1",
      logger.child({ stage: "generate" })
    );
    logger.info("Claim data:", getDataFromClaim(claim));
    const subClaimRes = await interactor.submitClaim(
      claim,
      ee,
      logger.child({ stage: "submit" })
    );
    logger.info("Submission data", subClaimRes);
    await interactor.postProcessClaim(
      claim,
      subClaimRes,
      ee,
      logger.child({ stage: "postProcess" })
    );
  }
);

/**
 * Exported handler for submitting (only), followed by pushing the data to SQS.
 */
export const submitAndStore = wrap(
  async (context: ArtilleryContext, ee: EventEmitter, logger: Logger) => {
    const body = await timeRequest(context, ee, async () => {
      const claim = await interactor.generateClaim(ee, "LSTBHAP1", logger);
      logger = logger.child({ claim_id: claim.id });
      logger.info("Claim data:", getDataFromClaim(claim));
      const submission = await interactor.submitClaim(claim, ee, logger);
      return { claim, submission };
    });

    // Store the claim and response for later processing. We do this outside the request/response
    // timing so it does not count toward our metrics.
    await sqs.send(
      new SendMessageCommand({
        QueueUrl: process.env.CLAIMS_SQS_QUEUE,
        MessageBody: JSON.stringify(body),
      })
    );
  }
);

/**
 * Exported handler for fetching data from SQS, then doing adjudication.
 */
export const adjudicateStored = wrap(
  async (context: ArtilleryContext, ee: EventEmitter, logger: Logger) => {
    // Start by fetching a claim from SQS. We do this outside the request/response
    // timing so it does not count toward our metrics.
    const { Messages } = await sqs.send(
      new ReceiveMessageCommand({
        QueueUrl: process.env.CLAIMS_SQS_QUEUE, // Value set in container env by ArtilleryDeployer.
        MaxNumberOfMessages: 1,
        VisibilityTimeout: 60, // Give ourselves ~5 minutes to deal with this claim.
        WaitTimeSeconds: 10, // Not sure how long we want to hang out waiting for a message...
      })
    );
    if (!Messages || !Messages.length) {
      throw new NoClaimsRemainingError();
    }
    await sqs.send(
      new DeleteMessageCommand({
        QueueUrl: process.env.CLAIMS_SQS_QUEUE,
        ReceiptHandle: Messages[0].ReceiptHandle,
      })
    );
    const { submission, claim } = JSON.parse(Messages[0].Body ?? "");
    // Enrich the logger with data about the claim.
    const child = logger.child({
      claim_id: claim.id,
      fineos_claim_id: submission.fineos_absence_id,
      stage: "postProcess",
    });
    await timeRequest(context, ee, () => {
      return interactor.postProcessClaim(claim, submission, ee, child);
    });
  }
);

class NoClaimsRemainingError extends Error {
  code: number;
  constructor() {
    super("No claims are waiting for processing.");
    this.code = 4404;
  }
}
