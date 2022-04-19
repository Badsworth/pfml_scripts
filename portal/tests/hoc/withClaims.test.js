import { screen, waitFor } from "@testing-library/react";
import ApiResourceCollection from "src/models/ApiResourceCollection";
import Claim from "../../src/models/Claim";
import React from "react";
import { renderPage } from "../test-utils";
import withClaims from "../../src/hoc/withClaims";

const mockPageContent = "Claims are loaded. This is the page.";

jest.mock("../../src/hooks/useAppLogic");

function setup({ addCustomSetup } = {}, apiParams) {
  const PageComponent = (props) => (
    <div>
      {mockPageContent}
      Page {props.paginationMeta.page_offset}
      {props.claims.items.map((claim) => (
        <div key={claim.fineos_absence_id}>{claim.fineos_absence_id}</div>
      ))}
    </div>
  );
  const WrappedComponent = withClaims(PageComponent, apiParams);

  renderPage(WrappedComponent, {
    addCustomSetup,
  });
}

describe("withClaims", () => {
  it("shows spinner when loading application state", async () => {
    setup({
      addCustomSetup: (appLogic) => {
        appLogic.claims.isLoadingClaims = true;
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

  it("renders the page when claims state is loaded", async () => {
    const mockClaim = new Claim({
      fineos_absence_id: "mock-fineos-id",
    });
    const mockPaginationMeta = { page_offset: 2 };

    setup({
      addCustomSetup: (appLogic) => {
        const claimsCollection = new ApiResourceCollection(
          "fineos_absence_id",
          [mockClaim]
        );
        appLogic.claims.claims = claimsCollection;
        appLogic.claims.paginationMeta = mockPaginationMeta;
        appLogic.claims.isLoadingClaims = false;
      },
    });

    expect(
      await screen.findByText(mockPageContent, { exact: false })
    ).toBeInTheDocument();

    // Assert that the HOC is passing in the claims and pagination data as props to our page component:
    expect(
      await screen.findByText(mockClaim.fineos_absence_id, { exact: false })
    ).toBeInTheDocument();
    expect(
      await screen.findByText(`Page ${mockPaginationMeta.page_offset}`, {
        exact: false,
      })
    ).toBeInTheDocument();
  });

  it("makes request with pagination, order, and filters params", () => {
    let spy;
    const apiParams = {
      page_offset: "2",
      employer_id: "mock-employer-id",
      is_reviewable: "yes",
      order_by: "employee",
      order_direction: "descending",
      request_decision: "approved",
      search: "foo",
    };

    setup(
      {
        addCustomSetup: (appLogic) => {
          spy = jest.spyOn(appLogic.claims, "loadPage");
        },
      },
      apiParams
    );

    expect(spy).toHaveBeenLastCalledWith({
      page_offset: "2",
      employer_id: "mock-employer-id",
      is_reviewable: "yes",
      order_by: "employee",
      order_direction: "descending",
      request_decision: "approved",
      search: "foo",
    });
  });

  it("makes request without the invalid order_by value", () => {
    let spy;
    const apiParams = {
      page_offset: "1",
      order_by: "invalid_param",
    };

    setup(
      {
        addCustomSetup: (appLogic) => {
          spy = jest.spyOn(appLogic.claims, "loadPage");
        },
      },
      apiParams
    );

    expect(spy).toHaveBeenLastCalledWith({
      page_offset: "1",
    });
  });
});
