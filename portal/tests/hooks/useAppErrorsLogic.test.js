import {
  DocumentsRequestError,
  ForbiddenError,
  NetworkError,
  ValidationError,
} from "../../src/errors";
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

      expect(appErrorsLogic.appErrors.items[0].name).toEqual("Error");
      expect(tracker.noticeError).toHaveBeenCalledTimes(1);
      expect(console.error).toHaveBeenCalledTimes(1);
    });

    describe("when generic Error is thrown", () => {
      it("displays an internationalized message", () => {
        act(() => {
          appErrorsLogic.catchError(new Error("Default error message"));
        });

        expect(appErrorsLogic.appErrors.items).toHaveLength(1);
        expect(appErrorsLogic.appErrors.items[0].message).toMatchInlineSnapshot(
          `"Sorry, an unexpected error in our system was encountered. If this continues to happen, you may call the Paid Family Leave Contact Center at 833‑344‑7365."`
        );
      });
    });

    describe("when ForbiddenError is thrown", () => {
      it("displays an internationalized message", () => {
        act(() => {
          appErrorsLogic.catchError(new ForbiddenError());
        });

        expect(appErrorsLogic.appErrors.items).toHaveLength(1);
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

        expect(appErrorsLogic.appErrors.items).toHaveLength(1);
        expect(appErrorsLogic.appErrors.items[0].message).toMatchInlineSnapshot(
          `"Sorry, an error was encountered. This may occur for a variety of reasons, including temporarily losing an internet connection or an unexpected error in our system. If this continues to happen, you may call the Paid Family Leave Contact Center at 833‑344‑7365"`
        );
      });
    });

    describe("when DocumentsRequestError is thrown", () => {
      it("displays an internationalized message", () => {
        act(() => {
          appErrorsLogic.catchError(
            new DocumentsRequestError("mock-application-id")
          );
        });

        expect(appErrorsLogic.appErrors.items).toHaveLength(1);
        expect(appErrorsLogic.appErrors.items[0].message).toMatchInlineSnapshot(
          `"An error was encountered while checking your application for documents. If this continues to happen, you may call the Paid Family Leave Contact Center at 833‑344‑7365"`
        );
        expect(appErrorsLogic.appErrors.items[0].meta).toEqual({
          application_id: "mock-application-id",
        });
      });
    });

    describe("when ValidationError is thrown", () => {
      let issues;

      beforeEach(() => {
        issues = [
          {
            field: "tax_identifier",
            type: "pattern",
            message: "This field should have a custom error message",
            rule: "/d{9}",
          },
          {
            rule: "min_leave_periods",
            type: "multiFieldIssue",
          },
          {
            field: "unknown_field",
            type: "pattern",
            message: "This validation should have a generic error message",
            rule: "/d{9}",
          },
          {
            field: "custom_field_validation",
            type: "customValidation",
            message: "This validation should show THIS message",
            rule: "custom",
          },
          {
            field: "validation_without_a_message",
            type: "noMessage",
          },
        ];
      });

      it("displays an internationalized message for each issue", () => {
        act(() => {
          appErrorsLogic.catchError(new ValidationError(issues, "claims"));
        });

        expect(appErrorsLogic.appErrors.items).toHaveLength(5);
        expect(appErrorsLogic.appErrors.items[0].field).toBe(issues[0].field);
        expect(appErrorsLogic.appErrors.items[0].name).toBe("ValidationError");

        // Compare the order of message fallbacks
        expect(appErrorsLogic.appErrors.items[0].message).toMatchInlineSnapshot(
          `"Enter a 9-digit number."`
        );
        expect(appErrorsLogic.appErrors.items[1].message).toMatchInlineSnapshot(
          `"You must choose at least one kind of leave (continuous, reduced schedule, or intermittent)."`
        );
        expect(appErrorsLogic.appErrors.items[2].message).toMatchInlineSnapshot(
          `"Field (unknown_field) didn't match expected format."`
        );
        expect(appErrorsLogic.appErrors.items[3].message).toMatchInlineSnapshot(
          `"This validation should show THIS message"`
        );
        expect(appErrorsLogic.appErrors.items[4].message).toMatchInlineSnapshot(
          `"Field (validation_without_a_message) has invalid value."`
        );
      });

      it("tracks which issues were encountered", () => {
        const error = new ValidationError(issues, "test");

        act(() => {
          appErrorsLogic.catchError(error);
        });

        expect(tracker.trackEvent.mock.calls[0][1]).toMatchSnapshot();
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
