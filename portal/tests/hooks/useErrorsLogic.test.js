import {
  AuthSessionMissingError,
  DocumentsUploadError,
  ForbiddenError,
  InternalServerError,
  NetworkError,
  ValidationError,
} from "../../src/errors";
import { act, renderHook } from "@testing-library/react-hooks";
import tracker from "../../src/services/tracker";
import useErrorsLogic from "../../src/hooks/useErrorsLogic";
import usePortalFlow from "../../src/hooks/usePortalFlow";

jest.mock("../../src/services/tracker");

const setup = () => {
  return renderHook(() => {
    const portalFlow = usePortalFlow();
    return useErrorsLogic({ portalFlow });
  });
};

describe("useErrorsLogic", () => {
  it("returns methods for setting errors", () => {
    const { result } = setup();
    expect(result.current.setErrors).toBeInstanceOf(Function);
    expect(result.current.errors).toHaveLength(0);
  });

  it.each([
    new ForbiddenError(),
    new NetworkError(),
    new InternalServerError(),
    new DocumentsUploadError("mock-application-id"),
  ])("catches and tracks %p error", (error) => {
    jest.spyOn(console, "error").mockImplementation(jest.fn());
    const { result } = setup();
    act(() => {
      result.current.catchError(error);
    });
    expect(result.current.errors).toHaveLength(1);

    expect(result.current.errors[0].name).toBe(error.name);
    expect(tracker.trackEvent).toHaveBeenCalledTimes(1);
  });

  it("catches and tracks generic Error instance", () => {
    jest.spyOn(console, "error").mockImplementation(jest.fn());
    const { result } = setup();
    act(() => {
      result.current.catchError(new Error());
    });
    expect(result.current.errors[0].name).toEqual("Error");
    expect(tracker.noticeError).toHaveBeenCalledTimes(1);
    expect(console.error).toHaveBeenCalledTimes(1);
  });

  it("redirects to login when AuthSessionMissingError is thrown", () => {
    let goToSpy;
    const { result } = renderHook(() => {
      const portalFlow = usePortalFlow();
      goToSpy = jest.spyOn(portalFlow, "goTo");
      portalFlow.pathWithParams = "/foo?bar=true";
      return useErrorsLogic({ portalFlow });
    });
    act(() => {
      result.current.catchError(new AuthSessionMissingError("No current user"));
    });

    expect(goToSpy).toHaveBeenCalledWith("/login", {
      next: "/foo?bar=true",
    });
  });

  it("tracks each issue when error includes issues array", () => {
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
    const { result } = setup();

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
      issueRule: "",
      issueType: "required",
    });
  });

  it("when multiple errors are caught, we can log and track them properly", () => {
    jest.spyOn(console, "error").mockImplementation(jest.fn());
    const { result } = setup();
    act(() => {
      result.current.catchError(new Error("error 1"));
      result.current.catchError(new Error("error 2"));
    });

    expect(result.current.errors).toHaveLength(2);
    expect(tracker.noticeError).toHaveBeenCalledTimes(2);
    expect(tracker.trackEvent).not.toHaveBeenCalled();
    expect(console.error).toHaveBeenCalledTimes(2);
  });

  it("when clearErrors is called, prior errors are removed", () => {
    const { result } = setup();
    act(() => {
      result.current.setErrors([new Error()]);
    });

    act(() => {
      result.current.clearErrors();
    });

    expect(result.current.errors).toHaveLength(0);
  });

  it("when clearRequiredFieldErrors is called, removes required field errors", () => {
    const { result } = setup();

    act(() => {
      result.current.setErrors([
        new ValidationError(
          [
            {
              field: "first_name",
              type: "required",
            },
            {
              field: "tax_identifier",
              type: "pattern",
            },
          ],
          "applications"
        ),
      ]);
    });

    act(() => {
      result.current.clearRequiredFieldErrors();
    });

    const { issues } = result.current.errors[0];
    expect(issues).toHaveLength(1);
    expect(issues.some((issue) => issue.type === "required")).toBe(false);
  });
});
