import * as MFAService from "../../../../src/services/mfa";
import { act, screen } from "@testing-library/react";
import { mockAuth, renderPage } from "../../../test-utils";
import ConfirmSMS from "../../../../src/pages/two-factor/sms/confirm";
import userEvent from "@testing-library/user-event";

const updateUser = jest.fn();
jest.mock("../../../../src/services/mfa", () => ({
  verifyMFAPhoneNumber: jest.fn(),
}));

beforeEach(() => {
  mockAuth(true);
  process.env.featureFlags = { claimantShowMFA: true };
});

describe("Two-factor SMS Confirm", () => {
  it("renders landing page content", () => {
    const { container } = renderPage(ConfirmSMS);
    expect(container.firstChild).toMatchSnapshot();
  });

  it("sends verification code and updates MFA preference when user saves and continues", async () => {
    renderPage(ConfirmSMS, {
      addCustomSetup: (appLogic) => {
        appLogic.users.updateUser = updateUser;
      },
    });

    const codeField = screen.getByLabelText("6-digit code");
    userEvent.type(codeField, "123456");
    const submitButton = screen.getByRole("button", {
      name: "Save and continue",
    });
    await act(async () => await userEvent.click(submitButton));

    expect(MFAService.verifyMFAPhoneNumber).toHaveBeenCalledWith("123456");
    expect(updateUser).toHaveBeenCalledWith(expect.any(String), {
      mfa_delivery_preference: "SMS",
    });
  });

  it("does not update MFA preference when verification code fails", async () => {
    MFAService.verifyMFAPhoneNumber.mockImplementation(() =>
      Promise.reject(new Error())
    );
    jest.spyOn(console, "error").mockImplementation(jest.fn());

    renderPage(ConfirmSMS);
    const codeField = screen.getByLabelText("6-digit code");
    userEvent.type(codeField, "123456");
    const submitButton = screen.getByRole("button", {
      name: "Save and continue",
    });
    await act(async () => await userEvent.click(submitButton));

    expect(MFAService.verifyMFAPhoneNumber).toHaveBeenCalledWith("123456");
    expect(updateUser).not.toHaveBeenCalled();
  });

  it("renders PageNotFound if the claimantShowMFA feature flag is not set", () => {
    process.env.featureFlags = { claimantShowMFA: false };
    renderPage(ConfirmSMS);

    const pageNotFoundHeading = screen.getByRole("heading", {
      name: /Page not found/,
    });
    expect(pageNotFoundHeading).toBeInTheDocument();
  });
});
