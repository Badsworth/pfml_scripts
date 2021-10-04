import {
  AuthSessionMissingError,
  ClaimWithdrawnError,
  DocumentsLoadError,
  DocumentsUploadError,
  ForbiddenError,
  LeaveAdminForbiddenError,
  NetworkError,
  ValidationError,
} from "../../src/errors";
import { act, renderHook } from "@testing-library/react-hooks";
import AppErrorInfo from "../../src/models/AppErrorInfo";
import AppErrorInfoCollection from "../../src/models/AppErrorInfoCollection";
import tracker from "../../src/services/tracker";
import useAppErrorsLogic from "../../src/hooks/useAppErrorsLogic";
import usePortalFlow from "../../src/hooks/usePortalFlow";

jest.mock("../../src/services/tracker");

const errorMessages = [
  [
    new Error("Default error message"),
    "Sorry, an unexpected error in our system was encountered. If this continues to happen, you may call the Paid Family Leave Contact Center at (833) 344‑7365.",
    null,
  ],
  [
    new ForbiddenError(),
    "Sorry, an authorization error was encountered. Please log out and then log in to try again.",
    null,
  ],
  [
    new NetworkError(),
    "Sorry, an error was encountered. This may occur for a variety of reasons, including temporarily losing an internet connection or an unexpected error in our system. If this continues to happen, you may call the Paid Family Leave Contact Center at (833) 344‑7365",
    null,
  ],
  [
    new DocumentsLoadError("mock-application-id"),
    "An error was encountered while checking your application for documents. If this continues to happen, call the Paid Family Leave Contact Center at (833) 344‑7365.",
    "mock-application-id",
  ],
  [
    new DocumentsUploadError("mock-application-id"),
    "We encountered an error when uploading your file. Try uploading your file again. If this continues to happen, call the Contact Center at (833) 344‑7365.",
    "mock-application-id",
  ],
];

const errorTracking = [
  [new ForbiddenError("Failed with forbidden error"), "ApiRequestError"],
  [new NetworkError(), "NetworkError"],
  [new AuthSessionMissingError("No current user"), "AuthSessionMissingError"],
];

const validationErrorIssues = [
  [
    [
      {
        field: "tax_identifier",
        type: "pattern",
        message: "This field should have a custom error message",
        rule: "/d{9}",
      },
    ],
    "Your Social Security Number or ITIN must be 9 digits.",
    "applications",
  ],
  [
    [
      {
        rule: "min_leave_periods",
        type: "multiFieldIssue",
      },
    ],
    "You must choose at least one kind of leave (continuous, reduced schedule, or intermittent).",
    "applications",
  ],
  [
    [
      {
        type: "fineos_client",
      },
    ],
    "We encountered an error when uploading your file. Try uploading your file again. If this continues to happen, call the Contact Center at (833) 344‑7365.",
    "documents",
  ],
  [
    [
      {
        field: "shop_name",
        type: "pattern",
        message: "This validation should have a generic error message",
        rule: "/d{9}",
      },
    ],
    "Field (shop_name) didn’t match expected format.",
    "applications",
  ],
  [
    [
      {
        field: "unknown_field",
        message: "does not match: [0-9]{7}",
      },
    ],
    "does not match: [0-9]{7}",
    "applications",
  ],
  [
    [
      {
        field: "validation_without_a_message",
        type: "noMessage",
      },
    ],
    "Field (validation_without_a_message) has invalid value.",
    "applications",
  ],
];

const render = () => {
  return renderHook(() => {
    const portalFlow = usePortalFlow();
    return useAppErrorsLogic({ portalFlow });
  });
};

