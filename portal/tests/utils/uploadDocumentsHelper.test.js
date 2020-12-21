import { makeFile } from "../test-utils";
import uploadDocumentsHelper from "../../src/utils/uploadDocumentsHelper";

describe("uploadDocumentsHelper", () => {
  const uploadPromises = [
    Promise.resolve({ success: true }),
    Promise.resolve({ success: true }),
    Promise.resolve({ success: false }),
  ];

  const filesWithUniqueId = [
    { id: "1", file: makeFile({ name: "file1" }) },
    { id: "2", file: makeFile({ name: "file2" }) },
    { id: "3", file: makeFile({ name: "file3" }) },
  ];
  const setFiles = jest.fn();

  it("calls setFiles for each successful upload", async () => {
    await uploadDocumentsHelper(uploadPromises, filesWithUniqueId, setFiles);
    expect(setFiles).toHaveBeenCalledTimes(2);
  });

  it("returns success = false when there are upload errors", async () => {
    const result = await uploadDocumentsHelper(
      uploadPromises,
      filesWithUniqueId,
      setFiles
    );
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
      filesWithUniqueId,
      setFiles
    );
    expect(result).toEqual({ success: true });
  });

  it("returns success = false when uploadPromises is undefined", async () => {
    const result = await uploadDocumentsHelper(
      undefined,
      filesWithUniqueId,
      setFiles
    );
    expect(result).toEqual({ success: false });
  });
});
