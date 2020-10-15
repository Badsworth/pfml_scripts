import { get } from "lodash";

/** @typedef {import('../models/AppErrorInfoCollection').default} AppErrorInfoCollection */
/**
 * Check if a DocumentsRequestError exists for the given application
 * @param {AppErrorInfoCollection} appErrors
 * @param {string} applicationId
 * @returns {boolean}
 */
const hasDocumentsLoadError = (appErrors, applicationId) =>
  appErrors.items.some(
    (error) =>
      error.name === "DocumentsRequestError" &&
      get(error, "meta.application_id") === applicationId
  );

export default hasDocumentsLoadError;
