import {
  getClaimMock,
  submitClaimReviewMock,
} from "../../src/api/EmployersApi";
import AppErrorInfo from "../../src/models/AppErrorInfo";
import AppErrorInfoCollection from "../../src/models/AppErrorInfoCollection";
import { act } from "react-dom/test-utils";
import { testHook } from "../test-utils";
import useAppErrorsLogic from "../../src/hooks/useAppErrorsLogic";
import useEmployersLogic from "../../src/hooks/useEmployersLogic";
import usePortalFlow from "../../src/hooks/usePortalFlow";

jest.mock("../../src/api/EmployersApi");

describe("useEmployersLogic", () => {
  const absenceId = "mock-fineos-absence-id-1";
  let appErrorsLogic, employersLogic, portalFlow;

  function renderHook() {
    testHook(() => {
      appErrorsLogic = useAppErrorsLogic();
      portalFlow = usePortalFlow();
      employersLogic = useEmployersLogic({ appErrorsLogic, portalFlow });
    });
  }

  beforeEach(() => {
    renderHook();
  });

  afterEach(() => {
    appErrorsLogic = null;
    employersLogic = null;
    portalFlow = null;
  });

  describe("load", () => {
    it("returns load as instance of function", () => {
      expect(employersLogic.load).toBeInstanceOf(Function);
    });

    it("returns claim data", async () => {
      await act(async () => {
        await employersLogic.load(absenceId);
      });

      expect(getClaimMock).toHaveBeenCalledWith(absenceId);
    });

    describe("errors", () => {
      beforeEach(() => {
        jest.spyOn(console, "error").mockImplementationOnce(jest.fn());
      });

      it("catches error", async () => {
        getClaimMock.mockImplementationOnce(() => {
          throw new Error();
        });

        await act(async () => {
          await employersLogic.load(absenceId);
        });

        expect(appErrorsLogic.appErrors.items[0].name).toEqual("Error");
      });
    });

    it("clears prior errors", async () => {
      act(() => {
        appErrorsLogic.setAppErrors(
          new AppErrorInfoCollection([new AppErrorInfo()])
        );
      });

      await act(async () => {
        await employersLogic.load(absenceId);
      });

      expect(appErrorsLogic.appErrors.items).toHaveLength(0);
    });
  });

  describe("submit", () => {
    const patchData = {
      employer_notification_date: "01-01-2021",
      employer_benefits: [],
      previous_leaves: [],
      hours_worked_per_week: 20,
      comment: "No comment",
    };

    it("returns submit as instance of function", () => {
      expect(employersLogic.submit).toBeInstanceOf(Function);
    });

    it("submits with absence id and patch data", async () => {
      await act(async () => {
        await employersLogic.submit(absenceId, patchData);
      });

      expect(submitClaimReviewMock).toHaveBeenCalledWith(absenceId, patchData);
    });

    describe("errors", () => {
      beforeEach(() => {
        jest.spyOn(console, "error").mockImplementationOnce(jest.fn());
      });

      it("catches error", async () => {
        submitClaimReviewMock.mockImplementationOnce(() => {
          throw new Error();
        });

        await act(async () => {
          await employersLogic.submit(absenceId, {});
        });

        expect(appErrorsLogic.appErrors.items[0].name).toEqual("Error");
      });
    });

    it("clears prior errors", async () => {
      act(() => {
        appErrorsLogic.setAppErrors(
          new AppErrorInfoCollection([new AppErrorInfo()])
        );
      });

      await act(async () => {
        await employersLogic.submit(absenceId, patchData);
      });

      expect(appErrorsLogic.appErrors.items).toHaveLength(0);
    });
  });
});
