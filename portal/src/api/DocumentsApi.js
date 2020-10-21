import BaseApi from "./BaseApi";
import Document from "../models/Document";
import DocumentCollection from "../models/DocumentCollection";
import assert from "assert";
import routes from "../routes";

/**
 * @typedef {object} DocumentApiSingleResult
 * @property {Document} document - If the request succeeded, this will contain the created claim
 * @property {number} status - Status code
 * @property {boolean} success - Did the request succeed or fail?
 */

/**
 * @typedef {object} DocumentApiListResult
 * @property {DocumentCollection} [documents] - If the request succeeded, this will contain a list of documents
 * @property {number} status - Status code
 * @property {boolean} success - Did the request succeed or fail?
 */

export default class DocumentsApi extends BaseApi {
  get basePath() {
    return routes.api.claims;
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
   * @returns {DocumentApiSingleResult} The result of the API call
   */
  attachDocument = async (application_id, file, document_type) => {
    const formData = new FormData();
    formData.append("document_type", document_type);
    formData.append("description", "Placeholder");

    assert(file);
    formData.set("file", file);
    formData.set("name", file.name);

    const { data, status, success } = await this.request(
      "POST",
      `${application_id}/documents`,
      formData,
      null,
      { multipartForm: true }
    );

    return {
      document: success ? new Document(data) : null,
      status,
      success,
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
    const { data, status, success } = await this.request(
      "GET",
      `${application_id}/documents`
    );
    let documents = null;
    if (success) {
      documents = data.map((documentData) => new Document(documentData));
      documents = new DocumentCollection(documents);
    }

    return {
      documents,
      success,
      status,
    };
  };
}
