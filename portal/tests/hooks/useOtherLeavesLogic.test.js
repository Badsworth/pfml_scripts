import { act, renderHook } from "@testing-library/react-hooks";
import {
  removeEmployerBenefit,
  removeOtherIncome,
  removePreviousLeave,
} from "../../src/api/OtherLeavesApi";
import { NotFoundError } from "../../src/errors";
import useAppErrorsLogic from "../../src/hooks/useAppErrorsLogic";
import useOtherLeavesLogic from "../../src/hooks/useOtherLeavesLogic";
import usePortalFlow from "../../src/hooks/usePortalFlow";

jest.mock("../../src/api/OtherLeavesApi");
jest.mock("../../src/services/tracker");

describe("useOtherLeavesLogic", () => {
  const applicationId = "mock-application-id-1";
  let appErrorsLogic, otherLeavesLogic;

  function setup() {
    renderHook(() => {
      const portalFlow = usePortalFlow();
      appErrorsLogic = useAppErrorsLogic({ portalFlow });
      otherLeavesLogic = useOtherLeavesLogic({
        appErrorsLogic,
      });
    });
  }

  beforeEach(() => {
    setup();
  });

  afterEach(() => {
    appErrorsLogic = null;
    otherLeavesLogic = null;
  });

  describe("#removeEmployerBenefit", () => {
    const employerBenefitId = "mock-employer-benefit-1";

    describe("successful request", () => {
      it("returns true", async () => {
        let result;

        await act(async () => {
          result = await otherLeavesLogic.removeEmployerBenefit(
            applicationId,
            employerBenefitId
          );
        });

        expect(result).toBe(true);
      });
    });

    describe("failed request", () => {
      let catchError;

      beforeEach(() => {
        jest.spyOn(console, "error").mockImplementationOnce(jest.fn());
        removeEmployerBenefit.mockImplementationOnce(() => {
          throw new NotFoundError();
        });
        catchError = jest.spyOn(appErrorsLogic, "catchError");
      });

      afterEach(() => {
        removeEmployerBenefit.mockRestore();
        catchError.mockRestore();
      });

      it("returns false", async () => {
        let result;

        await act(async () => {
          result = await otherLeavesLogic.removeEmployerBenefit(
            applicationId,
            employerBenefitId
          );
        });

        expect(result).toBe(false);
      });

      it("calls appErrorsLogic#catchError", async () => {
        await act(async () => {
          await otherLeavesLogic.removeEmployerBenefit(
            applicationId,
            employerBenefitId
          );
        });

        expect(catchError).toHaveBeenCalled();
      });
    });
  });

  describe("#removeOtherIncome", () => {
    const otherIncomeId = "mock-other-income-1";

    describe("successful request", () => {
      it("returns true", async () => {
        let result;

        await act(async () => {
          result = await otherLeavesLogic.removeOtherIncome(
            applicationId,
            otherIncomeId
          );
        });

        expect(result).toBe(true);
      });
    });

    describe("failed request", () => {
      let catchError;

      beforeEach(() => {
        jest.spyOn(console, "error").mockImplementationOnce(jest.fn());
        removeOtherIncome.mockImplementationOnce(() => {
          throw new NotFoundError();
        });
        catchError = jest.spyOn(appErrorsLogic, "catchError");
      });

      afterEach(() => {
        removeOtherIncome.mockRestore();
        catchError.mockRestore();
      });

      it("returns false", async () => {
        let result;

        await act(async () => {
          result = await otherLeavesLogic.removeOtherIncome(
            applicationId,
            otherIncomeId
          );
        });

        expect(result).toBe(false);
      });

      it("calls appErrorsLogic#catchError", async () => {
        await act(async () => {
          await otherLeavesLogic.removeOtherIncome(
            applicationId,
            otherIncomeId
          );
        });

        expect(catchError).toHaveBeenCalled();
      });
    });
  });

  describe("#removePreviousLeave", () => {
    const previousLeaveId = "mock-other-income-1";
    describe("successful request", () => {
      it("returns true", async () => {
        let result;

        await act(async () => {
          result = await otherLeavesLogic.removePreviousLeave(
            applicationId,
            previousLeaveId
          );
        });

        expect(result).toBe(true);
      });
    });

    describe("failed request", () => {
      let catchError;

      beforeEach(() => {
        jest.spyOn(console, "error").mockImplementationOnce(jest.fn());
        removePreviousLeave.mockImplementationOnce(() => {
          throw new NotFoundError();
        });
        catchError = jest.spyOn(appErrorsLogic, "catchError");
      });

      afterEach(() => {
        removePreviousLeave.mockRestore();
        catchError.mockRestore();
      });

      it("returns false", async () => {
        let result;

        await act(async () => {
          result = await otherLeavesLogic.removePreviousLeave(
            applicationId,
            previousLeaveId
          );
        });

        expect(result).toBe(false);
      });

      it("calls appErrorsLogic#catchError", async () => {
        await act(async () => {
          await otherLeavesLogic.removePreviousLeave(
            applicationId,
            previousLeaveId
          );
        });

        expect(catchError).toHaveBeenCalled();
      });
    });
  });
});
