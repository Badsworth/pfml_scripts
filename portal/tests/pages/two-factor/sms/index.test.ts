import { act, screen } from "@testing-library/react";
import { mockAuth, renderPage } from "../../../test-utils";
import IndexSMS from "../../../../src/pages/two-factor/sms/index";
import tracker from "../../../../src/services/tracker";
import userEvent from "@testing-library/user-event";

jest.mock("../../../../src/services/tracker");

beforeEach(() => {
  mockAuth(true);
  process.env.featureFlags = JSON.stringify({ claimantShowMFA: true });
});

const goToPageFor = jest.fn();
const updateUser = jest.fn();

describe("Two-factor SMS Index", () => {
  it("renders landing page content", () => {
    const { container } = renderPage(IndexSMS);
    expect(container.firstChild).toMatchSnapshot();
  });

  it("requires the user to select an option", async () => {
    renderPage(IndexSMS, {
      addCustomSetup: (appLogic) => {
        appLogic.portalFlow.goToPageFor = goToPageFor;
        appLogic.users.updateUser = updateUser;
      },
    });

    const submitButton = screen.getByRole("button", {
      name: "Save and continue",
    });
    await act(async () => await userEvent.click(submitButton));

    // User should not be updated, should still be on the same page
    expect(goToPageFor).not.toHaveBeenCalled();
    expect(updateUser).not.toHaveBeenCalled();
    // Error text should now appear
    expect(
      screen.queryByText(
        /Select Yes if you want to add a phone number for verifying logins./
      )
    ).toBeInTheDocument();
  });

  it("navigates to MFA phone setup page when use selects the enable mfa option", async () => {
    renderPage(IndexSMS, {
      addCustomSetup: (appLogic) => {
        appLogic.portalFlow.goToPageFor = goToPageFor;
        appLogic.users.updateUser = updateUser;
      },
    });

    const enableMFARadio = screen.getByLabelText(
      /Yes, I want to add a phone number for additional security/
    );
    await act(async () => await userEvent.click(enableMFARadio));

    const submitButton = screen.getByRole("button", {
      name: "Save and continue",
    });
    await act(async () => await userEvent.click(submitButton));

    expect(tracker.trackEvent).toHaveBeenCalledWith(
      "User entered MFA setup flow"
    );
    expect(goToPageFor).toHaveBeenCalledWith("EDIT_MFA_PHONE");
    expect(updateUser).not.toHaveBeenCalled();
  });

  it.each([
    // Both of these should opt the user out of MFA:
    [/No, I do not want to add a phone number/, "false"],
    [/I do not have a phone that can receive text messages/, "no_sms_phone"],
  ])(
    "updates user when user clicks disable MFA option",
    async (labelMatch, value) => {
      renderPage(IndexSMS, {
        addCustomSetup: (appLogic) => {
          appLogic.portalFlow.goToPageFor = goToPageFor;
          appLogic.users.updateUser = updateUser;
        },
      });

      const disableMFARadio = screen.getByLabelText(labelMatch);
      await act(async () => await userEvent.click(disableMFARadio));

      const submitButton = screen.getByRole("button", {
        name: "Save and continue",
      });
      await act(async () => await userEvent.click(submitButton));

      expect(tracker.trackEvent).toHaveBeenCalledWith("User opted out of MFA", {
        selectedOption: value,
      });
      expect(goToPageFor).toHaveBeenCalledWith("CONTINUE");
      expect(updateUser).toHaveBeenCalledWith(expect.any(String), {
        mfa_delivery_preference: "Opt Out",
      });
    }
  );

  it("renders PageNotFound if the claimantShowMFA feature flag is not set", () => {
    process.env.featureFlags = JSON.stringify({ claimantShowMFA: false });
    renderPage(IndexSMS);

    const pageNotFoundHeading = screen.getByRole("heading", {
      name: /Page not found/,
    });
    expect(pageNotFoundHeading).toBeInTheDocument();
  });
});
