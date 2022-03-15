/**
 * @file Mock Users API module for tests. Jest requires the file
 * to be adjacent to the module we're mocking.
 * @see https://jestjs.io/docs/en/manual-mocks#mocking-user-modules
 * @example jest.mock("../api/RolesApi")
 */
import User from "../../models/User";

const createMockUser = () =>
  new User({
    auth_id: "cognito-123",
    consented_to_data_sharing: true,
    email_address: "mock-user@example.com",
    user_id: "api-123",
    roles: [],
    user_leave_administrators: [],
  });

export const mockDeleteEmployerRole = jest.fn(() =>
  Promise.resolve({
    success: true,
    user: createMockUser(),
  })
);

export default jest.fn().mockImplementation(() => ({
  deleteEmployerRole: mockDeleteEmployerRole,
}));
