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
import webpackPreprocessor from "@cypress/webpack-preprocessor";
import { CypressStepThis } from "@/types";
import TestMailVerificationFetcher from "./TestMailVerificationFetcher";
import PortalSubmitter from "../../src/simulation/PortalSubmitter";

export type FillPDFTaskOptions = {
  source: string;
  data: { [k: string]: string };
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
      const tag = faker.random.alphaNumeric(8);
      return {
        username: `${E2E_TESTMAIL_NAMESPACE}.${tag}@inbox.testmail.app`,
        password: faker.internet.password(10) + faker.random.number(999),
      };
    },
    async submitClaimToAPI(
      application: CypressStepThis["application"]
    ): Promise<string> {
      if (!application) throw new Error("Application missing!");
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
      return new PortalSubmitter({
        ClientId,
        UserPoolId,
        Username,
        Password,
        ApiBaseUrl,
      })
        .submit(application)
        .then((fineosId) => fineosId)
        .catch((err) => {
          console.error("Failed to submit claim:", err.data);
          throw new Error(err);
        });
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
