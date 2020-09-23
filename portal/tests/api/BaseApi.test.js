import {
  ApiRequestError,
  BadRequestError,
  ForbiddenError,
  InternalServerError,
  NetworkError,
  RequestTimeoutError,
  ServiceUnavailableError,
  UnauthorizedError,
  ValidationError,
} from "../../src/errors";
import { Auth } from "@aws-amplify/auth";
import BaseApi from "../../src/api/BaseApi";
import tracker from "../../src/services/tracker";

jest.mock("@aws-amplify/auth");
jest.mock("../../src/services/tracker");

describe("BaseApi", () => {
  class TestsApi extends BaseApi {
    get basePath() {
      return "/api";
    }

    get i18nPrefix() {
      return "testPrefix";
    }
  }

  let testsApi;
  const accessTokenJwt =
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJuYW1lIjoiQnVkIn0.YDRecdsqG_plEwM0H8rK7t2z0R3XRNESJB5ZXk-FRN8";

  beforeEach(() => {
    jest.spyOn(Auth, "currentSession").mockImplementation(() =>
      Promise.resolve({
        accessToken: { jwtToken: accessTokenJwt },
      })
    );

    global.fetch = jest.fn().mockResolvedValueOnce({
      json: jest
        .fn()
        .mockResolvedValueOnce({ data: [], errors: [], warnings: [] }),
      ok: true,
      status: 200,
    });

    testsApi = new TestsApi();
  });

  it("includes an Authorization header with the user's JWT", async () => {
    expect.assertions();
    await testsApi.request("GET", "users");

    expect(fetch).toHaveBeenCalledWith(
      expect.any(String),
      expect.objectContaining({
        headers: expect.objectContaining({
          Authorization: `Bearer ${accessTokenJwt}`,
        }),
      })
    );
  });

  it("sends a GET request to the API", async () => {
    expect.assertions();
    const method = "GET";

    await testsApi.request(method, "users");

    expect(fetch).toHaveBeenCalledWith(
      `${process.env.apiUrl}/api/users`,
      expect.objectContaining({
        method,
      })
    );
  });

  it("sends a POST request to the API", async () => {
    expect.assertions();
    const method = "POST";
    const body = { first_name: "Anton" };

    await testsApi.request(method, "users", body);

    expect(fetch).toHaveBeenCalledWith(
      `${process.env.apiUrl}/api/users`,
      expect.objectContaining({
        body: JSON.stringify(body),
        method,
        headers: expect.objectContaining({
          "Content-Type": "application/json",
        }),
      })
    );
  });

  it("sends a PATCH request to the API", async () => {
    expect.assertions();
    const method = "PATCH";
    const body = { first_name: "Anton" };

    await testsApi.request(method, "users", body);

    expect(fetch).toHaveBeenCalledWith(
      `${process.env.apiUrl}/api/users`,
      expect.objectContaining({
        body: JSON.stringify(body),
        method,
        headers: expect.objectContaining({
          "Content-Type": "application/json",
        }),
      })
    );
  });

  it("sends a PUT request to the API", async () => {
    expect.assertions();
    const method = "PUT";
    const body = { first_name: "Anton" };

    await testsApi.request(method, "users", body);

    expect(fetch).toHaveBeenCalledWith(
      `${process.env.apiUrl}/api/users`,
      expect.objectContaining({
        body: JSON.stringify(body),
        method,
        headers: expect.objectContaining({
          "Content-Type": "application/json",
        }),
      })
    );
  });

  it("sends a DELETE request to the API", async () => {
    expect.assertions();
    const method = "DELETE";

    await testsApi.request(method, "users");

    expect(fetch).toHaveBeenCalledWith(
      `${process.env.apiUrl}/api/users`,
      expect.objectContaining({
        method,
      })
    );
  });

  it("only makes one api request at a time", async () => {
    await Promise.all([
      testsApi.request("GET", "users"),
      testsApi.request("GET", "applications"),
    ]);

    expect(fetch).toHaveBeenCalledTimes(1);
  });

  it("transforms the method to uppercase", async () => {
    expect.assertions();
    const method = "get";

    await testsApi.request(method, "users");

    expect(fetch).toHaveBeenCalledWith(
      expect.any(String),
      expect.objectContaining({
        method: "GET",
      })
    );
  });

  it("removes the leading slash from the path", async () => {
    expect.assertions();
    const method = "GET";
    const path = "/users";

    await testsApi.request(method, path);

    expect(fetch).toHaveBeenCalledWith(
      expect.not.stringMatching("//users"),
      expect.any(Object)
    );
  });

  describe("when the body is FormData", () => {
    it("sends the FormData in the request body", async () => {
      expect.assertions();
      const method = "PUT";
      const body = new FormData();
      body.append("first_name", "Anton");

      await testsApi.request(method, "users", body);

      expect(fetch).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({ body })
      );
    });
  });

  describe("when the method is invalid", () => {
    it("throws an error", async () => {
      expect.assertions();
      const method = "WRONG";

      await expect(
        testsApi.request(method, "users")
      ).rejects.toThrowErrorMatchingInlineSnapshot(
        `"Invalid method provided, expected one of: DELETE, GET, PATCH, POST, PUT"`
      );
    });
  });

  describe("when additionalHeaders are passed", () => {
    it("adds headers", async () => {
      expect.assertions();
      const method = "PUT";
      const body = null;
      const headers = { "X-Header": "X-Header-Value" };

      await testsApi.request(method, "users", body, headers);

      expect(fetch).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          body,
          headers: expect.objectContaining(headers),
        })
      );
    });
  });

  describe("when the request succeeds with a status in the 2xx range", () => {
    it("resolves with the body, status, and success properties", async () => {
      expect.assertions();

      global.fetch = jest.fn().mockResolvedValue({
        json: jest.fn().mockResolvedValue({ data: { mock_response: true } }),
        status: 200,
        ok: true,
      });

      await expect(testsApi.request("GET", "users")).resolves
        .toMatchInlineSnapshot(`
              Object {
                "data": Object {
                  "mock_response": true,
                },
                "errors": undefined,
                "status": 200,
                "success": true,
                "warnings": undefined,
              }
            `);
    });
  });

  it("throws an error if i18nPrefix isn't defined on the subclass", () => {
    class MyApi extends BaseApi {
      get basePath() {
        return "/api";
      }
    }

    expect(() => new MyApi()).toThrow();
  });

  describe("when the fetch request fails", () => {
    beforeEach(() => {
      // We expect console.error to be called in this scenario
      jest.spyOn(console, "error").mockImplementationOnce(jest.fn());
    });

    const errorCodes = [
      [400, BadRequestError],
      [401, UnauthorizedError],
      [403, ForbiddenError],
      [408, RequestTimeoutError],
      [500, InternalServerError],
      [503, ServiceUnavailableError],
      [undefined, ApiRequestError],
      [501, ApiRequestError],
    ];

    errorCodes.forEach(([code, errorClass]) => {
      describe(`due to a ${code} status`, () => {
        it(`throws ${errorClass.name}`, async () => {
          expect.assertions();

          global.fetch = jest.fn().mockResolvedValue({
            ok: false,
            status: code,
            json: jest.fn().mockResolvedValue({}),
          });

          await expect(testsApi.request("GET", "users")).rejects.toThrow(
            errorClass
          );
        });
      });
    });

    it("throws ValidationError when the errors field in the response has entries", async () => {
      expect.assertions();

      global.fetch = jest.fn().mockResolvedValue({
        ok: false,
        status: 400,
        json: jest.fn().mockResolvedValue({
          errors: [
            {
              type: "minLength",
              rule: "5",
              field: "residential_address.zip",
            },
          ],
        }),
      });

      try {
        await testsApi.request("GET", "users");
      } catch (error) {
        expect(error).toBeInstanceOf(ValidationError);
        expect(error.issues).toHaveLength(1);
        expect(error.i18nPrefix).toBe("testPrefix");
      }
    });

    it("throws an exception based on the status code when the errors field in the response is empty", async () => {
      expect.assertions();

      global.fetch = jest.fn().mockResolvedValue({
        ok: false,
        status: 400,
        json: jest.fn().mockResolvedValue({ errors: [] }),
      });

      await expect(testsApi.request("GET", "users")).rejects.toThrow(
        BadRequestError
      );
    });

    it("doesn't prevent subsequent requests", async () => {
      expect.assertions();

      global.fetch = jest.fn().mockRejectedValue(TypeError("Network failure"));

      await expect(testsApi.request("GET", "users")).rejects.toThrow(
        NetworkError
      );

      const response = { data: [] };
      global.fetch = jest.fn().mockResolvedValueOnce({
        json: jest.fn().mockResolvedValueOnce(response),
        ok: true,
        status: 200,
      });

      await expect(testsApi.request("GET", "users")).resolves.toEqual(
        expect.objectContaining(response)
      );
    });

    describe("due to a network issue", () => {
      it("throws NetworkError", async () => {
        expect.assertions();

        global.fetch = jest
          .fn()
          .mockRejectedValue(TypeError("Network failure"));

        await expect(testsApi.request("GET", "users")).rejects.toThrow(
          NetworkError
        );
      });

      it("sends error to New Relic", async () => {
        expect.assertions();

        global.fetch = jest
          .fn()
          .mockRejectedValue(TypeError("Network failure"));

        try {
          await testsApi.request("GET", "users");
        } catch (error) {}

        expect(tracker.noticeError).toHaveBeenCalledWith(expect.any(Error));
      });
    });
  });
});
