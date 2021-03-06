import FeatureFlagsApi from "../../src/api/FeatureFlagsApi";
import Flag from "../../src/models/Flag";
import dayjs from "dayjs";

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

describe("FeatureFlagsAPI", () => {
  let adminApi;
  const start = dayjs().add(5, "hour").toISOString(); // starts in 5 hours
  const end = dayjs().add(10, "hour").toISOString(); // ends in 10 hours
  const responseData = [
    {
      name: "maintenance",
      enabled: true,
      end,
      start,
      options: {
        page_routes: ["/applications/*"],
      },
    },
  ];

  const getResponse = () => {
    return {
      data: responseData,
    };
  };

  beforeEach(() => {
    jest.resetAllMocks();
    adminApi = new FeatureFlagsApi();
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
        const response = await adminApi.getFlags();

        expect(response[0]).toBeInstanceOf(Flag);
        expect(response).toEqual(responseData);
      });
    });

    describe("when the request is unsuccessful", () => {
      beforeEach(() => {
        global.fetch = mockFetch({
          response: { data: [] },
          status: 404,
          ok: false,
        });
      });

      it("throws error", async () => {
        await expect(adminApi.getFlags()).rejects.toThrow();
      });
    });
  });
});
