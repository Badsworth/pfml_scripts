import { act, screen, waitFor } from "@testing-library/react";
import { AppLogic } from "../../src/hooks/useAppLogic";
import ErrorInfo from "../../src/models/ErrorInfo";
import VerifyAccount from "../../src/pages/verify-account";
import { renderPage } from "../test-utils";
import userEvent from "@testing-library/user-event";

jest.mock("../../src/services/tracker");
jest.mock("../../src/hooks/useAppLogic");

describe("VerifyAccount", () => {
  let resolveResendVerifyAccountCodeMock: () => void;
  const username = "test@example.com";
  const verificationCode = "123456";
  let options = {};

  function render(options: Parameters<typeof renderPage>[1]) {
    return renderPage(VerifyAccount, options);
  }

  it("renders the initial page", () => {
    const { container } = render(options);
    expect(container.firstChild).toMatchSnapshot();
  });

  it("submits empty strings if user has not entered values yet", async () => {
    const verifyAccount = jest.fn();
    options = {
      addCustomSetup: (appLogic: AppLogic) => {
        appLogic.auth.verifyAccount = verifyAccount;
      },
    };
    render(options);
    userEvent.click(screen.getByRole("button", { name: "Submit" }));
    await waitFor(() => {
      expect(verifyAccount).toHaveBeenCalledWith("", "");
    });
  });

  describe("when authData.username is set", () => {
    const resendVerifyAccountCode = jest.fn();
    const verifyAccount = jest.fn();
    beforeEach(() => {
      options = {
        addCustomSetup: (appLogic: AppLogic) => {
          appLogic.auth.authData = { createAccountUsername: username };
          appLogic.auth.resendVerifyAccountCode = resendVerifyAccountCode;
          appLogic.auth.verifyAccount = verifyAccount;
        },
      };
      render(options);
    });

    it("does not render an email field", () => {
      expect(
        screen.queryByRole("textbox", { name: "Email address" })
      ).not.toBeInTheDocument();
    });

    it("calls resendVerifyAccountCode when resend code button is clicked", async () => {
      userEvent.click(screen.getByRole("button", { name: "Send a new code" }));

      await waitFor(() => {
        expect(resendVerifyAccountCode).toHaveBeenCalledWith(username);
      });
    });

    it("calls verifyAccount when form is submitted", async () => {
      userEvent.type(
        screen.getByRole("textbox", { name: "6-digit code" }),
        verificationCode
      );
      userEvent.click(screen.getByRole("button", { name: "Submit" }));
      await waitFor(() => {
        expect(verifyAccount).toHaveBeenCalledWith(username, verificationCode);
      });
    });
  });

  describe("when authData.username is not set", () => {
    const resendVerifyAccountCode = jest.fn();
    const verifyAccount = jest.fn();
    beforeEach(() => {
      options = {
        addCustomSetup: (appLogic: AppLogic) => {
          appLogic.auth.resendVerifyAccountCode = resendVerifyAccountCode;
          appLogic.auth.verifyAccount = verifyAccount;
        },
      };
      render(options);
    });
    it("renders an email field", () => {
      expect(
        screen.queryByRole("textbox", { name: "Email address" })
      ).toBeInTheDocument();
    });

    it("calls resendVerifyAccountCode when resend code button is clicked", async () => {
      userEvent.type(
        screen.getByRole("textbox", { name: "Email address" }),
        username
      );
      userEvent.click(screen.getByRole("button", { name: "Send a new code" }));
      await waitFor(() => {
        expect(resendVerifyAccountCode).toHaveBeenCalledWith(username);
      });
    });

    it("calls verifyAccount when form is submitted", async () => {
      userEvent.type(
        screen.getByRole("textbox", { name: "Email address" }),
        username
      );
      userEvent.type(
        screen.getByRole("textbox", { name: "6-digit code" }),
        verificationCode
      );
      userEvent.click(screen.getByRole("button", { name: "Submit" }));
      await waitFor(() => {
        expect(verifyAccount).toHaveBeenCalledWith(username, verificationCode);
      });
    });
  });

  it("shows success message after code is resent", async () => {
    options = {
      addCustomSetup: (appLogic: AppLogic) => {
        appLogic.auth.resendVerifyAccountCode = () =>
          new Promise((resolve) => {
            resolveResendVerifyAccountCodeMock = resolve;
          });
      },
    };
    render(options);
    await waitFor(() => {
      userEvent.click(screen.getByRole("button", { name: "Send a new code" }));
    });
    await act(async () => {
      await resolveResendVerifyAccountCodeMock();
    });
    expect(screen.getByText(/New verification code sent/)).toBeInTheDocument();
    expect(
      screen.getByText(
        /We sent a new 6-digit verification code to your email address. Enter the new code to verify your email./
      )
    ).toBeInTheDocument();
  });

  it("when there are errors, does not show success message when code is resent", async () => {
    options = {
      addCustomSetup: (appLogic: AppLogic) => {
        appLogic.errors = [new ErrorInfo({})];
        appLogic.auth.resendVerifyAccountCode = () =>
          new Promise((resolve) => {
            resolveResendVerifyAccountCodeMock = resolve;
          });
      },
    };
    render(options);

    await waitFor(() => {
      userEvent.click(screen.getByRole("button", { name: "Send a new code" }));
    });
    await act(async () => {
      await resolveResendVerifyAccountCodeMock();
    });

    expect(
      screen.queryByText(/New verification code sent/)
    ).not.toBeInTheDocument();
  });
});
