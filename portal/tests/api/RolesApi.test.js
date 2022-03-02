import { mockAuth, mockFetch } from "../test-utils";
import RolesApi from "../../src/api/RolesApi";

jest.mock("../../src/services/tracker");

const accessTokenJwt =
  "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJuYW1lIjoiQnVkIn0.YDRecdsqG_plEwM0H8rK7t2z0R3XRNESJB5ZXk-FRN8";
const headers = {
  Authorization: `Bearer ${accessTokenJwt}`,
  "Content-Type": "application/json",
};

describe("RolesApi", () => {
  beforeAll(() => {
    mockAuth();
  });

  it("deleteEmployerRole sends DELETE request to /roles", async () => {
    mockFetch();
    const rolesApi = new RolesApi();
    await rolesApi.deleteEmployerRole("mock_user_id");

    expect(fetch).toHaveBeenCalledWith(`${process.env.apiUrl}/roles`, {
      body: JSON.stringify({
        role: { role_description: "Employer" },
        user_id: "mock_user_id",
      }),
      headers,
      method: "DELETE",
    });
  });
});
