/// <reference types="cypress" />
// ***********************************************************
// This example plugins/index.js can be used to load plugins
//
// You can change the location of this file or turn off loading
// the plugins file with the 'pluginsFile' configuration option.
//
// You can read more here:
// https://on.cypress.io/plugins-guide
// ***********************************************************

import config from "../../src/config";
import faker from "faker";
import path from "path";
import webpackPreprocessor from "@cypress/webpack-preprocessor";
import { CypressStepThis } from "../../src/types";
import TestMailVerificationFetcher from "./TestMailVerificationFetcher";
import PortalSubmitter from "../../src/simulation/PortalSubmitter";
import {
  SimulationClaim,
  Employer,
  EmployeeRecord,
} from "../../src/simulation/types";
import { Credentials } from "../../src/types";
import { SimulationGenerator } from "../../src/simulation/simulate";
import { ApplicationResponse, DocumentUploadRequest } from "../../src/api";
import { makeDocUploadBody } from "../../src/simulation/SimulationRunner";
import { fromClaimData } from "../../src/simulation/EmployeeFactory";
import * as pilot3 from "../../src/simulation/scenarios/pilot3";
import * as pilot4 from "../../src/simulation/scenarios/pilot4";
import * as integrationScenarios from "../../src/simulation/scenarios/integrationScenarios";

import fs from "fs";
import pdf from "pdf-parse";
import { Result } from "pdf-parse";
import TestMailClient, { Email, GetEmailsOpts } from "./TestMailClient";
import AuthenticationManager from "../../src/simulation/AuthenticationManager";
import { CognitoUserPool } from "amazon-cognito-identity-js";
import DocumentWaiter from "./DocumentWaiter";

const scenarioFunctions: Record<string, SimulationGenerator> = {
  ...pilot3,
  ...pilot4,
  ...integrationScenarios,
};

// This function is called when a project is opened or re-opened (e.g. due to
// the project's config changing)
/**
 * @type {Cypress.PluginConfig}
 */
