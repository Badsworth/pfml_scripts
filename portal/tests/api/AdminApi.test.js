import AdminApi from "../../src/api/AdminApi";
import { Auth } from "@aws-amplify/auth";
import { DateTime } from "luxon";
import Flag from "../../src/models/Flag"

jest.mock("@aws-amplify/auth");
jest.mock("../../src/services/tracker");

const mockFetch = ({
  response = { data: {}, errors: [], warnings: [] },
  ok = true,
  status = 200,
}) => {
  return jest.fn().mockResolvedValueOnce({
    json: jest.fn().mockResolvedValueOnce(response),
    ok,
    status,
  });
};

describe("admin API", () => {
  let adminApi;
  const start = DateTime.local().plus({ hours: 5 }).toISO(); // starts in 5 hours
  const end = DateTime.local().plus({ hours: 10 }).toISO(); // ends in 10 hours
  const responseData = {
    name: null,
    enabled: true,
    end: end,
    start: start, 
    options: {
      page_routes: ["/applications/*"]
    }
  }

  const accessTokenJwt =
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJuYW1lIjoiQnVkIn0.YDRecdsqG_plEwM0H8rK7t2z0R3XRNESJB5ZXk-FRN8";
  const getResponse = () => {
    return {
      data: responseData,
    };
  };

  beforeEach(() => {
    jest.resetAllMocks();
    jest.spyOn(Auth, "currentSession").mockImplementation(() =>
      Promise.resolve({
        accessToken: { jwtToken: accessTokenJwt },
      })
    );
    adminApi = new AdminApi();
  });

  describe("get maintenance flag", () => {
    describe("when the request succeeds", () => {
      beforeEach(() => {
        global.fetch = mockFetch({
          response: getResponse(),
          status: 200,
          ok: true,
        });
      });

      it("resolves with the flag in the response", async () => {
        expect.assertions();

        const response = await adminApi.getFlag("maintenance");

        expect(response[0]).toBeInstanceOf(Flag);
        expect(response[0]).toEqual(responseData);
      });
    });

    describe("when the request is unsuccessful", () => {
      beforeEach(() => {
        global.fetch = mockFetch({
          response: { data: {} },
          status: 404,
          ok: false,
        });
      });

      it("throws error", async () => {
        await expect(adminApi.getFlag("abcde")).rejects.toThrow();
      });
    });
  });
});
