/**
 * @file Mock Users API module for tests. Jest requires the file
 * to be adjacent to the module we're mocking.
 * @see https://jestjs.io/docs/en/manual-mocks#mocking-user-modules
 * @example jest.mock("../api/UsersApi")
 */
import User, {
  RoleDescription,
  UserLeaveAdministrator,
  UserRole,
} from "../../models/User";

const createMockUser = () =>
  new User({
    auth_id: "cognito-123",
    consented_to_data_sharing: true,
    email_address: "mock-user@example.com",
    user_id: "api-123",
  });

const createMockEmployer = () => {
  const user = createMockUser();
  // @ts-expect-error ts-migrate(2339) FIXME: Property 'roles' does not exist on type 'User'.
  user.roles.push(new UserRole({ role_description: RoleDescription.employer }));
  // @ts-expect-error ts-migrate(2339) FIXME: Property 'user_leave_administrators' does not exis... Remove this comment to see the full error message
  user.user_leave_administrators.push(
    new UserLeaveAdministrator({
      employer_dba: "Test Company",
      employer_fein: "1298391823",
      employer_id: "dda903f-f093f-ff900",
      has_verification_data: true,
      verified: true,
    })
  );
  return user;
};

// @ts-expect-error ts-migrate(2304) FIXME: Cannot find name 'jest'.
export const mockCreateUser = jest.fn(() =>
  Promise.resolve({
    success: true,
    user: createMockUser(),
  })
);

// @ts-expect-error ts-migrate(2304) FIXME: Cannot find name 'jest'.
export const mockGetCurrentUser = jest.fn(() =>
  Promise.resolve({
    success: true,
    user: createMockUser(),
  })
);

// @ts-expect-error ts-migrate(2304) FIXME: Cannot find name 'jest'.
export const mockUpdateUser = jest.fn(() =>
  Promise.resolve({
    success: true,
    user: createMockUser(),
  })
);

// @ts-expect-error ts-migrate(2304) FIXME: Cannot find name 'jest'.
export const mockConvertUser = jest.fn(() =>
  Promise.resolve({
    success: true,
    user: createMockEmployer(),
  })
);

// @ts-expect-error ts-migrate(2304) FIXME: Cannot find name 'jest'.
export default jest.fn().mockImplementation(() => ({
  createUser: mockCreateUser,
  getCurrentUser: mockGetCurrentUser,
  updateUser: mockUpdateUser,
  convertUser: mockConvertUser,
}));
