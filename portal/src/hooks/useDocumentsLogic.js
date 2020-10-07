import { useMemo, useState } from "react";
import DocumentCollection from "../models/DocumentCollection";
import DocumentsApi from "../api/DocumentsApi";
import assert from "assert";
import useCollectionState from "./useCollectionState";

const useDocumentsLogic = ({ appErrorsLogic, portalFlow }) => {
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
  } = useCollectionState(new DocumentCollection([]));

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
  const load = async (application_id) => {
    assert(application_id);
    // if documents already contains docs for application_id, don't load again
    if (hasLoadedClaimDocuments(application_id)) {
      return;
    }
    appErrorsLogic.clearErrors();

    try {
      const {
        documents: loadedDocuments,
        success,
      } = await documentsApi.getDocuments(application_id);
      if (success) {
        setLoadedApplicationDocs((loadedApplicationDocs) => [
          ...loadedApplicationDocs,
          application_id,
        ]);
        addDocuments(loadedDocuments.items);
      }
    } catch (error) {
      appErrorsLogic.catchError(error);
    }
  };

  /**
   * Submit files to the API and set application errors if any
   * @param {string} application_id - application id for claim
   * @param {Array} files - array of objects {id: string, file: File object}
   * @param {string} documentType - category of documents
   */
  const attach = async (application_id, files, documentType) => {
    assert(application_id);
    appErrorsLogic.clearErrors();

    try {
      const { success, document } = await documentsApi.attachDocuments(
        application_id,
        files,
        documentType
      );
      if (success) {
        if (!hasLoadedClaimDocuments(application_id)) {
          await load(application_id);
        } else {
          addDocument(document);
        }
        const context = {};
        const params = { claim_id: application_id };
        portalFlow.goToNextPage(context, params);
      }
    } catch (error) {
      appErrorsLogic.catchError(error);
    }
  };

  return {
    attach,
    hasLoadedClaimDocuments,
    documents,
    load,
  };
};

export default useDocumentsLogic;
