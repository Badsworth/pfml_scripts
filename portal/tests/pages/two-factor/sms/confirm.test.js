import { mockAuth, renderPage } from "../../../test-utils";
import ConfirmSMS from "../../../../src/pages/two-factor/sms/confirm";
import { screen } from "@testing-library/react";

beforeEach(() => {
  mockAuth(true);
  process.env.featureFlags = { claimantShowMFA: true };
});

describe("Two-factor SMS Confirm", () => {
  it("renders landing page content", () => {
    const { container } = renderPage(ConfirmSMS);
    expect(container.firstChild).toMatchSnapshot();
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
