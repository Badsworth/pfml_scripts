import Cancel from "src/pages/applications/modify/cancel";
import { renderPage } from "../../../test-utils";
import { screen } from "@testing-library/react";

jest.mock("../../../../src/hooks/useAppLogic");

beforeEach(() => {
  process.env.featureFlags = JSON.stringify({
    claimantShowModifications: true,
  });
});

describe("Claim Modification Cancel", () => {
  it("renders page content", () => {
    const { container } = renderPage(Cancel);
    expect(container).toMatchSnapshot();
  });

  it("renders PageNotFound if the claimantShowModifications feature flag is not set", () => {
    process.env.featureFlags = JSON.stringify({
      claimantShowModification: false,
    });
    renderPage(Cancel);

    const pageNotFoundHeading = screen.getByRole("heading", {
      name: /Page not found/,
    });
    expect(pageNotFoundHeading).toBeInTheDocument();
  });
});
