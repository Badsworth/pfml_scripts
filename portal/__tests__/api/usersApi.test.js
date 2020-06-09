import User from "../../src/models/User";
import request from "../../src/api/request";
import usersApi from "../../src/api/usersApi";

jest.mock("../../src/api/request");

describe("users API", () => {
  describe("getCurrentUser", () => {
    describe("when the request succeeds", () => {
      beforeEach(() => {
        request.mockResolvedValueOnce({
          body: {
            email_address: "mock-user@example.com",
          },
          status: 200,
          success: true,
        });
      });

      it("resolves with the response", async () => {
        expect.assertions();

        const response = await usersApi.getCurrentUser();

        expect(response).toMatchInlineSnapshot(
          {
            user: expect.objectContaining({
              email_address: "mock-user@example.com",
            }),
          },
          `
          Object {
            "status": 200,
            "success": true,
            "user": ObjectContaining {
              "email_address": "mock-user@example.com",
            },
          }
        `
        );
      });

      it("includes instance of User in the response", async () => {
        expect.assertions();

        const response = await usersApi.getCurrentUser();

        expect(response.user).toBeInstanceOf(User);
      });
    });

    describe("when the request is unsuccessful", () => {
      beforeEach(() => {
        request.mockResolvedValueOnce({
          body: {},
          status: 400,
          success: false,
        });
      });

      it("reports success as false", async () => {
        expect.assertions();

        const response = await usersApi.getCurrentUser();

        expect(response.success).toBe(false);
      });

      it("does not set the User in the response", async () => {
        expect.assertions();

        const response = await usersApi.getCurrentUser();

        expect(response.user).toBeNull();
      });
    });
  });

  describe("updateUser", () => {
    const user = {
      date_of_birth: "02-02-2020",
    };

    it("is successful", async () => {
      const response = await usersApi.updateUser(user);
      expect(response.success).toBeTruthy();
    });

    it("includes User in the response", async () => {
      const response = await usersApi.updateUser(user);

      expect(response.user).toBeInstanceOf(User);
    });

    it("adds user request parameters to the user", async () => {
      const response = await usersApi.updateUser(user);

      expect(response.user).toMatchObject(user);
    });

    it("adds status and user_id fields to the user", async () => {
      const response = await usersApi.updateUser(user);

      expect(response.user).toMatchObject({
        user_id: expect.any(String),
        status: expect.any(String),
      });
    });
  });
});
