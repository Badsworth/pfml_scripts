import AppErrorInfo from "../../src/models/AppErrorInfo";
import AppErrorInfoCollection from "../../src/models/AppErrorInfoCollection";
import { act } from "react-dom/test-utils";
import { testHook } from "../test-utils";
import tracker from "../../src/services/tracker";
import useAppErrorsLogic from "../../src/hooks/useAppErrorsLogic";

jest.mock("../../src/services/tracker");

describe("useAppErrorsLogic", () => {
  let appErrorsLogic;

  beforeEach(() => {
    testHook(() => {
      appErrorsLogic = useAppErrorsLogic();
    });
  });

  it("returns methods for setting errors", () => {
    const { setAppErrors, appErrors } = appErrorsLogic;

    expect(setAppErrors).toBeInstanceOf(Function);
    expect(appErrors).toBeNull();
  });

  describe("catchError", () => {
    beforeEach(() => {
      // We expect console.error to be called in this scenario
      jest.spyOn(console, "error").mockImplementationOnce(jest.fn());
    });

    it("sets app error with error info and tracks errors", () => {
      act(() => {
        appErrorsLogic.catchError(new Error());
      });

      expect(appErrorsLogic.appErrors.items[0].type).toEqual("Error");
      expect(tracker.noticeError).toHaveBeenCalledTimes(1);
    });
  });

  describe("clearErrors", () => {
    it("removes previous errors", () => {
      act(() => {
        appErrorsLogic.setAppErrors(
          new AppErrorInfoCollection([new AppErrorInfo()])
        );
      });

      act(() => {
        appErrorsLogic.clearErrors();
      });

      expect(appErrorsLogic.appErrors).toBeNull();
    });
  });
});
