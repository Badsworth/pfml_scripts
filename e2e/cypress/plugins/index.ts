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
import GmailVerificationCodeFetcher from "./GmailVerificationCodeFetcher";
import retry from "p-retry";
import delay from "delay";
import fillPDF from "./fillPDF";
import webpackPreprocessor from "@cypress/webpack-preprocessor";

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
  // Load variables from .env.
  const env = dotenv();
  if ("error" in env && env.error) {
    // Allow missing .env files by swallowing the ENOENT missing .env file error.
    // This lets us pass in environment variables directly in prod.
    if (
      !("code" in env.error) ||
      (env.error as Error & { code: string }).code !== "ENOENT"
    ) {
      throw env.error;
    }
  }
  if ("parsed" in env) {
    configOverrides.env = env.parsed;
  }

  // Declare a client that we'll lazy-create in getAuthVerification().
  let verificationClient: GmailVerificationCodeFetcher;

  // Declare tasks here.
  on("task", {
    getAuthVerification: (toAddress: string) => {
      if (!verificationClient) {
        verificationClient = createClientFromEnv();
      }
      const attempt = () => {
        return verificationClient.getVerificationCodeForUser(toAddress);
      };
      return retry(attempt, {
        retries: 5,
        onFailedAttempt: () => {
          return delay(1000);
        },
      });
    },
    async fillPDF(options: FillPDFTaskOptions) {
      return fillPDF(options.source, options.data);
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

export function createClientFromEnv(): GmailVerificationCodeFetcher {
  let appCreds;
  let personalCreds;
  const { GMAIL_APP_CREDS, GMAIL_PERSONAL_CREDS } = process.env;
  if (GMAIL_APP_CREDS) {
    const tempCreds = JSON.parse(GMAIL_APP_CREDS);
    appCreds = {
      clientId: tempCreds.installed.client_id,
      clientSecret: tempCreds.installed.client_secret,
      redirectUri: tempCreds.installed.redirect_uris[0],
    };
  }
  if (!appCreds) {
    throw new Error("Unable to determine Gmail app creds from environment.");
  }
  if (GMAIL_PERSONAL_CREDS) {
    personalCreds = JSON.parse(GMAIL_PERSONAL_CREDS);
  }
  return new GmailVerificationCodeFetcher(appCreds, personalCreds);
}
