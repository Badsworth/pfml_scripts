import {
  MockBenefitsApplicationBuilder,
  renderPage,
} from "../../../test-utils";
import ApiResourceCollection from "src/models/ApiResourceCollection";
import BenefitsApplication from "src/models/BenefitsApplication";
import Success from "src/pages/applications/modify/success";
import { screen } from "@testing-library/react";

jest.mock("../../../../src/hooks/useAppLogic");

const props = {
  query: { claim_id: "7180eae0-0ad8-46a9-b140-5076863330d2" },
};

beforeEach(() => {
  process.env.featureFlags = JSON.stringify({
    claimantShowModifications: true,
  });
});

describe("Claim Modification Success", () => {
  it("renders page content", () => {
    const { container } = renderPage(
      Success,
      {
        addCustomSetup: (appLogicHook) => {
          appLogicHook.benefitsApplications.benefitsApplications =
            new ApiResourceCollection<BenefitsApplication>("application_id", [
              new MockBenefitsApplicationBuilder().create(),
            ]);
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
      Success,
      {
        addCustomSetup: (appLogicHook) => {
          appLogicHook.benefitsApplications.benefitsApplications =
            new ApiResourceCollection<BenefitsApplication>("application_id", [
              new MockBenefitsApplicationBuilder().create(),
            ]);
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
