import ApiResourceCollection from "src/models/ApiResourceCollection";
import BenefitsApplication from "src/models/BenefitsApplication";
import Review from "src/pages/applications/modify/cancel";
import { renderPage } from "../../../test-utils";
import { screen } from "@testing-library/react";

jest.mock("../../../../src/hooks/useAppLogic");

const props = {
  query: { change_request_id: "7180eae0-0ad8-46a9-b140-5076863330d2" },
};

beforeEach(() => {
  process.env.featureFlags = JSON.stringify({
    claimantShowModifications: true,
  });
});

describe("Claim Modification Review", () => {
  it("renders page content", () => {
    const { container } = renderPage(
      Review,
      {
        addCustomSetup: (appLogicHook) => {
          appLogicHook.benefitsApplications.benefitsApplications =
            new ApiResourceCollection<BenefitsApplication>(
              "application_id",
              []
            );
        },
      },
      props
    );
    expect(container.firstChild).toMatchSnapshot();
  });

  it("renders PageNotFound if the claimantShowModifications feature flag is not set", () => {
    process.env.featureFlags = JSON.stringify({
      claimantShowModification: false,
    });
    renderPage(
      Review,
      {
        addCustomSetup: (appLogicHook) => {
          appLogicHook.benefitsApplications.benefitsApplications =
            new ApiResourceCollection<BenefitsApplication>(
              "application_id",
              []
            );
        },
      },
      props
    );

    const pageNotFoundHeading = screen.getByRole("heading", {
      name: /Page not found/,
    });
    expect(pageNotFoundHeading).toBeInTheDocument();
  });
});
