import { act, screen } from "@testing-library/react";
import { mockAuth, renderPage } from "../../../test-utils";
import VerifySMS from "../../../../src/pages/two-factor/sms/verify";
import userEvent from "@testing-library/user-event";

jest.mock("../../../../src/services/tracker");

beforeEach(() => {
  mockAuth(true);
  process.env.featureFlags = { claimantShowMFA: true };
});

describe("Two-factor SMS Verify", () => {
  it("renders landing page content", () => {
    const { container } = renderPage(VerifySMS);
    expect(container.firstChild).toMatchSnapshot();
  });

  it("renders PageNotFound if the claimantShowMFA feature flag is not set", () => {
    process.env.featureFlags = { claimantShowMFA: false };
    renderPage(VerifySMS);

    const pageNotFoundHeading = screen.getByRole("heading", {
      name: /Page not found/,
    });
    expect(pageNotFoundHeading).toBeInTheDocument();
  });

  it("sends verification code and updates MFA preference when user saves and continues", async () => {
    const mockVerify = jest.fn();
    renderPage(
      VerifySMS,
      {
        addCustomSetup: (appLogic) => {
          appLogic.auth.verifyMFACodeAndLogin = mockVerify;
        },
      },
      { query: { next: "next" } }
    );

    const codeField = screen.getByLabelText("6-digit code");
    userEvent.type(codeField, "123456");
    const submitButton = screen.getByRole("button", {
      name: "Submit",
    });
    await act(async () => await userEvent.click(submitButton));

    expect(mockVerify).toHaveBeenCalledWith("123456", "next");
  });
});
