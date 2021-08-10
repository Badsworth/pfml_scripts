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

import config, { merged } from "../../src/config";
import path from "path";
import webpackPreprocessor from "@cypress/webpack-preprocessor";
import {
  getAuthManager,
  getEmployeePool,
  getEmployerPool,
  getPortalSubmitter,
  getVerificationFetcher,
} from "../../src/util/common";
import {
  ApplicationSubmissionResponse,
  Credentials,
  Scenarios,
} from "../../src/types";
import {
  generateCredentials,
  getClaimantCredentials,
  getLeaveAdminCredentials,
} from "../../src/util/credentials";

import fs from "fs";
import pdf from "pdf-parse";
import TestMailClient, {
  Email,
  GetEmailsOpts,
} from "../../src/submission/TestMailClient";
import DocumentWaiter from "./DocumentWaiter";
import {
  ClaimGenerator,
  DehydratedClaim,
  APIClaimSpec,
} from "../../src/generation/Claim";
import * as scenarios from "../../src/scenarios";
import { Employer, EmployerPickSpec } from "../../src/generation/Employer";
import * as postSubmit from "../../src/submission/PostSubmit";
import pRetry from "p-retry";
import { disconnectDB, connectDB } from "../claims_database/db";
import { ClaimModel } from "../claims_database/claims/claim.model";
import { IClaimDocument } from "../claims_database/claims/claim.types";
import { submitClaimDirectlyToAPI } from "../actions/portal";

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
  (async () => await connectDB(config("MONGO_CONNECTION_URI")))();

  // Keep a static cache of the SSO login cookies. This allows us to skip double-logins
  // in envrionments that use SSO. Double logins are a side effect of changing the baseUrl.
  let ssoCookies: string;

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
    ): Promise<ApplicationSubmissionResponse> {
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
      if (ssoCookies === undefined) {
        ssoCookies = await postSubmit.withFineosBrowser(
          async (page) => {
            return JSON.stringify(await page.context().cookies());
          },
          false,
          path.join(__dirname, "..", "screenshots")
        );
      }
      return ssoCookies;
    },

    waitForClaimDocuments:
      documentWaiter.waitForClaimDocuments.bind(documentWaiter),

    async generateClaim(scenarioID: Scenarios): Promise<DehydratedClaim> {
      if (!(scenarioID in scenarios)) {
        throw new Error(`Invalid scenario: ${scenarioID}`);
      }
      const scenario = scenarios[scenarioID];
      const claim = ClaimGenerator.generate(
        await getEmployeePool(),
        scenario.employee,
        scenario.claim as APIClaimSpec
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

    async getClaimFromDB(spec: Scenarios): Promise<IClaimDocument | undefined> {
      if (!(spec in scenarios)) {
        throw new Error(`Invalid scenario: ${spec}`);
      }
      const scenario = scenarios[spec];
      const { label, leave_dates } = scenario.claim;
      const startDate = leave_dates ? leave_dates[0] : undefined;
      const endDate = leave_dates ? leave_dates[1] : undefined;
      const claim = await ClaimModel.findOne({
        scenario: label,
        startDate,
        endDate,
        clean: true,
      });
      if (!claim) {
        // submit to api
        await submitClaimDirectlyToAPI(label);
        return;
      }
      claim.clean = false;
      await claim.save();
      return claim;
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

  on("after:run", disconnectDB);
  // Pass config values through as environment variables, which we will access via Cypress.env() in actions/common.ts.
  const configEntries = Object.entries(merged).map(([k, v]) => [`E2E_${k}`, v]);
  return {
    baseUrl: config("PORTAL_BASEURL"),
    env: Object.fromEntries(configEntries),
  };
}
