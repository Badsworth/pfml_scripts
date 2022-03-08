import EmployeePool from "../generation/Employee";
import AuthenticationManager from "../submission/AuthenticationManager";
import { getAuthManager } from "../util/common";
import { EventEmitter } from "events";
import * as scenarios from "../scenarios/lst";
import { ClaimGenerator, GeneratedClaim } from "../generation/Claim";
import { Credentials, LSTScenarios } from "../types";
import faker from "faker";
import { approveClaim } from "../submission/PostSubmit";
import { Fineos } from "../submission/fineos.pages";
import config from "../../src/config";
import getArtillerySubmitter from "./ArtilleryClaimSubmitter";
import winston from "winston";
import { getDataFromClaim, UsefulClaimData } from "./util";
import shuffle from "../generation/shuffle";

type ArtilleryDocRanges = "small" | "med" | "large";
type DocRangesToScenarios = Record<ArtilleryDocRanges, LSTScenarios[]>;
const docRangesToScenariosMap: DocRangesToScenarios = {
  small: ["LSTOLB1_150KB", "LSTBHAP_1MB", "LSTCHAP1_2MB", "LSTOLB1_4MB"],
  med: ["LSTBHAP_5MB", "LSTCHAP1_6MB", "LSTOLB1_7MB"],
  large: ["LSTBHAP_8MB", "LSTCHAP1_9MB"],
};

/**
 * This is the interaction layer.
 *
 * Each public method on this interactor is a step that can be performed in a load test.
 */
export default class ArtilleryPFMLInteractor {
  private employeePool?: EmployeePool;
  private authManager: AuthenticationManager;
  readonly scenarios: LSTScenarios[];
  private scenarioWheel?: ArtilleryDocRanges[];
  constructor() {
    this.authManager = getAuthManager();
    this.scenarios = this.setScenarios();
  }

  private async employees(): Promise<EmployeePool> {
    if (!this.employeePool) {
      this.employeePool = await EmployeePool.load(config("LST_EMPLOYEES_FILE"));
    }
    return this.employeePool;
  }
  registerClaimant(
    ee: EventEmitter,
    logger: winston.Logger
  ): Promise<Credentials> {
    return timed(ee, logger, "registerClaimant", async () => {
      const credentials = generateCredentials();
      await this.authManager.registerClaimant(
        credentials.username,
        credentials.password
      );
      return credentials;
    });
  }
  generateClaim(
    ee: EventEmitter,
    scenario: string,
    logger: winston.Logger
  ): Promise<GeneratedClaim> {
    return timed(ee, logger, "generateClaim", async () => {
      const pool = await this.employees();
      if (!(scenario in scenarios)) {
        throw new Error("Invalid or missing scenario");
      }
      const scenarioObj = scenarios[scenario as keyof typeof scenarios];
      const claim = ClaimGenerator.generate(
        pool,
        scenarioObj.employee,
        scenarioObj.claim
      );
      logger.debug("Fully generated claim", claim.claim);
      return claim;
    });
  }

  submitClaim(
    claim: GeneratedClaim,
    ee: EventEmitter,
    logger: winston.Logger,
    creds?: Credentials
  ): Promise<ApplicationSubmissionResponse> {
    return timed(ee, logger, "submitClaim", async () => {
      const claimantCredentials = creds ?? getClaimantCredentials();
      const leaveAdminCredentials = getLeaveAdminCredentials(
        claim.claim.employer_fein as string
      );
      const submitter = getArtillerySubmitter();
      const submission = await submitter.lstSubmit(
        claim,
        claimantCredentials,
        leaveAdminCredentials,
        logger
      );
      return submission;
    });
  }

  postProcessClaim(
    claim: GeneratedClaim,
    submission: ApplicationSubmissionResponse,
    ee: EventEmitter,
    logger: winston.Logger
  ): Promise<UsefulClaimData> {
    return timed(ee, logger, "postProcessClaim", async () => {
      logger.debug("Entering Fineos withBrowser");
      await Fineos.withBrowser(
        async (page) =>
          await approveClaim(
            page,
            claim,
            submission?.fineos_absence_id,
            logger
          ),
        { debug: false }
      );
      return getDataFromClaim(claim);
    });
  }


