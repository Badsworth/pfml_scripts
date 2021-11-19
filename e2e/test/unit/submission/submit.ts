import { mocked } from "ts-jest/utils";
import { describe, it, expect } from "@jest/globals";
import delay from "delay";
import { GeneratedClaim } from "../../../src/generation/Claim";
import * as utils from "../../../src/scripts/util";
import { ApplicationSubmissionResponse, Credentials } from "../../../src/types";
import { ClaimStateTrackerInterface } from "../../../src/submission/ClaimStateTracker";
import PortalSubmitter from "../../../src/submission/PortalSubmitter";
import { getPortalSubmitter } from "../../../src/util/common";
jest.mock("delay");
jest.mock("../../../src/util/common");

const EMPLOYEE_EMAIL = "foo@email.com";
const EMPLOYER_EMAIL = "bar@email.com";
const PASSWORD = "password";
jest.mock("../../../src/util/credentials", () => {
  const getClaimantCredentials = () => ({
    username: EMPLOYEE_EMAIL,
    password: PASSWORD,
  });
  const getLeaveAdminCredentials = () => ({
    username: EMPLOYER_EMAIL,
    password: PASSWORD,
  });
  return { getClaimantCredentials, getLeaveAdminCredentials };
});
// Create a typed mock object for getPortalSubmitter(). This only overrides the TS typing.
const getPortalSubmitterMock = mocked(getPortalSubmitter);

type MockRepsonse = {
  response: Record<string, unknown>;
  status: number;
  ok?: boolean;
};

const successResponse: ApplicationSubmissionResponse = {
  application_id: "1234",
  fineos_absence_id: "5678",
  first_name: "John",
  last_name: "Smith",
};

const errorResponse: MockRepsonse = {
  response: {
    data: undefined,
    errors: [],
    message: "This is a testing error",
    meta: {
      method: "POST",
      resource: "/v1/applications/applications",
    },
  },
  status: 500,
  ok: false,
};

describe("Portal backoff", () => {
  const generateClaims = async function* (count: number) {
    for (let i = 0; i < count; i++) {
      yield {
        id: i.toString(),
        claim: {
          employer_fein: "123",
        },
      } as GeneratedClaim;
    }
  };
  const tracker: ClaimStateTrackerInterface = {
    get: jest.fn(),
    set: jest.fn(),
    has: jest.fn(async () => false),
  };

  beforeAll(() => {
    jest.clearAllMocks();
    // Reset to original implementation before each test
    jest.useFakeTimers();
  });
  beforeEach(async () => {
    jest.spyOn(console, "debug").mockImplementation(() => null);
    jest.spyOn(console, "log").mockImplementation(() => null);
    jest.resetAllMocks();
  });

  it("Should slow down claim submission rate when 3 consec. errors occur and speed up once stabilized", async () => {
    const claims = await generateClaims(12);
    const submitter = {
      submit: jest.fn(() => {
        if (submitter.submit.mock.calls.length > 10) {
          return Promise.resolve(successResponse);
        }
        return Promise.reject(errorResponse);
      }),
    };
    getPortalSubmitterMock.mockReturnValueOnce(
      submitter as unknown as PortalSubmitter
    );
    await utils.submit(claims, tracker, 1, 1000);
    expect(submitter.submit).toHaveBeenCalledTimes(12);
    expect(delay).toHaveBeenCalledTimes(12);
    // delay is invoked by watchFailures during claim submission. The argument provided is the amount of ms to delay until the next claim submission
    expect(delay).toHaveBeenNthCalledWith(1, 0);
    expect(delay).toHaveBeenNthCalledWith(2, 0);
    expect(delay).toHaveBeenNthCalledWith(3, 15000);
    expect(delay).toHaveBeenNthCalledWith(4, 15000);
    expect(delay).toHaveBeenNthCalledWith(5, 15000);
    expect(delay).toHaveBeenNthCalledWith(6, 30000);
    expect(delay).toHaveBeenNthCalledWith(7, 30000);
    expect(delay).toHaveBeenNthCalledWith(8, 30000);
    expect(delay).toHaveBeenNthCalledWith(9, 30000);
    expect(delay).toHaveBeenNthCalledWith(10, 60000);
    expect(delay).toHaveBeenNthCalledWith(11, 15000);
    expect(delay).toHaveBeenNthCalledWith(12, 0);
  });

  it("Should not invoke postSubmit when an error occurs while still tracking failures", async () => {
    const claims = generateClaims(3);

    const submitter = {
      submit: jest.fn(() => Promise.reject(errorResponse)),
    };

    getPortalSubmitterMock.mockReturnValueOnce(
      submitter as unknown as PortalSubmitter
    );
    const postSubmitMock = jest.fn();
    await utils.submit(claims, tracker, 1, 1000, postSubmitMock);
    expect(postSubmitMock).toHaveBeenCalledTimes(0);
    expect(tracker.set).toHaveBeenCalledTimes(3);
  });

  it("Should invoke a postSubmit function if provided and when claim submission is successful", async () => {
    const claims = generateClaims(3);
    const submitter = {
      submit: jest.fn(() => Promise.resolve(successResponse)),
    };
    getPortalSubmitterMock.mockReturnValueOnce(
      submitter as unknown as PortalSubmitter
    );
    const postSubmitMock = jest.fn();
    await utils.submit(claims, tracker, 1, 1000, postSubmitMock);
    expect(postSubmitMock).toHaveBeenCalledTimes(3);
  });

  it("Errors thrown during postSubmit get tracked to the tracker", async () => {
    const claims = generateClaims(3);
    const submitter = {
      submit: jest.fn(() => Promise.resolve(successResponse)),
    };
    getPortalSubmitterMock.mockReturnValueOnce(
      submitter as unknown as PortalSubmitter
    );
    const postSubmitMock = jest.fn().mockRejectedValue({ error: "test" });
    await utils.submit(claims, tracker, 1, 1000, postSubmitMock);
    expect(postSubmitMock).toHaveBeenCalledTimes(3);
    expect(tracker.set).toHaveBeenCalledTimes(3);
  });

  it("Skips claim submission when tracker.has() resolves to true", async () => {
    const claims = generateClaims(3);
    mocked(tracker).has.mockImplementation(async () => true);
    const submitter = {
      submit: jest.fn(() => Promise.resolve(successResponse)),
    };
    getPortalSubmitterMock.mockReturnValueOnce(
      submitter as unknown as PortalSubmitter
    );
    const postSubmitMock = jest.fn();
    await utils.submit(claims, tracker, 1, 1000, postSubmitMock);
    expect(submitter.submit).toHaveBeenCalledTimes(0);
    expect(postSubmitMock).toHaveBeenCalledTimes(0);
  });

  it("Supplies the correct credentials to submitter.submit()", async () => {
    const claims = generateClaims(1);
    const submitter = {
      submit: jest.fn((_claim, _creds: Credentials, _erCreds: Credentials) =>
        Promise.resolve(successResponse)
      ),
    };
    getPortalSubmitterMock.mockReturnValueOnce(
      submitter as unknown as PortalSubmitter
    );
    await utils.submit(claims, tracker, 1, 1000);

    const [, employeeCreds, employerCreds] = submitter.submit.mock.calls[0];
    expect(employeeCreds.password).toBe(PASSWORD);
    expect(employeeCreds.username).toBe(EMPLOYEE_EMAIL);
    expect(employerCreds.password).toBe(PASSWORD);
    expect(employerCreds.username).toBe(EMPLOYER_EMAIL);
  });
});
