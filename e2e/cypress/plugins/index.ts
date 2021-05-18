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
// @todo: Move these utilities into src/.
import {
  getAuthManager,
  getClaimantCredentials,
  getEmployeePool,
  getEmployerPool,
  getPortalSubmitter,
  getVerificationFetcher,
  getLeaveAdminCredentials,
} from "../../src/util/common";
import { Credentials } from "../../src/types";
import { ApplicationResponse } from "../../src/api";

import fs from "fs";
import pdf from "pdf-parse";
import TestMailClient, {
  Email,
  GetEmailsOpts,
} from "../../src/submission/TestMailClient";
import DocumentWaiter from "./DocumentWaiter";
import { ClaimGenerator, DehydratedClaim } from "../../src/generation/Claim";
import * as scenarios from "../../src/scenarios";
import { Employer, EmployerPickSpec } from "../../src/generation/Employer";
import * as postSubmit from "../../src/submission/PostSubmit";
import pRetry from "p-retry";

// This function is called when a project is opened or re-opened (e.g. due to
// the project's config changing)
/**
 * @type {Cypress.PluginConfig}
 */
export default function (on: Cypress.PluginEvents): Cypress.ConfigOptions {
  const verificationFetcher = getVerificationFetcher();
  const authenticator = getAuthManager();
  const submitter = getPortalSubmitter();
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

    generateCredentials,
    async pickEmployer(spec: EmployerPickSpec): Promise<Employer> {
      return (await getEmployerPool()).pick(spec);
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
      application: DehydratedClaim & {
        credentials?: Credentials;
        employerCredentials?: Credentials;
      }
    ): Promise<ApplicationResponse> {
      if (!application.claim) throw new Error("Application missing!");
      const { credentials, employerCredentials, ...claim } = application;
      const { employer_fein } = application.claim;
      if (!employer_fein)
        throw new Error("Application is missing employer FEIN");
      return submitter
        .submit(
          await ClaimGenerator.hydrate(claim, "/tmp"),
          credentials ?? getClaimantCredentials(),
          employerCredentials ?? getLeaveAdminCredentials(employer_fein)
        )
        .catch((err) => {
          console.error("Failed to submit claim:", err.data);
          throw new Error(err);
        });
    },

    async completeSSOLoginFineos(): Promise<string> {
      return postSubmit.withFineosBrowser(
        async (page) => {
          const cookies = await page.context().cookies();
          return JSON.stringify(cookies);
        },
        false,
        path.join(__dirname, "..", "screenshots")
      );
    },

    waitForClaimDocuments: documentWaiter.waitForClaimDocuments.bind(
      documentWaiter
    ),

    async generateClaim(scenarioID: string): Promise<DehydratedClaim> {
      if (!(scenarioID in scenarios)) {
        throw new Error(`Invalid scenario: ${scenarioID}`);
      }
      const scenario = scenarios[scenarioID as keyof typeof scenarios];
      const claim = ClaimGenerator.generate(
        await getEmployeePool(),
        scenario.employee,
        scenario.claim
      );
      // Dehydrate (save) documents to the temp directory, where they can be picked up later on.
      // The file for a document is normally a callback function, which cannot be serialized and
      // sent to the browser using Cypress.
      return ClaimGenerator.dehydrate(claim, "/tmp");
    },

    async getParsedPDF(filename: string): Promise<pdf.Result> {
      return pdf(fs.readFileSync(filename));
    },

    async getNoticeFileName(downloadsFolder): Promise<string[]> {
      /*
       *  Retrying here in case the download folder isn't present yet
       *  using this to avoid any arbitrary waits after downloading
       *
       *  Returns array of filenames in the downloads folder
       */
      return await pRetry(
        async () => {
          return fs.readdirSync(downloadsFolder);
        },
        { maxTimeout: 5000 }
      );
    },

    async deleteDownloadFolder(folderName): Promise<true> {
      await fs.promises.rmdir(folderName, { maxRetries: 5, recursive: true });
      return true;
    },

    syslog(arg: unknown | unknown[]): null {
      if (Array.isArray(arg)) {
        console.log(...arg);
      } else {
        console.log(arg);
      }
      return null;
    },
  });

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
      E2E_EMPLOYER_PORTAL_PASSWORD: config("EMPLOYER_PORTAL_PASSWORD"),
      E2E_ENVIRONMENT: config("ENVIRONMENT"),
      E2E_HAS_FINEOS_SP: config("HAS_FINEOS_SP"),
    },
  };
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
