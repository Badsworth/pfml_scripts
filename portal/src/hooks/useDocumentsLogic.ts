import {
  DocumentsLoadError,
  DocumentsUploadError,
  ValidationError,
} from "../errors";
import { useMemo, useState } from "react";
import DocumentCollection from "../models/DocumentCollection";
import DocumentsApi from "../api/DocumentsApi";
import assert from "assert";
import useCollectionState from "./useCollectionState";

const useDocumentsLogic = ({ appErrorsLogic }) => {
  /**
   * State representing the collection of documents for the current user.
   * Initialize to empty collection, but will eventually store the document
   * state as API calls are made to fetch the documents on a per-application basis,
   * and as new documents are created.
   *
   * The DocumentCollection from useCollectionState stores all documents together,
   * and we filter documents based on application_id to provide the correct documents
   * to the requesting components.
   */

  const {
    collection: documents,
    addItem: addDocument,
    addItems: addDocuments,
    // @ts-expect-error ts-migrate(2554) FIXME: Expected 1 arguments, but got 0.
  } = useCollectionState(new DocumentCollection());

  const documentsApi = useMemo(() => new DocumentsApi(), []);
  const [loadedApplicationDocs, setLoadedApplicationDocs] = useState([]);

  /**
   * Check if docs for this application have been loaded
   * We use a separate array and state here, rather than using the DocumentCollection,
   * because documents that don't have items won't be represented in the DocumentCollection.
   *
   * @param {string} application_id
   * @returns {boolean}
   */
  const hasLoadedClaimDocuments = (application_id) =>
    loadedApplicationDocs.includes(application_id);

  /**
   * Load all documents for a user's claim
   * This must be called before documents are available
   * @param {string} application_id - application id for claim
   */
  const loadAll = async (application_id) => {
    assert(application_id);
    // if documents already contains docs for application_id, don't load again
    if (hasLoadedClaimDocuments(application_id)) {
      return;
    }
    appErrorsLogic.clearErrors();

    try {
      const { documents: loadedDocuments } = await documentsApi.getDocuments(
        application_id
      );

      setLoadedApplicationDocs((loadedApplicationDocs) => [
        ...loadedApplicationDocs,
        application_id,
      ]);
      addDocuments(loadedDocuments.items);
    } catch (error) {
      appErrorsLogic.catchError(new DocumentsLoadError(application_id));
    }
  };

  /**
   * Submit files to the API and set application errors if any
   * @param {string} application_id - application id for claim
   * @param {{id:string, file:File}[]} filesWithUniqueId - array of objects including unique Id and File to upload and attach to the application
   * @param {string} documentType - category of documents
   * @param {boolean} mark_evidence_received - Set the flag used to indicate whether
   * the doc is ready for review or not. Docs added to a claim that was completed
   * through a channel other than the Portal require this flag being set to `true`.
   * @returns {Promise[]}
   */
  const attach = (
    application_id,
    filesWithUniqueId = [],
    documentType,
    mark_evidence_received
  ) => {
    assert(application_id);
    appErrorsLogic.clearErrors();

    if (!filesWithUniqueId.length) {
      appErrorsLogic.catchError(
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
      return;
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
        appErrorsLogic.catchError(
          new DocumentsUploadError(
            application_id,
            fileWithUniqueId.id,
            error.issues ? error.issues[0] : null
          )
        );
        return { success: false };
      }
    });
    return uploadPromises;
  };

  /**
   * Download document from the API and sets app errors if any
   * @param {Document} document - Document instance to download
   * @returns {Blob}
   */
  const download = async (document) => {
    appErrorsLogic.clearErrors();
    try {
      const response = await documentsApi.downloadDocument(document);
      return response;
    } catch (error) {
      appErrorsLogic.catchError(error);
    }
  };

  return {
    attach,
    download,
    hasLoadedClaimDocuments,
    documents,
    loadAll,
  };
};

export default useDocumentsLogic;
