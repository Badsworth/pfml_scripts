import { ForbiddenError, NetworkError } from "../../src/errors";
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
    expect(appErrors.items).toHaveLength(0);
  });

  describe("catchError", () => {
    beforeEach(() => {
      // We expect console.error to be called in this scenario
      jest.spyOn(console, "error").mockImplementation(jest.fn());
    });

    it("sets app error with error info and tracks errors", () => {
      act(() => {
        appErrorsLogic.catchError(new Error());
      });

      expect(appErrorsLogic.appErrors.items[0].type).toEqual("Error");
      expect(tracker.noticeError).toHaveBeenCalledTimes(1);
      expect(console.error).toHaveBeenCalledTimes(1);
    });

    describe("when generic Error is thrown", () => {
      it("displays an internationalized message", () => {
        act(() => {
          appErrorsLogic.catchError(new Error("Default error message"));
        });

        expect(appErrorsLogic.appErrors.items[0].message).toMatchInlineSnapshot(
          `"Sorry, an unexpected error in our system was encountered. If this continues to happen, you may call the Paid Family Leave Contact Center at (XXX) XXX-XXXX"`
        );
      });
    });

    describe("when ForbiddenError is thrown", () => {
      it("displays an internationalized message", () => {
        act(() => {
          appErrorsLogic.catchError(new ForbiddenError());
        });

        expect(appErrorsLogic.appErrors.items[0].message).toMatchInlineSnapshot(
          `"Sorry, an authorization error was encountered. Please log out and then log in to try again."`
        );
      });
    });

    describe("when NetworkError is thrown", () => {
      it("displays an internationalized message", () => {
        act(() => {
          appErrorsLogic.catchError(new NetworkError());
        });

        expect(appErrorsLogic.appErrors.items[0].message).toMatchInlineSnapshot(
          `"Sorry, an error was encountered. This may occur for a variety of reasons, including temporarily losing an internet connection or an unexpected error in our system. If this continues to happen, you may call the Paid Family Leave Contact Center at (XXX) XXX-XXXX"`
        );
      });
    });

    describe("when multiple errors are caught", () => {
      it("adds adds all errors to the app errors list", () => {
        act(() => {
          appErrorsLogic.catchError(new Error("error 1"));
          appErrorsLogic.catchError(new Error("error 2"));
        });

        expect(appErrorsLogic.appErrors.items).toHaveLength(2);
        expect(tracker.noticeError).toHaveBeenCalledTimes(2);
        expect(console.error).toHaveBeenCalledTimes(2);
      });
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

      expect(appErrorsLogic.appErrors.items).toHaveLength(0);
    });
  });
});
