import { describe, beforeAll, test, expect } from "@jest/globals";
import { SimulationGenerator } from "../../src/simulation/simulate";
import type { Employer } from "../../src/simulation/types";
import * as integrationScenarios from "../../src/simulation/scenarios/integrationScenarios";
import { getEmployee } from "../../cypress/plugins";
import PortalSubmitter from "../../src/simulation/PortalSubmitter";
import AuthenticationManager from "../../src/simulation/AuthenticationManager";
import { CognitoUserPool } from "amazon-cognito-identity-js";
import config from "../../src/config";
import {
  DocumentUploadRequest,
  postApplicationsByApplication_idDocuments,
  RequestOptions,
} from "../../src/api";
import fs from "fs";

const scenarioFunctions: Record<string, SimulationGenerator> = {
  ...integrationScenarios,
};

let pmflApiOptions: RequestOptions;
let application_id: string;

describe("API Documents Test of various file sizes", () => {
  beforeAll(async () => {
    const userPool = new CognitoUserPool({
      ClientId: config("COGNITO_CLIENTID"),
      UserPoolId: config("COGNITO_POOL"),
    });

    const authenticator = new AuthenticationManager(
      userPool,
      config("API_BASEURL")
    );

    const defaultClaimantCredentials = {
      username: config("PORTAL_USERNAME"),
      password: config("PORTAL_PASSWORD"),
    };

    const session = await authenticator.authenticate(
      defaultClaimantCredentials.username,
      defaultClaimantCredentials.password
    );

    pmflApiOptions = {
      baseUrl: config("API_BASEURL"),
      headers: {
        Authorization: `Bearer ${session.getAccessToken().getJwtToken()}`,
        "User-Agent": "PFML Cypress Testing",
      },
    };

    const submitter = new PortalSubmitter(authenticator, config("API_BASEURL"));

    const employee = await getEmployee("financially eligible");

    const opts = {
      documentDirectory: "/tmp",
      employeeFactory: () => employee,
      employerFactory: () => ({ fein: employee.employer_fein } as Employer),
      shortClaim: true,
    };

    const claim = await scenarioFunctions["DHAP1"](opts);

    application_id = await submitter.submitPartOne(
      defaultClaimantCredentials,
      claim.claim
    );
  }, 60000);

  test("Should recieve an error when submitting a document of size 26MB", async () => {
    const document: DocumentUploadRequest = {
      document_type: "State managed Paid Leave Confirmation",
      description: "Large PDF Upload 26MB",
      file: fs.createReadStream("./cypress/fixtures/large.pdf"),
      name: `large.pdf`,
    };

    // Add large document to claim
    const docRes = await postApplicationsByApplication_idDocuments(
      { application_id: application_id },
      document,
      pmflApiOptions
    ).catch((err) => {
      return err;
    });

    expect(docRes.status).toBe(413);
    expect(docRes.statusText).toBe("Request Entity Too Large");
  }, 60000);

  test("Should submit Document less than 5MB successfully", async () => {
    const document: DocumentUploadRequest = {
      document_type: "State managed Paid Leave Confirmation",
      description: "Small PDF - Less than 1MB",
      file: fs.createReadStream("./cypress/fixtures/FOSTER.pdf"),
      name: `FOSTER.pdf`,
    };

    // Add small document to claim
    const docRes = await postApplicationsByApplication_idDocuments(
      { application_id: application_id },
      document,
      pmflApiOptions
    );

    expect(docRes.status).toBe(200);
    expect(docRes.data.message).toBe("Successfully uploaded document");
  }, 60000);
});
