import {
  MockBenefitsApplicationBuilder,
  renderPage,
} from "../../../test-utils";
import BenefitsApplication from "src/models/BenefitsApplication";
import Success from "src/pages/applications/modify/success";
import { screen } from "@testing-library/react";
import { setupBenefitsApplications } from "../../../test-utils/helpers";

const setup = ({ claim }: { claim: BenefitsApplication }) => {
  return renderPage(
    Success,
    {
      addCustomSetup: (appLogic) => {
        setupBenefitsApplications(appLogic, [claim]);
      },
    },
    { query: { claim_id: "mock_application_id" } }
  );
};

beforeEach(() => {
  process.env.featureFlags = JSON.stringify({
    claimantShowModifications: true,
  });
});

describe("Claim Modification Success", () => {
  it("renders page content", () => {
    const claim = new MockBenefitsApplicationBuilder().create();
    const { container } = setup({ claim });

    expect(container).toMatchSnapshot();
  });

  it("renders PageNotFound if the claimantShowModifications feature flag is not set", () => {
    process.env.featureFlags = JSON.stringify({
      claimantShowModification: false,
    });
    const claim = new MockBenefitsApplicationBuilder().create();
    setup({ claim });

    const pageNotFoundHeading = screen.getByRole("heading", {
      name: /Page not found/,
    });
    expect(pageNotFoundHeading).toBeInTheDocument();
  });
});
