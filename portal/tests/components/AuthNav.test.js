import User, { RoleDescription } from "../../src/models/User";
import { render, screen } from "@testing-library/react";
import AuthNav from "../../src/components/AuthNav";
import React from "react";
import userEvent from "@testing-library/user-event";

describe("AuthNav", () => {
  const user = new User({
    email_address: "email@address.com",
    user_id: "mock-user-id",
    consented_to_data_sharing: true,
  });

  it("renders the logged-out state", () => {
    const { container } = render(<AuthNav onLogout={jest.fn()} />);

    expect(container.firstChild).toMatchSnapshot();
    const [backToMass, logIn] = screen.getAllByRole("link");
    expect(backToMass).toHaveAccessibleName("Back to Mass.gov");
    expect(logIn).toHaveAccessibleName("Log in");
  });

  it("doesn't render the user's name", () => {
    render(<AuthNav onLogout={jest.fn()} />);

    expect(screen.queryByTestId("email_address")).not.toBeInTheDocument();
  });

  it("doesn't render a log out link", () => {
    render(<AuthNav onLogout={jest.fn()} />);

    expect(
      screen.queryByRole("button", { name: "Log out" })
    ).not.toBeInTheDocument();
  });

  it("renders the logged-in state", () => {
    const { container } = render(
      <AuthNav user={user} onLogout={() => jest.fn()} />
    );
    expect(container.firstChild).toMatchSnapshot();
    expect(screen.getByRole("button")).toHaveAccessibleName("Log out");
  });

  it("renders the user's name", () => {
    render(<AuthNav user={user} onLogout={() => jest.fn()} />);
    expect(screen.getByTestId("email_address")).toHaveTextContent(
      user.email_address
    );
  });

  it("does not render settings link when user role is employer and MFA feature flag is enabled", () => {
    process.env.featureFlags = JSON.stringify({ claimantShowMFA: true });
    render(
      <AuthNav
        user={
          new User({
            email_address: "email@address.com",
            user_id: "mock-user-id",
            consented_to_data_sharing: true,
            roles: [{ role_description: RoleDescription.employer, role_id: 1 }],
          })
        }
        onLogout={() => jest.fn()}
      />
    );

    expect(screen.getByText(/email@address.com/)).toBeInTheDocument();

    expect(
      screen.queryByRole("link", { name: /Settings/ })
    ).not.toBeInTheDocument();
  });

  it("does not render settings link when user has not consented to data sharing and MFA feature flag is enabled", () => {
    process.env.featureFlags = JSON.stringify({ claimantShowMFA: true });
    render(
      <AuthNav
        user={
          new User({
            email_address: "email@address.com",
            user_id: "mock-user-id",
          })
        }
        onLogout={() => jest.fn()}
      />
    );

    expect(screen.getByText(/email@address.com/)).toBeInTheDocument();

    expect(
      screen.queryByRole("link", { name: /Settings/ })
    ).not.toBeInTheDocument();
  });

  it("renders settings link and not email when user role is not employer, user consented to sharing, and MFA feature flag is enabled", () => {
    process.env.featureFlags = JSON.stringify({ claimantShowMFA: true });
    render(
      <AuthNav
        user={
          new User({
            email_address: "email@address.com",
            user_id: "mock-user-id",
            consented_to_data_sharing: true,
            roles: [],
          })
        }
        onLogout={() => jest.fn()}
      />
    );
    expect(screen.getByRole("link", { name: /Settings/ })).toBeInTheDocument();
    expect(screen.queryByText(/email@address.com/)).not.toBeInTheDocument();
  });

  it("doesn't render a Mass.gov link", () => {
    render(<AuthNav user={user} onLogout={() => jest.fn()} />);

    expect(
      screen.queryByRole("link", { name: "Back to Mass.gov" })
    ).not.toBeInTheDocument();
  });

  it("logs the user out when log out button is clicked", () => {
    const onLogoutMock = jest.fn();
    render(<AuthNav user={user} onLogout={onLogoutMock} />);
    const logOutButton = screen.getByRole("button", { name: "Log out" });

    userEvent.click(logOutButton);
    expect(onLogoutMock).toHaveBeenCalled();
  });
});
