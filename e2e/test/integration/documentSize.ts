import { jest, describe, beforeAll, test, expect } from "@jest/globals";
import {
  DocumentUploadRequest,
  RequestOptions,
  postApplicationsByApplication_idDocuments,
} from "../../src/api";
import * as fs from "fs";
import {
  getEmployeePool,
  getPortalSubmitter,
  getAuthManager,
} from "../../src/util/common";
import { getClaimantCredentials } from "../../src/util/credentials";
import { ClaimGenerator } from "../../src/generation/Claim";
import * as scenarios from "../../src/scenarios";
import config from "../../src/config";
import { documentTests, DocumentTestCase } from "../util";
import * as path from "path";
import pRetry from "p-retry";

const defaultClaimantCredentials = getClaimantCredentials();
let application_id: string;
let pmflApiOptions: RequestOptions;

const getExpectedResponseText = (
  statusCode: DocumentTestCase["statusCode"]
): Partial<{
  statusText: string;
  message: string;
}> => {
  if (statusCode === 200) {
    return { message: "Successfully uploaded document" };
  }

  if (statusCode === 400) {
    return { message: "File validation error." };
  }

  if (statusCode === 413) {
    return { statusText: "Request Entity Too Large" };
  }

  const exhaustiveCheck: never = statusCode;
  return exhaustiveCheck;
};

/**
 * @group stable
 */
describe("API Documents Test of various file sizes", () => {
  beforeAll(async () => {
    jest.retryTimes(2);
    const authenticator = getAuthManager();
    const submitter = getPortalSubmitter();
    const employeePool = await getEmployeePool();
    const session = await authenticator.authenticate(
      defaultClaimantCredentials.username,
      defaultClaimantCredentials.password
    );

    pmflApiOptions = {
      baseUrl: config("API_BASEURL"),
      headers: {
        Authorization: `Bearer ${session.getAccessToken().getJwtToken()}`,
        "User-Agent": "PFML Cypress Testing",
      },
    };

    // Before hooks will not be retried, so we have to handle our own retry logic here.
    application_id = await pRetry(
      async () => {
        const claim = ClaimGenerator.generate(
          employeePool,
          scenarios.BHAP1.employee,
          scenarios.BHAP1.claim
        );
        const res = await submitter.submitPartOne(
          defaultClaimantCredentials,
          claim.claim
        );
        expect(res).toMatchObject({
          application_id: expect.any(String),
        });
        return res.application_id;
      },
      { retries: 3 }
    );

    console.log(
      `Documents are being submitted to this application_id: "${application_id}"`
    );
  }, 120000);

  const tests: Parameters<typeof test["each"]>[0] = [];

  Object.values(documentTests).forEach((testSpec) => {
    const testCases = typeof testSpec === "function" ? testSpec() : testSpec;

    tests.push(
      ...testCases.map((testCase) => [testCase.description, testCase])
    );
  });

  test.each(tests)(
    "%s",
    async (description: string, testCase: DocumentTestCase) => {
      const { filepath, statusCode } = testCase;

      const document: DocumentUploadRequest = {
        document_type: "State managed Paid Leave Confirmation",
        description: description,
        file: fs.createReadStream(filepath),
        name: path.basename(filepath),
      };
      const docRes = await postApplicationsByApplication_idDocuments(
        { application_id: application_id },
        document,
        pmflApiOptions
      ).catch((err) => {
        return err;
      });

      if (docRes.errno) {
        throw new Error(
          `request to /applications/${application_id}/documents failed, reason: write EPIPE`
        );
      }

      if (docRes.status !== statusCode) {
        throw new Error(`Unable to add document: ${JSON.stringify(docRes)}`);
      }

      expect(docRes.status).toBe(statusCode);

      const { statusText, message } = getExpectedResponseText(statusCode);
      if (statusText) {
        expect(docRes.statusText).toBe(statusText);
      } else {
        expect(docRes.data.message).toBe(message);
      }
    },
    60000
  );
});
