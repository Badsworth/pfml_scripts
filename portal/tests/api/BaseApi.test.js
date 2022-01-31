import {
  ApiRequestError,
  AuthSessionMissingError,
  BadRequestError,
  ForbiddenError,
  InternalServerError,
  NetworkError,
  NotFoundError,
  RequestTimeoutError,
  ServiceUnavailableError,
  UnauthorizedError,
  ValidationError,
} from "../../src/errors";
import { Auth } from "@aws-amplify/auth";
import BaseApi from "../../src/api/BaseApi";
import { mockAuth } from "../test-utils";
import tracker from "../../src/services/tracker";

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
    mockAuth(true, accessTokenJwt);

    global.fetch = jest.fn().mockResolvedValue({
      json: jest.fn().mockResolvedValue({ data: [], errors: [], warnings: [] }),
      ok: true,
      status: 200,
      blob: jest.fn().mockResolvedValue(new Blob()),
    });

    testsApi = new TestsApi();
  });

  it("includes an Authorization header with the user's JWT", async () => {
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

  it("excludes Authorization header when excludeAuthHeader option is true", async () => {
    await testsApi.request("GET", "users", {}, { excludeAuthHeader: true });

    expect(fetch).toHaveBeenCalledWith(
      expect.any(String),
      expect.objectContaining({
        headers: expect.not.objectContaining({
          Authorization: `Bearer ${accessTokenJwt}`,
        }),
      })
    );
  });

  it("sends a GET request to the API", async () => {
    const method = "GET";

    await testsApi.request(method, "users");

    expect(fetch).toHaveBeenCalledWith(
      `${process.env.apiUrl}/api/users`,
      expect.objectContaining({
        method,
      })
    );
  });

  it("sends a GET request with params to the API", async () => {
    const method = "GET";

    await testsApi.request(method, "users", {
      page_offset: 1,
      order_by: "name",
    });

    expect(fetch).toHaveBeenCalledWith(
      `${process.env.apiUrl}/api/users?page_offset=1&order_by=name`,
      {
        body: null,
        method,
        headers: expect.any(Object),
      }
    );
  });

  it("tracks the fetch request", async () => {
    await testsApi.request("GET", "users");

    expect(tracker.trackFetchRequest).toHaveBeenCalledWith(
      `${process.env.apiUrl}/api/users`
    );
    expect(tracker.markFetchRequestEnd).toHaveBeenCalled();
  });

  it("sends a POST request to the API", async () => {
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
    const method = "DELETE";

    await testsApi.request(method, "users");

    expect(fetch).toHaveBeenCalledWith(
      `${process.env.apiUrl}/api/users`,
      expect.objectContaining({
        method,
      })
    );
  });

  it("can make multiple api requests at a time", async () => {
    await Promise.all([
      testsApi.request("GET", "users"),
      testsApi.request("GET", "users"),
    ]);

    expect(fetch).toHaveBeenCalledTimes(2);
  });

  it("removes the leading slash from the path", async () => {
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

  describe("when additionalHeaders are passed", () => {
    it("adds headers", async () => {
      const method = "PUT";
      const body = null;
      const headers = { "X-Header": "X-Header-Value" };

      await testsApi.request(method, "users", body, {
        additionalHeaders: headers,
      });

      expect(fetch).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          body,
          headers: expect.objectContaining(headers),
        })
      );
    });
  });

  describe("when options are passed", () => {
    describe("when multipartForm is true", () => {
      it("doesn't set the Content-Type header", async () => {
        const method = "PUT";
        const body = null;
        const options = { multipartForm: true };

        await testsApi.request(method, "users", body, options);

        expect(fetch).toHaveBeenCalledWith(
          expect.any(String),
          expect.objectContaining({
            body,
            headers: expect.not.objectContaining({
              "Content-Type": "application/json",
            }),
          })
        );
      });
    });
  });

  describe("when the request succeeds with a status in the 2xx range", () => {
    it("resolves with the body, and warnings properties", async () => {
      global.fetch = jest.fn().mockResolvedValue({
        json: jest.fn().mockResolvedValue({
          data: { mock_response: true },
          meta: { method: "GET", resource: "/v1/users/current" },
        }),
        status: 200,
        ok: true,
      });

      await expect(testsApi.request("GET", "users")).resolves
        .toMatchInlineSnapshot(`
              {
                "data": {
                  "mock_response": true,
                },
                "meta": {
                  "method": "GET",
                  "resource": "/v1/users/current",
                },
                "warnings": [],
              }
            `);
    });

    it("converts API warning array field paths to square bracket", async () => {
      global.fetch = jest.fn().mockResolvedValue({
        json: jest.fn().mockResolvedValue({
          data: { mock_response: true },
          warnings: [
            {
              field: "foo.0.bar.12.cat",
              type: "required",
            },
            {
              field: "beta[2].alpha[3].charlie",
              type: "required",
            },
            {
              field: "gamma.4",
              type: "required",
            },
          ],
        }),
        status: 200,
        ok: true,
      });

      const response = await testsApi.request("GET", "users");

      await expect(response.warnings).toEqual([
        expect.objectContaining({
          type: "required",
          field: "foo[0].bar[12].cat",
        }),
        expect.objectContaining({
          type: "required",
          field: "beta[2].alpha[3].charlie",
        }),
        expect.objectContaining({ type: "required", field: "gamma[4]" }),
      ]);
    });
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
      [404, NotFoundError],
      [408, RequestTimeoutError],
      [500, InternalServerError],
      [503, ServiceUnavailableError],
      [undefined, ApiRequestError],
      [501, ApiRequestError],
    ];

    errorCodes.forEach(([code, CustomError]) => {
      describe(`due to a ${code} status`, () => {
        it(`throws ${CustomError.name}`, async () => {
          global.fetch = jest.fn().mockResolvedValue({
            ok: false,
            status: code,
            json: jest
              .fn()
              .mockResolvedValue({ data: { mock_response: "mock-data" } }),
          });

          const request = async () => await testsApi.request("GET", "users");

          await expect(request).rejects.toThrow(
            new CustomError(
              { mock_response: "mock-data" },
              `${code} status code received`
            )
          );
        });
      });
    });

    it("throws ValidationError when the errors field in the response has entries", async () => {
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

    it("overrides the error's i18nPrefix when an override is passed as an argument", async () => {
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
        await testsApi.request("GET", "users", undefined, {
          i18nPrefix: "customPrefix",
        });
      } catch (error) {
        expect(error.i18nPrefix).toBe("customPrefix");
      }
    });

    it("converts API error array field paths to square brackets", async () => {
      global.fetch = jest.fn().mockResolvedValue({
        ok: false,
        status: 400,
        json: jest.fn().mockResolvedValue({
          errors: [
            {
              type: "required",
              field: "foo.0.bar.12.cat",
            },
          ],
        }),
      });

      try {
        await testsApi.request("GET", "users");
      } catch (error) {
        expect(error.issues).toEqual([
          expect.objectContaining({ field: "foo[0].bar[12].cat" }),
        ]);
      }
    });

    it("throws an exception based on the status code when the errors field in the response is empty", async () => {
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

    it("throws AuthSessionMissingError when Cognito session fails to be retrieved", async () => {
      jest
        .spyOn(Auth, "currentSession")
        .mockRejectedValueOnce("No current user");

      await expect(testsApi.request("GET", "users")).rejects.toThrow(
        AuthSessionMissingError
      );
    });
  });
});