export default function (on: Cypress.PluginEvents): Cypress.ConfigOptions {
  const userPool = new CognitoUserPool({
    ClientId: config("COGNITO_CLIENTID"),
    UserPoolId: config("COGNITO_POOL"),
  });
  const verificationFetcher = new TestMailVerificationFetcher(
    config("TESTMAIL_APIKEY"),
    config("TESTMAIL_NAMESPACE")
  );
  const authenticator = new AuthenticationManager(
    userPool,
    config("API_BASEURL"),
    verificationFetcher
  );
  const submitter = new PortalSubmitter(authenticator, config("API_BASEURL"));
  const defaultClaimantCredentials = {
    username: config("PORTAL_USERNAME"),
    password: config("PORTAL_PASSWORD"),
  };
  const documentWaiter = new DocumentWaiter(
    config("API_BASEURL"),
    authenticator
  );

  // Declare tasks here.
  on("task", {
    getAuthVerification: (toAddress: string) => {
      return verificationFetcher.getVerificationCodeForUser(toAddress);
    },
    getEmails(opts: GetEmailsOpts): Promise<Email[]> {
      const client = new TestMailClient(
        config("TESTMAIL_APIKEY"),
        config("TESTMAIL_NAMESPACE")
      );
      return client.getEmails(opts);
    },
    async generateCredentials(
      isEmployer: boolean
    ): Promise<CypressStepThis["credentials"]> {
      const namespace = config("TESTMAIL_NAMESPACE");
      const tag = faker.random.alphaNumeric(8);
      const credentials: Credentials = {
        username: `${namespace}.${tag}@inbox.testmail.app`,
        password: generatePassword(),
      };
      if (isEmployer) {
        await getEmployee("financially eligible").then((employee) => {
          credentials.fein = employee.employer_fein;
        });
      }
      return credentials;
    },

    async registerClaimant(options: Credentials): Promise<true> {
      await authenticator.registerClaimant(options.username, options.password);
      return true;
    },

    async registerLeaveAdmin(
      options: Credentials & { fein: string }
    ): Promise<true> {
      await authenticator.registerLeaveAdmin(
        options.username,
        options.password,
        options.fein
      );
      return true;
    },

    async submitClaimToAPI(
      application: SimulationClaim & {
        credentials?: Credentials;
        employerCredentials?: Credentials;
      }
    ): Promise<ApplicationResponse> {
      if (!application.claim) throw new Error("Application missing!");
      if (!application.documents.length) throw new Error("Documents missing!");
      const {
        claim,
        documents,
        credentials,
        paymentPreference,
        employerResponse,
        employerCredentials,
      } = application;
      const newDocuments: DocumentUploadRequest[] = documents.map(
        makeDocUploadBody("/tmp", "Direct API Upload")
      );
      return submitter
        .submit(
          credentials ?? defaultClaimantCredentials,
          claim,
          newDocuments,
          paymentPreference,
          employerCredentials,
          employerResponse
        )
        .catch((err) => {
          console.error("Failed to submit claim:", err.data);
          throw new Error(err);
        });
    },

    waitForClaimDocuments: documentWaiter.waitForClaimDocuments.bind(
      documentWaiter
    ),

    async generateClaim({ claimType, employeeType }): Promise<SimulationClaim> {
      if (!(claimType in scenarioFunctions)) {
        throw new Error(`Invalid claim type: ${claimType}`);
      }

      // Get the employee record here (read JSON, map to identifier).
      const employee = await getEmployee(employeeType);

      const opts = {
        documentDirectory: "/tmp",
        employeeFactory: () => employee,
        // Dummy employer factory. Doesn't return full employer objects, just
        // the FEIN. In this case, we know we don't need other employer props.
        employerFactory: () => ({ fein: employee.employer_fein } as Employer),
        shortClaim: true,
      };

      return scenarioFunctions[claimType](opts);
    },
    async noticeReader(noticeType: string): Promise<Result> {
      const PDFdataBuffer = fs.readFileSync(
        `./cypress/downloads-notices/${noticeType} Notice.pdf`
      );

      return pdf(PDFdataBuffer) as Promise<Result>;
    },
    deleteNoticePDF(): string {
      try {
        fs.unlinkSync("./cypress/downloads-notices/Denial Notice.pdf");
      } catch (err) {
        console.error(err);
      }
      return "Deleted Succesfully";
    },
  });

  const options = {
    webpackOptions: require("../../webpack.config.ts"),
  };
  on("file:preprocessor", webpackPreprocessor(options));

  on("before:browser:launch", (browser, options) => {
    const downloadDirectory = path.join(__dirname, "..", "downloads-notices");

    if (browser.family === "chromium" && browser.name !== "electron") {
      options.preferences.default["download"] = {
        default_directory: downloadDirectory,
      };

      return options;
    }
  });

  return {
    baseUrl: config("PORTAL_BASEURL"),
    env: {
      // Map through config => environment variables that we will need to use in our tests.
      E2E_FINEOS_BASEURL: config("FINEOS_BASEURL"),
      E2E_FINEOS_USERNAME: config("FINEOS_USERNAME"),
      E2E_FINEOS_PASSWORD: config("FINEOS_PASSWORD"),
      E2E_PORTAL_BASEURL: config("PORTAL_BASEURL"),
      E2E_PORTAL_USERNAME: config("PORTAL_USERNAME"),
      E2E_PORTAL_PASSWORD: config("PORTAL_PASSWORD"),
      E2E_EMPLOYER_PORTAL_PASSWORD: config("EMPLOYER_PORTAL_PASSWORD"),
      E2E_ENVIRONMENT: config("ENVIRONMENT"),
    },
  };
}

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

/**
 * Retrieves an existing employee from the employee file for the current environment.
 */
export async function getEmployee(
  employeeType: string
): Promise<EmployeeRecord> {
  const claims = await fs.promises
    .readFile(config("EMPLOYEES_FILE"), "utf-8")
    .then(JSON.parse);
  const factory = fromClaimData(claims);
  // @todo: We should probably just update this to match the employee factory wage spec
  // - it's just out of scope for what I'm doing right now.
  switch (employeeType) {
    case "financially eligible":
      return factory("eligible");
    case "financially ineligible":
      return factory("ineligible");
    default:
      throw new Error(`Unknown employee type: ${employeeType}`);
  }
}
