import { NetworkError, UnauthorizedError } from "../../src/errors";

import AdminApi from "../../src/api/AdminApi";
import AppErrorInfo from "../../src/models/AppErrorInfo";
import AppErrorInfoCollection from "../../src/models/AppErrorInfoCollection";
import { act } from "react-dom/test-utils";
import { testHook } from "../test-utils";
import useAppErrorsLogic from "../../src/hooks/useAppErrorsLogic";
import useFeatureFlagsLogic from "../../src/hooks/useFeatureFlagsLogic";
import usePortalFlow from "../../src/hooks/usePortalFlow";

jest.mock("../../src/api/AdminApi");

describe("useFeatureFlagsLogic", () => {
  let appErrorsLogic, adminApi, flagsLogic, portalFlow;
  
  function renderHook() {
    testHook(() => {
      portalFlow = usePortalFlow();
      appErrorsLogic = useAppErrorsLogic({ portalFlow });
      flagsLogic = useFeatureFlagsLogic({ appErrorsLogic });
    });
  }

  beforeEach(() => {
    adminApi = new AdminApi();
console.log("ADMIN API:", adminApi);
    jest.spyOn(console, "error").mockImplementationOnce(jest.fn());
  });

  describe("loadFeatureFlags", () => {
    beforeEach(() => {
      renderHook();
    });

    it("fetches maintenance flag from api", async () => {
      await act(async () => {
        await flagsLogic.loadFeatureFlags();
      });

      //expect(adminApi.getFlag).toHaveBeenCalled();
      expect(adminApi.getFlag).toHaveBeenCalledWith("maintenance");
    });

    it("throws NetworkError when fetch request fails", async () => {
      adminApi.getFlag.mockRejectedValueOnce(new NetworkError());

      await act(async () => {
        await flagsLogic.loadFeatureFlags();
      });

      expect(appErrorsLogic.appErrors.items[0].name).toBe("NetworkError");
    });
  });
});
