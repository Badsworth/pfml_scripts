import Address from "../../src/models/Address";
import { Auth } from "@aws-amplify/auth";
import Document from "../../src/models/Document";
import DocumentCollection from "../../src/models/DocumentCollection";
import EmployerClaim from "../../src/models/EmployerClaim";
import EmployersApi from "../../src/api/EmployersApi";

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
    blob: jest.fn().mockResolvedValueOnce(new Blob()),
  });
};
const accessTokenJwt =
  "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJuYW1lIjoiQnVkIn0.YDRecdsqG_plEwM0H8rK7t2z0R3XRNESJB5ZXk-FRN8";
const absenceId = "NTN-111-ABS-01";
const headers = {
  Authorization: `Bearer ${accessTokenJwt}`,
  "Content-Type": "application/json",
};
const mockClaim = new EmployerClaim({
  date_of_birth: "1994-03-05",
  employer_benefits: [],
  employer_fein: "133701337",
  fineos_absence_id: absenceId,
  first_name: "Test",
  last_name: "Person",
  leave_details: {
    continuous_leave_periods: [
      {
        end_date: "2021-10-28",
        start_date: "2021-06-24",
      },
    ],
    intermittent_leave_periods: null,
    reason: "Serious Health Condition - Employee",
    reduced_schedule_leave_periods: null,
  },
  middle_name: "",
  previous_leaves: [],
  residential_address: new Address({
    city: "Boston",
    line_1: "71 Main Road",
    line_2: "",
    state: "MA",
    zip: "2971",
  }),
  tax_identifier: "6161",
});
const mockDocumentCollection = [
  {
    created_at: "1943-03-02",
    document_type: "Driver's License Mass",
    content_type: "image/png",
    fineos_document_id: "some-unique-id",
    name: "license.png",
    description: "Mickey Mouse license",
  },
  {
    created_at: "1943-03-02",
    document_type: "Passport",
    content_type: "image/png",
    fineos_document_id: "a-unique-id",
    name: "passport.png",
    description: "Mickey Mouse passport",
  },
];
const mockClaimReview = {
  comment: "No comment",
  employer_benefits: [],
  employer_notification_date: "1970-01-01",
  hours_worked_per_week: 0,
  previous_leaves: [
    {
      leave_end_date: "1970-01-01",
      leave_start_date: "1970-01-01",
    },
  ],
};
const mockWithholding = {
  employer_id: "mock_employer_id",
  withholding_amount: "123",
  withholding_quarter: "2020-10-10",
};
const mockUserLeaveAdmin = {
  employer_id: "mock_employer_id",
  employer_fein: "XX-XXX-6789",
  employer_dba: "User Leave Admin 01",
};

