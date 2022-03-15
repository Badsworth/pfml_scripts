import * as MFAService from "../../../../src/services/mfa";
import { act, screen } from "@testing-library/react";
import { mockAuth, renderPage } from "../../../test-utils";
import ConfirmSMS from "../../../../src/pages/two-factor/sms/confirm";
import User from "../../../../src/models/User";
import { faker } from "@faker-js/faker";
import tracker from "../../../../src/services/tracker";
import userEvent from "@testing-library/user-event";

const updateUser = jest.fn();
const goToNextPage = jest.fn();

jest.mock("../../../../src/services/tracker");
jest.mock("../../../../src/services/mfa", () => ({
  sendMFAConfirmationCode: jest.fn(),
  verifyMFAPhoneNumber: jest.fn(),
}));

const user = new User({
  auth_id: faker.datatype.uuid(),
  consented_to_data_sharing: true,
  email_address: faker.internet.email(),
  mfa_phone_number: {
    int_code: "1",
    phone_number: "***-***-1234",
    phone_type: "Cell",
  },
});

beforeEach(() => {
  mockAuth(true);
  process.env.featureFlags = JSON.stringify({ claimantShowMFA: true });
});

describe("Two-factor SMS Confirm", () => {
  it("renders landing page content", () => {
    const { container } = renderPage(ConfirmSMS, {
      addCustomSetup: (appLogic) => {
        appLogic.users.user = user;
      },
    });
    expect(container.firstChild).toMatchSnapshot();
  });

  it("throws validation errors when the code was not entered", async () => {
    renderPage(ConfirmSMS);

    // don't enter anything in the code field
    const submitButton = screen.getByRole("button", {
      name: "Save and continue",
    });
    await act(async () => await userEvent.click(submitButton));

    expect(
      screen.getByText(/Enter the 6-digit code sent to your phone number/)
    ).toBeInTheDocument();
  });

  it("throws validation errors when an incorrectly formatted code was entered", async () => {
    renderPage(ConfirmSMS);

    const codeField = screen.getByLabelText("6-digit code");
    userEvent.type(codeField, "aaaa");
    const submitButton = screen.getByRole("button", {
      name: "Save and continue",
    });
    await act(async () => await userEvent.click(submitButton));

    expect(
      screen.getByText(
        /Enter the 6-digit code sent to your phone number and ensure it does not include any punctuation./
      )
    ).toBeInTheDocument();
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
    expect(tracker.trackEvent).toHaveBeenCalledWith(
      "User confirmed MFA phone number"
    );
    expect(updateUser).toHaveBeenCalledWith(expect.any(String), {
      mfa_delivery_preference: "SMS",
    });
  });

  it("resends the SMS code when user clicks the resend button", async () => {
    renderPage(ConfirmSMS, {});

    const resendButton = screen.getByRole("button", {
      name: "Resend the code",
    });
    await act(async () => await userEvent.click(resendButton));

    expect(tracker.trackEvent).toHaveBeenCalledWith(
      "User resent MFA confirmation code"
    );
    expect(MFAService.sendMFAConfirmationCode).toHaveBeenCalled();
  });

  it("routes the user to the next page when they submit", async () => {
    renderPage(ConfirmSMS, {
      addCustomSetup: (appLogic) => {
        appLogic.users.updateUser = updateUser;
        appLogic.portalFlow.goToNextPage = goToNextPage;
      },
    });

    const codeField = screen.getByLabelText("6-digit code");
    userEvent.type(codeField, "123456");
    const submitButton = screen.getByRole("button", {
      name: "Save and continue",
    });
    await act(async () => await userEvent.click(submitButton));

    expect(goToNextPage).toHaveBeenCalledWith(
      {},
      { smsMfaConfirmed: "true" },
      undefined
    );
  });

  it("returns the user to the settings page if they initiated mfa changes from there", async () => {
    renderPage(
      ConfirmSMS,
      {
        addCustomSetup: (appLogic) => {
          appLogic.users.updateUser = updateUser;
          appLogic.portalFlow.goToNextPage = goToNextPage;
        },
      },
      {
        query: { returnToSettings: "true" },
      }
    );

    const codeField = screen.getByLabelText("6-digit code");
    userEvent.type(codeField, "123456");
    const submitButton = screen.getByRole("button", {
      name: "Save and continue",
    });
    await act(async () => await userEvent.click(submitButton));

    expect(goToNextPage).toHaveBeenCalledWith(
      {},
      { smsMfaConfirmed: "true" },
      "RETURN_TO_SETTINGS"
    );
  });

  it("does not update MFA preference and displays an error when verification code fails", async () => {
    jest
      .spyOn(MFAService, "verifyMFAPhoneNumber")
      .mockRejectedValueOnce(new Error());
    jest.spyOn(console, "error").mockImplementationOnce(jest.fn());

    renderPage(ConfirmSMS, {
      addCustomSetup: (appLogic) => {
        appLogic.users.updateUser = updateUser;
        appLogic.portalFlow.goToNextPage = goToNextPage;
      },
    });

    const codeField = screen.getByLabelText("6-digit code");
    userEvent.type(codeField, "123456");
    const submitButton = screen.getByRole("button", {
      name: "Save and continue",
    });
    await act(async () => await userEvent.click(submitButton));

    expect(MFAService.verifyMFAPhoneNumber).toHaveBeenCalledWith("123456");
    expect(updateUser).not.toHaveBeenCalled();
    expect(goToNextPage).not.toHaveBeenCalled();

    expect(
      screen.getByText(
        /The security code you entered is invalid. Make sure the code matches the security code we texted to you./
      )
    ).toBeInTheDocument();
  });

  it("displays an error when a user attempts the code too many times", async () => {
    jest.spyOn(MFAService, "verifyMFAPhoneNumber").mockRejectedValueOnce({
      code: "LimitExceededException",
      message: "limit exceeded",
    });
    jest.spyOn(console, "error").mockImplementationOnce(jest.fn());

    renderPage(ConfirmSMS, {
      addCustomSetup: (appLogic) => {
        appLogic.users.updateUser = updateUser;
        appLogic.portalFlow.goToNextPage = goToNextPage;
      },
    });

    const codeField = screen.getByLabelText("6-digit code");
    userEvent.type(codeField, "123456");
    const submitButton = screen.getByRole("button", {
      name: "Save and continue",
    });
    await act(async () => await userEvent.click(submitButton));

    expect(MFAService.verifyMFAPhoneNumber).toHaveBeenCalledWith("123456");
    expect(updateUser).not.toHaveBeenCalled();
    expect(goToNextPage).not.toHaveBeenCalled();

    expect(
      screen.getByText(
        /We can't confirm your phone number because of too many failed verification attempts. Wait 15 minutes before trying again./
      )
    ).toBeInTheDocument();
  });

  it("renders PageNotFound if the claimantShowMFA feature flag is not set", () => {
    process.env.featureFlags = JSON.stringify({ claimantShowMFA: false });
    renderPage(ConfirmSMS);

    const pageNotFoundHeading = screen.getByRole("heading", {
      name: /Page not found/,
    });
    expect(pageNotFoundHeading).toBeInTheDocument();
  });
});
