import FeatureFlagsApi from "../../src/api/FeatureFlagsApi";
import Flag from "../../src/models/Flag";
import { act } from "react-dom/test-utils";
import { testHook } from "../test-utils";
import useAppErrorsLogic from "../../src/hooks/useAppErrorsLogic";
import useFeatureFlagsLogic from "../../src/hooks/useFeatureFlagsLogic";
import usePortalFlow from "../../src/hooks/usePortalFlow";

jest.mock("../../src/api/FeatureFlagsApi");

describe("useFeatureFlagsLogic", () => {
  let appErrorsLogic, featureFlagsApi, flagsLogic, portalFlow;

  function renderHook() {
    testHook(() => {
      portalFlow = usePortalFlow();
      appErrorsLogic = useAppErrorsLogic({ portalFlow });
      flagsLogic = useFeatureFlagsLogic({ appErrorsLogic });
    });
  }

  beforeEach(() => {
    featureFlagsApi = new FeatureFlagsApi();

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

      expect(featureFlagsApi.getFlags).toHaveBeenCalled();
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
