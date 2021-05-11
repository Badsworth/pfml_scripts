import { describe, beforeAll, test, expect } from "@jest/globals";
import { getAuthManager } from "../../src/util/common";
import config from "../../src/config";
import { RMVCheckRequest, postRmvCheck } from "../../src/api";
import * as data from "../util";

/*
  Note: The function will skip this test if E2E_ENVIRONMENT
  is NOT stage.  The id-proofing test will only work in stage based
  on specific claimant in RMV database
*/
const describeIf = (condition: boolean) =>
  condition ? describe : describe.skip;

let token: string;

describeIf(
  config("ENVIRONMENT") === "stage" || config("ENVIRONMENT") === "test"
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
