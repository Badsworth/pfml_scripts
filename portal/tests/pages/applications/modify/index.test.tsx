import Index from "../../../../src/pages/applications/modify/index";
import { renderPage } from "../../../test-utils";
import { screen } from "@testing-library/react";

jest.mock("../../../../src/hooks/useAppLogic");

const props = {
  query: { absence_id: "7180eae0-0ad8-46a9-b140-5076863330d2" },
};

beforeEach(() => {
  process.env.featureFlags = JSON.stringify({
    claimantShowModifications: true,
  });
});

describe("Claim Modification Index", () => {
  it("renders page content", () => {
    const { container } = renderPage(Index, {}, props);
    expect(container).toMatchSnapshot();
  });

  it("renders PageNotFound if the claimantShowModifications feature flag is not set", () => {
    process.env.featureFlags = JSON.stringify({
      claimantShowModification: false,
    });
    renderPage(Index, {}, props);

    const pageNotFoundHeading = screen.getByRole("heading", {
      name: /Page not found/,
    });
    expect(pageNotFoundHeading).toBeInTheDocument();
  });
});
