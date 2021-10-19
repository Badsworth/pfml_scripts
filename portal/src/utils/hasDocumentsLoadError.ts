import { get } from "lodash";

/** @typedef {import('../models/AppErrorInfoCollection').default} AppErrorInfoCollection */
/**
 * Check if a DocumentsLoadError related to loading exists for the given application
 * @param {AppErrorInfoCollection} appErrors
 * @param {string} applicationId
 * @returns {boolean}
 */
const hasDocumentsLoadError = (appErrors, applicationId) =>
  appErrors.items.some(
    (error) =>
      error.name === "DocumentsLoadError" &&
      get(error, "meta.application_id") === applicationId &&
      // Error with file_id is from uploading request
      !get(error, "meta.file_id")
  );

export default hasDocumentsLoadError;
