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
  getPortalSubmitter,
  getVerificationFetcher,
} from "../../src/scripts/util";
import { Credentials } from "../../src/types";
import { ApplicationResponse } from "../../src/api";

import fs from "fs";
import pdf from "pdf-parse";
import { Result } from "pdf-parse";
import TestMailClient, { Email, GetEmailsOpts } from "./TestMailClient";
import DocumentWaiter from "./DocumentWaiter";
import { ClaimGenerator, DehydratedClaim } from "../../src/generation/Claim";
import * as scenarios from "../../src/scenarios";
import EmployerPool from "../../src/generation/Employer";
import * as postSubmit from "../../src/submission/PostSubmit";
import * as actions from "../../src/utils";

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
    async generateLeaveAdminCredentials(): Promise<Credentials> {
      const credentials = generateCredentials();
      const employerPool = await EmployerPool.load(config("EMPLOYERS_FILE"));
      const employer = employerPool.pick();
      return { ...credentials, fein: employer.fein };
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
      return submitter
        .submit(
          await ClaimGenerator.hydrate(claim, "/tmp"),
          credentials ?? getClaimantCredentials(),
          employerCredentials
        )
        .catch((err) => {
          console.error("Failed to submit claim:", err.data);
          throw new Error(err);
        });
    },

    async completeSSOLoginFineos(): Promise<string> {
      let cookiesJson = "";
      await postSubmit.withFineosBrowser(
        actions.getFineosBaseUrl(),
        async (page) => {
          await page.fill('input[name="loginfmt"]', config("SSO_USERNAME"));
          await page.click("text=Next");
          await page.fill('input[name="passwd"]', config("SSO_PASSWORD"));
          await page.click('input[type="submit"]');
          await page.click("text=No");
          const cookies = await page.context().cookies();
          cookiesJson = JSON.stringify(cookies);
        }
      );
      return cookiesJson;
    },

    async approveFineosClaim(fineos_absence_id): Promise<boolean> {
      await postSubmit.withFineosBrowser(
        actions.getFineosBaseUrl(),
        async (page) => {
          await postSubmit.approveClaim(page, fineos_absence_id);
        }
      );
      return true;
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
