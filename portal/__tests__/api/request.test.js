import { Auth } from "aws-amplify";
import { NetworkError } from "../../src/errors";
import request from "../../src/api/request";
import tracker from "../../src/services/tracker";

jest.mock("aws-amplify");
jest.mock("../../src/services/tracker");

describe("request", () => {
  const accessTokenJwt =
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJuYW1lIjoiQnVkIn0.YDRecdsqG_plEwM0H8rK7t2z0R3XRNESJB5ZXk-FRN8";

  beforeEach(() => {
    jest.spyOn(Auth, "currentSession").mockImplementation(() =>
      Promise.resolve({
        accessToken: { jwtToken: accessTokenJwt },
      })
    );

    global.fetch = jest.fn().mockResolvedValueOnce({
      json: jest.fn(),
    });
  });

  it("includes an Authorization header with the user's JWT", async () => {
    expect.assertions();
    await request("GET", "users");

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

    await request(method, "users");

    expect(fetch).toHaveBeenCalledWith(
      `${process.env.apiUrl}/users`,
      expect.objectContaining({
        method,
      })
    );
  });

  it("sends a POST request to the API", async () => {
    expect.assertions();
    const method = "POST";
    const body = { first_name: "Anton" };

    await request(method, "users", body);

    expect(fetch).toHaveBeenCalledWith(
      `${process.env.apiUrl}/users`,
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

    await request(method, "users", body);

    expect(fetch).toHaveBeenCalledWith(
      `${process.env.apiUrl}/users`,
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

    await request(method, "users", body);

    expect(fetch).toHaveBeenCalledWith(
      `${process.env.apiUrl}/users`,
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

    await request(method, "users");

    expect(fetch).toHaveBeenCalledWith(
      `${process.env.apiUrl}/users`,
      expect.objectContaining({
        method,
      })
    );
  });

  it("transforms the method to uppercase", async () => {
    expect.assertions();
    const method = "get";

    await request(method, "users");

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

    await request(method, path);

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

      await request(method, "users", body);

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
        request(method, "users")
      ).rejects.toThrowErrorMatchingInlineSnapshot(
        `"Invalid method provided, expected one of: DELETE, GET, PATCH, POST, PUT"`
      );
    });
  });

  describe("when the request succeeds with a status in the 2xx range", () => {
    it("resolves with the body, status, and success properties", async () => {
      expect.assertions();

      global.fetch = jest.fn().mockResolvedValue({
        json: jest.fn().mockResolvedValue({ mock_response: true }),
        status: 200,
        ok: true,
      });

      await expect(request("GET", "users")).resolves.toMatchInlineSnapshot(`
              Object {
                "apiErrors": undefined,
                "body": Object {
                  "mock_response": true,
                },
                "status": 200,
                "success": true,
              }
            `);
    });
  });

  describe("when the request succeeds, but returns a status outside the 2xx range", () => {
    beforeEach(() => {
      global.fetch = jest.fn().mockResolvedValue({
        json: jest.fn().mockResolvedValue({ mock_response: true }),
        status: 400,
        ok: false,
      });
    });

    it("resolves, but it's success property is set to false", async () => {
      expect.assertions();

      await expect(request("GET", "users")).resolves.toMatchInlineSnapshot(`
              Object {
                "apiErrors": undefined,
                "body": undefined,
                "status": 400,
                "success": false,
              }
            `);
    });

    it("does not set the body", async () => {
      expect.assertions();

      const response = await expect(request("GET", "users"));

      expect(response.body).toBeUndefined();
    });

    it("sends error to New Relic", async () => {
      expect.assertions();

      await request("GET", "users");

      expect(tracker.noticeError).toHaveBeenCalledWith(expect.any(Error));
    });
  });

  describe("when the fetch request fails", () => {
    beforeEach(() => {
      // We expect console.error to be called in this scenario
      jest.spyOn(console, "error").mockImplementationOnce(jest.fn());
    });

    it("throws NetworkError", async () => {
      expect.assertions();

      global.fetch = jest.fn().mockRejectedValue(TypeError("Network failure"));

      await expect(request("GET", "users")).rejects.toThrow(NetworkError);
    });

    it("sends error to New Relic", async () => {
      expect.assertions();

      global.fetch = jest.fn().mockRejectedValue(TypeError("Network failure"));

      try {
        await request("GET", "users");
      } catch (error) {}

      expect(tracker.noticeError).toHaveBeenCalledWith(expect.any(Error));
    });
  });
});
