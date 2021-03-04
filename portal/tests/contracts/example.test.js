const { Pact, Matchers } = require("@pact-foundation/pact");
const { eachLike, like } = Matchers;
const path = require("path");

import { Auth } from "@aws-amplify/auth";
import ClaimsApi from "../../src/api/ClaimsApi";
import Claim from "../../src/models/Claim";
import User from "../../src/models/User";
import ClaimCollection from "../../src/models/ClaimCollection";
import { UnauthorizedError } from "../../src/errors";

jest.mock("@aws-amplify/auth");
jest.mock("../../src/services/tracker");

describe("PFML Claims API", () => {
  const user = new User({ user_id: "mock-user-id" });
  const claimDefault = Claim.defaults;
  const claimsApi = new ClaimsApi({ user });
  const provider = new Pact({
    consumer: "Claimant Portal",
    provider: "PFML API",
    port: 1234,
    log: path.resolve(process.cwd(), "logs", "pact.log"),
    dir: path.resolve(process.cwd(), "../pacts"),
    logLevel: "INFO",
  });
  const accessTokenJwt =
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJuYW1lIjoiQnVkIn0.YDRecdsqG_plEwM0H8rK7t2z0R3XRNESJB5ZXk-FRN8";
  const baseRequestHeaders = {
    Authorization: `Bearer ${accessTokenJwt}`,
    "Content-Type": "application/json",
  };

  beforeAll(() => provider.setup());
  beforeEach(() => {
    process.env.featureFlags = {};
    process.env.apiUrl = "http://localhost:1234";

    jest.resetAllMocks();
    jest.spyOn(Auth, "currentSession").mockImplementation(() =>
      Promise.resolve({
        accessToken: { jwtToken: accessTokenJwt },
      })
    );
  });
  afterEach(() => provider.verify());
  afterAll(() => provider.finalize());

  describe("getClaims", () => {
    describe("When a bad request is made", () => {
      beforeEach(() => {
        provider.addInteraction({
          state: "user is not logged in",
          uponReceiving: "a request to get claims",
          withRequest: {
            method: "GET",
            path: `/applications`,
          },
          willRespondWith: {
            status: 401,
            body: {},
          },
        });
      });

      // TODO: figure out why auth headers are still being sent
      test("should not return claims", async () => {
        await expect(claimsApi.getClaims).rejects.toThrow(UnauthorizedError);
      });
    });

    describe("When a request to get claims is made", () => {
      beforeEach(() =>
        provider.addInteraction({
          state: "user is logged in",
          uponReceiving: "a request to get claims",
          withRequest: {
            method: "GET",
            path: `/applications`,
            headers: {
              Authorization: like("Bearer 2020-02-10T11:34:18.045Z"),
            },
          },
          willRespondWith: {
            body: {
              data: [
                {
                  application_id: like("2a340cf8-6d2a-4f82-a075-73588d003f8f"),
                },
              ],
            },
            status: 200,
          },
        })
      );

      test("should return the correct data", async () => {
        const response = await claimsApi.getClaims();
        expect(response.claims.items.length).toBe(1);
        expect(response.claims).toBeInstanceOf(ClaimCollection);
        expect(response.claims.items[0]).toBeInstanceOf(Claim);
        expect(response.claims.items[0].application_id).toBe(
          "2a340cf8-6d2a-4f82-a075-73588d003f8f"
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
          },
          willRespondWith: {
            body: {
              data: {
                application_id: like("2a340cf8-6d2a-4f82-a075-73588d003f8f"),
              },
            },
            status: 200,
          },
        })
      );

      test("should return the correct data", async () => {
        const response = await claimsApi.createClaim();
        expect(response.claim).toBeInstanceOf(Claim);
        expect(response.claim.application_id).toBe(
          "2a340cf8-6d2a-4f82-a075-73588d003f8f"
        );
      });
    });
  });
});
