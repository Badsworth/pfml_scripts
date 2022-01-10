import React from "react";
import { create } from "react-test-renderer";
import { render, screen } from "@testing-library/react";
import "@testing-library/jest-dom";
import WithPermissions, {
  Props as WithPermissionsProps,
} from "../../src/components/WithPermissions";
import { AdminUserResponse } from "../../src/api";

const useRouter = jest.spyOn(require("next/router"), "useRouter");

const mockUser: AdminUserResponse = {
  sub_id: "mock_user",
  email_address: "mock@user.com",
  groups: ["NON_PROD", "NON_PROD_ADMIN"],
  permissions: ["USER_READ"],
};

const componentText = "A component";

const defaultProps: WithPermissionsProps = {
  user: mockUser,
  permissions: mockUser?.permissions || [],
  isPage: false,
  children: <p>{componentText}</p>,
};

const renderComponent = (passedProps: Partial<WithPermissionsProps> = {}) => {
  const props: WithPermissionsProps = {
    ...defaultProps,
    ...passedProps,
  };
  return render(<WithPermissions {...props} />);
};

describe("WithPermissions", () => {
  beforeEach(() => {
    useRouter.mockImplementation(() => ({
      push: jest.fn(),
    }));
  });

  test("renders the default component", () => {
    const component = create(<WithPermissions {...defaultProps} />).toJSON();
    expect(component).toMatchSnapshot();
  });

  test("renders contents when user has permission to read", () => {
    renderComponent({
      permissions: ["USER_READ"],
    });
    expect(screen.getByText(componentText)).toBeInTheDocument();
  });

  test("renders no content when user has no permission to edit", () => {
    const { container } = renderComponent({
      permissions: ["USER_EDIT"],
    });
    expect(container.childElementCount).toEqual(0);
  });

  test("renders page when user has permission to read", () => {
    renderComponent({
      permissions: ["USER_READ"],
      isPage: true,
    });
    expect(screen.getByText(componentText)).toBeInTheDocument();
  });

  test("redirects from page when user has no permission to edit", () => {
    const { container } = renderComponent({
      permissions: ["USER_EDIT"],
      isPage: true,
    });
    expect(container.childElementCount).toEqual(0);
  });

  test("renders no content when user has no permissions at all", () => {
    const { container } = renderComponent({
      user: { ...mockUser, permissions: [] },
      permissions: ["USER_READ"],
    });
    expect(container.childElementCount).toEqual(0);
  });
});
