import { mockAuth, renderPage } from "../../../test-utils";
import VerifySMS from "../../../../src/pages/two-factor/sms/verify";
import { screen } from "@testing-library/react";

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
});
