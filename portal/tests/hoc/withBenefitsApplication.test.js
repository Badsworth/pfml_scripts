import { screen, waitFor } from "@testing-library/react";
import ApiResourceCollection from "../../src/models/ApiResourceCollection";
import BenefitsApplication from "../../src/models/BenefitsApplication";
import React from "react";
import { renderPage } from "../test-utils";
import routes from "../../src/routes";
import withBenefitsApplication from "../../src/hoc/withBenefitsApplication";

const mockApplicationId = "mock-application-id";
const mockPageContent = "Application is loaded. This is the page.";

jest.mock("../../src/hooks/useAppLogic");

function setup({ addCustomSetup, query } = {}) {
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
        ...query,
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

  it("shows Page Not Found when application ID isn't found", () => {
    setup({
      query: {
        claim_id: "",
      },
    });

    expect(
      screen.getByRole("heading", { name: "Page not found" })
    ).toBeInTheDocument();
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
          new ApiResourceCollection("application_id", [mockClaim]);
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

  it("redirects to index if the claim is completed and it's on the checklist or review page", () => {
    let spy;
    const completedClaim = new BenefitsApplication({
      status: "Completed",
      application_id: mockApplicationId,
    });

    setup({
      addCustomSetup: (appLogic) => {
        spy = jest.spyOn(appLogic.portalFlow, "goTo");
        appLogic.portalFlow.pathname = routes.applications.checklist;

        appLogic.benefitsApplications.benefitsApplications =
          new ApiResourceCollection("application_id", [completedClaim]);
      },
      query: { claim_id: mockApplicationId },
    });

    expect(spy).toHaveBeenCalled();

    setup({
      addCustomSetup: (appLogic) => {
        spy = jest.spyOn(appLogic.portalFlow, "goTo");
        appLogic.portalFlow.pathname = routes.applications.review;

        appLogic.benefitsApplications.benefitsApplications =
          new ApiResourceCollection("application_id", [completedClaim]);
      },
      query: { claim_id: mockApplicationId },
    });

    expect(spy).toHaveBeenCalled();
  });

  it("does not redirect to index if the claim is completed and it's not on the checklist or review page", () => {
    let spy;
    const completedClaim = new BenefitsApplication({
      status: "Completed",
      application_id: mockApplicationId,
    });

    setup({
      addCustomSetup: (appLogic) => {
        spy = jest.spyOn(appLogic.portalFlow, "goTo");
        appLogic.portalFlow.pathname = routes.applications.success;

        appLogic.benefitsApplications.benefitsApplications =
          new ApiResourceCollection("application_id", [completedClaim]);
      },
      query: { claim_id: mockApplicationId },
    });

    expect(spy).not.toHaveBeenCalled();
  });
});
