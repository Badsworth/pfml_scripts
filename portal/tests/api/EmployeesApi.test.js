import EmployeesApi from "../../src/api/EmployeesApi";
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
    blob: jest.fn().mockResolvedValueOnce(new Blob()),
  });
};
const accessTokenJwt =
  "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJuYW1lIjoiQnVkIn0.YDRecdsqG_plEwM0H8rK7t2z0R3XRNESJB5ZXk-FRN8";
const headers = {
  Authorization: `Bearer ${accessTokenJwt}`,
  "Content-Type": "application/json",
};

const mockUserSearchRequest = {
  first_name: "mockUser",
  last_name: "User",
  tax_identifier_last4: "6789",
  employer_fein: "123456789",
};

const mockUserSearchResponse = {
  employee_id: "mockUserId",
  tax_identifier_last4: "6789",
  first_name: "mock",
  middle_name: null,
  last_name: "User",
  other_name: null,
  email_address: null,
  phone_number: null,
  organization_units: [
    {
      organization_unit_id: "dep-1",
      fineos_id: "f-dep-1",
      name: "Department One",
      employer_id: "123456789",
      linked: true,
    },
    {
      organization_unit_id: "dep-2",
      fineos_id: "f-dep-2",
      name: "Department Two",
      employer_id: "123456789",
      linked: false,
    },
  ],
};

describe("EmployeesApi", () => {
  let employeesApi;
  beforeEach(() => {
    jest.resetAllMocks();
    mockAuth(true, accessTokenJwt);
    employeesApi = new EmployeesApi();
  });

  describe("search", () => {
    describe("successful request", () => {
      beforeEach(() => {
        global.fetch = mockFetch({
          response: {
            data: mockUserSearchResponse,
            status: 200,
          },
        });
      });

      it("sends POST request to /employees/search", async () => {
        const employee = await employeesApi.search(mockUserSearchRequest);

        expect(fetch).toHaveBeenCalledTimes(1);
        expect(fetch).toHaveBeenCalledWith(
          `${process.env.apiUrl}/employees/search`,
          expect.objectContaining({
            body: JSON.stringify(mockUserSearchRequest),
            headers,
            method: "POST",
          })
        );
        expect(employee).toEqual(mockUserSearchResponse);
      });
    });
  });
});
