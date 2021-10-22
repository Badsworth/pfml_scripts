import { screen, waitFor } from "@testing-library/react";
import BenefitsApplication from "../../src/models/BenefitsApplication";
import BenefitsApplicationCollection from "../../src/models/BenefitsApplicationCollection";
import React from "react";
import { renderPage } from "../test-utils";
import withBenefitsApplication from "../../src/hoc/withBenefitsApplication";

const mockApplicationId = "mock-application-id";
const mockPageContent = "Application is loaded. This is the page.";

jest.mock("../../src/hooks/useAppLogic");

function setup({ addCustomSetup } = {}) {
  const PageComponent = (props) => (
    <div>
      {mockPageContent}
      Application: {props.claim?.application_id}
    </div>
  );
  const WrappedComponent = withBenefitsApplication(PageComponent);

  renderPage(
    WrappedComponent,
    {
      addCustomSetup,
    },
    {
      query: {
        claim_id: mockApplicationId,
      },
    }
  );
}

describe("withBenefitsApplication", () => {
  it("shows spinner when loading application state", async () => {
    setup({
      addCustomSetup: (appLogic) => {
        jest
          .spyOn(
            appLogic.benefitsApplications,
            "hasLoadedBenefitsApplicationAndWarnings"
          )
          .mockReturnValue(false);
      },
    });

    expect(await screen.findByRole("progressbar")).toBeInTheDocument();
  });

  it("requires user to be logged in", async () => {
    let spy;

    setup({
      addCustomSetup: (appLogic) => {
        spy = jest.spyOn(appLogic.auth, "requireLogin");
      },
    });

    await waitFor(() => {
      expect(spy).toHaveBeenCalled();
    });
  });

  it("renders the page when application state is loaded", async () => {
    const mockClaim = new BenefitsApplication({
      application_id: mockApplicationId,
    });
    setup({
      addCustomSetup: (appLogic) => {
        jest
          .spyOn(
            appLogic.benefitsApplications,
            "hasLoadedBenefitsApplicationAndWarnings"
          )
          .mockReturnValue(true);

        appLogic.benefitsApplications.benefitsApplications =
          new BenefitsApplicationCollection([mockClaim]);
      },
    });

    expect(
      await screen.findByText(mockPageContent, { exact: false })
    ).toBeInTheDocument();

    // Assert that the HOC is passing in the application as a prop to our page component:
    expect(
      await screen.findByText(mockClaim.application_id, { exact: false })
    ).toBeInTheDocument();
  });
});
