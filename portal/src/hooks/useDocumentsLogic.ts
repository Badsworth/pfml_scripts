import {
  BenefitsApplicationDocument,
  DocumentTypeEnum,
} from "../models/Document";
import {
  DocumentsLoadError,
  DocumentsUploadError,
  ValidationError,
} from "../errors";
import { useMemo, useState } from "react";
import ApiResourceCollection from "../models/ApiResourceCollection";
import DocumentsApi from "../api/DocumentsApi";
import { ErrorsLogic } from "./useErrorsLogic";
import TempFile from "../models/TempFile";
import assert from "assert";
import useCollectionState from "./useCollectionState";

const useDocumentsLogic = ({ errorsLogic }: { errorsLogic: ErrorsLogic }) => {
  /**
   * State representing the collection of documents for the current user.
   * Initialize to empty collection, but will eventually store the document
   * state as API calls are made to fetch the documents on a per-application basis,
   * and as new documents are created.
   *
   * The collection from useCollectionState stores all documents together,
   * and we filter documents based on application_id to provide the correct documents
   * to the requesting components.
   */

  const {
    collection: documents,
    addItem: addDocument,
    addItems: addDocuments,
  } = useCollectionState(
    new ApiResourceCollection<BenefitsApplicationDocument>("fineos_document_id")
  );

  const documentsApi = useMemo(() => new DocumentsApi(), []);
  const [loadedApplicationDocs, setLoadedApplicationDocs] = useState<{
    [application_id: string]: { isLoading: boolean };
  }>({});

  /**
   * Check if docs for this application have been loaded
   * We use a separate array and state here, rather than using the collection,
   * because documents that don't have items won't be represented in the collection.
   */
  const hasLoadedClaimDocuments = (application_id: string) =>
    application_id in loadedApplicationDocs &&
    loadedApplicationDocs[application_id].isLoading === false;

  const isLoadingClaimDocuments = (application_id: string) =>
    application_id in loadedApplicationDocs &&
    loadedApplicationDocs[application_id].isLoading === true;

  /**
   * Load all documents for a user's claim
   * This must be called before documents are available
   */
  const loadAll = async (application_id: string) => {
    // if documents already contains docs for application_id, don't load again
    // or if we started making a request to the API to load documents, don't load again
    if (
      hasLoadedClaimDocuments(application_id) ||
      isLoadingClaimDocuments(application_id)
    )
      return;

    errorsLogic.clearErrors();

    setLoadedApplicationDocs((loadingClaimDocuments) => {
      const docs = { ...loadingClaimDocuments };
      docs[application_id] = {
        isLoading: true,
      };
      return docs;
    });

    try {
      const { documents: loadedDocuments } = await documentsApi.getDocuments(
        application_id
      );
      addDocuments(loadedDocuments.items);
      setLoadedApplicationDocs((loadingClaimDocuments) => {
        const docs = { ...loadingClaimDocuments };
        docs[application_id] = {
          isLoading: false,
        };
        return docs;
      });
    } catch (error) {
      errorsLogic.catchError(new DocumentsLoadError(application_id));
    }
  };

  /**
   * Submit files to the API and set application errors if any
   * @param application_id - application id for claim
   * @param filesWithUniqueId - array of objects including unique Id and File to upload and attach to the application
   * @param documentType - category of documents
   * @param mark_evidence_received - Set the flag used to indicate whether
   * the doc is ready for review or not. Docs added to a claim that was completed
   * through a channel other than the Portal require this flag being set to `true`.
   */
  const attach = (
    application_id: string,
    filesWithUniqueId: TempFile[],
    documentType: DocumentTypeEnum,
    mark_evidence_received: boolean
  ) => {
    assert(application_id);
    errorsLogic.clearErrors();

    if (!filesWithUniqueId.length) {
      errorsLogic.catchError(
        new ValidationError(
          [
            {
              // field and type will be used for forming the internationalized error message
              field: "file", // 'file' is the field name in the API
              message:
                "Client requires at least one file before sending request",
              type: "required",
            },
          ],
          "documents"
        )
      );
      return [];
    }

    const uploadPromises = filesWithUniqueId.map(async (fileWithUniqueId) => {
      try {
        const { document } = await documentsApi.attachDocument(
          application_id,
          fileWithUniqueId.file,
          documentType,
          mark_evidence_received
        );
        addDocument(document);
        return { success: true };
      } catch (error) {
        errorsLogic.catchError(
          new DocumentsUploadError(
            application_id,
            fileWithUniqueId.id,
            error instanceof ValidationError && error.issues.length
              ? error.issues[0]
              : null
          )
        );
        return { success: false };
      }
    });
    return uploadPromises;
  };

  /**
   * Download document from the API and sets app errors if any
   */
  const download = async (document: BenefitsApplicationDocument) => {
    errorsLogic.clearErrors();
    try {
      const response = await documentsApi.downloadDocument(document);
      return response;
    } catch (error) {
      errorsLogic.catchError(error);
    }
  };

  return {
    attach,
    download,
    hasLoadedClaimDocuments,
    isLoadingClaimDocuments,
    documents,
    loadAll,
  };
};

export default useDocumentsLogic;
