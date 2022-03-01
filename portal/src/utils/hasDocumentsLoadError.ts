import ErrorInfo from "../models/ErrorInfo";
import { get } from "lodash";

/**
 * Check if a DocumentsLoadError related to loading exists for the given application
 */
const hasDocumentsLoadError = (errors: ErrorInfo[], applicationId: string) =>
  errors.some(
    (error) =>
      error.name === "DocumentsLoadError" &&
      get(error, "meta.application_id") === applicationId &&
      // Error with file_id is from uploading request
      !get(error, "meta.file_id")
  );

export default hasDocumentsLoadError;
