import { screen, waitFor } from "@testing-library/react";
import ApiResourceCollection from "../../src/models/ApiResourceCollection";
import ChangeRequest from "../../src/models/ChangeRequest";
import React from "react";
import { renderPage } from "../test-utils";
import withChangeRequests from "../../src/hoc/withChangeRequests";

const mockAbsenceId = "mock-absence-id";
const mockPageContent = "Change request is loaded. This is the page.";

jest.mock("../../src/hooks/useAppLogic");

function setup({ addCustomSetup, query } = {}) {
  const PageComponent = (props) => (
    <div>
      {mockPageContent}
      Change requests:{" "}
      {props.change_requests.items.map((cr) => cr.change_request_id).join(",")}
    </div>
  );
  const WrappedComponent = withChangeRequests(PageComponent);

  renderPage(
    WrappedComponent,
    {
      addCustomSetup,
    },
    {
      query: {
        absence_id: mockAbsenceId,
        ...(query || {}),
      },
    }
  );
}

describe(withChangeRequests, () => {
  it("shows spinner when loading change request state", async () => {
    setup({
      addCustomSetup: (appLogic) => {
        appLogic.changeRequests.isLoadingChangeRequests = true;
      },
    });

    expect(await screen.findByRole("progressbar")).toBeInTheDocument();
  });

  it("shows Page Not Found when absence id isn't found", () => {
    setup({ query: { absence_id: "" } });

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

  it("renders the page when change requests state is loaded", async () => {
    const mockChangeRequest1 = new ChangeRequest({
      change_request_id: "id-1",
      fineos_absence_id: mockAbsenceId,
    });
    const mockChangeRequest2 = new ChangeRequest({
      change_request_id: "id-2",
      fineos_absence_id: mockAbsenceId,
    });
    setup({
      addCustomSetup: (appLogic) => {
        appLogic.changeRequests.changeRequests = new ApiResourceCollection(
          "change_request_id",
          [mockChangeRequest1, mockChangeRequest2]
        );
      },
    });

    expect(
      await screen.findByText(mockPageContent, { exact: false })
    ).toBeInTheDocument();

    expect(
      await screen.findByText(mockChangeRequest1.change_request_id, {
        exact: false,
      })
    ).toBeInTheDocument();
    expect(
      await screen.findByText(mockChangeRequest2.change_request_id, {
        exact: false,
      })
    ).toBeInTheDocument();
  });
});
