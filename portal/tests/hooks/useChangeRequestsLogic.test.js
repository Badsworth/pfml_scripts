import { act, renderHook } from "@testing-library/react-hooks";
import { mockAuth, mockFetch } from "../test-utils";
import { ValidationError } from "../../src/errors";
import useChangeRequestsLogic from "../../src/hooks/useChangeRequestsLogic";
import useErrorsLogic from "../../src/hooks/useErrorsLogic";
import usePortalFlow from "../../src/hooks/usePortalFlow";

jest.mock("../../src/services/tracker");

function mockChangeRequestFetch(mockResponseData = [], warnings) {
  mockFetch({
    response: {
      data: mockResponseData,
      warnings,
    },
  });
}

let changeRequestsLogic, errorsLogic, portalFlow;
function setup() {
  const { waitFor } = renderHook(() => {
    portalFlow = usePortalFlow();
    errorsLogic = useErrorsLogic({ portalFlow });
    changeRequestsLogic = useChangeRequestsLogic({ errorsLogic, portalFlow });
  });

  return { waitFor };
}

mockAuth();

describe(useChangeRequestsLogic, () => {
  it("sets initial change request data to empty collection", () => {
    setup();

    expect(changeRequestsLogic.changeRequests).toMatchInlineSnapshot(`
      ApiResourceCollection {
        "idKey": "change_request_id",
        "map": Map {},
      }
    `);
  });

  describe("loadAll", () => {
    let waitFor;
    beforeEach(() => {
      mockChangeRequestFetch([
        { change_request_id: "id-1" },
        { change_request_id: "id-2" },
      ]);
      ({ waitFor } = setup());
    });

    it("sends API request", async () => {
      await act(async () => {
        await changeRequestsLogic.loadAll("fineos-absence-id");
      });

      expect(global.fetch).toHaveBeenCalledWith(
        `${process.env.apiUrl}/change-request?fineos_absence_id=fineos-absence-id`,
        expect.objectContaining({ method: "GET" })
      );
    });

    it("sets change requests", async () => {
      await act(async () => {
        await changeRequestsLogic.loadAll("fineos-absence-id");
      });

      expect(
        changeRequestsLogic.changeRequests.items.map(
          (cr) => cr.change_request_id
        )
      ).toEqual(["id-1", "id-2"]);
    });

    it("sets isLoadingChangeRequests to true when a page is being loaded", async () => {
      expect(changeRequestsLogic.isLoadingChangeRequests).toBeUndefined();

      await act(async () => {
        changeRequestsLogic.loadAll("fineos-absence-id");

        await waitFor(() => {
          expect(changeRequestsLogic.isLoadingChangeRequests).toBe(true);
        });
      });

      expect(changeRequestsLogic.isLoadingChangeRequests).toBe(false);
    });

    it("sets hasLoadedChangeRequests to true", async () => {
      expect(changeRequestsLogic.hasLoadedChangeRequests).toBeUndefined();

      await act(
        async () => await changeRequestsLogic.loadAll("fineos-absence-id")
      );

      expect(changeRequestsLogic.hasLoadedChangeRequests).toBe(true);
    });

    it("does not load if already loaded", async () => {
      await act(async () => {
        await changeRequestsLogic.loadAll("fineos-absence-id");
        await changeRequestsLogic.loadAll("fineos-absence-id");
      });

      expect(global.fetch).toHaveBeenCalledTimes(1);
    });

    it("does not load while loading", async () => {
      await act(async () => {
        changeRequestsLogic.loadAll("fineos-absence-id");

        await waitFor(() => {
          expect(changeRequestsLogic.isLoadingChangeRequests).toBe(true);
          changeRequestsLogic.loadAll("fineos-absence-id");
        });
      });

      expect(global.fetch).toHaveBeenCalledTimes(1);
    });
  });

  describe("create", () => {
    beforeEach(() => {
      setup();
      mockChangeRequestFetch({ change_request_id: "id-1" });
    });

    it("sends API request", async () => {
      await act(
        async () => await changeRequestsLogic.create("fineos-absence-id")
      );
      expect(global.fetch).toHaveBeenCalledWith(
        `${process.env.apiUrl}/change-request/?fineos_absence_id=fineos-absence-id`,
        expect.objectContaining({ method: "POST" })
      );
    });

    it("sets hasLoadedChangeRequests to false", async () => {
      expect(changeRequestsLogic.hasLoadedChangeRequests).toBeUndefined();
      await act(
        async () => await changeRequestsLogic.create("fineos-absence-id")
      );
      expect(changeRequestsLogic.hasLoadedChangeRequests).toBe(false);
    });
  });

  describe("destroy", () => {
    beforeEach(async () => {
      setup();
      mockChangeRequestFetch([
        { change_request_id: "id-1" },
        { change_request_id: "id-2" },
      ]);
      await act(
        async () => await changeRequestsLogic.loadAll("fineos-absence-id")
      );
      mockChangeRequestFetch({ change_request_id: "id-1" });
      await act(async () => await changeRequestsLogic.destroy("id-1"));
    });

    it("sends API request", () => {
      expect(global.fetch).toHaveBeenCalledWith(
        `${process.env.apiUrl}/change-request/id-1`,
        expect.objectContaining({ method: "DELETE" })
      );
    });

    it("removes change request from collection", () => {
      expect(
        changeRequestsLogic.changeRequests.items.map(
          (cr) => cr.change_request_id
        )
      ).toEqual(["id-2"]);
    });
  });

  describe("update", () => {
    const patchData = {
      startDate: "2022-12-31",
    };

    beforeEach(async () => {
      setup();
      mockChangeRequestFetch({
        change_request_id: "change-request-id",
        ...patchData,
      });
      await act(async () => {
        await changeRequestsLogic.update("change-request-id", patchData);
      });
    });

    it("sends API request", () => {
      expect(global.fetch).toHaveBeenCalledWith(
        `${process.env.apiUrl}/change-request/change-request-id`,
        expect.objectContaining({ method: "PATCH" })
      );
    });

    it("sets change request", () => {
      expect(changeRequestsLogic.changeRequests.getItem("change-request-id"))
        .toMatchInlineSnapshot(`
        ChangeRequest {
          "change_request_id": "change-request-id",
          "change_request_type": null,
          "documents_submitted_at": null,
          "end_date": null,
          "fineos_absence_id": undefined,
          "startDate": "2022-12-31",
          "start_date": null,
          "submitted_time": null,
        }
      `);
    });

    describe("when warnings are returned", () => {
      it("raises ValidationError", async () => {
        // ValidationErrors are filtered by page depending on
        // what fields are on that page. We need to mock portalFlow
        // with a page context so we can test that ValidationErrors
        // are returned correctly.
        const fieldName = "start_date";
        portalFlow.page = { meta: { fields: [fieldName] } };

        mockChangeRequestFetch(
          {
            change_request_id: "change-request-id",
          },
          [{ field: fieldName, type: "invalid" }]
        );
        const catchErrorSpy = jest.spyOn(errorsLogic, "catchError");
        await act(async () => {
          await changeRequestsLogic.update("change-request-id", {});
        });
        expect(catchErrorSpy).toHaveBeenCalledWith(expect.any(ValidationError));
      });
    });
  });

  describe("submit", () => {
    beforeEach(async () => {
      setup();
      mockChangeRequestFetch({ change_request_id: "change-request-id" });
      await act(async () => {
        await changeRequestsLogic.submit("change-request-id");
      });
    });

    it("sends API request", () => {
      expect(global.fetch).toHaveBeenCalledWith(
        `${process.env.apiUrl}/change-request/change-request-id/submit`,
        expect.objectContaining({ method: "POST" })
      );
    });

    it("sets change request", () => {
      expect(changeRequestsLogic.changeRequests.getItem("change-request-id"))
        .toMatchInlineSnapshot(`
        ChangeRequest {
          "change_request_id": "change-request-id",
          "change_request_type": null,
          "documents_submitted_at": null,
          "end_date": null,
          "fineos_absence_id": undefined,
          "start_date": null,
          "submitted_time": null,
        }
      `);
    });
  });
});
