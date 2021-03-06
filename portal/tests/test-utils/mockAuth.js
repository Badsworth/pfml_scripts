import { Auth } from "@aws-amplify/auth";

const defaultJwtToken =
  "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJuYW1lIjoiQnVkIn0.YDRecdsqG_plEwM0H8rK7t2z0R3XRNESJB5ZXk-FRN8";

/**
 * Mock the Cognito authentication session so a test user appears logged in
 */
const mockAuth = (isLoggedIn = true, jwtToken = defaultJwtToken) => {
  if (isLoggedIn) {
    jest.spyOn(Auth, "currentUserInfo").mockResolvedValue({
      attributes: {
        email: "test@example.com",
      },
    });
    jest.spyOn(Auth, "currentSession").mockResolvedValue({
      getAccessToken: () => ({ getJwtToken: () => jwtToken }),
    });
  } else {
    jest.spyOn(Auth, "currentUserInfo").mockResolvedValue(null);
    jest
      .spyOn(Auth, "currentSession")
      .mockRejectedValue("mockAuth: Not logged in");
  }
};

export default mockAuth;
