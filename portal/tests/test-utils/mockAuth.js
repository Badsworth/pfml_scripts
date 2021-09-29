import { Auth } from "@aws-amplify/auth";

/**
 * Mock the Cognito authentication session so a test user appears logged in
 */
const mockAuth = (isLoggedIn = true) => {
  if (isLoggedIn) {
    const jwtToken =
      "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJuYW1lIjoiQnVkIn0.YDRecdsqG_plEwM0H8rK7t2z0R3XRNESJB5ZXk-FRN8";

    jest
      .spyOn(Auth, "currentUserInfo")
      .mockResolvedValue({ id: "us-east-1:XXXXXX" });
    jest.spyOn(Auth, "currentSession").mockResolvedValue({
      accessToken: { jwtToken },
    });
  } else {
    jest.spyOn(Auth, "currentUserInfo").mockResolvedValue(null);
    jest
      .spyOn(Auth, "currentSession")
      .mockRejectedValue("mockAuth: Not logged in");
  }
};

export default mockAuth;
