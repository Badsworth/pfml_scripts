import { makeFile } from "../test-utils";
import uploadDocumentsHelper from "../../src/utils/uploadDocumentsHelper";

describe("uploadDocumentsHelper", () => {
  const uploadPromises = [
    Promise.resolve({ success: true }),
    Promise.resolve({ success: true }),
    Promise.resolve({ success: false }),
  ];

  const files = [makeFile(), makeFile(), makeFile()];
  const setFiles = jest.fn();

  it("calls setFiles for each successful upload", async () => {
    await uploadDocumentsHelper(uploadPromises, files, setFiles);
    expect(setFiles).toHaveBeenCalledTimes(2);
  });

  it("returns success = false when there are upload errors", async () => {
    const result = await uploadDocumentsHelper(uploadPromises, files, setFiles);
    expect(result).toEqual({ success: false });
  });

  it("returns success = true when there are no upload errors", async () => {
    const successfulPromises = [
      Promise.resolve({ success: true }),
      Promise.resolve({ success: true }),
      Promise.resolve({ success: true }),
    ];

    const result = await uploadDocumentsHelper(
      successfulPromises,
      files,
      setFiles
    );
    expect(result).toEqual({ success: true });
  });
});
