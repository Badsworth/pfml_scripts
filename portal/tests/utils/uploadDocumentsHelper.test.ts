import ApiResourceCollection from "../../src/models/ApiResourceCollection";
import TempFile from "../../src/models/TempFile";
import { makeFile } from "../test-utils";
import uploadDocumentsHelper from "../../src/utils/uploadDocumentsHelper";

describe("uploadDocumentsHelper", () => {
  const uploadPromises = [
    Promise.resolve({ success: true }),
    Promise.resolve({ success: true }),
    Promise.resolve({ success: false }),
  ];

  const tempFiles = new ApiResourceCollection("id", [
    new TempFile({ file: makeFile({ name: "file1" }) }),
    new TempFile({ file: makeFile({ name: "file2" }) }),
    new TempFile({ file: makeFile({ name: "file3" }) }),
  ]);
  const removeTempFile = jest.fn();

  it("calls removeTempFile for each successful upload", async () => {
    await uploadDocumentsHelper(uploadPromises, tempFiles, removeTempFile);
    expect(removeTempFile).toHaveBeenCalledTimes(2);
  });

  it("returns success = false when there are upload errors", async () => {
    const result = await uploadDocumentsHelper(
      uploadPromises,
      tempFiles,
      removeTempFile
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
      tempFiles,
      removeTempFile
    );
    expect(result).toEqual({ success: true });
  });
});
