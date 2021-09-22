import { EventEmitter } from "events";
import ArtilleryPFMLInteractor from "./ArtilleryInteractor";
import { createLogger, format, Logger, transports } from "winston";
import { getDataFromClaim } from "./util";
import { hostname } from "os";

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

function fn(cb: ProcessorCB) {
  return async function (
    context: ArtilleryContext,
    ee: EventEmitter,
    done: DoneCB
  ) {
    const child = logger.child({ uid: context._uid });
    try {
      ee.emit("request");
      const startedAt = process.hrtime.bigint();
      await cb(context, ee, child);
      const endedAt = process.hrtime.bigint();
      const deltaMs = Math.round(Number(endedAt - startedAt) / 1000000);
      ee.emit("response", deltaMs, 200, context._uid);
      done();
    } catch (e) {
      child.error(e.message);
      done(e);
    }
  };
}

type DoneCB = (err?: Error) => void;

logger.info(`DEBUG IS SET TO: ${process.env.E2E_DEBUG}`);
export const submitAndAdjudicate = fn(
  async (_context: ArtilleryContext, ee: EventEmitter, logger: Logger) => {
    const claim = await interactor.generateClaim(ee, "LSTBHAP1", logger);
    logger.info("Claim data:", getDataFromClaim(claim));
    const subClaimRes = await interactor.submitClaim(claim, ee, logger);
    logger.info("Submission data", subClaimRes);
    await interactor.postProcessClaim(claim, subClaimRes, ee, logger);
  }
);
