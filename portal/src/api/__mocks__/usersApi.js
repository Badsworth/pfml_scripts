/**
 * @file Mock Users API module for tests. Jest requires the file
 * to be adjacent to the module we're mocking.
 * @see https://jestjs.io/docs/en/manual-mocks#mocking-user-modules
 * @example jest.mock("../api/UsersApi")
 */
import User from "../../models/User";
const usersApi = jest.genMockFromModule("../usersApi").default;

const mockUser = new User({
  user_id: "api-123",
  auth_id: "cognito-123",
  email_address: "mock-user@example.com",
});

usersApi.getCurrentUser = jest.fn(() =>
  Promise.resolve({
    success: true,
    user: mockUser,
  })
);

usersApi.updateUser = jest.fn(() =>
  Promise.resolve({
    success: true,
    user: mockUser,
  })
);

module.exports = usersApi;
