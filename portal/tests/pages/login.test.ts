import { mockAuth, renderPage } from "../test-utils";
import { screen, waitFor } from "@testing-library/react";
import { AppLogic } from "../../src/hooks/useAppLogic";
import Login from "../../src/pages/login";
import userEvent from "@testing-library/user-event";

describe("Login", () => {
  const options: Parameters<typeof renderPage>[1] = { isLoggedIn: false };
  const props = { query: {} };
  let query;
  const email = "ali@test.com";
  const password = "Qwerty123456!";

  beforeEach(() => {
    mockAuth(false);
  });

  it("renders the page", () => {
    const { container } = renderPage(Login, options, props);
    expect(container.firstChild).toMatchSnapshot();
    expect(
      screen.getByText(/Log in to your paid leave account/)
    ).toBeInTheDocument();
    expect(
      screen.getByRole("textbox", { name: "Email address" })
    ).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: "Forgot your password?" })
    ).toBeInTheDocument();
  });

  it("when account-verified query param is true displays verification success message", () => {
    query = {
      "account-verified": "true",
    };
    props.query = query;
    renderPage(Login, options, props);
    expect(screen.getByText(/Email successfully verified/)).toBeInTheDocument();
    expect(
      screen.getByText(
        /Thanks for verifying your email address. You may now log in to your account./
      )
    ).toBeInTheDocument();
  });

  it("when session-timed-out query param is true displays session timed out info message", () => {
    query = {
      "session-timed-out": "true",
    };
    props.query = query;
    renderPage(Login, options, props);
    expect(screen.getByText(/Session timed out/)).toBeInTheDocument();
    expect(
      screen.getByText(/You were logged out due to inactivity/)
    ).toBeInTheDocument();
  });

  it("user can submit and login is called", async () => {
    const login = jest.fn();
    options.addCustomSetup = (appLogicHook: AppLogic) => {
      appLogicHook.auth.login = login;
    };
    renderPage(Login, options, props);

    const emailInput = screen.getByRole("textbox", { name: "Email address" });
    const passwordInput = screen.getByLabelText(/Password/);
    userEvent.type(emailInput, email);
    userEvent.type(passwordInput, password);

    userEvent.click(screen.getByRole("button", { name: "Log in" }));
    await waitFor(() => {
      expect(login).toHaveBeenCalledWith(email, password);
    });
  });

  it("on submit, it calls login with query param", async () => {
    const nextPage = "/next-page";
    query = {
      next: nextPage,
    };
    props.query = query;
    const login = jest.fn();
    options.addCustomSetup = (appLogicHook: AppLogic) => {
      appLogicHook.auth.login = login;
    };
    renderPage(Login, options, props);

    const emailInput = screen.getByRole("textbox", { name: "Email address" });
    const passwordInput = screen.getByLabelText(/Password/);
    userEvent.type(emailInput, email);
    userEvent.type(passwordInput, password);
    userEvent.click(screen.getByRole("button", { name: "Log in" }));
    await waitFor(() => {
      expect(login).toHaveBeenCalledWith(email, password, nextPage);
    });
  });
});
