import { describe, beforeAll, test, expect } from "@jest/globals";
import {
  DocumentUploadRequest,
  RequestOptions,
  postApplicationsByApplication_idDocuments,
} from "../../src/api";
import fs from "fs";
import {
  getClaimantCredentials,
  getEmployeePool,
  getPortalSubmitter,
  getAuthManager,
} from "../../src/scripts/util";
import { ClaimGenerator } from "../../src/generation/Claim";
import * as scenarios from "../../src/scenarios";
import config from "../../src/config";

const defaultClaimantCredentials = getClaimantCredentials();
let application_id: string;
let pmflApiOptions: RequestOptions;

describe("API Documents Test of various file sizes", () => {
  beforeAll(async () => {
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

    const claim = ClaimGenerator.generate(
      employeePool,
      scenarios.BHAP1.employee,
      scenarios.BHAP1.claim
    );

    const res = await submitter.submitPartOne(
      defaultClaimantCredentials,
      claim.claim
    );

    if (!res.application_id || !res.fineos_absence_id) {
      throw new Error(
        `Unable to determine application ID or absence ID from response ${JSON.stringify(
          res
        )}`
      );
    }

    application_id = res.application_id;
  }, 60000);

  /**
   *  Idea here is to test the file size limit (4.5MB) w/each accepted
   *  filetype: PDF/JPG/PNG in three different ways.
   *    - smaller than limit
   *    - right at limit ex. 4.4MB
   *    - larger than limit
   *
   *  @Todo
   *  - Add more test for other file types and sizes
   *  - Add test for file type not accepted (Ex: .csv, .psd)
   */

  const tests = [
    [
      "less than 4.5MB successfully",
      "./cypress/fixtures/docTesting/small-150KB.pdf",
      "Successfully uploaded document",
      200,
    ],
    [
      "right at 4.5MB successfully",
      "./cypress/fixtures/docTesting/limit-4.5MB.pdf",
      "Successfully uploaded document",
      200,
    ],
    [
      "larger than 4.5MB (10MB) unsuccessfully and return API error",
      "./cypress/fixtures/docTesting/large-10MB.pdf",
      "Request Entity Too Large",
      413,
    ],
  ];

  test.each(tests)(
    "Should submit a PDF document with file size %s",
    async (
      description: string,
      filepath: string,
      message: string,
      statusCode: number
    ) => {
      const document: DocumentUploadRequest = {
        document_type: "State managed Paid Leave Confirmation",
        description: description,
        file: fs.createReadStream(filepath),
        name: `large.pdf`,
      };
      const docRes = await postApplicationsByApplication_idDocuments(
        { application_id: application_id },
        document,
        pmflApiOptions
      ).catch((err) => {
        return err;
      });

      expect(docRes.status).toBe(statusCode);
      if (statusCode === 413) {
        expect(docRes.statusText).toBe("Request Entity Too Large");
      } else {
        expect(docRes.data.message).toBe(message);
      }
    },
    60000
  );
});
