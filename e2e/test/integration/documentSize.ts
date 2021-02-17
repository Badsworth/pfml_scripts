import { describe, beforeAll, test, expect } from "@jest/globals";
import { SimulationGenerator } from "../../src/simulation/simulate";
import type { Employer } from "../../src/simulation/types";
import * as integrationScenarios from "../../src/simulation/scenarios/integrationScenarios";
import { getEmployee } from "../../cypress/plugins";
import PortalSubmitter from "../../src/simulation/PortalSubmitter";
import AuthenticationManager from "../../src/simulation/AuthenticationManager";
import { CognitoUserPool } from "amazon-cognito-identity-js";
import config from "../../src/config";
import TestMailVerificationFetcher from "../../cypress/plugins/TestMailVerificationFetcher";
import { Credentials } from "../../src/types";
import { DocumentUploadRequest } from "api";
import fs from "fs";

const scenarioFunctions: Record<string, SimulationGenerator> = {
  ...integrationScenarios,
};

let userPool: CognitoUserPool;
let verificationFetcher: TestMailVerificationFetcher;
let authenticator: AuthenticationManager;
let defaultClaimantCredentials: Credentials;
let submitter: PortalSubmitter;

describe("API Documents Test of various file sizes", () => {
  beforeAll(() => {
    userPool = new CognitoUserPool({
      ClientId: config("COGNITO_CLIENTID"),
      UserPoolId: config("COGNITO_POOL"),
    });

    verificationFetcher = new TestMailVerificationFetcher(
      config("TESTMAIL_APIKEY"),
      config("TESTMAIL_NAMESPACE")
    );

    authenticator = new AuthenticationManager(
      userPool,
      config("API_BASEURL"),
      verificationFetcher
    );

    defaultClaimantCredentials = {
      username: config("PORTAL_USERNAME"),
      password: config("PORTAL_PASSWORD"),
    };

    submitter = new PortalSubmitter(authenticator, config("API_BASEURL"));
  });

  test("Should recieve an error when submitting a document of size 20MB", async () => {
    const employee = await getEmployee("financially eligible");

    const opts = {
      documentDirectory: "/tmp",
      employeeFactory: () => employee,
      employerFactory: () => ({ fein: employee.employer_fein } as Employer),
      shortClaim: true,
    };

    const claim = await scenarioFunctions["DHAP1"](opts);

    // Submit Claim w/o Document
    const appRes = await submitter
      .submit(
        defaultClaimantCredentials,
        claim.claim,
        [],
        claim.paymentPreference
      )
      .catch((err) => {
        console.error("Failed to submit claim:", err);
        throw new Error(err);
      });

    // Add large document to claim
    const document: DocumentUploadRequest[] = [
      {
        document_type: "State managed Paid Leave Confirmation",
        description: "Large PDF Upload 30MB",
        file: fs.createReadStream("./cypress/fixtures/large.pdf"),
        name: `large.pdf`,
      },
    ];

    const docRes = await submitter
      .submitDocumentOnly(
        defaultClaimantCredentials,
        appRes.application_id as string,
        appRes.fineos_absence_id as string,
        document
      )
      .catch((err) => {
        return err;
      });

    expect(docRes.status).toBe(413);
    expect(docRes.statusText).toBe("Request Entity Too Large");
  }, 60000);
});
