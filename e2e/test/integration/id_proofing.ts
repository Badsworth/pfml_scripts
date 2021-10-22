import { describe, beforeAll, test, expect } from "@jest/globals";
import { getAuthManager } from "../../src/util/common";
import config from "../../src/config";
import { RMVCheckRequest, postRmvCheck } from "../../src/api";
import * as data from "../util";

/*
  Note: The function will skip this test if E2E_ENVIRONMENT
  is equal to test and training. The id-proofing test will not
  work in test based on the environment being fulled mocked for ID-Proofing.

  @Reminder: Add RMV claimants to E2E data generation script in order to add
  training back - based on data wipes not adding training.
*/
const describeIf = (condition: boolean) =>
  condition ? describe : describe.skip;

let token: string;

/**
 * @group stable
 */
describeIf(
  config("ENVIRONMENT") !== "test" && config("ENVIRONMENT") !== "training"
)("ID Proofing Tests", () => {
  beforeAll(async () => {
    const authenticator = getAuthManager();

    const apiCreds = {
      clientID: config("API_FINEOS_CLIENT_ID"),
      secretID: config("API_FINEOS_CLIENT_SECRET"),
    };

    token = await authenticator.getAPIBearerToken(apiCreds);
  });

  test.each(data.id_proofing)(
    "Claimant RMV check should be %s",
    async (
      description: string,
      rmvCheckRequest: RMVCheckRequest,
      message: string,
      verified: boolean
    ) => {
      const pmflApiOptions = {
        baseUrl: config("API_BASEURL"),
        headers: {
          Authorization: `Bearer ${token}`,
          "User-Agent": `PFML Integration Testing (RMV Check ${description})`,
        },
      };
      const res = await postRmvCheck(rmvCheckRequest, pmflApiOptions);

      expect(res.status).toBe(200);
      expect(res.data.data?.description).toBe(message);
      expect(res.data.data?.verified).toBe(verified);
    },
    60000
  );
});
