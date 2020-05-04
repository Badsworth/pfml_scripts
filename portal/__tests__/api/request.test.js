import request from "../../src/api/request";

describe("request", () => {
  beforeEach(() => {
    global.fetch = jest.fn().mockResolvedValueOnce({
      json: jest.fn(),
    });
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
    it("resolves, but it's success property is set to false", async () => {
      expect.assertions();

      global.fetch = jest.fn().mockResolvedValue({
        json: jest.fn().mockResolvedValue({ mock_response: true }),
        status: 400,
        ok: false,
      });

      await expect(request("GET", "users")).resolves.toMatchInlineSnapshot(`
              Object {
                "body": Object {
                  "mock_response": true,
                },
                "status": 400,
                "success": false,
              }
            `);
    });
  });

  describe("when the fetch request fails", () => {
    it("rejects with the error returned by fetch", async () => {
      expect.assertions();

      global.fetch = jest.fn().mockRejectedValue(Error("Network failure"));

      await expect(
        request("GET", "users")
      ).rejects.toThrowErrorMatchingInlineSnapshot(`"Network failure"`);
    });
  });
});
