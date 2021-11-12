import { act, renderHook } from "@testing-library/react-hooks";
import AppErrorInfo from "../../src/models/AppErrorInfo";
import AppErrorInfoCollection from "../../src/models/AppErrorInfoCollection";
import { searchMock } from "../../src/api/EmployeesApi";
import useAppErrorsLogic from "../../src/hooks/useAppErrorsLogic";
import useEmployeesLogic from "../../src/hooks/useEmployeesLogic";
import usePortalFlow from "../../src/hooks/usePortalFlow";

jest.mock("../../src/api/EmployeesApi");
jest.mock("../../src/services/tracker");

describe("useEmployersLogic", () => {
  let appErrorsLogic, employeesLogic, portalFlow;

  function setup() {
    renderHook(() => {
      portalFlow = usePortalFlow();
      appErrorsLogic = useAppErrorsLogic({ portalFlow });
      employeesLogic = useEmployeesLogic({
        appErrorsLogic,
        portalFlow,
      });
    });
  }

  beforeEach(() => {
    setup();
  });

  afterEach(() => {
    appErrorsLogic = null;
    employeesLogic = null;
    portalFlow = null;
  });

  describe("search", () => {
    const postData = {
      first_name: "mock",
      last_name: "User",
      tax_identifier_last4: "6789",
      employer_fein: "123456789",
    };

    it("makes API call with POST data", async () => {
      await act(async () => {
        await employeesLogic.search(postData);
      });

      expect(searchMock).toHaveBeenCalledWith(postData);
    });

    describe("errors", () => {
      beforeEach(() => {
        jest.spyOn(console, "error").mockImplementationOnce(jest.fn());
      });

      it("catches error", async () => {
        searchMock.mockImplementationOnce(() => {
          throw new Error();
        });

        await act(async () => {
          await employeesLogic.search({
            first_name: "",
            last_name: "",
            tax_identifier_last4: "",
            employer_fein: "",
          });
        });

        expect(appErrorsLogic.appErrors.items[0].name).toEqual("Error");
      });

      it("clears prior errors", async () => {
        act(() => {
          appErrorsLogic.setAppErrors(
            new AppErrorInfoCollection([new AppErrorInfo()])
          );
        });

        await act(async () => {
          await employeesLogic.search(postData);
        });

        expect(appErrorsLogic.appErrors.items).toHaveLength(0);
      });
    });
  });
});
