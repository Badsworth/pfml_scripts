import { mockAuth, mockFetch } from "../test-utils";
import ApplicationImportsApi from "src/api/ApplicationImportsApi";
import BenefitsApplication from "src/models/BenefitsApplication";
import { ValidationError } from "src/errors";

jest.mock("src/services/tracker");

describe("ApplicationImportsApi", () => {
  beforeAll(() => {
    mockAuth();
  });

  describe("importClaim", () => {
    it("sends POST request to /application-imports and resolves with BenefitsApplication", async () => {
      const api = new ApplicationImportsApi();
      const requestBody = {
        absence_case_id: "mock-absence-id",
        tax_identifier: "123-45-6789",
      };
      mockFetch({
        response: {
          data: {
            application_id: "mock-application_id",
          },
        },
      });

      const application = await api.importClaim(requestBody);

      expect(fetch).toHaveBeenCalledWith(
        `${process.env.apiUrl}/application-imports`,
        {
          body: JSON.stringify(requestBody),
          headers: expect.any(Object),
          method: "POST",
        }
      );

      expect(application).toBeInstanceOf(BenefitsApplication);
      expect(application.application_id).toBe("mock-application_id");
    });

    it("throws error", async () => {
      const api = new ApplicationImportsApi();
      const requestBody = {
        absence_case_id: null,
        tax_identifier: null,
      };
      mockFetch({
        response: { data: null, errors: [{ field: "tax_identifier" }] },
        status: 400,
      });

      try {
        await api.importClaim(requestBody);
      } catch (error) {
        expect(error).toBeInstanceOf(ValidationError);
        expect((error as ValidationError).issues[0].namespace).toBe(
          "applicationImports"
        );
      }
    });
  });
});
