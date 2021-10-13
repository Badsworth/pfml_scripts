import { mockAuth, renderPage } from "../test-utils";
import { screen, waitFor } from "@testing-library/react";
import ResetPassword from "../../src/pages/reset-password";
import userEvent from "@testing-library/user-event";

describe("ResetPassword", () => {
  let props;
  const options = { isLoggedIn: false };
  const username = "test@example.com";

  const renderResetPassword = (options, props) => {
    return renderPage(ResetPassword, options, props);
  };

  beforeEach(() => {
    mockAuth(false);
  });

  it("renders form", () => {
    const { container } = renderResetPassword();
    expect(container.firstChild).toMatchSnapshot();
    expect(
      screen.getByRole("textbox", { name: "Email address" })
    ).toBeInTheDocument();
  });

  it("when authData.username is set, does not render an email field", () => {
    options.addCustomSetup = (appLogicHook) => {
      appLogicHook.auth.authData = { resetPasswordUsername: username };
    };
    renderResetPassword(options, props);
    expect(
      screen.queryByRole("textbox", { name: "Email address" })
    ).not.toBeInTheDocument();
  });

  it("when authData.username is set, the email field is not displayed and still submitted", async () => {
    const password = "abcdef12345678";
    const code = "123456";
    const resetPassword = jest.fn();
    options.addCustomSetup = (appLogicHook) => {
      appLogicHook.auth.authData = { resetPasswordUsername: username };
      appLogicHook.auth.resetPassword = resetPassword;
    };
    renderResetPassword(options, props);

    userEvent.type(screen.getByRole("textbox", { name: "6-digit code" }), code);
    userEvent.type(screen.getByLabelText("New password"), password);
    userEvent.click(screen.getByRole("button", { name: "Set new password" }));
    await waitFor(() => {
      expect(resetPassword).toHaveBeenCalledWith(username, code, password);
    });
  });

  it("when authData.username is not set, the email field is displayed and submitted", async () => {
    const email = "email@test.com";
    const password = "abcdef12345678";
    const code = "123456";
    const resetPassword = jest.fn();
    options.addCustomSetup = (appLogicHook) => {
      appLogicHook.auth.resetPassword = resetPassword;
    };
    renderResetPassword(options, props);

    userEvent.type(screen.getByRole("textbox", { name: "6-digit code" }), code);
    userEvent.type(screen.getByLabelText("New password"), password);
    userEvent.type(
      screen.getByRole("textbox", { name: "Email address" }),
      email
    );
    userEvent.click(screen.getByRole("button", { name: "Set new password" }));
    await waitFor(() => {
      expect(resetPassword).toHaveBeenCalledWith(email, code, password);
    });
  });

  it("user can click resend code and alert is displayed", async () => {
    const resendForgotPasswordCode = jest.fn();
    options.addCustomSetup = (appLogicHook) => {
      appLogicHook.auth.authData = { resetPasswordUsername: username };
      appLogicHook.auth.resendForgotPasswordCode = resendForgotPasswordCode;
    };
    renderResetPassword(options, props);

    expect(screen.queryByText("Check your email")).not.toBeInTheDocument();
    userEvent.click(screen.getByRole("button", { name: "Send a new code" }));
    await waitFor(() => {
      expect(resendForgotPasswordCode).toHaveBeenCalledWith(username);
      expect(
        screen.getByRole("heading", { name: "Check your email" })
      ).toBeInTheDocument();
      expect(screen.getByRole("alert")).toBeInTheDocument();
      expect(screen.getByRole("alert")).toHaveClass("usa-alert--warning");
    });
  });
});
