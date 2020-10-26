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

import { config as dotenv } from "dotenv";
import retry from "p-retry";
import delay from "delay";
import faker from "faker";
import fs from "fs";
import webpackPreprocessor from "@cypress/webpack-preprocessor";
import { CypressStepThis } from "@/types";
import TestMailVerificationFetcher from "./TestMailVerificationFetcher";
import PortalSubmitter from "../../src/simulation/PortalSubmitter";
import {
  SimulationClaim,
  SimulationGenerator,
} from "../../src/simulation/types";
import { ApplicationResponse, DocumentUploadRequest } from "../../src/api";
import { makeDocUploadBody } from "../../src/simulation/SimulationRunner";
import * as pilot3 from "../../src/simulation/scenarios/pilot3";
import * as pilot4 from "../../src/simulation/scenarios/pilot4";
import * as integrationScenarios from "../../src/simulation/scenarios/integrationScenarios";

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
  const configOverrides: Cypress.ConfigOptions = {};

  // Load variables from .env. This populates process.env with .env file values.
  // .env files only exist in local environments. In CI, we populate real env variables.
  dotenv();

  // "lift" any environment variable that we care about into Cypress.
  configOverrides.env = Object.entries(process.env)
    .filter(([k]) => k.startsWith("E2E_"))
    .reduce(
      (collected, [k, v]) => ({ ...collected, [k]: v }),
      {} as { [k: string]: unknown }
    );

  // Declare tasks here.
  on("task", {
    getAuthVerification: (toAddress: string) => {
      const attempt = () =>
        createClientFromEnv().getVerificationCodeForUser(toAddress);
      return retry(attempt, {
        retries: 5,
        onFailedAttempt: () => {
          return delay(1000);
        },
      });
    },
    generateCredentials(): CypressStepThis["credentials"] {
      const { E2E_TESTMAIL_NAMESPACE } = process.env;
      if (!E2E_TESTMAIL_NAMESPACE) {
        throw new Error(
          "Unable to determine E2E_TESTMAIL_NAMESPACE. You must set this environment variable."
        );
      }
      const tag = faker.random.alphaNumeric(8);
      return {
        username: `${E2E_TESTMAIL_NAMESPACE}.${tag}@inbox.testmail.app`,
        password: faker.internet.password(10) + faker.random.number(999),
      };
    },

    async submitClaimToAPI(
      application: SimulationClaim
    ): Promise<ApplicationResponse> {
      if (!application.claim) throw new Error("Application missing!");
      if (!application.documents.length) throw new Error("Documents missing!");
      const { claim, documents } = application;
      const {
        E2E_COGNITO_CLIENTID: ClientId,
        E2E_COGNITO_POOL: UserPoolId,
        E2E_PORTAL_USERNAME: Username,
        E2E_PORTAL_PASSWORD: Password,
        E2E_API_BASEURL: ApiBaseUrl,
      } = process.env;
      if (!ClientId || !UserPoolId || !Username || !Password || !ApiBaseUrl) {
        throw new Error(
          "Task 'submitClaimToAPI' failed due to missing environment variables!"
        );
      }

      const newDocuments: DocumentUploadRequest[] = documents.map(
        makeDocUploadBody("/tmp", "Direct API Upload")
      );

      return new PortalSubmitter({
        ClientId,
        UserPoolId,
        Username,
        Password,
        ApiBaseUrl,
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
      if (!employee) {
        throw new Error("Employee Type Not Found!");
      }

      const opts = {
        documentDirectory: "/tmp",
        employeeFactory: () => employee,
      };

      return scenarioFunctions[claimType](opts);
    },
  });

  // @see https://github.com/TheBrainFamily/cypress-cucumber-webpack-typescript-example
  // @see https://github.com/cypress-io/cypress-webpack-preprocessor
  const options = {
    webpackOptions: require("../../webpack.config.ts"),
  };
  on("file:preprocessor", webpackPreprocessor(options));

  return configOverrides;
}

export function createClientFromEnv(): TestMailVerificationFetcher {
  const { E2E_TESTMAIL_APIKEY, E2E_TESTMAIL_NAMESPACE } = process.env;
  if (!E2E_TESTMAIL_APIKEY || !E2E_TESTMAIL_NAMESPACE) {
    throw new Error(
      "Unable to create Test Mail API client due to missing environment variables."
    );
  }
  return new TestMailVerificationFetcher(
    E2E_TESTMAIL_APIKEY,
    E2E_TESTMAIL_NAMESPACE
  );
}

async function getEmployee(
  employeeType: string
): Promise<Record<string, string>> {
  const content = await fs.promises.readFile("employee.json");
  return JSON.parse(content.toString("utf-8"))[employeeType];
}
