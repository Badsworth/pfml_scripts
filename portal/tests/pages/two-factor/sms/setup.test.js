import { act, screen } from "@testing-library/react";
import { mockAuth, renderPage } from "../../../test-utils";
import SetupSMS from "../../../../src/pages/two-factor/sms/setup";
import userEvent from "@testing-library/user-event";

const updateUser = jest.fn();

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

    expect(updateUser).toHaveBeenCalledWith(expect.any(String), {
      mfa_phone_number: {
        int_code: "1",
        phone_type: "Cell",
        phone_number: "555-555-5555",
      },
    });
  });

  it("renders PageNotFound if the claimantShowMFA feature flag is not set", () => {
    process.env.featureFlags = { claimantShowMFA: false };
    renderPage(SetupSMS);

    const pageNotFoundHeading = screen.getByRole("heading", {
      name: /Page not found/,
    });
    expect(pageNotFoundHeading).toBeInTheDocument();
  });
});
