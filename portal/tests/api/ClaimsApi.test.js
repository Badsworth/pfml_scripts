import PaymentPreference, {
  PaymentPreferenceMethod,
} from "../../src/models/PaymentPreference";
import { Auth } from "@aws-amplify/auth";
import Claim from "../../src/models/Claim";
import ClaimCollection from "../../src/models/ClaimCollection";
import ClaimsApi from "../../src/api/ClaimsApi";

jest.mock("@aws-amplify/auth");
jest.mock("../../src/services/tracker");

const mockFetch = ({
  response = { data: [], errors: [], warnings: [] },
  ok = true,
  status = 200,
}) => {
  return jest.fn().mockResolvedValueOnce({
    json: jest.fn().mockResolvedValueOnce(response),
    ok,
    status,
  });
};

describe("ClaimsApi", () => {
  /** @type {ClaimsApi} */
  let claimsApi;
  const accessTokenJwt =
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJuYW1lIjoiQnVkIn0.YDRecdsqG_plEwM0H8rK7t2z0R3XRNESJB5ZXk-FRN8";
  const headers = {
    Authorization: `Bearer ${accessTokenJwt}`,
    "Content-Type": "application/json",
  };

  beforeEach(() => {
    jest.resetAllMocks();
    jest.spyOn(Auth, "currentSession").mockImplementation(() =>
      Promise.resolve({
        accessToken: { jwtToken: accessTokenJwt },
      })
    );
    claimsApi = new ClaimsApi();
  });

  beforeEach(() => {
    jest.spyOn(Auth, "currentSession").mockImplementation(() =>
      Promise.resolve({
        accessToken: { jwtToken: accessTokenJwt },
      })
    );
  });

  describe("getClaim", () => {
    let claim;

    beforeEach(() => {
      claim = new Claim({ application_id: "mock-application_id" });
      global.fetch = mockFetch({
        response: {
          data: claim,
          warnings: [
            {
              field: "first_name",
              type: "required",
              message: "First name is required",
            },
          ],
        },
      });
    });

    it("sends GET request to /applications/:application_id", async () => {
      await claimsApi.getClaim(claim.application_id);
      expect(fetch).toHaveBeenCalledWith(
        `${process.env.apiUrl}/applications/${claim.application_id}`,
        {
          body: null,
          headers,
          method: "GET",
        }
      );
    });

    it("resolves with claim, success, status, and warnings properties", async () => {
      const { claim: claimResponse, ...rest } = await claimsApi.getClaim(
        claim.application_id
      );

      expect(claimResponse).toBeInstanceOf(Claim);
      expect(claimResponse).toEqual(claim);
      expect(rest).toMatchInlineSnapshot(`
        Object {
          "status": 200,
          "success": true,
          "warnings": Array [
            Object {
              "field": "first_name",
              "message": "First name is required",
              "type": "required",
            },
          ],
        }
      `);
    });
  });

  describe("getClaims", () => {
    describe("successful request", () => {
      let claim;

      beforeEach(() => {
        claim = new Claim({ application_id: "mock-application_id" });
        global.fetch = mockFetch({
          response: {
            data: [
              {
                ...claim,
              },
            ],
          },
        });
      });

      it("sends GET request to /applications", async () => {
        await claimsApi.getClaims();
        expect(fetch).toHaveBeenCalledWith(
          `${process.env.apiUrl}/applications`,
          {
            body: null,
            headers,
            method: "GET",
          }
        );
      });

      it("resolves with claims, success, status properties", async () => {
        const { claims: claimsResponse, ...rest } = await claimsApi.getClaims();

        expect(claimsResponse).toBeInstanceOf(ClaimCollection);
        expect(claimsResponse.items).toEqual([claim]);
        expect(rest).toMatchInlineSnapshot(`
          Object {
            "status": 200,
            "success": true,
          }
        `);
      });
    });
  });

  describe("createClaim", () => {
    describe("successful request", () => {
      let claim;

      beforeEach(() => {
        claim = new Claim({ application_id: "mock-application_id" });

        global.fetch = mockFetch({
          response: {
            data: {
              ...claim,
            },
          },
          status: 201,
        });
      });

      it("sends POST request to /applications", async () => {
        await claimsApi.createClaim();
        expect(fetch).toHaveBeenCalledWith(
          `${process.env.apiUrl}/applications`,
          {
            body: null,
            headers,
            method: "POST",
          }
        );
      });

      it("resolves with claim, success, status properties", async () => {
        const { claim: claimResponse, ...rest } = await claimsApi.createClaim();

        expect(claimResponse).toBeInstanceOf(Claim);
        expect(claimResponse).toEqual(claim);
        expect(rest).toMatchInlineSnapshot(`
          Object {
            "status": 201,
            "success": true,
          }
        `);
      });
    });

    describe("unsuccessful request", () => {
      beforeEach(() => {
        global.fetch = mockFetch({
          response: { data: null },
          status: 400,
          ok: false,
        });
      });

      it("throws error", async () => {
        await expect(claimsApi.createClaim()).rejects.toThrow();
      });
    });
  });

  describe("completeClaim", () => {
    let claim;

    beforeEach(() => {
      claim = new Claim({
        application_id: "mock-application_id",
      });

      global.fetch = mockFetch({
        response: { data: { ...claim } },
      });
    });

    it("sends POST request to /applications/:application_id/complete_application", async () => {
      await claimsApi.completeClaim(claim.application_id);
      expect(fetch).toHaveBeenCalledWith(
        `${process.env.apiUrl}/applications/${claim.application_id}/complete_application`,
        {
          body: null,
          headers,
          method: "POST",
        }
      );
    });

    it("resolves with claim, success, status properties", async () => {
      const { claim: claimResponse, ...rest } = await claimsApi.completeClaim(
        claim.application_id
      );

      expect(claimResponse).toBeInstanceOf(Claim);
      expect(claimResponse).toEqual(claim);
      expect(rest).toMatchInlineSnapshot(`
        Object {
          "status": 200,
          "success": true,
        }
      `);
    });
  });

  describe("updateClaim", () => {
    let claim;

    beforeEach(() => {
      claim = new Claim({
        application_id: "mock-application_id",
      });

      global.fetch = mockFetch({
        response: { data: { ...claim } },
      });
    });

    it("sends PATCH request to /applications/:application_id", async () => {
      await claimsApi.updateClaim(claim.application_id, claim);

      expect(fetch).toHaveBeenCalledWith(
        `${process.env.apiUrl}/applications/${claim.application_id}`,
        {
          body: JSON.stringify(claim),
          headers: {
            ...headers,
            "X-PFML-Warn-On-Missing-Required-Fields": true,
          },
          method: "PATCH",
        }
      );
    });

    it("resolves with claim, errors, success, status, and warnings properties", async () => {
      const { claim: claimResponse, ...rest } = await claimsApi.updateClaim(
        claim.application_id,
        claim
      );

      expect(claimResponse).toBeInstanceOf(Claim);
      expect(claimResponse).toEqual(claim);
      expect(rest).toMatchInlineSnapshot(`
        Object {
          "errors": undefined,
          "status": 200,
          "success": true,
          "warnings": Array [],
        }
      `);
    });
  });

  describe("submitClaim", () => {
    let claim;

    beforeEach(() => {
      claim = new Claim({
        application_id: "mock-application_id",
      });

      global.fetch = mockFetch({
        response: { data: { ...claim } },
        status: 201,
      });
    });

    it("sends POST request to /applications/:application_id/submit_application", async () => {
      await claimsApi.submitClaim(claim.application_id);
      expect(fetch).toHaveBeenCalledWith(
        `${process.env.apiUrl}/applications/${claim.application_id}/submit_application`,
        {
          body: null,
          headers,
          method: "POST",
        }
      );
    });

    it("resolves with claim, success, status properties", async () => {
      const { claim: claimResponse, ...rest } = await claimsApi.submitClaim(
        claim.application_id
      );

      expect(claimResponse).toBeInstanceOf(Claim);
      expect(claimResponse).toEqual(claim);
      expect(rest).toMatchInlineSnapshot(`
        Object {
          "status": 201,
          "success": true,
        }
      `);
    });
  });

  describe("submitPaymentPreference", () => {
    let claim, payment_preference;

    beforeEach(() => {
      payment_preference = new PaymentPreference({
        payment_method: PaymentPreferenceMethod.check,
      });

      claim = new Claim({ payment_preference });

      global.fetch = mockFetch({
        response: { data: { ...claim } },
        status: 201,
      });
    });

    it("sends POST request to /applications/:application_id/submit_payment_preference", async () => {
      await claimsApi.submitPaymentPreference(
        claim.application_id,
        payment_preference
      );
      expect(fetch).toHaveBeenCalledWith(
        `${process.env.apiUrl}/applications/${claim.application_id}/submit_payment_preference`,
        {
          body: JSON.stringify(payment_preference),
          headers,
          method: "POST",
        }
      );
    });

    it("resolves with claim, success, status properties", async () => {
      const {
        claim: claimResponse,
        ...rest
      } = await claimsApi.submitPaymentPreference(
        claim.application_id,
        payment_preference
      );

      expect(claimResponse).toBeInstanceOf(Claim);
      expect(claimResponse).toEqual(claim);
      expect(rest).toMatchInlineSnapshot(`
        Object {
          "errors": undefined,
          "status": 201,
          "success": true,
          "warnings": Array [],
        }
      `);
    });
  });
});
