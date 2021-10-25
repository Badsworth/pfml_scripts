import { render, screen } from "@testing-library/react";
import AuthNav from "../../src/components/AuthNav";
import React from "react";
import User from "../../src/models/User";
import userEvent from "@testing-library/user-event";

describe("AuthNav", () => {
  const user = new User({
    email_address: "email@address.com",
    user_id: "mock-user-id",
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
