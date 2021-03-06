import { mockAuth, renderPage } from "../test-utils";
import { screen, waitFor } from "@testing-library/react";
import { AppLogic } from "../../src/hooks/useAppLogic";
import ForgotPassword from "../../src/pages/forgot-password";
import userEvent from "@testing-library/user-event";

describe("ForgotPassword", () => {
  beforeEach(() => {
    mockAuth(false);
  });

  it("renders form", () => {
    const { container } = renderPage(ForgotPassword, { isLoggedIn: false });
    expect(container.firstChild).toMatchSnapshot();
    expect(screen.getByText(/Forgot your password?/)).toBeInTheDocument();
    expect(
      screen.getByRole("textbox", { name: "Email address" })
    ).toBeInTheDocument();
  });

  it("when the form is submitted calls forgotPassword", async () => {
    const email = "email@test.com";
    const forgotPassword = jest.fn();
    const options = {
      isLoggedIn: false,
      addCustomSetup: (appLogicHook: AppLogic) => {
        appLogicHook.auth.forgotPassword = forgotPassword;
      },
    };
    renderPage(ForgotPassword, options);

    userEvent.type(
      screen.getByRole("textbox", { name: "Email address" }),
      email
    );
    userEvent.click(screen.getByRole("button", { name: "Send code" }));
    await waitFor(() => {
      expect(forgotPassword).toHaveBeenCalledWith(email);
    });
  });
});
