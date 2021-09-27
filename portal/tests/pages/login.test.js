import { screen, waitFor } from "@testing-library/react";
import Login from "../../src/pages/login";
import { renderPage } from "../test-utils";
import userEvent from "@testing-library/user-event";

jest.mock("../../src/hooks/useAppLogic");
jest.mock("../../src/hooks/useLoggedInRedirect");

describe("Login", () => {
  const options = { isLoggedIn: false };
  const props = { query: {} };
  let query;
  const email = "ali@test.com";
  const password = "Qwerty123456!";

  const renderLogin = (options, properties) => {
    return renderPage(Login, options, properties);
  };

  it("renders the page", () => {
    const { container } = renderLogin(options, props);
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
    renderLogin(options, props);
    expect(screen.getByText(/Email successfully verified/)).toBeInTheDocument();
    expect(
      screen.getByText(
        /Thanks for verifying your email address. You may now log into your account./
      )
    ).toBeInTheDocument();
  });

  it("when session-timed-out query param is true displays session timed out info message", () => {
    query = {
      "session-timed-out": "true",
    };
    props.query = query;
    renderLogin(options, props);
    expect(screen.getByText(/Session timed out/)).toBeInTheDocument();
    expect(
      screen.getByText(/You were logged out due to inactivity/)
    ).toBeInTheDocument();
  });

  it("user can submit and login is called", async () => {
    const login = jest.fn();
    options.addCustomSetup = (appLogicHook) => {
      appLogicHook.auth.login = login;
    };
    renderLogin(options, props);

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
    options.addCustomSetup = (appLogicHook) => {
      appLogicHook.auth.login = login;
    };
    renderLogin(options, props);

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