describe("EmployersApi", () => {
  let employersApi;
  beforeEach(() => {
    jest.resetAllMocks();
    jest.spyOn(Auth, "currentSession").mockImplementation(() =>
      Promise.resolve({
        accessToken: { jwtToken: accessTokenJwt },
      })
    );
    employersApi = new EmployersApi();
  });

  describe("addEmployer", () => {
    describe("successful request", () => {
      beforeEach(() => {
        global.fetch = mockFetch({
          response: {
            data: mockUserLeaveAdmin,
            status: 200,
          },
        });
      });

      it("sends POST request to /employers/add", async () => {
        await employersApi.addEmployer({ ein: "123456789" });

        expect(fetch).toHaveBeenCalledTimes(1);
        expect(fetch).toHaveBeenCalledWith(
          `${process.env.apiUrl}/employers/add`,
          expect.objectContaining({
            body: JSON.stringify({ ein: "123456789" }),
            headers,
            method: "POST",
          })
        );
      });
    });
  });

  describe("getClaim", () => {
    describe("successful request", () => {
      beforeEach(() => {
        global.fetch = mockFetch({
          response: {
            data: mockClaim,
            status: 200,
          },
        });
      });

      it("sends GET request to /employers/claims/{absenceId}/review", async () => {
        await employersApi.getClaim(absenceId);

        expect(fetch).toHaveBeenCalledWith(
          `${process.env.apiUrl}/employers/claims/${absenceId}/review`,
          expect.objectContaining({
            headers,
            method: "GET",
          })
        );
      });

      it("sends GET request with headers to /employers/claim/{absenceId}/review", async () => {
        process.env.featureFlags = { claimantShowOtherLeaveStep: true };

        await employersApi.getClaim(absenceId);

        expect(fetch).toHaveBeenCalledWith(
          `${process.env.apiUrl}/employers/claims/${absenceId}/review`,
          expect.objectContaining({
            headers: {
              ...headers,
              "X-FF-Default-To-V2": true,
            },
            method: "GET",
          })
        );
      });

      it("resolves with claim", async () => {
        const response = await employersApi.getClaim(absenceId);

        expect(response.claim).toBeInstanceOf(EmployerClaim);
        expect(response.claim).toEqual(mockClaim);
      });
    });
  });

  describe("downloadDocument", () => {
    describe("successful request", () => {
      beforeEach(() => {
        global.fetch = mockFetch({
          response: {
            response: {},
            status: 200,
            ok: true,
          },
        });
      });

      it("sends GET request to /employers/claims/{absence_id}/documents/{document_id}", async () => {
        const document = new Document({
          fineos_document_id: 1234,
          content_type: "image/png",
        });

        await employersApi.downloadDocument(absenceId, document);

        expect(fetch).toHaveBeenCalledWith(
          `${process.env.apiUrl}/employers/claims/${absenceId}/documents/${document.fineos_document_id}`,
          {
            headers: { ...headers, "Content-Type": "image/png" },
            method: "GET",
          }
        );
      });

      it("returns a Blob object", async () => {
        const document = new Document({
          fineos_document_id: 1234,
          content_type: "image/png",
        });

        const response = await employersApi.downloadDocument(
          absenceId,
          document
        );

        expect(response).toBeInstanceOf(Blob);
      });
    });
  });

  describe("getDocuments", () => {
    describe("successful request", () => {
      beforeEach(() => {
        global.fetch = mockFetch({
          response: {
            data: mockDocumentCollection,
            status: 200,
          },
        });
      });

      it("sends GET request to /employers/claims/{absenceId}/documents", async () => {
        await employersApi.getDocuments(absenceId);

        expect(fetch).toHaveBeenCalledWith(
          `${process.env.apiUrl}/employers/claims/${absenceId}/documents`,
          expect.objectContaining({
            headers,
            method: "GET",
          })
        );
      });

      it("resolves with documents", async () => {
        const expectedDocuments = mockDocumentCollection.map(
          (documentInfo) => new Document(documentInfo)
        );

        const response = await employersApi.getDocuments(absenceId);

        expect(response.documents).toBeInstanceOf(DocumentCollection);
        expect(response.documents.items).toEqual(expectedDocuments);
      });
    });
  });

  describe("getWithholding", () => {
    describe("successful request", () => {
      let withholding;

      beforeEach(() => {
        withholding = { filing_period: "1970-06-01" };
        global.fetch = mockFetch({
          response: {
            data: withholding,
            status: 200,
          },
        });
      });

      it("sends GET request to /employers/withholding/:employer_id", async () => {
        await employersApi.getWithholding("my-employer-id");
        expect(fetch).toHaveBeenCalledWith(
          `${process.env.apiUrl}/employers/withholding/my-employer-id`,
          expect.objectContaining({
            body: null,
            headers,
            method: "GET",
          })
        );
      });

      it("resolves with withholding data", async () => {
        const response = await employersApi.getWithholding("my-employer-id");
        expect(response).toEqual({
          filing_period: "1970-06-01",
        });
      });
    });
  });

  describe("submitClaimReview", () => {
    describe("successful request", () => {
      beforeEach(() => {
        global.fetch = mockFetch({
          response: {
            data: null,
          },
          status: 200,
        });
      });

      it("sends PATCH request to /employers/claims/{absenceId}/review", async () => {
        await employersApi.submitClaimReview(absenceId, mockClaimReview);

        expect(fetch).toHaveBeenCalledWith(
          `${process.env.apiUrl}/employers/claims/${absenceId}/review`,
          expect.objectContaining({
            body: JSON.stringify(mockClaimReview),
            headers,
            method: "PATCH",
          })
        );
      });

      it("resolves with empty promise", async () => {
        await employersApi.submitClaimReview(absenceId, mockClaimReview);

        expect(fetch).toHaveBeenCalledTimes(1);
      });
    });
  });

  describe("submitWithholding", () => {
    describe("successful request", () => {
      beforeEach(() => {
        global.fetch = mockFetch({
          response: {
            data: null,
          },
          status: 200,
        });
      });

      it("sends POST request to /employers/verifications", async () => {
        await employersApi.submitWithholding(mockWithholding);

        expect(fetch).toHaveBeenCalledTimes(1);
        expect(fetch).toHaveBeenCalledWith(
          `${process.env.apiUrl}/employers/verifications`,
          expect.objectContaining({
            body: JSON.stringify(mockWithholding),
            headers,
            method: "POST",
          })
        );
      });
    });
  });
});
