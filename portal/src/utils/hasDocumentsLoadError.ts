import AppErrorInfoCollection from "../models/AppErrorInfoCollection";
import { get } from "lodash";

/**
 * Check if a DocumentsLoadError related to loading exists for the given application
 */
const hasDocumentsLoadError = (
  appErrors: AppErrorInfoCollection,
  applicationId: string
) =>
  appErrors.items.some(
    (error) =>
      error.name === "DocumentsLoadError" &&
      get(error, "meta.application_id") === applicationId &&
      // Error with file_id is from uploading request
      !get(error, "meta.file_id")
  );

export default hasDocumentsLoadError;
