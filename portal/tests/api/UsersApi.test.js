import User from "../../src/models/User";
import UsersApi from "../../src/api/UsersApi";
import portalRequest from "../../src/api/portalRequest";

jest.mock("../../src/api/portalRequest");

describe("users API", () => {
  let usersApi;

  beforeEach(() => {
    usersApi = new UsersApi();
  });

  describe("getCurrentUser", () => {
    describe("when the request succeeds", () => {
      beforeEach(() => {
        portalRequest.mockResolvedValueOnce({
          data: {
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
        portalRequest.mockResolvedValueOnce({
          data: {},
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
      portalRequest.mockResolvedValueOnce({
        data: {
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
          "email_address": null,
          "status": null,
          "user_id": "mock-user_id",
        }
      `);
    });
  });
});
