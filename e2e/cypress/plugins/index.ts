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
  DBClaimMetadata,
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
import { MongoConnector } from "../claims_database/db";
import ClaimModel from "../claims_database/models/claim";
import { extractLeavePeriod } from "../../src/util/claims";

async function generateClaim(scenarioID: Scenarios): Promise<DehydratedClaim> {
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
}

async function submitClaimToAPI(
  application: DehydratedClaim & {
    credentials?: Credentials;
    employerCredentials?: Credentials;
  }
): Promise<ApplicationSubmissionResponse> {
  const submitter = getPortalSubmitter();
  if (!application.claim) throw new Error("Application missing!");
  const { credentials, employerCredentials, ...claim } = application;
  const { employer_fein } = application.claim;
  if (!employer_fein) throw new Error("Application is missing employer FEIN");
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
}

// This function is called when a project is opened or re-opened (e.g. due to
// the project's config changing)
/**
 * @type {Cypress.PluginConfig}
 */
export default function (on: Cypress.PluginEvents): Cypress.ConfigOptions {
  const verificationFetcher = getVerificationFetcher();
  const authenticator = getAuthManager();
  const documentWaiter = new DocumentWaiter(
    config("API_BASEURL"),
    authenticator
  );

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

    generateClaim,

    submitClaimToAPI,

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

    /**
     * Returns a claim submitted from prior E2E runs based on the claim specification
     * @param filters - DBClaimMetaData
     * @returns
     */
    async getClaimFromDB({ filters, fallbackScenario }: GetClaimFromDB) {
      const { connectDB, disconnectDB } = MongoConnector();
      await connectDB(config("MONGO_CONNECTION_URI"));
      if (!(fallbackScenario in scenarios)) {
        throw new Error(`Invalid scenario: ${fallbackScenario}`);
      }
      let claim = await ClaimModel.findOne(filters);
      if (!claim) {
        // submit to api
        const genApplication = await generateClaim(fallbackScenario);
        const submittedClaim = await submitClaimToAPI(genApplication);
        const extractLeaveType = (application: DehydratedClaim) => {
          if (application.claim.has_intermittent_leave_periods)
            return "intermittent_leave_periods";
          if (application.claim.has_reduced_schedule_leave_periods)
            return "reduced_schedule_leave_periods";
          return "continuous_leave_periods";
        };
        const [startDate, endDate] = extractLeavePeriod(
          genApplication.claim,
          extractLeaveType(genApplication)
        );
        const doc = {
          scenario: fallbackScenario,
          claimId: submittedClaim.application_id,
          fineosAbsenceId: submittedClaim.fineos_absence_id,
          startDate,
          endDate,
          status: "in-progress",
          environment: config("ENVIRONMENT"),
          submittedDate: Date.now(),
        };
        claim = await ClaimModel.create(doc);
      } else {
        claim.status = "in-progress";
        await claim.save();
      }
      await disconnectDB();
      return claim;
    },
    // @todo: surpress potential errors
    async saveClaim(arg: DBClaimMetadata): Promise<null> {
      const { connectDB, disconnectDB } = MongoConnector();
      await connectDB(config("MONGO_CONNECTION_URI"));
      await ClaimModel.create(arg);
      await disconnectDB();
      return null;
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

  // Pass config values through as environment variables, which we will access via Cypress.env() in actions/common.ts.
  const configEntries = Object.entries(merged).map(([k, v]) => [`E2E_${k}`, v]);
  return {
    baseUrl: config("PORTAL_BASEURL"),
    env: Object.fromEntries(configEntries),
  };
}
