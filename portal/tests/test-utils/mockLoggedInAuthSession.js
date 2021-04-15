import { Auth } from "@aws-amplify/auth";

/**
 * Mock the Cognito authentication session so a test user appears logged in
 */
const mockLoggedInAuthSession = () => {
  const accessTokenJwt =
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJuYW1lIjoiQnVkIn0.YDRecdsqG_plEwM0H8rK7t2z0R3XRNESJB5ZXk-FRN8";

  jest.spyOn(Auth, "currentSession").mockImplementation(() =>
    Promise.resolve({
      accessToken: { jwtToken: accessTokenJwt },
    })
  );
};

export default mockLoggedInAuthSession;
