import * as MFAService from "../../../../src/services/mfa";
import { act, screen } from "@testing-library/react";
import { mockAuth, renderPage } from "../../../test-utils";
import ConfirmSMS from "../../../../src/pages/two-factor/sms/confirm";
import User from "../../../../src/models/User";
import faker from "faker";
import userEvent from "@testing-library/user-event";

const updateUser = jest.fn();
jest.mock("../../../../src/services/mfa", () => ({
  verifyMFAPhoneNumber: jest.fn(),
}));

const user = new User({
  auth_id: faker.datatype.uuid(),
  consented_to_data_sharing: true,
  email_address: faker.internet.email(),
  mfa_phone_number: {
    phone_number: "***-***-1234",
  },
});

beforeEach(() => {
  mockAuth(true);
  process.env.featureFlags = { claimantShowMFA: true };
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
    expect(updateUser).toHaveBeenCalledWith(
      expect.any(String),
      {
        mfa_delivery_preference: "SMS",
      },
      undefined,
      undefined,
      undefined
    );
  });

  it("returns the user to the settings page if they reached they initiated mfa changes from there", async () => {
    renderPage(
      ConfirmSMS,
      {
        addCustomSetup: (appLogic) => {
          appLogic.users.updateUser = updateUser;
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

    expect(updateUser).toHaveBeenCalledWith(
      expect.any(String),
      {
        mfa_delivery_preference: "SMS",
      },
      undefined,
      undefined,
      "RETURN_TO_SETTINGS"
    );
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
