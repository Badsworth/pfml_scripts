import { screen, waitFor } from "@testing-library/react";
import ApiResourceCollection from "../../src/models/ApiResourceCollection";
import BenefitsApplication from "../../src/models/BenefitsApplication";
import React from "react";
import { renderPage } from "../test-utils";
import withBenefitsApplications from "../../src/hoc/withBenefitsApplications";

const mockPageContent = "Applications are loaded. This is the page.";

jest.mock("../../src/hooks/useAppLogic");

function setup({ addCustomSetup } = {}, apiParams) {
  const PageComponent = (props) => (
    <div>
      {mockPageContent}
      Page {props.paginationMeta?.page_offset}
      {props.claims.items.map((application) => (
        <div key={application.application_id}>{application.application_id}</div>
      ))}
    </div>
  );
  const WrappedComponent = withBenefitsApplications(PageComponent, apiParams);
  renderPage(WrappedComponent, {
    addCustomSetup,
  });
}

describe("withBenefitsApplications", () => {
  it("shows spinner when loading application state", async () => {
    setup({
      addCustomSetup: (appLogic) => {
        appLogic.benefitsApplications.loadPage = jest.fn();
        appLogic.benefitsApplications.isLoadingClaims = true;
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
        appLogic.benefitsApplications.loadPage = jest.fn();
        spy = jest.spyOn(appLogic.auth, "requireLogin");
      },
    });

    await waitFor(() => {
      expect(spy).toHaveBeenCalled();
    });
  });

  it("renders the page when application state is loaded", async () => {
    const mockClaim = new BenefitsApplication({
      application_id: "mock-application-id",
    });

    setup({
      addCustomSetup: (appLogic) => {
        const claims = new ApiResourceCollection("application_id", [mockClaim]);
        appLogic.benefitsApplications.benefitsApplications = claims;
        appLogic.benefitsApplications.isLoadingClaims = false;
        appLogic.benefitsApplications.loadPage = jest.fn();
      },
    });

    expect(
      await screen.findByText(mockPageContent, { exact: false })
    ).toBeInTheDocument();

    // Assert that the HOC is passing in the applications as a prop to our page component:
    expect(
      await screen.findByText(mockClaim.application_id, { exact: false })
    ).toBeInTheDocument();
  });
});
