import ApiResourceCollection from "../models/ApiResourceCollection";
import TempFile from "../models/TempFile";
import { zip } from "lodash";

/**
 * Convenience function for code shared on upload pages.  If we combine the upload-id and upload-certification
 * pages, this logic can be moved into the combined page, instead.
 * Calls documentsLogic.attach to trigger the upload request, and removes successfully uploaded files from the "files"
 * array to update the FileCardList's displayed FileCards.
 */
const uploadDocumentsHelper = async (
  uploadPromises: Array<Promise<{ success: boolean }>> = [],
  tempFiles: ApiResourceCollection<TempFile>,
  removeTempFile: (id: string) => void
) => {
  if (!uploadPromises.length) {
    return { success: false };
  }

  const results = await Promise.all(
    zip(tempFiles.items, uploadPromises).map(
      async ([successfullyUploadedFile, uploadPromise]) => {
        if (!uploadPromise || !successfullyUploadedFile) return true;
        const { success } = await uploadPromise;
        if (success) {
          removeTempFile(successfullyUploadedFile.id);
          return success;
        }
        return false;
      }
    )
  );

  return { success: results.every((result) => result === true) };
};

export default uploadDocumentsHelper;
