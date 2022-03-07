import { DocumentsLoadError } from "../errors";

/**
 * Check if a DocumentsLoadError related to loading exists for the given application
 */
const hasDocumentsLoadError = (errors: Error[], applicationId: string) =>
  errors.some(
    (error) =>
      error instanceof DocumentsLoadError &&
      error.application_id === applicationId
  );

export default hasDocumentsLoadError;
