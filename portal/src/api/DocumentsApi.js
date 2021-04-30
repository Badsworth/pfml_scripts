import BaseApi, {
  createRequestUrl,
  getAuthorizationHeader,
  handleError,
  handleNotOkResponse,
} from "./BaseApi";
import Document from "../models/Document";
import DocumentCollection from "../models/DocumentCollection";
import assert from "assert";
import routes from "../routes";

/**
 * @typedef {object} DocumentApiSingleResult
 * @property {Document} document - If the request succeeded, this will contain the created claim
 */

/**
 * @typedef {object} DocumentApiListResult
 * @property {DocumentCollection} [documents] - If the request succeeded, this will contain a list of documents
 */

/**
 * @typedef {{ blob: Blob }} DocumentResponse
 * @property {Blob} blob - Document data
 */

export default class DocumentsApi extends BaseApi {
  get basePath() {
    return routes.api.applications;
  }

  get i18nPrefix() {
    return "documents";
  }

  /**
   * Submit documents one at a time
   *
   * Corresponds to this API endpoint: /application/{application_id}/documents
   * @param {string} application_id ID of the Claim
   * @param {File} file - The File object to upload
   * @param {string} document_type type of documents
   * @param {boolean} mark_evidence_received - Set the flag used to indicate whether
   * the doc is ready for review or not. Docs added to a claim that was completed
   * through a channel other than the Portal require this flag being set to `true`.
   * @returns {DocumentApiSingleResult} The result of the API call
   */
  attachDocument = async (
    application_id,
    file,
    document_type,
    mark_evidence_received
  ) => {
    const formData = new FormData();
    formData.append("document_type", document_type);
    if (file.name.includes("Compressed_")) {
      formData.append("description", "Compressed Image");
    }

    assert(file);
    formData.append("file", file);
    formData.append("name", file.name);
    formData.append("mark_evidence_received", mark_evidence_received);

    const { data } = await this.request(
      "POST",
      `${application_id}/documents`,
      formData,
      null,
      { multipartForm: true }
    );

    return {
      document: new Document(data),
    };
  };

  /**
   * Load all documents for an application
   *
   * Corresponds to this API endpoint: /application/{application_id}/documents
   * @param {string} application_id ID of the Claim
   * @returns {DocumentApiListResult} The result of the API call
   */
  getDocuments = async (application_id) => {
    const { data } = await this.request("GET", `${application_id}/documents`);
    let documents = data.map((documentData) => new Document(documentData));
    documents = new DocumentCollection(documents);

    return {
      documents,
    };
  };

  /**
   * Download document
   *
   * Corresponds to this API endpoint: /application/{application_id}/documents/{fineos_document_id}
   * @param {Document} document instance of Document to download
   * @returns {Blob} file data
   */
  downloadDocument = async (document) => {
    assert(document);
    const { application_id, content_type, fineos_document_id } = document;
    const subPath = `${application_id}/documents/${fineos_document_id}`;
    const method = "GET";
    const url = createRequestUrl(method, this.basePath, subPath);
    const authHeader = await getAuthorizationHeader();

    const headers = {
      ...authHeader,
      "Content-Type": content_type,
    };

    let blob, response;
    try {
      response = await fetch(url, { headers, method });
      blob = await response.blob();
    } catch (error) {
      handleError(error);
    }

    if (!response.ok) {
      handleNotOkResponse(url, response);
    }

    return blob;
  };
}
