import { Matchers, Pact } from "@pact-foundation/pact";
import { Auth } from "@aws-amplify/auth";
import Claim from "../../src/models/Claim";
import ClaimCollection from "../../src/models/ClaimCollection";
import ClaimsApi from "../../src/api/ClaimsApi";
import { UnauthorizedError } from "../../src/errors";
import path from "path";

jest.mock("@aws-amplify/auth");
jest.mock("../../src/services/tracker");

const expiredJwtToken =
  "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE2MTcwMDAwMDAsInN1YiI6ImZlNTFiZWRiLTExNGYtNDQwMi04YzY0LTNjNzQ1ZjNkZTQyMiJ9.jkurNNMpABY-bfMis--U80WwrAPv82b_5SfNQVDNDxs";

/**
 * Mock the Access Token that's resolved for the Cognito session
 * @param {string} jwtToken
 */
function mockAccessToken(jwtToken) {
  jest.spyOn(Auth, "currentSession").mockImplementation(() =>
    Promise.resolve({
      accessToken: { jwtToken },
    })
  );
}

describe("PFML Claims API", () => {
  const claimsApi = new ClaimsApi();
  const provider = new Pact({
    consumer: "Claimant Portal",
    provider: "PFML API",
    port: 1234,
    log: path.resolve(process.cwd(), "logs", "pact.log"),
    dir: path.resolve(process.cwd(), "../api/pacts"),
    logLevel: "INFO",
  });
  const jwtToken = process.env.JWT_TOKEN;
  const baseRequestHeaders = {
    Authorization: `Bearer ${jwtToken}`,
    "Content-Type": "application/json",
  };

  beforeAll(async () => {
    if (!jwtToken) throw Error("JWT_TOKEN not set");

    // Start the mock server
    await provider.setup();
  });

  beforeEach(() => {
    process.env.apiUrl = "http://localhost:1234";
    mockAccessToken(jwtToken);
  });

  afterEach(async () => {
    // Ensure our Pact expectations were correct
    await provider.verify();
  });

  afterAll(async () => {
    // Record the interactions to the mock server into the pact
    // file & shut down the mock server
    await provider.finalize();
  });

  describe("getClaims", () => {
    describe("When a bad request is made", () => {
      beforeEach(() => {
        mockAccessToken(expiredJwtToken);

        provider.addInteraction({
          state: "user access token is expired",
          uponReceiving: "a request to get claims",
          withRequest: {
            method: "GET",
            path: `/applications`,
            headers: Object.assign({}, baseRequestHeaders, {
              Authorization: `Bearer ${expiredJwtToken}`,
            }),
          },
          willRespondWith: {
            status: 401,
            body: {},
          },
        });
      });

      it("should not return claims", async () => {
        await expect(claimsApi.getClaims).rejects.toThrow(UnauthorizedError);
      });
    });

    describe("When a request to get claims is made", () => {
      beforeEach(
        async () =>
          await provider.addInteraction({
            state: "user is logged in",
            uponReceiving: "a request to get claims",
            withRequest: {
              method: "GET",
              path: `/applications`,
              headers: baseRequestHeaders,
            },
            willRespondWith: {
              body: {
                data: [
                  {
                    application_id: Matchers.uuid(),
                  },
                ],
              },
              status: 200,
            },
          })
      );

      it("should return the correct data", async () => {
        const response = await claimsApi.getClaims();
        expect(response.claims.items.length).toBe(1);
        expect(response.claims).toBeInstanceOf(ClaimCollection);
        expect(response.claims.items[0]).toBeInstanceOf(Claim);
        expect(response.claims.items[0].application_id).toEqual(
          expect.any(String)
        );
      });
    });
  });

  describe("createClaim", () => {
    describe("When a request to create a claim is made", () => {
      beforeEach(() =>
        provider.addInteraction({
          uponReceiving: "a request to create a claim",
          withRequest: {
            method: "POST",
            path: `/applications`,
            headers: baseRequestHeaders,
          },
          willRespondWith: {
            body: {
              data: {
                application_id: Matchers.uuid(),
              },
            },
            status: 201,
          },
        })
      );

      it("should return the correct data", async () => {
        const response = await claimsApi.createClaim();
        expect(response.claim).toBeInstanceOf(Claim);
        expect(response.claim.application_id).toEqual(expect.any(String));
      });
    });
  });
});
