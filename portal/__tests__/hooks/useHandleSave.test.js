import { testHook } from "../test-utils";
import useHandleSave from "../../src/hooks/useHandleSave";

describe("useHandleSave", () => {
  describe("handleSave", () => {
    it("calls function to send API request", async () => {
      expect.assertions();

      let handleSave, onSuccess, saveToApi;
      testHook(() => {
        saveToApi = jest.fn().mockResolvedValue({ success: true });
        onSuccess = jest.fn();
        handleSave = useHandleSave(saveToApi, onSuccess);
      });

      const formState = { name: "Anton" };
      await handleSave(formState);

      expect(saveToApi).toHaveBeenCalledTimes(1);
      expect(saveToApi).toHaveBeenCalledWith(formState);
    });

    describe("when API result is successful", () => {
      it("calls onSuccess callback with the API result", async () => {
        expect.assertions();

        let handleSave, onSuccess, saveToApi;
        const result = { success: true };

        testHook(() => {
          saveToApi = jest.fn().mockResolvedValue(result);
          onSuccess = jest.fn();
          handleSave = useHandleSave(saveToApi, onSuccess);
        });

        const formState = { name: "Anton" };
        await handleSave(formState);

        expect(onSuccess).toHaveBeenCalledTimes(1);
        expect(onSuccess).toHaveBeenCalledWith(result);
      });
    });

    describe("when API result is not successful", () => {
      it("does not call the onSuccess callback", async () => {
        expect.assertions();

        let handleSave, onSuccess, saveToApi;
        const result = { success: false };

        testHook(() => {
          saveToApi = jest.fn().mockResolvedValue(result);
          onSuccess = jest.fn();
          handleSave = useHandleSave(saveToApi, onSuccess);
        });

        const formState = { name: "Anton" };
        await handleSave(formState);

        expect(onSuccess).toHaveBeenCalledTimes(0);
      });
    });

    describe("when API request throws an error", () => {
      it("does not call the onSuccess callback", async () => {
        expect.assertions();

        let handleSave, onSuccess, saveToApi;

        testHook(() => {
          saveToApi = jest
            .fn()
            .mockRejectedValueOnce(Error("No internet connection"));
          onSuccess = jest.fn();
          handleSave = useHandleSave(saveToApi, onSuccess);
        });

        const formState = { name: "Anton" };
        await handleSave(formState);

        expect(onSuccess).toHaveBeenCalledTimes(0);
      });
    });
  });
});
