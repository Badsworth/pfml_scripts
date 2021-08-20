import EmployeePool from "../generation/Employee";
import AuthenticationManager from "../submission/AuthenticationManager";
import { getAuthManager } from "../util/common";
import { EventEmitter } from "events";
import * as scenarios from "../scenarios/lst";
import { ClaimGenerator, GeneratedClaim } from "../generation/Claim";
import { Credentials } from "../types";
import faker from "faker";
import { ApplicationResponse } from "../api";
import { approveClaim } from "../submission/PostSubmit";
import { Fineos } from "../submission/fineos.pages";
import config from "../../src/config";
import getArtillerySubmitter from "./ArtilleryClaimSubmitter";

export type ArtilleryContext = {
  claimantCredentials?: Credentials;
  claim?: GeneratedClaim;
  submission?: ApplicationResponse;
  [k: string]: unknown;
};

/**
 * This is the interaction layer.
 *
 * Each public method on this interactor is a step that can be performed in a load test.
 */
export default class ArtilleryPFMLInteractor {
  private employeePool?: EmployeePool;
  private authManager: AuthenticationManager;

  constructor() {
    this.authManager = getAuthManager();
  }

  private async employees(): Promise<EmployeePool> {
    if (!this.employeePool) {
      this.employeePool = await EmployeePool.load(config("EMPLOYEES_FILE"));
    }
    return this.employeePool;
  }
  registerClaimant(context: ArtilleryContext, ee: EventEmitter): Promise<void> {
    return timed(ee, "registerClaimant", async () => {
      const credentials = generateCredentials();
      await this.authManager.registerClaimant(
        credentials.username,
        credentials.password
      );
      context.claimantCredentials = credentials;
    });
  }
  generateClaim(
    context: ArtilleryContext,
    ee: EventEmitter,
    scenario: string
  ): Promise<void> {
    return timed(ee, "generateClaim", async () => {
      const pool = await this.employees();
      if (!(scenario in scenarios)) {
        throw new Error("Invalid or missing scenario");
      }
      const scenarioObj = scenarios[scenario as keyof typeof scenarios];
      context.claim = ClaimGenerator.generate(
        pool,
        scenarioObj.employee,
        scenarioObj.claim
      );
    });
  }

  submitClaim(context: ArtilleryContext, ee: EventEmitter): Promise<void> {
    return timed(ee, "submitClaim", async () => {
      const claim = context.claim as GeneratedClaim | undefined;
      if (!claim) {
        throw new Error("No claim given");
      }
      if (!claim.claim.employer_fein) {
        throw new Error("No FEIN given on claim");
      }
      const claimantCredentials =
        (context.claimantCredentials as Credentials | undefined) ??
        getClaimantCredentials();
      const leaveAdminCredentials = getLeaveAdminCredentials(
        claim.claim.employer_fein
      );
      const submitter = getArtillerySubmitter();
      context.submission = await submitter.lstSubmit(
        claim,
        claimantCredentials,
        leaveAdminCredentials
      );
    });
  }

  postProcessClaim(context: ArtilleryContext, ee: EventEmitter): Promise<void> {
    if (!context.submission?.fineos_absence_id || !context.claim) {
      throw new Error(
        `Cannot post-process because no claim was successfully submitted`
      );
    }
    return timed(ee, "postProcessClaim", async () => {
      await Fineos.withBrowser(
        async (page) =>
          await approveClaim(
            page,
            context.claim as GeneratedClaim,
            context.submission?.fineos_absence_id as string
          ),
        false
      );
      console.log("Claim post-processed");
    });
  }
}

async function timed(ee: EventEmitter, name: string, cb: () => Promise<void>) {
  const startedAt = process.hrtime();
  ee.emit("counter", `${name}.count.started`, 1);
  await cb();
  const endedAt = process.hrtime(startedAt);
  const delta = endedAt[0] * 1e9 + endedAt[1];
  // Convert to milliseconds.
  ee.emit("histogram", `${name}.time`, delta / 1e6);
  ee.emit("counter", `${name}.count.completed`, 1);
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
