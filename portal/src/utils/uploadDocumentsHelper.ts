import { every, zip } from "lodash";
/**
 * Convenience function for code shared on upload pages.  If we combine the upload-id and upload-certification
 * pages, this logic can be moved into the combined page, instead.
 * Calls documentsLogic.attach to trigger the upload request, and removes successfully uploaded files from the "files"
 * array to update the FileCardList's displayed FileCards.  Returns an object with a {hasuploadErrors} boolean to allow
 * handling of errors and navigation in parent page.
 *
 * @param {Promise[]} uploadPromises - array of Promises returned by documentsLogic.attach
 * @param {TempFileCollection} tempFiles - instance of TempFileCollection
 * @param {Function} removeTempFile - function for removing succesfully uploaded file from tempFiles
 * @returns {object} - {success: bool}
 */
const uploadDocumentsHelper = async (
  uploadPromises,
  tempFiles,
  removeTempFile
) => {
  if (!uploadPromises) {
    return { success: false };
  }
  const success = every(
    await Promise.all(
      zip(tempFiles.items, uploadPromises).map(
        async ([successfullyUploadedFile, uploadPromise]) => {
          // @ts-expect-error ts-migrate(2339) FIXME: Property 'success' does not exist on type '{}'.
          const { success } = await uploadPromise;
          if (success) {
            // @ts-expect-error ts-migrate(2339) FIXME: Property 'id' does not exist on type 'unknown'.
            removeTempFile(successfullyUploadedFile.id);
            return success;
          }
          return false;
        }
      )
    )
  );

  return { success };
};

export default uploadDocumentsHelper;
