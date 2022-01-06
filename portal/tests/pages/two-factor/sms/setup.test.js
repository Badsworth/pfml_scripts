import { act, screen } from "@testing-library/react";
import { mockAuth, renderPage } from "../../../test-utils";
import SetupSMS from "../../../../src/pages/two-factor/sms/setup";
import userEvent from "@testing-library/user-event";

const updateUser = jest.fn();
const goToPageFor = jest.fn();

beforeEach(() => {
  mockAuth(true);
  process.env.featureFlags = { claimantShowMFA: true };
});

describe("Two-factor SMS Setup", () => {
  it("renders landing page content", () => {
    const { container } = renderPage(SetupSMS);
    expect(container.firstChild).toMatchSnapshot();
  });

  it("updates phone number when user saves and continues", async () => {
    renderPage(SetupSMS, {
      addCustomSetup: (appLogic) => {
        appLogic.users.updateUser = updateUser;
      },
    });

    const phoneNumberField = screen.getByLabelText(/Phone number/);
    userEvent.type(phoneNumberField, "555-555-5555");

    const submitButton = screen.getByRole("button", {
      name: "Save and continue",
    });

    await act(async () => await userEvent.click(submitButton));

    expect(updateUser).toHaveBeenCalledWith(
      expect.any(String),
      {
        mfa_phone_number: {
          int_code: "1",
          phone_type: "Cell",
          phone_number: "555-555-5555",
        },
      },
      undefined,
      undefined
    );
  });

  it("passes the returnToSettings query param to the next page if it is set", async () => {
    renderPage(
      SetupSMS,
      {
        addCustomSetup: (appLogic) => {
          appLogic.users.updateUser = updateUser;
        },
      },
      {
        query: { returnToSettings: "true" },
      }
    );

    const phoneNumberField = screen.getByLabelText(/Phone number/);
    userEvent.type(phoneNumberField, "555-555-5555");

    const submitButton = screen.getByRole("button", {
      name: "Save and continue",
    });

    await act(async () => await userEvent.click(submitButton));

    expect(updateUser).toHaveBeenCalledWith(
      expect.any(String),
      {
        mfa_phone_number: {
          int_code: "1",
          phone_type: "Cell",
          phone_number: "555-555-5555",
        },
      },
      undefined,
      { returnToSettings: "true" }
    );
  });

  it("renders PageNotFound if the claimantShowMFA feature flag is not set", () => {
    process.env.featureFlags = { claimantShowMFA: false };
    renderPage(SetupSMS);

    const pageNotFoundHeading = screen.getByRole("heading", {
      name: /Page not found/,
    });
    expect(pageNotFoundHeading).toBeInTheDocument();
  });

  // TODO: These errors will never happen because they're provided by the backend
  it("shows appropriate error when no phone number entered", async () => {
    renderPage(SetupSMS, {
      addCustomSetup: (appLogic) => {
        appLogic.portalFlow.goToPageFor = goToPageFor;
        appLogic.users.updateUser = updateUser;
      },
    });

    // Click submit without typing anything into the phone number field
    const submitButton = screen.getByRole("button", {
      name: "Save and continue",
    });
    await act(async () => await userEvent.click(submitButton));

    // User should not be updated, should still be on the same page
    expect(goToPageFor).not.toHaveBeenCalled();
    expect(updateUser).not.toHaveBeenCalled();
    // The phone number format error is displayed
    const error_text = "Enter a phone number";
    expect(screen.queryByText(error_text)).toBeInTheDocument();
  });

  // TODO: These errors will never happen because they're provided by the backend
  it("shows appropriate error when wrong number of digits entered", async () => {
    renderPage(SetupSMS, {
      addCustomSetup: (appLogic) => {
        appLogic.portalFlow.goToPageFor = goToPageFor;
        appLogic.users.updateUser = updateUser;
      },
    });

    // Correct phone numbers have 10 digits, enter a number with 9 digits
    const phoneNumberField = screen.getByLabelText(/Phone number/);
    userEvent.type(phoneNumberField, "802-573-222");

    // Click submit
    const submitButton = screen.getByRole("button", {
      name: "Save and continue",
    });
    await act(async () => await userEvent.click(submitButton));

    // User should not be updated, should still be on the same page
    expect(goToPageFor).not.toHaveBeenCalled();
    expect(updateUser).not.toHaveBeenCalled();
    // The phone number format error is displayed
    const error_text = "Enter a valid phone number";
    expect(screen.queryByText(error_text)).toBeInTheDocument();
  });

  // TODO: These errors will never happen because they're provided by the backend
  it("shows appropriate error when international number entered", async () => {
    renderPage(SetupSMS, {
      addCustomSetup: (appLogic) => {
        appLogic.portalFlow.goToPageFor = goToPageFor;
        appLogic.users.updateUser = updateUser;
      },
    });

    // Enter an international number starting with [+countrycode]
    const phoneNumberField = screen.getByLabelText(/Phone number/);
    userEvent.type(phoneNumberField, "+61 1300 133 655");

    // Click submit
    const submitButton = screen.getByRole("button", {
      name: "Save and continue",
    });
    await act(async () => await userEvent.click(submitButton));

    // User should not be updated, should still be on the same page
    expect(goToPageFor).not.toHaveBeenCalled();
    expect(updateUser).not.toHaveBeenCalled();
    // The phone number format error is displayed
    const error_text =
      "Sorry, we don't support international phone numbers yet. Enter a U.S. phone number to set up additional login verifications.";
    expect(screen.queryByText(error_text)).toBeInTheDocument();
  });
});