describe("useAppErrorsLogic", () => {
  it("returns methods for setting errors", () => {
    const { result } = render();
    expect(result.current.setAppErrors).toBeInstanceOf(Function);
    expect(result.current.appErrors.items).toHaveLength(0);
  });

  it.each(errorMessages)(
    "Returns expected internationalized message when %p error is thrown",
    (error, message, applicationId) => {
      jest.spyOn(console, "error").mockImplementation(jest.fn());
      const { result } = render();
      act(() => {
        result.current.catchError(error);
      });
      expect(result.current.appErrors.items).toHaveLength(1);
      expect(result.current.appErrors.items[0].message).toBe(message);
      if (applicationId) {
        expect(result.current.appErrors.items[0].meta).toEqual({
          application_id: applicationId,
        });
      }
    }
  );

  it.each(errorTracking)("Tracks %p error in New Relic", (error, errorName) => {
    jest.spyOn(console, "error").mockImplementation(jest.fn());
    const { result } = render();

    act(() => {
      result.current.catchError(error);
    });

    expect(tracker.trackEvent).toHaveBeenCalledWith(errorName, {
      errorMessage: error.message,
      errorName: error.name,
    });
    expect(tracker.noticeError).not.toHaveBeenCalled();
  });

  it("sets app error with error info and tracks the error", () => {
    jest.spyOn(console, "error").mockImplementation(jest.fn());
    const { result } = render();
    act(() => {
      result.current.catchError(new Error());
    });
    expect(result.current.appErrors.items[0].name).toEqual("Error");
    expect(tracker.noticeError).toHaveBeenCalledTimes(1);
    expect(console.error).toHaveBeenCalledTimes(1);
  });

  it("redirects to login when AuthSessionMissingError is thrown", () => {
    let goToSpy;
    const { result } = renderHook(() => {
      const portalFlow = usePortalFlow();
      goToSpy = jest.spyOn(portalFlow, "goTo");
      portalFlow.pathWithParams = "/foo?bar=true";
      return useAppErrorsLogic({ portalFlow });
    });
    act(() => {
      result.current.catchError(new AuthSessionMissingError("No current user"));
    });

    expect(goToSpy).toHaveBeenCalledWith("/login", {
      next: "/foo?bar=true",
    });
  });

  it("for ClaimWithdrawnError, it displays an html error message and Options includes an absenceId", () => {
    jest.spyOn(console, "error").mockImplementation(jest.fn());
    const { result } = render();

    act(() => {
      result.current.catchError(
        new ClaimWithdrawnError("mock-absence-id", {
          type: "fineos_claim_withdrawn",
        })
      );
    });

    expect(result.current.appErrors.items).toHaveLength(1);
    expect(result.current.appErrors.items[0].message).toMatchInlineSnapshot(`
          <Trans
            components={
              Object {
                "contact-center-phone-link": <a
                  href="tel:(833) 344-7365"
                />,
              }
            }
            i18nKey="errors.claimStatus.fineos_claim_withdrawn"
            tOptions={
              Object {
                "absenceId": "mock-absence-id",
              }
            }
          />
        `);
  });

  it("When ValidationError is thrown, it sets field, rule, and type properties of AppErrorInfo", () => {
    const issues = [
      {
        field: "tax_identifier",
        type: "pattern",
        message: "This field should have a custom error message",
        rule: "/d{9}",
      },
    ];
    const { result } = render();

    act(() => {
      result.current.catchError(new ValidationError(issues, "applications"));
    });

    const appErrorInfo = result.current.appErrors.items[0];

    expect(appErrorInfo).toEqual(
      expect.objectContaining({
        field: "tax_identifier",
        type: "pattern",
        rule: "/d{9}",
      })
    );
  });

  it.each(validationErrorIssues)(
    "When ValidationError is thrown, it sets AppErrorInfo.message based on the content of issue",
    (issues, message, i18nPrefix) => {
      const { result } = render();

      act(() => {
        result.current.catchError(new ValidationError(issues, i18nPrefix));
      });

      expect(result.current.appErrors.items[0].message).toBe(message);
    }
  );

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
    const { result } = render();

    act(() => {
      result.current.catchError(new ValidationError(issues, "applications"));
    });

    expect(result.current.appErrors.items).toHaveLength(2);
    expect(result.current.appErrors.items[0].field).toBe(issues[0].field);
    expect(result.current.appErrors.items[0].name).toBe("ValidationError");
    expect(result.current.appErrors.items[1].rule).toBe(issues[1].rule);
  });

  it("For ValidationErrors, tracks each issue in New Relic", () => {
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
    const { result } = render();

    act(() => {
      result.current.catchError(new ValidationError(issues, "applications"));
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

  it("When LeaveAdminForbiddenError is thrown and has_verification_data is true, we track event", () => {
    const { result } = renderHook(() => {
      const portalFlow = usePortalFlow();
      portalFlow.pathWithParams = "/foo?bar=true";
      return useAppErrorsLogic({ portalFlow });
    });

    act(() => {
      result.current.catchError(
        new LeaveAdminForbiddenError(
          "some-employer-id",
          true,
          "User is not Verified"
        )
      );
    });

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

  it("When LeaveAdminForbiddenError is thrown and has_verification_data is true, we redirect to verify contributions page", () => {
    let goToSpy;
    const { result } = renderHook(() => {
      const portalFlow = usePortalFlow();
      goToSpy = jest.spyOn(portalFlow, "goTo");
      portalFlow.pathWithParams = "/foo?bar=true";
      return useAppErrorsLogic({ portalFlow });
    });

    act(() => {
      result.current.catchError(
        new LeaveAdminForbiddenError(
          "some-employer-id",
          true,
          "User is not Verified"
        )
      );
    });

    expect(goToSpy).toHaveBeenCalledWith(
      "/employers/organizations/verify-contributions",
      {
        employer_id: "some-employer-id",
        next: "/foo?bar=true",
      }
    );
  });

  it("When LeaveAdminForbiddenError is thrown and has_verification_data is false, we track the event", () => {
    const { result } = renderHook(() => {
      const portalFlow = usePortalFlow();
      portalFlow.pathWithParams = "/foo?bar=true";
      return useAppErrorsLogic({ portalFlow });
    });

    act(() => {
      result.current.catchError(
        new LeaveAdminForbiddenError(
          "some-employer-id",
          false,
          "User is not Verified"
        )
      );
    });

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

  it("When LeaveAdminForbiddenError is thrown and has_verification_data is false, we redirect to cannot verify page", () => {
    let goToSpy;
    const { result } = renderHook(() => {
      const portalFlow = usePortalFlow();
      goToSpy = jest.spyOn(portalFlow, "goTo");
      portalFlow.pathWithParams = "/foo?bar=true";
      return useAppErrorsLogic({ portalFlow });
    });

    act(() => {
      result.current.catchError(
        new LeaveAdminForbiddenError(
          "some-employer-id",
          false,
          "User is not Verified"
        )
      );
    });

    expect(goToSpy).toHaveBeenCalledWith(
      "/employers/organizations/cannot-verify",
      {
        employer_id: "some-employer-id",
      }
    );
  });

  it("when multiple errors are caught, we can log and track them properly", () => {
    jest.spyOn(console, "error").mockImplementation(jest.fn());
    const { result } = render();
    act(() => {
      result.current.catchError(new Error("error 1"));
      result.current.catchError(new Error("error 2"));
    });

    expect(result.current.appErrors.items).toHaveLength(2);
    expect(tracker.noticeError).toHaveBeenCalledTimes(2);
    expect(tracker.trackEvent).not.toHaveBeenCalled();
    expect(console.error).toHaveBeenCalledTimes(2);
  });

  it("returns Trans component when error type is fineos_case_creation_issues", () => {
    const issues = [
      {
        message: "register_employee did not find a match",
        type: "fineos_case_creation_issues",
      },
    ];
    const { result } = render();

    act(() => {
      result.current.catchError(new ValidationError(issues, "applications"));
    });

    expect(result.current.appErrors.items[0].message).toMatchInlineSnapshot(`
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
    const { result } = render();

    act(() => {
      result.current.catchError(new ValidationError(issues, "employers"));
    });

    expect(result.current.appErrors.items[0].message).toMatchInlineSnapshot(`
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
    const { result } = render();

    act(() => {
      result.current.catchError(new ValidationError(issues, "employers"));
    });

    expect(result.current.appErrors.items[0].message).toMatchInlineSnapshot(`
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
    const { result } = render();

    act(() => {
      result.current.catchError(new ValidationError(issues, "employers"));
    });

    expect(result.current.appErrors.items[0].message).toMatchInlineSnapshot(`
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

  it("when clearErrors is called, prior errors are removed", () => {
    const { result } = render();
    act(() => {
      result.current.setAppErrors(
        new AppErrorInfoCollection([new AppErrorInfo()])
      );
    });

    act(() => {
      result.current.clearErrors();
    });

    expect(result.current.appErrors.items).toHaveLength(0);
  });

  it("when clearRequiredFieldErrors is called, removes required field errors", () => {
    const { result } = render();

    act(() => {
      result.current.setAppErrors(
        new AppErrorInfoCollection([
          new AppErrorInfo(),
          new AppErrorInfo({ type: "required" }),
        ])
      );
    });

    act(() => {
      result.current.clearRequiredFieldErrors();
    });

    expect(result.current.appErrors.items).toHaveLength(1);
    expect(
      result.current.appErrors.items.some((error) => error.type === "required")
    ).toBe(false);
  });
});
