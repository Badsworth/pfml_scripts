import { act, renderHook } from "@testing-library/react-hooks";
import TempFileCollection from "../../src/models/TempFileCollection";
import { ValidationError } from "../../src/errors";
import { makeFile } from "../test-utils";
import tracker from "../../src/services/tracker";
import useFilesLogic from "../../src/hooks/useFilesLogic";

jest.mock("../../src/services/tracker");

describe("useFilesLogic", () => {
  let catchError, clearErrors, files, processFiles, removeFile;
  beforeEach(() => {
    clearErrors = jest.fn();
    catchError = jest.fn();

    // This file depends on these env vars being present
    process.env.fileSizeMaxBytesApiGateway = "10000000";
    process.env.fileSizeMaxBytesFineos = "4500000";

    renderHook(() => {
      ({ processFiles, removeFile, files } = useFilesLogic({
        clearErrors,
        catchError,
      }));
    });
  });

  it("returns collection and callback functions", () => {
    expect(files).toBeInstanceOf(TempFileCollection);
    expect(typeof processFiles).toBe("function");
    expect(typeof removeFile).toBe("function");
  });

  describe("processFiles", () => {
    it("adds item to collection", async () => {
      await act(
        async () =>
          await processFiles([
            makeFile({ name: "file1" }),
            makeFile({ name: "file2" }),
          ])
      );
      expect(catchError).not.toHaveBeenCalled();
      expect(files.items).toEqual([
        { id: "TempFile1", file: makeFile({ name: "file1" }) },
        { id: "TempFile2", file: makeFile({ name: "file2" }) },
      ]);
    });

    it("clears errors", async () => {
      await act(
        async () =>
          await processFiles([
            makeFile({ name: "file1" }),
            makeFile({ name: "file2" }),
          ])
      );

      expect(clearErrors).toHaveBeenCalled();
    });

    it("catches error when the file size is invalid", async () => {
      const invalidSizeFile = makeFile({ name: "file1" });
      Object.defineProperty(invalidSizeFile, "size", {
        get: () => 4500001,
      });
      await act(
        async () =>
          await processFiles([invalidSizeFile, makeFile({ name: "file2" })])
      );

      expect(catchError).toHaveBeenCalledTimes(1);
      const error = catchError.mock.calls[0][0];
      expect(error).toBeInstanceOf(ValidationError);
      expect(error.issues).toMatchInlineSnapshot(`
        [
          {
            "message": "We could not upload: file1. Files must be smaller than 4.5 MB.",
          },
        ]
      `);
      expect(files.items.length).toBe(1);
      expect(files.items[0].file.name).toBe("file2");

      expect(tracker.trackEvent).toHaveBeenCalledWith(
        "FileValidationError",
        expect.any(Object)
      );
    });

    it("does not validate PDF file size when sendLargePdfToApi feature flag is enabled and PDF is less than 10mb", async () => {
      const compressiblePdf = makeFile({
        name: "file1",
        type: "application/pdf",
      });
      Object.defineProperty(compressiblePdf, "size", {
        get: () => 9500000,
      });

      // Before feature flag
      await act(async () => await processFiles([compressiblePdf]));
      expect(files.items).toEqual([]);

      // After feature flag
      process.env.featureFlags = JSON.stringify({ sendLargePdfToApi: true });
      await act(async () => await processFiles([compressiblePdf]));
      expect(files.items).toEqual([
        { id: expect.any(String), file: compressiblePdf },
      ]);
    });

    it("prevents PDF files when sendLargePdfToApi feature flag is enabled and PDF is more than 10mb", async () => {
      process.env.featureFlags = JSON.stringify({ sendLargePdfToApi: true });
      const tooBigPdf = makeFile({ name: "file1", type: "application/pdf" });
      Object.defineProperty(tooBigPdf, "size", {
        get: () => 10000000,
      });

      await act(async () => await processFiles([tooBigPdf]));
      expect(catchError).toHaveBeenCalledTimes(1);
      const error = catchError.mock.calls[0][0];
      expect(error).toBeInstanceOf(ValidationError);
      expect(error.issues).toMatchInlineSnapshot(`
        [
          {
            "message": "We could not upload: file1. Files must be smaller than 10 MB.",
          },
        ]
      `);
      expect(files.items).toEqual([]);
    });

    it("catches error when the file type is invalid", async () => {
      const invalidTypeFile = makeFile({ name: "file1", type: "image/heic" });
      await act(
        async () =>
          await processFiles([invalidTypeFile, makeFile({ name: "file2" })])
      );

      expect(catchError).toHaveBeenCalledTimes(1);
      const error = catchError.mock.calls[0][0];
      expect(error).toBeInstanceOf(ValidationError);
      expect(error.issues).toMatchInlineSnapshot(`
        [
          {
            "message": "We could not upload: file1. Choose a PDF or an image file (.jpg, .jpeg, .png).",
          },
        ]
      `);
      expect(files.items.length).toBe(1);
      expect(files.items[0].file.name).toBe("file2");

      expect(tracker.trackEvent).toHaveBeenCalledWith(
        "FileValidationError",
        expect.any(Object)
      );
    });

    it("catches error when the file type and size is invalid", async () => {
      const invalidFile = makeFile({ name: "file1", type: "image/heic" });
      Object.defineProperty(invalidFile, "size", {
        get: () => 4500001,
      });
      await act(
        async () =>
          await processFiles([invalidFile, makeFile({ name: "file2" })])
      );

      expect(catchError).toHaveBeenCalledTimes(1);
      const error = catchError.mock.calls[0][0];
      expect(error).toBeInstanceOf(ValidationError);
      expect(error.issues).toMatchInlineSnapshot(`
        [
          {
            "message": "We could not upload: file1. Choose a PDF or an image file (.jpg, .jpeg, .png) that is smaller than 4.5 MB.",
          },
        ]
      `);
      expect(files.items.length).toBe(1);
      expect(files.items[0].file.name).toBe("file2");

      expect(tracker.trackEvent).toHaveBeenCalledWith(
        "FileValidationError",
        expect.any(Object)
      );
    });
  });

  describe("removeFile", () => {
    it("removes file from collection", async () => {
      await act(
        async () =>
          await processFiles([
            makeFile({ name: "file1" }),
            makeFile({ name: "file2" }),
            makeFile({ name: "file3" }),
          ])
      );
      const removedFileId = files.items[0].id;
      const firstFileId = files.items[1].id;
      const secondFileId = files.items[2].id;
      act(() => removeFile(removedFileId));
      expect(files.items.map((tempFile) => tempFile.id)).toEqual([
        firstFileId,
        secondFileId,
      ]);
    });
  });
});
