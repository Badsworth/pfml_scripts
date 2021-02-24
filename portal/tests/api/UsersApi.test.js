import { Auth } from "@aws-amplify/auth";
import User from "../../src/models/User";
import UsersApi from "../../src/api/UsersApi";

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

describe("users API", () => {
  let usersApi;
  const accessTokenJwt =
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJuYW1lIjoiQnVkIn0.YDRecdsqG_plEwM0H8rK7t2z0R3XRNESJB5ZXk-FRN8";
  const getResponse = (roles) => {
    const nestedRoles = [
      { role: { role_description: "Employer", role_id: 1 } },
      { role: { role_description: "User", role_id: 2 } },
    ];
    return {
      data: {
        email_address: "mock-user@example.com",
        roles: roles || nestedRoles,
        user_leave_administrators: [
          {
            employer_dba: "Book Bindings 'R Us",
            employer_fein: "1298391823",
            employer_id: "dda903f-f093f-ff900",
            has_verification_data: true,
            verified: false,
          },
          {
            employer_dba: "Knitting Castle",
            employer_fein: "390293443",
            employer_id: "dda930f-93jfk-iej08",
            has_verification_data: true,
            verified: true,
          },
        ],
      },
    };
  };

  beforeEach(() => {
    jest.resetAllMocks();
    jest.spyOn(Auth, "currentSession").mockImplementation(() =>
      Promise.resolve({
        accessToken: { jwtToken: accessTokenJwt },
      })
    );
    usersApi = new UsersApi();
  });

  describe("getCurrentUser", () => {
    describe("when the request succeeds", () => {
      beforeEach(() => {
        global.fetch = mockFetch({
          response: getResponse(),
          status: 200,
          ok: true,
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

      it("returns transformed user roles", async () => {
        const response = await usersApi.getCurrentUser();

        expect(response.user.roles).toEqual([
          {
            role_description: "Employer",
            role_id: 1,
          },
          {
            role_description: "User",
            role_id: 2,
          },
        ]);
      });

      it("returns flattened user roles as is", async () => {
        const flattenedRoles = [
          { role_description: "Employer", role_id: 1 },
          { role_description: "Other User", role_id: 3 },
        ];
        global.fetch = mockFetch({
          response: getResponse(flattenedRoles),
          status: 200,
          ok: true,
        });

        const response = await usersApi.getCurrentUser();

        expect(response.user.roles).toEqual([
          {
            role_description: "Employer",
            role_id: 1,
          },
          {
            role_description: "Other User",
            role_id: 3,
          },
        ]);
      });

      it("returns transformed user leave administrators", async () => {
        const response = await usersApi.getCurrentUser();

        expect(response.user.user_leave_administrators).toEqual([
          {
            employer_dba: "Book Bindings 'R Us",
            employer_fein: "1298391823",
            employer_id: "dda903f-f093f-ff900",
            has_verification_data: true,
            verified: false,
          },
          {
            employer_dba: "Knitting Castle",
            employer_fein: "390293443",
            employer_id: "dda930f-93jfk-iej08",
            has_verification_data: true,
            verified: true,
          },
        ]);
      });
    });

    describe("when the request is unsuccessful", () => {
      beforeEach(() => {
        global.fetch = mockFetch({
          response: { data: {} },
          status: 400,
          ok: false,
        });
      });

      it("throws error", async () => {
        await expect(usersApi.getCurrentUser()).rejects.toThrow();
      });
    });
  });

  describe("updateUser", () => {
    const user = new User({
      user_id: "mock-user_id",
      consented_to_data_sharing: true,
    });

    beforeEach(() => {
      global.fetch = mockFetch({
        response: {
          data: {
            user_id: "mock-user_id",
            consented_to_data_sharing: true,
            roles: [
              {
                role: {
                  role_description: "Employer",
                  role_id: 1,
                },
              },
            ],
          },
        },
        status: 200,
        ok: true,
      });
    });

    it("responds with an instance of a User", async () => {
      const response = await usersApi.updateUser(user.user_id, user);
      expect(response.user).toBeInstanceOf(User);
      expect(response.user).toMatchInlineSnapshot(`
        User {
          "auth_id": null,
          "consented_to_data_sharing": true,
          "email_address": null,
          "roles": Array [
            Object {
              "role_description": "Employer",
              "role_id": 1,
            },
          ],
          "status": null,
          "user_id": "mock-user_id",
          "user_leave_administrators": Array [],
        }
      `);
    });
  });
});
