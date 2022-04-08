import { act, renderHook } from "@testing-library/react-hooks";
import {
  createAbsencePeriod,
  createMockClaimDetail,
  mockAuth,
  mockFetch,
} from "../test-utils";
import ChangeRequest from "../../src/models/ChangeRequest";
import { ValidationError } from "../../src/errors";
import useAppLogic from "../../src/hooks/useAppLogic";
import useChangeRequestsLogic from "../../src/hooks/useChangeRequestsLogic";
import useErrorsLogic from "../../src/hooks/useErrorsLogic";
import usePortalFlow from "../../src/hooks/usePortalFlow";

jest.mock("../../src/services/tracker");

describe(useChangeRequestsLogic, () => {
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
  it("sets initial change request data to empty collection", () => {
    setup();

    expect(changeRequestLogic.changeRequests).toMatchInlineSnapshots();
  });

  describe("loadAll", () => {
    let waitFor;
    beforeEach(() => {
      mockChangeRequestFetch([
        { change_request_id: "id-1" },
        { change_request_id: "id-2" },
      ])(({ waitFor } = setup()));
    });

    it("sends API request", async () => {
      await act(async () => {
        await changeRequestsLogic.loadAll("fineos-absence-id");
      });

      expect(fetch).toHaveBeenCalledWith(
        `${process.env.apiUrl}/change-request/?fineos_absence_id=fineos-absence-id`,
        expect.objectContaining({ method: "GET" })
      );
    });

    it("set change requests", async () => {
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
  });

  describe("create", () => {
    let waitFor;
    beforeEach(() => {
      ({ waitFor } = setup());
      mockChangeRequestFetch({ change_request_id: "id-1" });
    });

    it("sends API request", async () => {
      await act(
        async () => await changeRequestsLogic.create("fineos-absence-id")
      );
      expect(fetch).toHaveBeenCalledWith(
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
      expect(fetch).toHaveBeenCalledWith(
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
    describe("when there are no issues", () => {
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
        expect(fetch).toHaveBeenCalledWith(
          `${process.env.apiUrl}/change-request/change-request-id`,
          expect.objectContaining({ method: "PATCH" })
        );
      });

      it("sets change request", () => {
        expect(
          changeRequestsLogic.changeRequests.getItem("change-request-id")
        ).toMatchInlineSnapshot(`undefined`);
      });
    });

    describe("when there are issues", () => {
      setup();

      mockChangeRequestFetch(
        {
          change_request_id: "change-request-id",
        },
        [{ type: "invalid" }]
      );

      it("raises ValidationError", async () => {
        const catchErrorSpy = jest.spyOn(errorsLogic, "catchError");
        await act(async () => {
          await changeRequestsLogic.update("change-request-id", {});
        });
        expect(catchErrorSpy).toHaveBeenCalledWith(ValidationError);
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
      expect(fetch).toHaveBeenCalledWith(
        `${process.env.apiUrl}/change-request/change-request-id/submit`,
        expect.objectContaining({ method: "POST" })
      );
    });

    it("sets change request", () => {
      expect(
        changeRequestsLogic.changeRequests.getItem("change-request-id")
      ).toMatchInlineSnapshot(`undefined`);
    });
  });
});
