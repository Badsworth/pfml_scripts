import { every, zip } from "lodash";
/**
 * Convenience function for code shared on upload pages.  If we combine the upload-id and upload-certification
 * pages, this logic can be moved into the combined page, instead.
 * Calls documentsLogic.attach to trigger the upload request, and removes successfully uploaded files from the "files"
 * array to update the FileCardList's displayed FileCards.  Returns an object with a {hasuploadErrors} boolean to allow
 * handling of errors and navigation in parent page.
 *
 * @param {Promise[]} uploadPromises - array of Promises returned by documentsLogic.attach
 * @param {object[]} files - array of {id: string, file: File} objects
 * @param {Function} setFiles - setter function for updating the list of files
 * @returns {object} - {success: bool}
 */
const uploadDocumentsHelper = async (uploadPromises, files, setFiles) => {
  const success = every(
    await Promise.all(
      zip(files, uploadPromises).map(
        async ([successfullyUploadedFile, uploadPromise]) => {
          const { success } = await uploadPromise;
          if (success) {
            setFiles((files) => {
              return files.filter((file) => file !== successfullyUploadedFile);
            });
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
