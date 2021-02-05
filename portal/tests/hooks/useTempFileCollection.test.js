import TempFile from "../../src/models/TempFile";
import TempFileCollection from "../../src/models/TempFileCollection";
import { act } from "react-dom/test-utils";
import { testHook } from "../test-utils";
import useTempFileCollection from "../../src/hooks/useTempFileCollection";

describe("useCollectionState", () => {
  let addTempFiles, clearErrors, removeTempFile, setTempFiles, tempFiles;
  beforeEach(() => {
    clearErrors = jest.fn();
    testHook(() => {
      ({
        addTempFiles,
        removeTempFile,
        setTempFiles,
        tempFiles,
      } = useTempFileCollection(new TempFileCollection(), { clearErrors }));
    });
  });

  it("returns collection and callback functions", () => {
    expect(tempFiles).toBeInstanceOf(TempFileCollection);
    expect(typeof setTempFiles).toBe("function");
    expect(typeof addTempFiles).toBe("function");
    expect(typeof removeTempFile).toBe("function");
  });

  describe("addTempFiles", () => {
    it("adds item to collection", () => {
      act(() =>
        addTempFiles([new TempFile({ id: "123" }), new TempFile({ id: "456" })])
      );
      expect(tempFiles.items).toEqual([
        { id: "123", file: null },
        { id: "456", file: null },
      ]);
    });

    it("clears errors", () => {
      act(() =>
        addTempFiles([new TempFile({ id: "123" }), new TempFile({ id: "456" })])
      );

      expect(clearErrors).toHaveBeenCalled();
    });
  });

  describe("setTempFiles", () => {
    it("sets temp file collection", () => {
      act(() =>
        setTempFiles(
          new TempFileCollection([
            new TempFile({ id: "123" }),
            new TempFile({ id: "456" }),
            new TempFile({ id: "789" }),
          ])
        )
      );
      expect(tempFiles.items.map((tempFile) => tempFile.id)).toEqual([
        "123",
        "456",
        "789",
      ]);
    });
  });

  describe("removeItem", () => {
    it("removes item from collection", () => {
      act(() =>
        setTempFiles(
          new TempFileCollection([
            new TempFile({ id: "123" }),
            new TempFile({ id: "456" }),
            new TempFile({ id: "789" }),
          ])
        )
      );
      act(() => removeTempFile("456"));
      expect(tempFiles.items.map((tempFile) => tempFile.id)).toEqual([
        "123",
        "789",
      ]);
    });
  });
});
