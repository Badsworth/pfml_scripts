import {
  AuthSessionMissingError,
  DocumentsLoadError,
  DocumentsUploadError,
  ForbiddenError,
  LeaveAdminForbiddenError,
  NetworkError,
  ValidationError,
} from "../../src/errors";
import AppErrorInfo from "../../src/models/AppErrorInfo";
import AppErrorInfoCollection from "../../src/models/AppErrorInfoCollection";
import { act } from "react-dom/test-utils";
import { testHook } from "../test-utils";
import tracker from "../../src/services/tracker";
import useAppErrorsLogic from "../../src/hooks/useAppErrorsLogic";
import usePortalFlow from "../../src/hooks/usePortalFlow";

jest.mock("../../src/services/tracker");

describe("useAppErrorsLogic", () => {
  let appErrorsLogic, portalFlow;

  beforeEach(() => {
    testHook(() => {
      portalFlow = usePortalFlow();
      appErrorsLogic = useAppErrorsLogic({ portalFlow });
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
          `"Sorry, an unexpected error in our system was encountered. If this continues to happen, you may call the Paid Family Leave Contact Center at (833) 344‑7365."`
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

      it("tracks the error as an event in New Relic", () => {
        const error = new ForbiddenError("Failed with forbidden error");

        act(() => {
          appErrorsLogic.catchError(error);
        });

        expect(tracker.trackEvent).toHaveBeenCalledWith("ApiRequestError", {
          errorMessage: error.message,
          errorName: "ForbiddenError",
        });
        expect(tracker.noticeError).not.toHaveBeenCalled();
      });
    });

    describe("when NetworkError is thrown", () => {
      it("displays an internationalized message", () => {
        act(() => {
          appErrorsLogic.catchError(new NetworkError());
        });

        expect(appErrorsLogic.appErrors.items).toHaveLength(1);
        expect(appErrorsLogic.appErrors.items[0].message).toMatchInlineSnapshot(
          `"Sorry, an error was encountered. This may occur for a variety of reasons, including temporarily losing an internet connection or an unexpected error in our system. If this continues to happen, you may call the Paid Family Leave Contact Center at (833) 344‑7365"`
        );
      });

      it("tracks the error as JavaScriptError in New Relic", () => {
        const error = new NetworkError();

        act(() => {
          appErrorsLogic.catchError(error);
        });

        expect(tracker.noticeError).not.toHaveBeenCalled();
        expect(tracker.trackEvent).toHaveBeenCalledWith("NetworkError", {
          errorMessage: error.message,
          errorName: error.name,
        });
      });
    });

    describe("when AuthSessionMissingError is thrown", () => {
      it("redirects to /login page", () => {
        const goToSpy = jest.spyOn(portalFlow, "goTo");
        portalFlow.pathWithParams = "/foo?bar=true";

        act(() => {
          appErrorsLogic.catchError(
            new AuthSessionMissingError("No current user")
          );
        });

        expect(goToSpy).toHaveBeenCalledWith("/login", {
          next: "/foo?bar=true",
        });
      });

      it("tracks the error as an event in New Relic", () => {
        const error = new AuthSessionMissingError("No current user");

        act(() => {
          appErrorsLogic.catchError(error);
        });

        expect(tracker.trackEvent).toHaveBeenCalledWith(
          "AuthSessionMissingError",
          {
            errorMessage: error.message,
            errorName: "AuthSessionMissingError",
          }
        );
        expect(tracker.noticeError).not.toHaveBeenCalled();
      });
    });

    describe("when DocumentsLoadError is thrown", () => {
      it("displays an internationalized message", () => {
        act(() => {
          appErrorsLogic.catchError(
            new DocumentsLoadError("mock-application-id")
          );
        });

        expect(appErrorsLogic.appErrors.items).toHaveLength(1);
        expect(appErrorsLogic.appErrors.items[0].message).toMatchInlineSnapshot(
          `"An error was encountered while checking your application for documents. If this continues to happen, call the Paid Family Leave Contact Center at (833) 344‑7365."`
        );
        expect(appErrorsLogic.appErrors.items[0].meta).toEqual({
          application_id: "mock-application-id",
        });
      });
    });

    describe("when DocumentsUploadError is thrown", () => {
      it("displays an internationalized message", () => {
        act(() => {
          appErrorsLogic.catchError(
            new DocumentsUploadError("mock-application-id")
          );
        });

        expect(appErrorsLogic.appErrors.items).toHaveLength(1);
        expect(appErrorsLogic.appErrors.items[0].message).toMatchInlineSnapshot(
          `"We encountered an error when uploading your file. Try uploading your file again. If this continues to happen, call the Contact Center at (833) 344‑7365."`
        );
        expect(appErrorsLogic.appErrors.items[0].meta).toEqual({
          application_id: "mock-application-id",
        });
      });
    });

    describe("when ValidationError is thrown", () => {
      it("sets field, rule, and type properties of AppErrorInfo", () => {
        const issues = [
          {
            field: "tax_identifier",
            type: "pattern",
            message: "This field should have a custom error message",
            rule: "/d{9}",
          },
        ];

        act(() => {
          appErrorsLogic.catchError(
            new ValidationError(issues, "applications")
          );
        });

        const appErrorInfo = appErrorsLogic.appErrors.items[0];

        expect(appErrorInfo).toEqual(
          expect.objectContaining({
            field: "tax_identifier",
            type: "pattern",
            rule: "/d{9}",
          })
        );
      });

      it("sets AppErrorInfo.message based on the issue's 'field' and 'type' properties", () => {
        const issues = [
          {
            field: "tax_identifier",
            type: "pattern",
            message: "This field should have a custom error message",
            rule: "/d{9}",
          },
        ];

        act(() => {
          appErrorsLogic.catchError(
            new ValidationError(issues, "applications")
          );
        });

        expect(appErrorsLogic.appErrors.items[0].message).toMatchInlineSnapshot(
          `"Your Social Security Number or ITIN must be 9 digits."`
        );
      });

      it("sets AppErrorInfo.message based on the issue's 'rule' property when 'field' property isn't set", () => {
        const issues = [
          {
            rule: "min_leave_periods",
            type: "multiFieldIssue",
          },
        ];

        act(() => {
          appErrorsLogic.catchError(
            new ValidationError(issues, "applications")
          );
        });

        expect(appErrorsLogic.appErrors.items[0].message).toMatchInlineSnapshot(
          `"You must choose at least one kind of leave (continuous, reduced schedule, or intermittent)."`
        );
      });

      it("sets AppErrorInfo.message based on the issue's 'type' property when 'field' and 'rule' properties aren't set", () => {
        const issues = [
          {
            type: "fineos_client",
          },
        ];

        act(() => {
          appErrorsLogic.catchError(new ValidationError(issues, "documents"));
        });

        expect(appErrorsLogic.appErrors.items[0].message).toMatchInlineSnapshot(
          `"We encountered an error when uploading your file. Try uploading your file again. If this continues to happen, call the Contact Center at (833) 344‑7365."`
        );
      });

      it("sets AppErrorInfo.message to generic field-level fallback based on the issue's 'type' when 'type' is 'pattern' and field-level message is missing", () => {
        const issues = [
          {
            field: "shop_name",
            type: "pattern",
            message: "This validation should have a generic error message",
            rule: "/d{9}",
          },
        ];

        act(() => {
          appErrorsLogic.catchError(
            new ValidationError(issues, "applications")
          );
        });

        expect(appErrorsLogic.appErrors.items[0].message).toMatchInlineSnapshot(
          `"Field (shop_name) didn’t match expected format."`
        );
      });

      it("sets AppErrorInfo.message based on the issue 'message' property when other fallback messages are missing", () => {
        const issues = [
          {
            field: "unknown_field",
            message: "does not match: [0-9]{7}",
          },
        ];

        act(() => {
          appErrorsLogic.catchError(
            new ValidationError(issues, "applications")
          );
        });

        expect(appErrorsLogic.appErrors.items[0].message).toMatchInlineSnapshot(
          `"does not match: [0-9]{7}"`
        );
      });

      it("sets AppErrorInfo.message to generic fallback message when issue 'message' property is not set and other fallback messages are missing", () => {
        const issues = [
          {
            field: "validation_without_a_message",
            type: "noMessage",
          },
        ];

        act(() => {
          appErrorsLogic.catchError(
            new ValidationError(issues, "applications")
          );
        });

        expect(appErrorsLogic.appErrors.items[0].message).toMatchInlineSnapshot(
          `"Field (validation_without_a_message) has invalid value."`
        );
      });

      it("sets appErrors in same order as issues", () => {
        const issues = [
          {
            field: "first_name",
            message: "first_name is required",
            type: "required",
          },
          {
            rule: "min_leave_periods",
          },
        ];

        act(() => {
          appErrorsLogic.catchError(
            new ValidationError(issues, "applications")
          );
        });

        expect(appErrorsLogic.appErrors.items).toHaveLength(2);
        expect(appErrorsLogic.appErrors.items[0].field).toBe(issues[0].field);
        expect(appErrorsLogic.appErrors.items[0].name).toBe("ValidationError");
        expect(appErrorsLogic.appErrors.items[1].rule).toBe(issues[1].rule);
      });

      it("tracks each issue in New Relic", () => {
        const issues = [
          {
            field: "tax_identifier",
            type: "pattern",
            message: "123123123 is invalid",
            rule: "/d{9}",
          },
          {
            field: "first_name",
            type: "required",
            message: "First name is required",
          },
        ];

        act(() => {
          appErrorsLogic.catchError(
            new ValidationError(issues, "applications")
          );
        });

        expect(tracker.trackEvent).toHaveBeenCalledWith("ValidationError", {
          issueField: "tax_identifier",
          issueRule: "/d{9}",
          issueType: "pattern",
        });

        expect(tracker.trackEvent).toHaveBeenCalledWith("ValidationError", {
          issueField: "first_name",
          issueType: "required",
        });
      });
    });

    describe("LeaveAdminForbiddenError is thrown", () => {
      let goToSpy;
      beforeEach(() => {
        goToSpy = jest.spyOn(portalFlow, "goTo");
        portalFlow.pathWithParams = "/foo?bar=true";
      });

      describe("when has_verification_data is true", () => {
        beforeEach(() => {
          act(() => {
            appErrorsLogic.catchError(
              new LeaveAdminForbiddenError(
                "some-employer-id",
                true,
                "User is not Verified"
              )
            );
          });
        });

        it("tracks the event", () => {
          expect(tracker.trackEvent).toHaveBeenCalledWith(
            "LeaveAdminForbiddenError",
            {
              errorMessage: "User is not Verified",
              errorName: "LeaveAdminForbiddenError",
              employerId: "some-employer-id",
              hasVerificationData: true,
            }
          );
        });

        it("redirects to verify contributions page", () => {
          expect(goToSpy).toHaveBeenCalledWith(
            "/employers/organizations/verify-contributions",
            {
              employer_id: "some-employer-id",
              next: "/foo?bar=true",
            }
          );
        });

        it("does not add the error to appErrors collection", () => {
          expect(appErrorsLogic.appErrors.items).toHaveLength(0);
        });
      });

      describe("when has_verification_data is false", () => {
        beforeEach(() => {
          act(() => {
            appErrorsLogic.catchError(
              new LeaveAdminForbiddenError(
                "some-employer-id",
                false,
                "User is not Verified"
              )
            );
          });
        });

        it("tracks the event", () => {
          expect(tracker.trackEvent).toHaveBeenCalledWith(
            "LeaveAdminForbiddenError",
            {
              errorMessage: "User is not Verified",
              errorName: "LeaveAdminForbiddenError",
              employerId: "some-employer-id",
              hasVerificationData: false,
            }
          );
        });

        it("redirects to cannot verify page", () => {
          expect(goToSpy).toHaveBeenCalledWith(
            "/employers/organizations/cannot-verify",
            {
              employer_id: "some-employer-id",
            }
          );
        });

        it("does not add the error to appErrors collection", () => {
          expect(appErrorsLogic.appErrors.items).toHaveLength(0);
        });
      });
    });

    describe("when multiple Errors are caught", () => {
      beforeEach(() => {
        act(() => {
          appErrorsLogic.catchError(new Error("error 1"));
          appErrorsLogic.catchError(new Error("error 2"));
        });
      });

      it("adds adds all errors to the app errors list", () => {
        expect(appErrorsLogic.appErrors.items).toHaveLength(2);
      });

      it("tracks the errors as JavaScriptError in New Relic", () => {
        expect(tracker.noticeError).toHaveBeenCalledTimes(2);
        expect(tracker.trackEvent).not.toHaveBeenCalled();
      });

      it("logs the errors to the console", () => {
        expect(console.error).toHaveBeenCalledTimes(2);
      });
    });

    it("returns Trans component when error type is fineos_case_creation_issues", () => {
      const issues = [
        {
          message: "register_employee did not find a match",
          type: "fineos_case_creation_issues",
        },
      ];

      act(() => {
        appErrorsLogic.catchError(new ValidationError(issues, "applications"));
      });

      expect(appErrorsLogic.appErrors.items[0].message).toMatchInlineSnapshot(`
        <Trans
          components={
            Object {
              "mass-gov-form-link": <a
                href="https://www.mass.gov/forms/apply-for-paid-leave-if-you-received-an-error"
                rel="noreferrer noopener"
                target="_blank"
              />,
            }
          }
          i18nKey="errors.applications.fineos_case_creation_issues"
        />
      `);
    });

    it("returns Trans component when error type is unauthorized_leave_admin", () => {
      const issues = [
        {
          message: "User is not authorized for access",
          type: "unauthorized_leave_admin",
        },
      ];

      act(() => {
        appErrorsLogic.catchError(new ValidationError(issues, "employers"));
      });

      expect(appErrorsLogic.appErrors.items[0].message).toMatchInlineSnapshot(`
        <Trans
          components={
            Object {
              "add-org-link": <a
                href="/employers/organizations/add-organization"
              />,
            }
          }
          i18nKey="errors.employers.unauthorized_leave_admin"
        />
      `);
    });

    it("returns Trans component when error type is contains_v1_and_v2_eforms", () => {
      const issues = [
        {
          message: "Claim contains both V1 and V2 eforms.",
          type: "contains_v1_and_v2_eforms",
        },
      ];

      act(() => {
        appErrorsLogic.catchError(new ValidationError(issues, "employers"));
      });

      expect(appErrorsLogic.appErrors.items[0].message).toMatchInlineSnapshot(`
        <Trans
          components={
            Object {
              "contact-center-phone-link": <a
                href="tel:(833) 344-7365"
              />,
              "h3": <h3 />,
              "li": <li />,
              "ul": <ul />,
            }
          }
          i18nKey="errors.employers.contains_v1_and_v2_eforms"
        />
      `);
    });

    it("returns Trans component when error type is employer_verification_data_required", () => {
      const issues = [
        {
          field: "ein",
          type: "employer_verification_data_required",
        },
      ];

      act(() => {
        appErrorsLogic.catchError(new ValidationError(issues, "employers"));
      });

      expect(appErrorsLogic.appErrors.items[0].message).toMatchInlineSnapshot(`
        <Trans
          components={
            Object {
              "file-a-return-link": <a
                href="https://www.mass.gov/pfml-zero-balance-employer"
                rel="noreferrer noopener"
                target="_blank"
              />,
            }
          }
          i18nKey="errors.employers.ein.employer_verification_data_required"
        />
      `);
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

  describe("clearRequiredFieldErrors", () => {
    it("removes required field errors", () => {
      act(() => {
        appErrorsLogic.setAppErrors(
          new AppErrorInfoCollection([
            new AppErrorInfo(),
            new AppErrorInfo({ type: "required" }),
          ])
        );
      });

      act(() => {
        appErrorsLogic.clearRequiredFieldErrors();
      });

      expect(appErrorsLogic.appErrors.items).toHaveLength(1);
      expect(
        appErrorsLogic.appErrors.items.some(
          (error) => error.type === "required"
        )
      ).toBe(false);
    });
  });
});
