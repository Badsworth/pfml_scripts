import { screen, waitFor } from "@testing-library/react";
import ResetPassword from "../../src/pages/reset-password";
import { renderPage } from "../test-utils";
import userEvent from "@testing-library/user-event";

jest.mock("../../src/hooks/useAppLogic");
jest.mock("../../src/hooks/useLoggedInRedirect");

describe("ResetPassword", () => {
  let props;
  const options = { isLoggedIn: false };
  const username = "test@example.com";

  const renderResetPassword = (options, props) => {
    return renderPage(ResetPassword, options, props);
  };

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

  it("when authData.username is not set, the email field is displayed and submitte", async () => {
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

  it("user can click resend code", async () => {
    const resendForgotPasswordCode = jest.fn();
    options.addCustomSetup = (appLogicHook) => {
      appLogicHook.auth.authData = { resetPasswordUsername: username };
      appLogicHook.auth.resendForgotPasswordCode = resendForgotPasswordCode;
    };
    renderResetPassword(options, props);

    userEvent.click(screen.getByRole("button", { name: "Send a new code" }));
    await waitFor(() => {
      expect(resendForgotPasswordCode).toHaveBeenCalledWith(username);
    });
  });
});
