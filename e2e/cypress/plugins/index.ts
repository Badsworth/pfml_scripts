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
import webpackPreprocessor from "@cypress/webpack-preprocessor";
import { CypressStepThis } from "../../src/types";
import TestMailVerificationFetcher from "./TestMailVerificationFetcher";
import TestMailNotificationFetcher from "./TestMailNotificationFetcher";
import PortalSubmitter from "../../src/simulation/PortalSubmitter";
import {
  SimulationClaim,
  Employer,
  EmployeeRecord,
} from "../../src/simulation/types";
import { Credentials, notificationRequest } from "../../src/types";
import {
  SimulationGenerator,
  generateLeaveDates,
} from "../../src/simulation/simulate";
import { ApplicationResponse, DocumentUploadRequest } from "../../src/api";
import { makeDocUploadBody } from "../../src/simulation/SimulationRunner";
import { fromClaimsFactory } from "../../src/simulation/EmployeeFactory";
import * as pilot3 from "../../src/simulation/scenarios/pilot3";
import * as pilot4 from "../../src/simulation/scenarios/pilot4";
import * as integrationScenarios from "../../src/simulation/scenarios/integrationScenarios";

import fs from "fs";

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
  // Declare tasks here.
  on("task", {
    getAuthVerification: (toAddress: string) => {
      const client = new TestMailVerificationFetcher(
        config("TESTMAIL_APIKEY"),
        config("TESTMAIL_NAMESPACE")
      );
      return client.getVerificationCodeForUser(toAddress);
    },
    getNotification: (notificationRequestData: notificationRequest) => {
      const client = new TestMailNotificationFetcher(
        config("TESTMAIL_APIKEY"),
        config("TESTMAIL_NAMESPACE")
      );
      return client.getNotificationContent(notificationRequestData);
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

    async submitClaimToAPI(
      application: SimulationClaim
    ): Promise<ApplicationResponse> {
      if (!application.claim) throw new Error("Application missing!");
      if (!application.documents.length) throw new Error("Documents missing!");
      const { claim, documents } = application;
      const newDocuments: DocumentUploadRequest[] = documents.map(
        makeDocUploadBody("/tmp", "Direct API Upload")
      );

      return new PortalSubmitter({
        ClientId: config("COGNITO_CLIENTID"),
        UserPoolId: config("COGNITO_POOL"),
        Username: config("PORTAL_USERNAME"),
        Password: config("PORTAL_PASSWORD"),
        ApiBaseUrl: config("API_BASEURL"),
      })

        .submit(claim, newDocuments)
        .catch((err) => {
          console.error("Failed to submit claim:", err.data);
          throw new Error(err);
        });
    },
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
    async createContinuousLeaveDates(): Promise<Date[]> {
      return generateLeaveDates({ days: 1 });
    },
  });

  // @see https://github.com/TheBrainFamily/cypress-cucumber-webpack-typescript-example
  // @see https://github.com/cypress-io/cypress-webpack-preprocessor
  const options = {
    webpackOptions: require("../../webpack.config.ts"),
  };
  on("file:preprocessor", webpackPreprocessor(options));

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
async function getEmployee(employeeType: string): Promise<EmployeeRecord> {
  const claims = await fs.promises
    .readFile(config("EMPLOYEES_FILE"), "utf-8")
    .then(JSON.parse);
  const factory = fromClaimsFactory(claims);
  switch (employeeType) {
    case "financially eligible":
      return factory(false);
    case "financially ineligible":
      return factory(true);
    default:
      throw new Error(`Unknown employee type: ${employeeType}`);
  }
}
