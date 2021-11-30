import { mockAuth, renderPage } from "../../../test-utils";
import SetupSMS from "../../../../src/pages/two-factor/sms/setup";
import { screen } from "@testing-library/react";

beforeEach(() => {
  mockAuth(true);
  process.env.featureFlags = { claimantShowMFA: true };
});

describe("Two-factor SMS Setup", () => {
  it("renders landing page content", () => {
    const { container } = renderPage(SetupSMS);
    expect(container.firstChild).toMatchSnapshot();
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
