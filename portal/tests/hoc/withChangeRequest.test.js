import { screen, waitFor } from "@testing-library/react";
import ApiResourceCollection from "../../src/models/ApiResourceCollection";
import ChangeRequest from "../../src/models/ChangeRequest";
import React from "react";
import { renderPage } from "../test-utils";
import withChangeRequest from "../../src/hoc/withChangeRequest";

const mockAbsenceId = "mock-absence-id";
const mockChangeRequestId = "mock-change-request-id";
const mockPageContent = "Change request is loaded. This is the page.";

jest.mock("../../src/hooks/useAppLogic");

function setup({ addCustomSetup, query } = {}) {
  const PageComponent = (props) => (
    <div>
      {mockPageContent}
      Change request: {props.change_request?.change_request_id}
    </div>
  );
  const WrappedComponent = withChangeRequest(PageComponent);

  renderPage(
    WrappedComponent,
    {
      addCustomSetup,
    },
    {
      query: {
        absence_id: mockAbsenceId,
        ...query,
      },
    }
  );
}

describe(withChangeRequest, () => {
  it("shows spinner when loading change request state", async () => {
    setup({
      addCustomSetup: (appLogic) => {
        appLogic.changeRequests.isLoadingChangeRequests = true;
      },
      query: {
        change_request_id: "",
      },
    });

    expect(await screen.findByRole("progressbar")).toBeInTheDocument();
  });

  it("shows Page Not Found when change request id isn't found", () => {
    setup({
      addCustomSetup: (appLogic) => {
        appLogic.changeRequests.changeRequests = new ApiResourceCollection(
          "change_request_id",
          []
        );
      },
      query: {
        change_request_id: "",
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
        appLogic.changeRequests.changeRequests = new ApiResourceCollection(
          "change_request_id",
          []
        );
        spy = jest.spyOn(appLogic.auth, "requireLogin");
      },
    });

    await waitFor(() => {
      expect(spy).toHaveBeenCalled();
    });
  });

  it("renders the page when change request state is loaded", async () => {
    const mockChangeRequest = new ChangeRequest({
      change_request_id: mockChangeRequestId,
    });
    setup({
      addCustomSetup: (appLogic) => {
        appLogic.changeRequests.changeRequests = new ApiResourceCollection(
          "change_request_id",
          [mockChangeRequest]
        );
      },
      query: {
        change_request_id: mockChangeRequestId,
      },
    });

    expect(
      await screen.findByText(mockPageContent, { exact: false })
    ).toBeInTheDocument();

    expect(
      await screen.findByText(mockChangeRequest.change_request_id, {
        exact: false,
      })
    ).toBeInTheDocument();
  });
});
