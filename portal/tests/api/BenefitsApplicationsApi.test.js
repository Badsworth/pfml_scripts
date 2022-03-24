import PaymentPreference, {
  PaymentPreferenceMethod,
} from "../../src/models/PaymentPreference";
import ApiResourceCollection from "../../src/models/ApiResourceCollection";
import BenefitsApplication from "../../src/models/BenefitsApplication";
import BenefitsApplicationsApi from "../../src/api/BenefitsApplicationsApi";
import { ValidationError } from "../../src/errors";
import { mockAuth } from "../test-utils";

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

describe("BenefitsApplicationsApi", () => {
  /** @type {BenefitsApplicationsApi} */
  let claimsApi;
  const accessTokenJwt =
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJuYW1lIjoiQnVkIn0.YDRecdsqG_plEwM0H8rK7t2z0R3XRNESJB5ZXk-FRN8";
  const baseRequestHeaders = {
    Authorization: `Bearer ${accessTokenJwt}`,
    "Content-Type": "application/json",
  };

  beforeEach(() => {
    jest.resetAllMocks();
    mockAuth(true, accessTokenJwt);

    claimsApi = new BenefitsApplicationsApi();
  });

  describe("getClaim", () => {
    let claim;

    beforeEach(() => {
      claim = new BenefitsApplication({
        application_id: "mock-application_id",
      });
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
          headers: baseRequestHeaders,
          method: "GET",
        }
      );
    });

    it("resolves with claim, and warnings properties", async () => {
      const { claim: claimResponse, ...rest } = await claimsApi.getClaim(
        claim.application_id
      );

      expect(claimResponse).toBeInstanceOf(BenefitsApplication);
      expect(claimResponse).toEqual(claim);
      expect(rest).toMatchInlineSnapshot(`
        {
          "warnings": [
            {
              "field": "first_name",
              "message": "First name is required",
              "namespace": "applications",
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
        claim = new BenefitsApplication({
          application_id: "mock-application_id",
        });
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
          `${process.env.apiUrl}/applications?order_by=created_at&order_direction=descending&page_offset=1`,
          {
            body: null,
            headers: baseRequestHeaders,
            method: "GET",
          }
        );
      });

      it("resolves with claims properties", async () => {
        const { claims: claimsResponse } = await claimsApi.getClaims();

        expect(claimsResponse).toBeInstanceOf(ApiResourceCollection);
        expect(claimsResponse.items).toEqual([claim]);
      });
    });
  });

  describe("createClaim", () => {
    describe("successful request", () => {
      let claim;

      beforeEach(() => {
        claim = new BenefitsApplication({
          application_id: "mock-application_id",
        });

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
            headers: baseRequestHeaders,
            method: "POST",
          }
        );
      });

      it("resolves with claim properties", async () => {
        const { claim: claimResponse } = await claimsApi.createClaim();

        expect(claimResponse).toBeInstanceOf(BenefitsApplication);
        expect(claimResponse).toEqual(claim);
      });
    });

    describe("unsuccessful request", () => {
      beforeEach(() => {
        global.fetch = mockFetch({
          response: { data: null, errors: [{ type: "invalid" }] },
          status: 400,
          ok: false,
        });
      });

      it("throws error", async () => {
        try {
          await claimsApi.createClaim({});
        } catch (error) {
          expect(error).toBeInstanceOf(ValidationError);
          expect(error.issues[0].namespace).toBe("applications");
        }
      });
    });
  });

  describe("completeClaim", () => {
    let claim;

    beforeEach(() => {
      claim = new BenefitsApplication({
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
          headers: baseRequestHeaders,
          method: "POST",
        }
      );
    });

    it("resolves with claim properties", async () => {
      const { claim: claimResponse } = await claimsApi.completeClaim(
        claim.application_id
      );

      expect(claimResponse).toBeInstanceOf(BenefitsApplication);
      expect(claimResponse).toEqual(claim);
    });
  });

  describe("updateClaim", () => {
    let claim;

    beforeEach(() => {
      claim = new BenefitsApplication({
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
          headers: baseRequestHeaders,
          method: "PATCH",
        }
      );
    });

    it("resolves with claim, errors and warnings properties", async () => {
      const { claim: claimResponse, ...rest } = await claimsApi.updateClaim(
        claim.application_id,
        claim
      );

      expect(claimResponse).toBeInstanceOf(BenefitsApplication);
      expect(claimResponse).toEqual(claim);
      expect(rest).toMatchInlineSnapshot(`
        {
          "warnings": [],
        }
      `);
    });
  });

  describe("submitClaim", () => {
    let claim;

    beforeEach(() => {
      claim = new BenefitsApplication({
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
          headers: baseRequestHeaders,
          method: "POST",
        }
      );
    });

    it("resolves with claim properties", async () => {
      const { claim: claimResponse } = await claimsApi.submitClaim(
        claim.application_id
      );

      expect(claimResponse).toBeInstanceOf(BenefitsApplication);
      expect(claimResponse).toEqual(claim);
    });

    it("makes a request using the FF header when splitClaimsAcrossBY is true", async () => {
      process.env.featureFlags = JSON.stringify({ splitClaimsAcrossBY: true });
      await claimsApi.submitClaim(claim.application_id);
      expect(fetch).toHaveBeenCalledWith(
        `${process.env.apiUrl}/applications/${claim.application_id}/submit_application`,
        {
          body: null,
          headers: {
            ...baseRequestHeaders,
            "X-FF-Split-Claims-Across-BY": "true",
          },
          method: "POST",
        }
      );
    });

    it("should handle an API response with a split application", async () => {
      claim = new BenefitsApplication({
        application_id: "mock-application_id",
      });

      global.fetch = mockFetch({
        response: {
          data: { existingApplication: { ...claim }, splitApplication: null },
        },
        status: 201,
      });
      const { claim: claimResponse } = await claimsApi.submitClaim(
        claim.application_id
      );

      expect(claimResponse).toBeInstanceOf(BenefitsApplication);
      expect(claimResponse).toEqual(claim);
    });
  });

  describe("submitPaymentPreference", () => {
    let claim, payment_preference;

    beforeEach(() => {
      payment_preference = new PaymentPreference({
        payment_method: PaymentPreferenceMethod.check,
      });

      claim = new BenefitsApplication({ payment_preference });

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
          headers: baseRequestHeaders,
          method: "POST",
        }
      );
    });

    it("resolves with claim properties", async () => {
      const { claim: claimResponse, ...rest } =
        await claimsApi.submitPaymentPreference(
          claim.application_id,
          payment_preference
        );

      expect(claimResponse).toBeInstanceOf(BenefitsApplication);
      expect(claimResponse).toEqual(claim);
      expect(rest).toMatchInlineSnapshot(`
        {
          "warnings": [],
        }
      `);
    });
  });

  describe("SubmitTaxWithholdingPreference", () => {
    let claim, tax_preference;

    beforeEach(() => {
      claim = new BenefitsApplication();
      tax_preference = { is_withholding_tax: true };

      global.fetch = mockFetch({
        response: { data: { ...claim } },
        status: 201,
      });
    });

    it("sends POST request to /applications/:application_id/submit_tax_withholding_preference", async () => {
      await claimsApi.submitTaxWithholdingPreference(
        claim.application_id,
        tax_preference
      );

      expect(fetch).toHaveBeenCalledWith(
        `${process.env.apiUrl}/applications/${claim.application_id}/submit_tax_withholding_preference`,
        {
          body: JSON.stringify(tax_preference),
          headers: baseRequestHeaders,
          method: "POST",
        }
      );
    });

    it("resolves with claim properties", async () => {
      const { claim: claimResponse, ...rest } =
        await claimsApi.submitTaxWithholdingPreference(
          claim.application_id,
          tax_preference
        );

      expect(claimResponse).toBeInstanceOf(BenefitsApplication);
      expect(claimResponse).toEqual(claim);
      expect(rest).toMatchInlineSnapshot(`
        {
          "warnings": [],
        }
      `);
    });
  });
});
