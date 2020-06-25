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
    const user = new User({
      user_id: "mock-user_id",
      consented_to_data_sharing: true,
    });

    beforeEach(() => {
      request.mockResolvedValueOnce({
        body: {
          user_id: "mock-user_id",
          consented_to_data_sharing: true,
        },
        status: 200,
        success: true,
      });
    });

    it("responds with success status", async () => {
      const response = await usersApi.updateUser(user.user_id, user);
      expect(response.success).toBeTruthy();
    });

    it("responds with an instance of a User", async () => {
      const response = await usersApi.updateUser(user.user_id, user);
      expect(response.user).toBeInstanceOf(User);
      expect(response.user).toMatchInlineSnapshot(`
        User {
          "auth_id": null,
          "consented_to_data_sharing": true,
          "date_of_birth": null,
          "email_address": null,
          "has_state_id": null,
          "state_id": null,
          "status": null,
          "user_id": "mock-user_id",
        }
      `);
    });
  });
});
