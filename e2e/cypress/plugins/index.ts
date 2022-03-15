import {
  ApiResponse,
  GETClaimsByFineosAbsenceIdResponse,
} from "./../../src/_api";
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

import config, { configuration } from "../../src/config";
import path from "path";
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
import TwilioClient, { MFAOpts } from "../../src/submission/TwilioClient";
import DocumentWaiter from "./DocumentWaiter";
import { ClaimGenerator, DehydratedClaim } from "../../src/generation/Claim";
import * as scenarios from "../../src/scenarios";
import { Employer, EmployerPickSpec } from "../../src/generation/Employer";
import pRetry from "p-retry";
import { chooseRolePreset } from "../../src/util/fineosRoleSwitching";
import { FineosSecurityGroups } from "../../src/submission/fineos.pages";
import { Fineos } from "../../src/submission/fineos.pages";
import { beforeRunCollectMetadata } from "../reporters/new-relic-collect-metadata";
import { getClaimsByFineos_absence_id } from "_api";
import EmployeePool from "../../src/generation/Employee";

export default function (
  on: Cypress.PluginEvents,
  cypressConfig: Cypress.ConfigOptions
): Cypress.ConfigOptions {
  const verificationFetcher = getVerificationFetcher();
  const authenticator = getAuthManager();
  const submitter = getPortalSubmitter();
  const twilio_client = new TwilioClient(
    config("TWILIO_ACCOUNTSID"),
    config("TWILIO_AUTHTOKEN")
  );
  const documentWaiter = new DocumentWaiter(
    config("API_BASEURL"),
    authenticator
  );

  // Declare tasks here.
  on("task", {
    getAuthVerification: (toAddress: string) => {
      return verificationFetcher.getVerificationCodeForUser(toAddress);
    },
    async mfaVerification(opts: MFAOpts): Promise<string> {
      return await twilio_client.getPhoneVerification(opts);
    },
    async chooseFineosRole({
      userId,
      preset,
      debug = false,
    }: {
      userId: string;
      preset: FineosSecurityGroups;
      debug: boolean;
    }) {
      await Fineos.withBrowser(
        async (page) => {
          await chooseRolePreset(
            page,
            // ID of the account you want to switch the roles for
            userId,
            // Role preset you want to switch to.
            preset
          );
        },
        { debug }
      );
      return null;
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

    async completeSSOLoginFineos(credentials?: Credentials): Promise<string> {
      const ssoCookies = await Fineos.withBrowser(
        async (page) => {
          return JSON.stringify(await page.context().cookies());
        },
        {
          debug: false,
          screenshots: path.join(__dirname, "..", "screenshots"),
          credentials,
        }
      );
      return ssoCookies;
    },

    waitForClaimDocuments:
      documentWaiter.waitForClaimDocuments.bind(documentWaiter),

    async generateClaim(
      arg: Scenarios | { scenario: Scenarios; employeePoolFileName?: string }
    ): Promise<DehydratedClaim> {
      let scenarioID: Scenarios;
      let employeePoolFileName: string | null = null;

      if (typeof arg === "object") {
        scenarioID = arg.scenario;
        employeePoolFileName = arg.employeePoolFileName || null;
      } else {
        scenarioID = arg;
      }
      if (!(scenarioID in scenarios)) {
        throw new Error(`Invalid scenario: ${scenarioID}`);
      }
      const scenario = scenarios[scenarioID];
      const claim = ClaimGenerator.generate(
        employeePoolFileName
          ? await EmployeePool.load(employeePoolFileName)
          : await getEmployeePool(),
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
      try {
        await fs.promises.rmdir(folderName, { maxRetries: 5, recursive: true });
      } catch (error) {
        // Ignore the error if download folder doesn't exist.
        if (error.code === "ENOENT") return true;
        throw error;
      }
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

    async findFirstApprovedClaim({
      applications,
      credentials,
    }: {
      applications: ApplicationResponse[];
      credentials: Credentials;
    }): Promise<ApplicationResponse | 0> {
      const authManager = getAuthManager();
      const session = await authManager.authenticate(
        credentials.username,
        credentials.password
      );
      for (let i = 0; i < applications.length && i < 15; i++) {
        let response: ApiResponse<GETClaimsByFineosAbsenceIdResponse>;
        try {
          response = await getClaimsByFineos_absence_id(
            {
              fineos_absence_id: applications[i].fineos_absence_id as string,
            },
            {
              baseUrl: authManager.apiBaseUrl,
              headers: {
                Authorization: `Bearer ${session
                  .getAccessToken()
                  .getJwtToken()}`,
                "User-Agent": "PFML Business Simulation Bot",
              },
            }
          );
        } catch (e) {
          if (!new RegExp(/withdrawn/i).test(e.message)) throw e;
          else continue;
        }
        if (!response.data.data?.absence_periods)
          throw Error("Missing absence_period property from response");
        const { absence_periods } = response.data.data;
        if (
          absence_periods.length > 0 &&
          absence_periods[0].request_decision === "Approved"
        )
          return applications[i];
      }
      return 0;
    },
  });

  // Pass config values through as environment variables, which we will access via Cypress.env() in actions/common.ts.
  const configEntries = Object.entries(configuration).map(([k, v]) => [
    `E2E_${k}`,
    v,
  ]);

  // Add dynamic options for the New Relic reporter.
  let reporterOptions = cypressConfig.reporterOptions ?? {};
  if (cypressConfig.reporter?.match(/new-relic/)) {
    // Add metadata collection for the New Relic runner.
    on("before:run", beforeRunCollectMetadata);

    // Add dynamic reporter options based on config values.
    reporterOptions = {
      accountId: config("NEWRELIC_ACCOUNTID"),
      apiKey: config("NEWRELIC_INGEST_KEY"),
      environment: config("ENVIRONMENT"),
      branch: path.relative("refs/heads", process.env.GITHUB_REF as string),
      ...reporterOptions,
    };
  }
  return {
    baseUrl: config("PORTAL_BASEURL"),
    env: Object.fromEntries(configEntries),
    reporterOptions,
  };
}
