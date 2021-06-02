import { describe, beforeAll, test, expect } from "@jest/globals";
import {
  DocumentUploadRequest,
  RequestOptions,
  postApplicationsByApplication_idDocuments,
} from "../../src/api";
import fs from "fs";
import {
  getEmployeePool,
  getPortalSubmitter,
  getAuthManager,
} from "../../src/util/common";
import { getClaimantCredentials } from "../../src/util/credentials";
import { ClaimGenerator } from "../../src/generation/Claim";
import * as scenarios from "../../src/scenarios";
import config from "../../src/config";
import * as data from "../util";
import path from "path";

const defaultClaimantCredentials = getClaimantCredentials();
let application_id: string;
let pmflApiOptions: RequestOptions;

describe("API Documents Test of various file sizes", () => {
  beforeAll(async () => {
    jest.retryTimes(3);
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
    console.log(
      `Documents are being submitted to this application_id: "${res.application_id}"`
    );
    application_id = res.application_id;
  }, 60000);

  /**
   *  Idea here is to test the file size limit (4.5MB) w/each accepted
   *  filetype: PDF/JPG/PNG in three different ways.
   *    - smaller than limit
   *    - right at limit ex. 4.4MB
   *    - larger than limit
   */

  const tests = [...data.pdf, ...data.jpg, ...data.png, ...data.badFileTypes];

  test.each(tests)(
    "%s",
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
      if (statusCode === 413) {
        expect(docRes.statusText).toBe("Request Entity Too Large");
      } else {
        expect(docRes.data.message).toBe(message);
      }
    },
    60000
  );
});
