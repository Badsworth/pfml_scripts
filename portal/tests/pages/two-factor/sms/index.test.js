import { mockAuth, renderPage } from "../../../test-utils";
import IndexSMS from "../../../../src/pages/two-factor/sms/index";
import { screen } from "@testing-library/react";

beforeEach(() => {
  mockAuth(true);
  process.env.featureFlags = { claimantShowMFA: true };
});

describe("Two-factor SMS Index", () => {
  it("renders landing page content", () => {
    const { container } = renderPage(IndexSMS);
    expect(container.firstChild).toMatchSnapshot();
  });

  it("renders PageNotFound if the claimantShowMFA feature flag is not set", () => {
    process.env.featureFlags = { claimantShowMFA: false };
    renderPage(IndexSMS);

    const pageNotFoundHeading = screen.getByRole("heading", {
      name: /Page not found/,
    });
    expect(pageNotFoundHeading).toBeInTheDocument();
  });
});
