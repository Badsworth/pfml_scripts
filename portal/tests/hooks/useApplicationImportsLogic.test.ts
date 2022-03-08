import { act, renderHook } from "@testing-library/react-hooks";
import { mockAuth, mockFetch } from "../test-utils";
import useApplicationImportsLogic from "src/hooks/useApplicationImportsLogic";
import useErrorsLogic from "src/hooks/useErrorsLogic";
import usePortalFlow from "src/hooks/usePortalFlow";

jest.mock("src/services/tracker");

function setup() {
  return renderHook(() => {
    const portalFlow = usePortalFlow();
    const errorsLogic = useErrorsLogic({ portalFlow });
    const importsLogic = useApplicationImportsLogic({
      errorsLogic,
      portalFlow,
    });

    return {
      portalFlow,
      errorsLogic,
      importsLogic,
    };
  });
}

describe("useApplicationImportsLogic", () => {
  beforeAll(() => {
    mockAuth();
  });

  describe("associate", () => {
    const mockAssociateFormState = {
      absence_case_id: "mock-absence-id",
      tax_identifier: "123-45-6789",
    };

    it("transforms the absence ID to uppercase before sending the request", async () => {
      const mockedFetch = mockFetch();
      const { result } = setup();

      await act(async () => {
        await result.current.importsLogic.associate(mockAssociateFormState);
      });

      expect(mockedFetch).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          body: JSON.stringify({
            ...mockAssociateFormState,
            absence_case_id: "MOCK-ABSENCE-ID",
          }),
        })
      );
    });

    it("routes to next page page with applicationAssociated query param", async () => {
      mockFetch({
        response: {
          data: {
            fineos_absence_id: "mock-id",
          },
        },
      });
      const { result } = setup();
      const spy = jest.spyOn(result.current.portalFlow, "goToNextPage");

      await act(async () => {
        await result.current.importsLogic.associate(mockAssociateFormState);
      });

      expect(spy).toHaveBeenCalledWith(
        {},
        { applicationAssociated: "mock-id" }
      );
    });

    it("catches exceptions thrown from the API module", async () => {
      jest.spyOn(console, "error").mockImplementationOnce(jest.fn());
      mockFetch({
        status: 400,
      });
      const { result } = setup();

      await act(async () => {
        await result.current.importsLogic.associate(mockAssociateFormState);
      });

      expect(result.current.errorsLogic.errors[0].name).toBe("BadRequestError");
    });

    it("clears prior errors", async () => {
      jest.spyOn(console, "error").mockImplementationOnce(jest.fn());
      mockFetch();
      const { result } = setup();

      act(() => {
        result.current.errorsLogic.catchError(new Error("mock error"));
      });

      expect(result.current.errorsLogic.errors).toHaveLength(1);

      await act(async () => {
        await result.current.importsLogic.associate(mockAssociateFormState);
      });

      expect(result.current.errorsLogic.errors).toHaveLength(0);
    });
  });
});
