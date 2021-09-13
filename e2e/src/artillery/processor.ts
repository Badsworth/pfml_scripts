import { EventEmitter } from "events";
import ArtilleryPFMLInteractor from "./ArtilleryInteractor";
import Reporter from "./Reporter";
import { createLogger, format, transports } from "winston";
import { getDataFromClaim, UsefulClaimData } from "./util";

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
});

const interactor = new ArtilleryPFMLInteractor();
const reporter = new Reporter();
reporter.listen();

let claim: GeneratedClaim;
let subClaimRes: ApplicationSubmissionResponse;
let processClaim: UsefulClaimData;

function fn(cb: (context: [k: string], ee: EventEmitter) => Promise<void>) {
  return async function (context: [k: string], ee: EventEmitter, done: DoneCB) {
    try {
      await cb(context, ee);
      done();
    } catch (e) {
      console.error(e);
      done(e);
    }
  };
}

type DoneCB = (err?: Error) => void;

logger.info(`DEBUG IS SET TO: ${process.env.E2E_DEBUG}`);
export const submitAndAdjudicate = fn(
  async (_context: [k: string], ee: EventEmitter) => {
    try {
      claim = await interactor.generateClaim(ee, "LSTBHAP1", logger);
      const childLoggerClaimInfo = logger.child(getDataFromClaim(claim));
      subClaimRes = await interactor.submitClaim(
        claim,
        ee,
        childLoggerClaimInfo
      );
      const childLoggerSubmission = logger.child({
        ...getDataFromClaim(claim),
        ...subClaimRes,
      });
      processClaim = await interactor.postProcessClaim(
        claim,
        subClaimRes,
        ee,
        childLoggerSubmission
      );
    } catch (e) {
      logger.error(e);
      throw new Error("LST Failure");
    } finally {
      logger.info("LST Results (each method)", {
        generateClaim: !claim ? "Failure" : "Success",
        submitClaim: !subClaimRes ? "Failure" : "Success",
        postProcessClaim: !processClaim ? "Failure" : "Success",
      });
    }
  }
);