  searchClaimant(
    type: string,
    ee: EventEmitter,
    logger: winston.Logger
  ){
    return timed(ee, logger, "generateClaim", async () => {
      const pool = await this.employees();
      if (!(type in ['first', 'last'])) {
        throw new Error("Invalid or missing type");
      }
      const employee = pool.shuffle().slice(0,1).getFirst()
      logger.debug("Search For Name", employee.first_name);

      const submitter = getArtillerySubmitter();
      const submission = await submitter.lstSearch(
        employee.first_name,
        logger
      );
      return submission;
    });
  }


  private setScenarios(): LSTScenarios[] {
    const range = config("LST_FILE_RANGE");
    switch (range) {
      case "small":
        this.scenarioWheel = ["small"];
        return docRangesToScenariosMap.small;
      case "large":
        this.scenarioWheel = [
          ...Array(70).fill("med"),
          ...Array(30).fill("large"),
        ];
        return docRangesToScenariosMap.large;
      // default to full range of scenarios
      default:
        this.scenarioWheel = [
          ...Array(70).fill("small"),
          ...Array(20).fill("med"),
          ...Array(10).fill("large"),
        ];
        return Object.keys(docRangesToScenariosMap).reduce<LSTScenarios[]>(
          (acc, curr) => {
            const files = docRangesToScenariosMap[curr as ArtilleryDocRanges];
            acc.push(...files);
            return acc;
          },
          []
        );
    }
  }

  getScenario(): LSTScenarios {
    if (!this.scenarioWheel)
      throw Error("scenarioWheel undefined, unable to get random scenario");
    const range =
      this.scenarioWheel[Math.floor(Math.random() * this.scenarioWheel.length)];
    const possibleScenarios = docRangesToScenariosMap[range];
    return shuffle(possibleScenarios)[0];
  }
}

async function timed<T>(
  ee: EventEmitter,
  logger: winston.Logger,
  name: string,
  cb: () => Promise<T>
): Promise<T> {
  logger.info(`Starting ${name}`);
  const startedAt = process.hrtime();
  ee.emit("counter", `${name}.count.started`, 1);
  try {
    const res = await cb();
    ee.emit("counter", `${name}.count.completed`, 1);
    logger.info(`Completed ${name}`);
    return res;
  } catch (e) {
    ee.emit("counter", `${name}.count.error`, 1);
    logger.info(`Completed ${name} with error.`);
    throw e;
  } finally {
    const endedAt = process.hrtime(startedAt);
    const delta = endedAt[0] * 1e9 + endedAt[1];
    // Convert to milliseconds.
    ee.emit("histogram", `${name}.time`, delta / 1e6);
  }
}

/**
 * Generates a random set of credentials.
 */
function generateCredentials(): Credentials {
  const namespace = config("TESTMAIL_NAMESPACE");
  const tag = faker.random.alphaNumeric(8);
  return {
    username: `${namespace}.${tag}@inbox.testmail.app`,
    password: generatePassword(),
  };
}

/**
 * Generates a random password for a Cognito account.
 */
function generatePassword(): string {
  // Password = {uppercase}{lowercase}{random*10){number}{symbol}
  return (
    faker.internet.password(1, false, /[A-Z]/) +
    faker.internet.password(1, false, /[a-z]/) +
    faker.internet.password(10) +
    faker.random.number(999) +
    faker.random.arrayElement(["@#$%^&*"])
  );
}

function getLeaveAdminCredentials(fein: string): Credentials {
  const password = config("EMPLOYER_PORTAL_PASSWORD");
  if (!password) {
    throw new Error(
      `You must set the E2E_EMPLOYER_PORTAL_PASSWORD environment variable.`
    );
  }
  return {
    username: `gqzap.employer.${fein.replace("-", "")}@inbox.testmail.app`,
    password,
  };
}

function getClaimantCredentials(): Credentials {
  return {
    username: config("PORTAL_USERNAME"),
    password: config("PORTAL_PASSWORD"),
  };
}
