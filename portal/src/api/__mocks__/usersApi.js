/**
 * @file Mock Users API module for tests. Jest requires the file
 * to be adjacent to the module we're mocking.
 * @see https://jestjs.io/docs/en/manual-mocks#mocking-user-modules
 * @example jest.mock("../api/UsersApi")
 */
import User from "../../models/User";
const usersApi = jest.genMockFromModule("../usersApi").default;

usersApi.updateUser = jest.fn(() =>
  Promise.resolve({
    success: true,
    user: new User({
      first_name: "Mock",
    }),
  })
);

module.exports = usersApi;
