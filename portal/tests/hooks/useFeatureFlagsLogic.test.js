import { act, renderHook } from "@testing-library/react-hooks";
import FeatureFlagsApi from "../../src/api/FeatureFlagsApi";
import Flag from "../../src/models/Flag";
import { NetworkError } from "../../src/errors";
import useAppErrorsLogic from "../../src/hooks/useAppErrorsLogic";
import useFeatureFlagsLogic from "../../src/hooks/useFeatureFlagsLogic";
import usePortalFlow from "../../src/hooks/usePortalFlow";

jest.mock("../../src/api/FeatureFlagsApi");

describe("useFeatureFlagsLogic", () => {
  let appErrorsLogic, featureFlagsApi, flagsLogic, portalFlow;

  function setup() {
    renderHook(() => {
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
      setup();
    });

    it("fetches flags from the api", async () => {
      await act(async () => {
        await flagsLogic.loadFlags();
      });

      expect(featureFlagsApi.getFlags).toHaveBeenCalled();
    });

    it("does not throw NetworkError when fetch request fails", async () => {
      featureFlagsApi.getFlags.mockRejectedValueOnce(new NetworkError());

      await act(async () => {
        await flagsLogic.loadFlags();
      });

      expect(appErrorsLogic.appErrors.items).toHaveLength(0);
    });
  });

  describe("getFlag", () => {
    beforeEach(() => {
      setup();
    });

    it("returns a specified feature flag from the state", async () => {
      const flagMock = new Flag({
        name: "maintenance",
        start: null,
        end: null,
        enabled: 1,
        options: {
          page_routes: ["/*"],
        },
      });

      await act(async () => {
        featureFlagsApi.getFlags.mockResolvedValueOnce([
          new Flag({
            name: "maintenance",
            start: null,
            end: null,
            enabled: 1,
            options: {
              page_routes: ["/*"],
            },
          }),
          new Flag({
            name: "test 1",
            start: null,
            end: null,
            enabled: 0,
            options: null,
          }),
          new Flag({
            name: "test 2",
            start: null,
            end: null,
            enabled: 0,
            options: null,
          }),
        ]);
        await flagsLogic.loadFlags();
      });

      const maintenanceFlag = flagsLogic.getFlag("maintenance");

      expect(maintenanceFlag).toEqual(flagMock);
    });

    it("returns a default, disabled feature flag if one is not found", async () => {
      const flagMock = new Flag();

      await act(async () => {
        featureFlagsApi.getFlags.mockResolvedValueOnce([
          new Flag({
            name: "maintenance",
            start: null,
            end: null,
            enabled: 1,
            options: {
              page_routes: ["/*"],
            },
          }),
          new Flag({
            name: "test 1",
            start: null,
            end: null,
            enabled: 0,
            options: null,
          }),
          new Flag({
            name: "test 2",
            start: null,
            end: null,
            enabled: 0,
            options: null,
          }),
        ]);
        await flagsLogic.loadFlags();
      });

      const maintenanceFlag = flagsLogic.getFlag("testFlag");

      expect(maintenanceFlag).toEqual(flagMock);
    });
  });
});
