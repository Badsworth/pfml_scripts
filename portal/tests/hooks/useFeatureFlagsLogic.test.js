import AdminApi from "../../src/api/AdminApi";
import Flag from "../../src/models/Flag";
import { NetworkError } from "../../src/errors";
import { act } from "react-dom/test-utils";
import { testHook } from "../test-utils";
import useAppErrorsLogic from "../../src/hooks/useAppErrorsLogic";
import useFeatureFlagsLogic from "../../src/hooks/useFeatureFlagsLogic";
import usePortalFlow from "../../src/hooks/usePortalFlow";

jest.mock("../../src/api/AdminApi");

describe("useFeatureFlagsLogic", () => {
  let adminApi, appErrorsLogic, flagsLogic, portalFlow;

  function renderHook() {
    testHook(() => {
      portalFlow = usePortalFlow();
      appErrorsLogic = useAppErrorsLogic({ portalFlow });
      flagsLogic = useFeatureFlagsLogic({ appErrorsLogic });
    });
  }

  beforeEach(() => {
    adminApi = new AdminApi();

    jest.spyOn(console, "error").mockImplementationOnce(jest.fn());
  });

  describe("loadFlags", () => {
    beforeEach(() => {
      renderHook();
    });

    it("fetches flags from the api", async () => {
      await act(async () => {
        await flagsLogic.loadFlags();
      });

      expect(adminApi.getFlags).toHaveBeenCalled();
    });

    it("throws NetworkError when fetch request fails", async () => {
      adminApi.getFlags.mockRejectedValueOnce(new NetworkError());

      await act(async () => {
        await flagsLogic.loadFlags();
      });

      expect(appErrorsLogic.appErrors.items[0].name).toBe("NetworkError");
    });
  });

  describe("getFlag", () => {
    beforeEach(() => {
      renderHook();
    });

    it("returns a specified feature flag from the state", () => {
      const flagMock = new Flag({
        name: "maintenance",
        enabled: true,
        start: null,
        end: null,
        options: {
          page_routes: ["/*"],
        },
      });

      flagsLogic.getFlag = jest.fn().mockImplementation((flag_name) => {
        return {
          ...flagMock,
          name: flag_name,
        };
      });

      const maintenanceFlag = flagsLogic.getFlag("maintenance");

      expect(flagsLogic.getFlag).toHaveBeenCalledWith("maintenance");
      expect(maintenanceFlag).toEqual(flagMock);
    });
  });
});
